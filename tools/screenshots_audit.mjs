// Screenshots de todas las pantallas para auditar visualmente un cambio de UI.
// Corre contra la app en modo navegador (start.bat / python main.py --navegador), no contra la ventana.
// Uso:  node tools/screenshots_audit.mjs [fecha-iso]
// Salida: screenshots/ en la raíz del repo (gitignoreada).
import { chromium } from 'playwright';
import { mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const BASE_URL = 'http://127.0.0.1:5000';
const ROOT     = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT_DIR  = join(ROOT, 'screenshots');

// Fecha de referencia: la del día a fotografiar (conviene una con datos cargados).
const DAY   = process.argv[2] || new Date().toISOString().slice(0, 10);
const [Y, M] = DAY.split('-');

mkdirSync(OUT_DIR, { recursive: true });

const pages = [
  { name: '01_mes',        path: `/calendar/${Y}/${Number(M)}` },
  { name: '02_semana',     path: `/week/${DAY}` },
  { name: '03_dia',        path: `/day/${DAY}` },
  { name: '04_rutinas',    path: '/recurring' },
  { name: '05_journal',    path: '/journal' },
  { name: '06_stats',      path: '/estadisticas' },
  { name: '06b_tareas',    path: '/tareas' },
  { name: '07_export',     path: '/export' },
  { name: '08_ajustes',    path: '/ajustes' },
  { name: '09_buscar',     path: '/search?q=a' },
];

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  for (const p of pages) {
    const url = BASE_URL + p.path;
    console.log(`Navegando a ${url} ...`);
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(800);
      const file = join(OUT_DIR, p.name + '.png');
      await page.screenshot({ path: file, fullPage: true });
      console.log(`  ✓ ${file}`);
    } catch (e) {
      console.error(`  ✗ Error en ${url}: ${e.message}`);
    }
  }

  // Extra: la vista del día con el formulario de nota rápida y el selector de color abiertos.
  console.log(`\nExtras: interacciones en /day/${DAY}...`);
  try {
    await page.goto(`${BASE_URL}/day/${DAY}`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);

    if (await page.locator('textarea').count() > 0) {
      await page.screenshot({ path: join(OUT_DIR, '03b_dia_textarea.png'), fullPage: true });
      console.log('  ✓ 03b_dia_textarea.png');
    }

    const colorPicker = page.locator('[data-color], .color-btn, .color-circle, input[type="color"]');
    if (await colorPicker.count() > 0) {
      await colorPicker.first().click();
      await page.waitForTimeout(400);
      await page.screenshot({ path: join(OUT_DIR, '03c_dia_color.png'), fullPage: true });
      console.log('  ✓ 03c_dia_color.png');
    }
  } catch (e) {
    console.error(`  ✗ Error en extras del día: ${e.message}`);
  }

  // Extra: el modal de la rueda de emociones (se abre desde Notas especiales).
  console.log('\nExtras: rueda de emociones...');
  try {
    await page.goto(`${BASE_URL}/journal`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: join(OUT_DIR, '05b_journal_categorias.png'), fullPage: true });
    console.log('  ✓ 05b_journal_categorias.png');
  } catch (e) {
    console.error(`  ✗ Error en extras de journal: ${e.message}`);
  }

  await browser.close();
  console.log('\n✓ Listo.');
}

run().catch(console.error);
