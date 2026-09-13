// Auditoría del refresco entre ventanas, pantalla por pantalla y de punta a punta.
//
// Por qué existe: el modo de falla de esta feature es callado. La ventana se ve perfecta y
// muestra datos viejos, sin error ni señal. Así vivieron rotas SEIS de las catorce pantallas
// —todas las que tenían un campo que el JS rellena al cargar— hasta que el usuario lo notó
// usando la app. Los tests de pytest fijan las condiciones necesarias; esto prueba lo que
// ninguno de ellos puede: que un cambio hecho en una ventana APAREZCA en la otra.
//
// Levanta su propio servidor con base temporal (tools/servidor_prueba.py), así que no toca los
// datos de nadie.
//
// Uso:  node tools/refresco_audit.mjs
// Necesita playwright instalado (npm i playwright), igual que screenshots_audit.mjs.
import { chromium } from 'playwright';
import { spawn } from 'child_process';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const PUERTO = 5199;
const BASE = `http://127.0.0.1:${PUERTO}`;
const HOY = new Date().toISOString().slice(0, 10);
const [Y, M] = HOY.split('-');

// Cuánto se le da al poleo (3 s) para traer el cambio.
const ESPERA = 9000;

const PANTALLAS = [
  { nombre: 'día',              path: `/day/${HOY}` },
  { nombre: 'mes',              path: `/calendar/${Y}/${Number(M)}` },
  { nombre: 'semana',           path: `/week/${HOY}` },
  { nombre: 'rutinas',          path: '/recurring' },
  { nombre: 'notas especiales', path: '/journal' },
  { nombre: 'estadísticas',     path: '/estadisticas' },
  { nombre: 'tareas',           path: '/tareas' },
  { nombre: 'buscar',           path: '/search' },
  { nombre: 'ajustes',          path: '/ajustes' },
  { nombre: 'datos',            path: '/export' },
  { nombre: 'versión',          path: '/version' },
  { nombre: 'widget · nota',    path: '/widget?p=nota' },
  { nombre: 'widget · tareas',  path: '/widget?p=tareas' },
  { nombre: 'widget · mes',     path: '/widget?p=calendario' },
];

function python() {
  const venv = join(ROOT, 'venv', 'Scripts', 'python.exe');
  if (existsSync(venv)) return venv;
  const venvNix = join(ROOT, 'venv', 'bin', 'python');
  if (existsSync(venvNix)) return venvNix;
  return 'python';
}

async function esperarServidor(ms = 30000) {
  const hasta = Date.now() + ms;
  while (Date.now() < hasta) {
    try {
      const r = await fetch(BASE + '/refresco');
      if (r.ok) return true;
    } catch { /* todavía no levantó */ }
    await new Promise((r) => setTimeout(r, 400));
  }
  return false;
}

async function run() {
  const servidor = spawn(python(), [join(ROOT, 'tools', 'servidor_prueba.py'), String(PUERTO)],
                         { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
  let salidaServidor = '';
  servidor.stdout.on('data', (d) => { salidaServidor += d; });
  servidor.stderr.on('data', (d) => { salidaServidor += d; });

  if (!await esperarServidor()) {
    console.error('El servidor de prueba no levantó:\n' + salidaServidor);
    servidor.kill();
    return 2;
  }

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const resultados = [];

  for (const p of PANTALLAS) {
    const mirada = await ctx.newPage();      // la ventana que tiene que enterarse
    const escribe = await ctx.newPage();     // la que hace el cambio
    try {
      await mirada.goto(BASE + p.path, { waitUntil: 'load' });
      await mirada.waitForTimeout(700);
      // Una marca que no sobrevive a una recarga: es cómo se detecta que recargó.
      await mirada.evaluate(() => { window.__sinRecargar = true; });

      // El cambio va por HTTP desde la otra página, que es el caso real: otra ventana.
      await escribe.goto(BASE + `/day/${HOY}`, { waitUntil: 'load' });
      await escribe.evaluate(async (fecha) => {
        const cuerpo = new URLSearchParams({ content: 'auditoría ' + Date.now(), color: '' });
        await fetch(`/day/${fecha}/note/add`, { method: 'POST', body: cuerpo });
      }, HOY);

      await mirada.waitForTimeout(ESPERA);
      const refresco = await mirada.evaluate(() => ({
        recargo: window.__sinRecargar !== true,
        aviso: !!document.querySelector('.refresco-aviso'),
      }));
      // Vale cualquiera de las dos: recargó sola, o avisó para que lo hagas vos.
      resultados.push({ ...p, ...refresco, ok: refresco.recargo || refresco.aviso });
    } catch (e) {
      resultados.push({ ...p, ok: false, error: String(e).slice(0, 80) });
    } finally {
      await mirada.close();
      await escribe.close();
    }
  }

  await browser.close();
  servidor.kill();

  const ancho = Math.max(...PANTALLAS.map((p) => p.nombre.length));
  console.log('');
  for (const r of resultados) {
    const como = r.recargo ? 'se refrescó sola' : r.aviso ? 'avisó (había un borrador)' :
                 r.error ? r.error : 'NO SE ENTERÓ';
    console.log(`  ${r.ok ? 'ok  ' : 'MAL '} ${r.nombre.padEnd(ancho)}  ${como}`);
  }

  const malas = resultados.filter((r) => !r.ok);
  console.log('');
  if (malas.length) {
    console.log(`${malas.length} de ${resultados.length} pantallas no se enteran de los cambios` +
                ' de la otra ventana.');
    return 1;
  }
  console.log(`Las ${resultados.length} pantallas se enteran de los cambios de la otra ventana.`);
  return 0;
}

run().then((c) => process.exit(c)).catch((e) => { console.error(e); process.exit(2); });
