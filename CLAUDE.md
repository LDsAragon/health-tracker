# Bitácora — CLAUDE.md

Diario personal de hábitos y salud. App de escritorio cross-platform (Windows + Linux) construida con Flask + pywebview. Sin backend remoto, sin cuentas: todo local en SQLite.

## Stack

- **Python**: Flask (app factory en `app.py`), pywebview para la ventana nativa
- **Renderer**: Edge WebView2 (Windows) / WebKitGTK vía PyGObject (Linux)
- **Frontend**: Jinja2 + vanilla JS + Chart.js (vendorizado en `static/js/vendor/`); sin bundler, sin framework JS
- **DB**: SQLite (`database/conn.py`); `get_db()` lee `DB_PATH` dinámicamente (los tests lo parchean)
- **Tema**: CSS variables en `static/css/base.css`; `data-theme` en `<html>`; 8 temas en `appconfig.py`

## Estructura

```
app.py                  # Flask app factory (create_app)
desktop.py              # Entrada pywebview; auto-backup diario; APP_DIR por plataforma
appconfig.py            # THEMES, SETTINGS y PET_ART (fuente única de defaults)
services.py             # Presentación compartida: events_by_date, journal_badges y, para el
                        #   visor de tareas, overdue_buckets / todos_overview / overdue_cutoff
helpers.py              # _setting, _week_start, _dow_names, MESES[], _fmt_clock, safe_back
filters.py              # Filtros Jinja2 (humantime, fechacorta, dur_fmt, rango_fmt)
fieldtypes.py           # Catálogo de tipos de campo de notas especiales
updater.py              # Auto-actualización via GitHub Releases (check/download/apply)
notify.py               # Notificación del escritorio (toast WinRT vía PowerShell / notify-send)

database/               # Paquete; __init__.py re-exporta todo (`import database as db`)
  conn.py               # get_db, snapshot_to, backup_path, is_valid_db, reset_db, restore_from
  schema.py             # SCHEMA + MIGRATIONS declarativas (idempotente)
  stats.py              # Motor de series de Estadísticas: build_series, grouped_series,
                        #   chartable_fields, y time_summary() para "Tiempo por actividad"
  journal.py            # Categorías + entradas de notas especiales; migrate_entry_values
  notes.py / events.py / charts.py / settings.py
  todos.py              # Tareas por día + el motor del visor: get_overdue_todos,
                        #   count_overdue_todos, snooze_todo, move_todos, get_todos_filtered

routes/
  main.py               # / (home según start_view), /calendar/<año>/<mes>, /week/<fecha>,
                        #   /search, /ajustes[/guardar], /version, /estadisticas[/grafico/...],
                        #   /export[/download], /backup, /restore, /reset
  day.py                # /day/<fecha> y todas las acciones del día; /todos/<id>/move (AJAX)
  todos.py              # /tareas (visor) + acciones sobre atrasadas + /tareas/alerta (JSON)
  recurring.py          # /recurring/* (rutinas)
  journal.py            # /journal/* (notas especiales + categorías)
  update.py             # /update/* (auto-actualización: status/check/download/progress/apply/quit)

templates/              # base.html → herencia; _macros.html para date_field
                        # calendar.html, week.html, day.html, journal.html, recurring.html,
                        # stats.html, search.html, export.html ("Datos"), settings.html,
                        # todos.html (visor de tareas),
                        # version.html (tab 🔄 Versión: chequeo manual + changelog)
static/css/             # base.css, calendar.css, day.css, pages.css, wheel.css
static/js/
  zoom.js               # Zoom Ctrl+rueda / Ctrl±, persistido en localStorage
  date-es.js            # Campo de fecha con formato configurable (hidden ISO para el backend)
  day.js / stats.js     # JS de la vista del día y del constructor de gráficos
  field-registry.js     # window.FIELD_BUILDERS: tipo → builder (despacho único)
  field-blocks.js       # Builders escala / sino / opciones / numero
  time-fields.js        # Builders duracion / rango
  emotion-wheel*.js     # Rueda Willcox (3 niveles) + su contenido psicológico
  ekman-wheel*.js       # Rueda Ekman (Atlas of Emotions, 2 niveles) + contenido
  emotion-wheel-visual.js  # Render SVG data-driven, común a ambas ruedas
  emotion-guided.js     # Exploración guiada (árbol de decisión, tercer tab del modal)
  vendor/               # chart.umd.min.js
docs/                   # manual.html → Bitacora-Manual.pdf (tools/make_manual.ps1,
                        #   shipeado en zip/tar.gz); LEEME.txt y LEEME-Linux.txt
tools/                  # Builds (make_release*.ps1|sh, publish_release.ps1), instalador y
                        #   launcher Linux (linux/), smoke tests, make_icon.py, compare_dbs.py,
                        #   screenshots_audit.mjs (Playwright, auditoría visual de todas las pantallas)
```

## Datos de usuario

| Plataforma | Ruta de la DB |
|------------|---------------|
| Windows    | `%LOCALAPPDATA%\Bitacora\health.db` |
| Linux      | `~/.local/share/Bitacora/health.db` |

Todos los backups (diarios + pre-operación) van a `<dir DB>/backups/` via `backup_path(prefix)` en `conn.py`.

Prefijos de backup:
- `health-auto-<date>` — diario automático (rotación a 7, gestionado en `desktop.py`)
- `health-preupdate-<ts>` — antes de aplicar una auto-actualización
- `health-prereset-<ts>` — antes de borrar todo
- `health-prerestore-<ts>` — antes de restaurar un backup externo
- `health-prerename-<ts>` — antes de migrar renombres de campos/opciones

## Tests

```bash
pytest tests/          # 278 tests, ~9s
```

Los tests parchean `database.conn.DB_PATH` para usar una DB temporal. **No mockear SQLite** — los tests tocan una DB real en `tmp_path`. Correr en venv Windows normal (no WSL).

Smoke tests fuera de pytest (necesitan display / ventana real): `tools/smoke_desktop.py` (migración de primer arranque, headless), `tools/smoke_download_linux.py` (descargas en GTK), `tools/snap_settings.py` (screenshot en WebKitGTK para bugs de rendering que no se reproducen en Windows).

## Build y release

**Windows** — PyInstaller:
```powershell
.\publicar.bat           # build + upload a GitHub Releases
# o solo el build:
powershell -File tools\make_release.ps1
```
Ojo: `Bitacora.exe` debe estar cerrada antes del build (`make_release.ps1` aborta si detecta el proceso). El zip lleva la carpeta `Bitacora`, `docs/LEEME.txt` y `docs/Bitacora-Manual.pdf`; el PDF se regenera aparte con `tools\make_manual.ps1` (Edge headless) cuando cambia `docs/manual.html`.

**Linux** — tarball con instalador:
```bat
release-linux.bat        # llama a WSL → tools/make_release_linux.sh
```
El tarball incluye `tools/linux/instalar.sh` (detecta apt/dnf/pacman) y `tools/linux/bitacora.sh` (launcher con env vars).

**Publicar a GitHub Releases** (ambas plataformas):
```powershell
.\publicar.bat
# re-publicar un tag existente:
powershell -File tools\publish_release.ps1 -Tag v2026-06-12.1
```

**CI**: `.github/workflows/ci.yml` — pytest + tarball Linux como artifact, corre en push/PR a main.

## Tareas y tareas atrasadas

Una tarea pertenece a **un** día (`todos.todo_date`) y **nunca se mueve sola**: si queda sin cerrar
se queda en su fecha hasta que el usuario la traiga a hoy, posponga el aviso o la borre. Arrastrarlas
automáticamente reescribiría datos históricos sobre una suposición (mismo criterio que los renombres).

- `done_at` — timestamp local del cierre; el toggle lo setea y lo borra al reabrir.
- `snoozed_until` — fecha ISO hasta la que la tarea no cuenta como atrasada. Es el "posponer el
  aviso" **sin** tocar `todo_date`.
- Qué es "atrasada": `services.overdue_cutoff(hoy, modo, _week_start)` → con `todo_overdue_from=week`
  (default) el corte es el inicio de la semana en curso; con `day`, hoy. El corte es exclusivo.
- Avisos, en escalera por el ajuste `todo_alert` (`off` → `badge` → `modal`): contador en el navbar
  (`overdue_count`, inyectado por el context processor de `app.py`; con `off` no paga la query) y
  modal al arrancar (`#todo-modal` en `base.html`, una vez por arranque vía `sessionStorage`).
- "Empezó una semana nueva" sale de comparar el lunes actual contra la clave
  `appconfig.LAST_WEEK_SEEN_KEY` en la tabla `settings`. **Esa clave va fuera de `SETTINGS`** a
  propósito: `get_all_settings()` clampea contra `choices` solo lo que está en el esquema, así que
  una fecha ISO libre sobreviviría igual.
- El bloque de atrasadas ignora el filtro de período (lo viejo se avisa siempre); período y estado
  solo acotan el listado de abajo. Los contadores se calculan sobre todo el período **sin** filtrar
  por estado — si no, con "Pendientes" el contador de hechas daría siempre 0.
- El filtro de tiempo se llama `periodo` (en la URL y en el código), nunca "rango": la palabra suena
  antinatural en la UI. El título del listado dice el período en palabras ("Tareas de los últimos
  3 meses"), que sale de la tercera columna de `routes.todos.PERIODOS`.

## Auto-actualización

`updater.py` + `routes/update.py` — chequea GitHub Releases (`LDsAragon/health-tracker`) en un hilo daemon al arrancar (`check_in_background()` desde `desktop.py`). Flujo: `/update/status` → `/update/download` → `/update/progress` → `/update/apply` (backup DB → extrae asset → lanza script externo) → `/update/quit`. UI en `base.html` + `static/css/pages.css`.

- La versión sale de `_version.py`, **generado por el build** e incluido en el bundle (no está en el repo). En modo dev no existe → `current_version()` devuelve `None` y el updater no corre.
- Comparación de versiones por tupla: `v2026-06-12.1` → `(2026, 6, 12, 1)` (`_version_tuple`).
- Chequeo bajo demanda desde el tab 🔄 Versión (`/version`): `POST /update/check` → `force_check()` (mismo `_do_check`, pero sin exigir versión propia). El front poletea `/update/status` hasta `checked: true` y reusa `updateShowModal()` de `base.html` para instalar o reinstalar.
- `changelog(body)` parsea el cuerpo del release que arma `publish_release.ps1` (bullets de commits; corta en el `---` que separa las instrucciones de instalación).
- ⚠️ **`available` y `can_reinstall` exigen `current_version()`**: `apply_update()` copia sobre `_base_dir()`, que en dev es el repo, y en Windows con `robocopy /MIR`. Sin esa guarda, un chequeo forzado en dev habilitaría un botón que borra el repo.

## Convenciones de código

- Mensajes de commit en español, prefijo minúscula: `fix:`, `stats:`, `journal:`, `linux:`, etc.
- Sin `Co-Authored-By` en los commits.
- Sin comentarios que expliquen el *qué* — solo el *por qué* cuando no es obvio.
- `MESES[]` hardcodeado en `helpers.py` (no `calendar.month_name` — depende del locale del sistema).
- Renames de datos de usuario: solo con señal explícita (hidden `field_oldlabel[]` o control de UI); nunca por heurística.
- **Agregar un ajuste**: una entrada en `appconfig.SETTINGS` (default + choices). `settings_save()` itera el esquema y valida contra `choices`; no hay que tocar la ruta.
- **Agregar un tipo de campo**: entrada en `fieldtypes.FIELD_TYPES` + builder registrado en `static/js/field-registry.js` + su display en `day.html`.
- Los valores de las entradas se guardan como `{etiqueta: valor}` en `values_json` — por eso renombrar un campo obliga a `migrate_entry_values()` (que además re-clava las etiquetas en la tabla `charts`).

## Quirks conocidos

- **Linux / WebKitGTK**: exportar `PYWEBVIEW_GUI=gtk` y `WEBKIT_DISABLE_DMABUF_RENDERER=1` (lo hace `bitacora.sh`).
- **Linux / WebKitGTK**: `color-scheme: dark/light` en CSS controla el rendering de `<select>` nativos (sin esto salen con tema GTK del sistema, blanco sobre blanco en tema oscuro).
- **Linux / descargas**: `webview.settings["ALLOW_DOWNLOADS"] = True` es necesario (está en `desktop.py`); por defecto pywebview cancela descargas silenciosamente.
- **Arch / keyring**: `instalar.sh` detecta keyring sin inicializar chequeando `/etc/pacman.d/gnupg/trustdb.gpg` (no solo el directorio — el dir puede existir vacío).
- **Windows / Mark of the Web**: si el zip viajó por internet, .NET se niega a cargar `Python.Runtime.dll`. `desktop.py::_unblock_dlls()` borra el stream `Zone.Identifier` de las DLLs de `_internal/` en cada arranque; el updater hace lo mismo tras copiar los archivos nuevos.
- **pywebview / localStorage**: `webview.start(private_mode=False, storage_path=...)` — sin eso pywebview borra el zoom y el tamaño de celdas al cerrar.
- **DB path en tests**: `database.conn.DB_PATH` se parchea directamente; `get_db()` lo lee en cada call.
