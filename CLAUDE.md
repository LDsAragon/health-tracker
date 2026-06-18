# Bitácora — CLAUDE.md

Diario personal de hábitos y salud. App de escritorio cross-platform (Windows + Linux) construida con Flask + pywebview. Sin backend remoto, sin cuentas: todo local en SQLite.

## Stack

- **Python**: Flask (app factory en `app.py`), pywebview para la ventana nativa
- **Renderer**: Edge WebView2 (Windows) / WebKitGTK vía PyGObject (Linux)
- **Frontend**: Jinja2 + vanilla JS + Chart.js; sin bundler, sin framework JS
- **DB**: SQLite (`database/conn.py`); `get_db()` lee `DB_PATH` dinámicamente (los tests lo parchean)
- **Tema**: CSS variables en `static/css/base.css`; `data-theme` en `<html>`; 8 temas en `appconfig.py`

## Estructura

```
app.py                  # Flask app factory (create_app)
desktop.py              # Entrada pywebview; auto-backup diario; APP_DIR por plataforma
appconfig.py            # THEMES y SETTINGS (fuente única de defaults)
helpers.py              # _week_start, MESES[], _fmt_clock, safe_back
filters.py              # Filtros Jinja2 (dur_fmt_filter, rango_fmt_filter, etc.)
fieldtypes.py           # Catálogo de tipos de campo de notas especiales

database/
  conn.py               # get_db, snapshot_to, backup_path, reset_db, restore_from
  schema.py             # SCHEMA + MIGRATIONS declarativas (idempotente)
  stats.py              # time_summary() para "Tiempo por actividad"
  journal.py            # Categorías + entradas de notas especiales; migrate_entry_values
  notes.py / events.py / todos.py / charts.py / settings.py

routes/
  main.py               # /  (home/mes), /stats, /export, /backup, /restore, /reset, /settings
  day.py                # /day/<date> y todas las acciones del día
  recurring.py          # /events/* (rutinas)
  journal.py            # /journal/* (notas especiales + categorías)

templates/              # Jinja2; base.html → herencia; _macros.html para date_field
static/css/             # base.css, calendar.css, day.css, pages.css, wheel.css
static/js/              # day.js y JS inline en templates
```

## Datos de usuario

| Plataforma | Ruta de la DB |
|------------|---------------|
| Windows    | `%LOCALAPPDATA%\Bitacora\health.db` |
| Linux      | `~/.local/share/Bitacora/health.db` |

Todos los backups (diarios + pre-operación) van a `<dir DB>/backups/` via `backup_path(prefix)` en `conn.py`.

Prefijos de backup:
- `health-auto-<date>` — diario automático (rotación a 7, gestionado en `desktop.py`)
- `health-prereset-<ts>` — antes de borrar todo
- `health-prerestore-<ts>` — antes de restaurar un backup externo
- `health-prerename-<ts>` — antes de migrar renombres de campos/opciones

## Tests

```bash
pytest tests/
```

Los tests parchean `database.conn.DB_PATH` para usar una DB temporal. **No mockear SQLite** — los tests tocan una DB real en `tmp_path`. Correr en venv Windows normal (no WSL).

## Build y release

**Windows** — PyInstaller:
```powershell
.\publicar.bat           # build + upload a GitHub Releases
# o solo el build:
powershell -File tools\make_release.ps1
```
Ojo: `Bitacora.exe` debe estar cerrada antes del build (PyInstaller falla si está abierta).

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

## Convenciones de código

- Mensajes de commit en español, prefijo minúscula: `fix:`, `stats:`, `journal:`, `linux:`, etc.
- Sin `Co-Authored-By` en los commits.
- Sin comentarios que expliquen el *qué* — solo el *por qué* cuando no es obvio.
- `MESES[]` hardcodeado en `helpers.py` (no `calendar.month_name` — depende del locale del sistema).
- Renames de datos de usuario: solo con señal explícita (hidden `field_oldlabel[]` o control de UI); nunca por heurística.

## Quirks conocidos

- **Linux / WebKitGTK**: exportar `PYWEBVIEW_GUI=gtk` y `WEBKIT_DISABLE_DMABUF_RENDERER=1` (lo hace `bitacora.sh`).
- **Linux / WebKitGTK**: `color-scheme: dark/light` en CSS controla el rendering de `<select>` nativos (sin esto salen con tema GTK del sistema, blanco sobre blanco en tema oscuro).
- **Linux / descargas**: `webview.settings["ALLOW_DOWNLOADS"] = True` es necesario (está en `desktop.py`); por defecto pywebview cancela descargas silenciosamente.
- **Arch / keyring**: `instalar.sh` detecta keyring sin inicializar chequeando `/etc/pacman.d/gnupg/trustdb.gpg` (no solo el directorio — el dir puede existir vacío).
- **DB path en tests**: `database.conn.DB_PATH` se parchea directamente; `get_db()` lo lee en cada call.
