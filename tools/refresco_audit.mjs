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

// Pantallas donde además se prueba lo que este rediseño vino a conseguir: que el cambio entre
// SIN pisar lo que estás escribiendo. Necesitan una zona `data-refresco` que cambie con una nota
// nueva y un campo de texto donde dejar el borrador.
const CON_BORRADOR = [
  { nombre: 'día',    path: `/day/${HOY}`,
    abrir: '#rapida-collapsed', campo: '#rapida-form .day-add-input' },
  { nombre: 'mes',    path: `/calendar/${Y}/${Number(M)}`,
    campo: '.cal-quick-input' },
  { nombre: 'semana', path: `/week/${HOY}`,
    campo: '.cal-quick-input' },
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

// Deja la página lista para detectar qué pasó: una marca que no sobrevive a una recarga, y una
// foto del contenido de cada zona para ver si alguna se actualizó en el lugar.
async function marcar(page) {
  await page.evaluate(() => {
    window.__sinRecargar = true;
    window.__zonas = [...document.querySelectorAll('[data-refresco]')]
      .map((z) => z.getAttribute('data-refresco') + '::' + z.innerHTML);
  });
}

// ⚠️ La prueba fuerte del rediseño: que no haya quedado contenido VIEJO. Si una parte que
// cambia con los datos se quedó fuera de toda zona `data-refresco`, la pantalla se da por al día
// y muestra algo desactualizado — el mismo fallo callado de siempre, en versión chica. Se compara
// el texto visible de <main> contra el que sirve el servidor en este momento.
async function quedoViejo(page) {
  return page.evaluate(async () => {
    if (!document.querySelector('[data-refresco-parcial]')) return { cubierta: false };
    const r = await fetch(location.href, { cache: 'no-store' });
    if (!r.ok) return { cubierta: true };
    const doc = new DOMParser().parseFromString(await r.text(), 'text/html');
    const norm = (n) => (n ? n.textContent.replace(/\s+/g, ' ').trim() : '');
    const mio = norm(document.querySelector('main'));
    const suyo = norm(doc.querySelector('main'));
    if (mio === suyo) return { cubierta: true };
    // Dónde empieza a diferir, que es lo único accionable del reporte.
    let i = 0;
    while (i < mio.length && i < suyo.length && mio[i] === suyo[i]) i++;
    return { cubierta: true,
             diff: { enPantalla: mio.slice(Math.max(0, i - 30), i + 70),
                     enElServidor: suyo.slice(Math.max(0, i - 30), i + 70) } };
  });
}

async function quePaso(page) {
  return page.evaluate(() => {
    const ahora = [...document.querySelectorAll('[data-refresco]')]
      .map((z) => z.getAttribute('data-refresco') + '::' + z.innerHTML);
    const previas = window.__zonas || [];
    const zonaCambio = ahora.length === previas.length &&
                       ahora.some((z, i) => z !== previas[i]);
    return {
      recargo: window.__sinRecargar !== true,
      zonaCambio,
      aviso: !!document.querySelector('.refresco-aviso'),
    };
  });
}

// El cambio va por HTTP desde otra página, que es el caso real: la otra ventana.
//
// Se tocan una nota Y una tarea a propósito: cada pantalla muestra cosas distintas, y con un solo
// tipo de dato quedaban zonas sin ejercitar (la pestaña de tareas del widget no muestra notas, y
// ahí viven el "⚠️ Sin cerrar · N" y el "Nada anotado para hoy", que también tienen que
// actualizarse).
async function hacerCambios(page, marca) {
  await page.evaluate(async ([fecha, t]) => {
    await fetch(`/day/${fecha}/note/add`, {
      method: 'POST', body: new URLSearchParams({ content: 'nota ' + t, color: '' }),
    });
    await fetch(`/day/${fecha}/todo/add`, {
      method: 'POST', body: new URLSearchParams({ text: 'tarea ' + t }),
    });
  }, [HOY, marca]);
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
  const borradores = [];

  // ── 1. ¿Se entera cada pantalla? ────────────────────────────────────────────
  for (const p of PANTALLAS) {
    const mirada = await ctx.newPage();      // la ventana que tiene que enterarse
    const escribe = await ctx.newPage();     // la que hace el cambio
    try {
      await mirada.goto(BASE + p.path, { waitUntil: 'load' });
      await mirada.waitForTimeout(700);
      await marcar(mirada);

      await escribe.goto(BASE + `/day/${HOY}`, { waitUntil: 'load' });
      await hacerCambios(escribe, 'auditoría ' + Date.now());

      await mirada.waitForTimeout(ESPERA);
      const r = await quePaso(mirada);
      const estado = await quedoViejo(mirada);
      const viejo = estado.diff || null;
      // En una pantalla cubierta manda la comparación contra el servidor: estar al día vale
      // aunque no haya cambiado nada visible (una nota nueva no toca la pestaña de tareas del
      // widget). En las demás, que se hayan enterado: actualizando, recargando o avisando.
      const seEntero = r.zonaCambio || r.recargo || r.aviso;
      resultados.push({ ...p, ...r, viejo,
                        ok: estado.cubierta ? !viejo : seEntero });
    } catch (e) {
      resultados.push({ ...p, ok: false, error: String(e).slice(0, 80) });
    } finally {
      await mirada.close();
      await escribe.close();
    }
  }

  // ── 2. ¿Entra el cambio SIN pisar lo que estás escribiendo? ─────────────────
  // Es el objetivo del rediseño, y con `location.reload()` era imposible por definición.
  const BORRADOR = 'esto lo estoy escribiendo';
  for (const p of CON_BORRADOR) {
    const mirada = await ctx.newPage();
    const escribe = await ctx.newPage();
    try {
      await mirada.goto(BASE + p.path, { waitUntil: 'load' });
      await mirada.waitForTimeout(700);
      if (p.abrir) await mirada.click(p.abrir);
      await mirada.fill(p.campo, BORRADOR);
      await marcar(mirada);

      await escribe.goto(BASE + `/day/${HOY}`, { waitUntil: 'load' });
      await hacerCambios(escribe, 'con borrador ' + Date.now());

      await mirada.waitForTimeout(ESPERA);
      const r = await quePaso(mirada);
      const sobrevivio = await mirada.evaluate((sel) => {
        const el = document.querySelector(sel);
        return !!el && el.value === 'esto lo estoy escribiendo';
      }, p.campo);
      borradores.push({ ...p, entro: r.zonaCambio, sobrevivio,
                        ok: r.zonaCambio && sobrevivio });
    } catch (e) {
      borradores.push({ ...p, ok: false, error: String(e).slice(0, 80) });
    } finally {
      await mirada.close();
      await escribe.close();
    }
  }

  await browser.close();
  servidor.kill();

  const ancho = Math.max(...PANTALLAS.map((p) => p.nombre.length));
  console.log('\n  ¿Se entera de los cambios de la otra ventana?\n');
  for (const r of resultados) {
    const como = r.error ? r.error :
                 r.viejo ? 'QUEDÓ CONTENIDO VIEJO' :
                 r.zonaCambio ? 'se actualizó sin recargar' :
                 r.recargo ? 'recargó (fallback)' :
                 r.aviso ? 'avisó (había un borrador)' : 'ya estaba al día';
    console.log(`  ${r.ok ? 'ok  ' : 'MAL '} ${r.nombre.padEnd(ancho)}  ${como}`);
    if (r.viejo) {
      console.log(`         en pantalla: ...${r.viejo.enPantalla}...`);
      console.log(`         el servidor: ...${r.viejo.enElServidor}...`);
    }
  }

  console.log('\n  ¿El cambio entra sin pisar lo que estás escribiendo?\n');
  for (const b of borradores) {
    const como = b.ok ? 'el cambio entró y el borrador quedó intacto' :
                 b.error ? b.error :
                 !b.entro ? 'EL CAMBIO NO ENTRÓ' : 'SE PERDIÓ EL BORRADOR';
    console.log(`  ${b.ok ? 'ok  ' : 'MAL '} ${b.nombre.padEnd(ancho)}  ${como}`);
  }

  const malas = [...resultados, ...borradores].filter((r) => !r.ok);
  console.log('');
  if (malas.length) {
    console.log(`${malas.length} problema(s): ` + malas.map((m) => m.nombre).join(', '));
    return 1;
  }
  console.log(`Las ${resultados.length} pantallas se enteran, y en ${borradores.length} se` +
              ' verificó que el cambio entra sin pisar un borrador.');
  return 0;
}

run().then((c) => process.exit(c)).catch((e) => { console.error(e); process.exit(2); });
