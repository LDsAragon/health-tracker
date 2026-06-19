import { chromium } from 'playwright';
import { mkdirSync, existsSync } from 'fs';
import { join } from 'path';

const BASE_URL = 'http://127.0.0.1:5000';
const OUT_DIR = 'D:/Archivos/Documentos/GitHub/health-tracker/screenshots';

if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });

const pages = [
  { name: '01_mes',         path: '/' },
  { name: '02_semana',      path: '/week' },
  { name: '03_dia',         path: '/day/2026-06-14' },
  { name: '04_eventos',     path: '/events' },
  { name: '05_evento_new',  path: '/events/new' },
  { name: '06_journal',     path: '/journal' },
  { name: '07_journal_new', path: '/journal/new' },
  { name: '08_stats',       path: '/stats' },
  { name: '09_export',      path: '/export' },
  { name: '10_settings',    path: '/settings' },
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
      console.log(`  ✓ Screenshot guardado: ${file}`);
    } catch(e) {
      console.error(`  ✗ Error en ${url}: ${e.message}`);
    }
  }

  // Extra: abrir formulario de nota rápida en /day para ver el selector de color
  console.log('\nExtras: interacciones en /day/2026-06-14...');
  try {
    await page.goto(BASE_URL + '/day/2026-06-14', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);

    // Buscar botón/link para nueva nota rápida o textarea
    const hasQuickNote = await page.locator('textarea, [href*="note"], button:has-text("nota"), a:has-text("nota")').count();
    console.log(`  Elementos de nota encontrados: ${hasQuickNote}`);

    // Screenshot del formulario si hay textarea
    if (await page.locator('textarea').count() > 0) {
      await page.screenshot({ path: join(OUT_DIR, '03b_dia_textarea.png'), fullPage: true });
    }

    // Intentar hacer click en algún elemento de color si existe
    const colorPicker = page.locator('[data-color], .color-btn, .color-circle, input[type="color"]');
    if (await colorPicker.count() > 0) {
      await colorPicker.first().click();
      await page.waitForTimeout(400);
      await page.screenshot({ path: join(OUT_DIR, '03c_dia_color_selected.png'), fullPage: true });
      console.log('  ✓ Screenshot con color seleccionado');
    }
  } catch(e) {
    console.error(`  ✗ Error en extras dia: ${e.message}`);
  }

  // Extra: /events/new - ver el picker de hora
  console.log('\nExtras: /events/new - picker de hora...');
  try {
    await page.goto(BASE_URL + '/events/new', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);
    const timeInputs = page.locator('input[type="time"], select[name*="hora"], select[name*="hour"], input[name*="hora"]');
    const cnt = await timeInputs.count();
    console.log(`  Inputs de hora encontrados: ${cnt}`);
    await page.screenshot({ path: join(OUT_DIR, '05b_evento_new_form.png'), fullPage: true });
  } catch(e) {
    console.error(`  ✗ Error en extras events/new: ${e.message}`);
  }

  // Extra: /journal/new - ver formulario completo
  console.log('\nExtras: /journal/new - formulario...');
  try {
    await page.goto(BASE_URL + '/journal/new', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: join(OUT_DIR, '07b_journal_new_form.png'), fullPage: true });
  } catch(e) {
    console.error(`  ✗ Error en extras journal/new: ${e.message}`);
  }

  await browser.close();
  console.log('\n✓ Todos los screenshots completados.');
}

run().catch(console.error);
