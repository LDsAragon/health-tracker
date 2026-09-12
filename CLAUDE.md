# Bitácora — CLAUDE.md

Diario personal de hábitos y salud. App de escritorio cross-platform (Windows + Linux) construida con Flask + pywebview. Sin backend remoto, sin cuentas: todo local en SQLite.

## Stack

- **Python**: Flask (app factory en `bitacora/app.py`), pywebview para la ventana nativa
- **Renderer**: Edge WebView2 (Windows) / WebKitGTK vía PyGObject (Linux)
- **Frontend**: Jinja2 + vanilla JS + Chart.js (vendorizado en `bitacora/static/js/vendor/`); sin bundler, sin framework JS
- **DB**: SQLite (`bitacora/database/conn.py`); `get_db()` lee `DB_PATH` dinámicamente (los tests lo parchean)
- **Tema**: CSS variables en `bitacora/static/css/base.css`; `data-theme` en `<html>`; 8 temas en `bitacora/appconfig.py`

## Estructura

Todo el código de la app vive en el paquete `bitacora/`; la raíz solo tiene el punto de entrada,
configuración y docs. El paquete de arriba (Flask + SQLite) **no importa nada de
`bitacora/escritorio/`** — es lo que permite correr en el navegador y testear sin display.

```
main.py                 # ÚNICO entry point: ventana, o --navegador para el modo browser.
                        #   Es lo que empaqueta PyInstaller y lo que corren start.bat y el
                        #   launcher de Linux
bitacora/
  app.py                # Flask app factory (create_app) + el context processor global
  appconfig.py          # THEMES, SETTINGS y PET_ART (fuente única de defaults)
  services.py           # Presentación compartida: events_by_date, journal_badges y, para el
                        #   visor de tareas, overdue_buckets / overdue_cutoff / periodo_ventana
  helpers.py            # _setting, _week_start, _dow_names, MESES[], _fmt_clock, safe_back
  filters.py            # Filtros Jinja2 (humantime, fechacorta, dur_fmt, rango_fmt)
  fieldtypes.py         # Catálogo de tipos de campo de notas especiales
  profiles.py           # Perfiles locales: índice perfiles.json, crear/usar/borrar, cambio
                        #   en caliente. Sin HT_PERFILES se desactiva solo (tests, navegador)
  sync.py               # Merge entre dos dispositivos: exportar/analizar/aplicar. El paquete
                        #   es un .db y el merge se resuelve en SQL con ATTACH
  database/             # Paquete; __init__.py re-exporta todo (`from bitacora import database as db`)
    conn.py             # get_db, snapshot_to, backup_path, is_valid_db, reset_db, restore_from
    schema.py           # SCHEMA + MIGRATIONS declarativas (idempotente)
    stats.py            # Motor de series de Estadísticas: build_series, grouped_series,
                        #   chartable_fields, y time_summary() para "Tiempo por actividad"
    journal.py          # Categorías + entradas de notas especiales; migrate_entry_values
    todos.py            # Tareas por día + el motor del visor: get_overdue_todos,
                        #   count_overdue_todos, move_todos, get_todos_filtered
    notes.py / events.py / charts.py / settings.py
  routes/
    main.py             # / (home según start_view), /calendar/<año>/<mes>, /week/<fecha>,
                        #   /search, /ajustes[/guardar|/set], /version, /estadisticas[/grafico/...],
                        #   /export[/download], /backup, /restore, /reset
    day.py              # /day/<fecha> y todas las acciones del día; /todos/<id>/move (AJAX)
    todos.py            # /tareas (visor) + /tareas/agregar + acciones sobre atrasadas
                        #   + /tareas/alerta (JSON)
    perfiles.py         # /perfiles/* (crear, usar, renombrar, borrar)
    sync.py             # /sync/* (exportar, importar, previa, aplicar, descartar)
    widget.py           # /widget (panel chico) + sus acciones, el control de la ventana
                        #   y /instancia/mostrar (la llama una segunda instancia)
    recurring.py        # /recurring/* (rutinas)
    journal.py          # /journal/* (notas especiales + categorías)
    update.py           # /update/* (auto-actualización: status/check/download/progress/apply/quit)
  templates/            # base.html → herencia; _macros.html para date_field
                        # calendar.html, week.html, day.html, journal.html, recurring.html,
                        # stats.html, search.html, export.html ("Datos"), settings.html,
                        # todos.html (visor de tareas), widget.html,
                        # version.html (tab 🔄 Versión: chequeo manual + changelog)
  static/
    css/                # base.css, calendar.css, day.css, pages.css, wheel.css, widget.css
    js/
      zoom.js           # Zoom Ctrl+rueda / Ctrl±, persistido en localStorage
      colapsables.js    # recordarColapsable(): estado de un <details> en localStorage
      ajustes.js        # Guardado al instante de Ajustes; esconde el botón Guardar
      date-es.js        # Campo de fecha con formato configurable (hidden ISO para el backend)
      day.js / stats.js # JS de la vista del día y del constructor de gráficos
      field-registry.js # window.FIELD_BUILDERS: tipo → builder (despacho único)
      field-blocks.js   # Builders escala / sino / opciones / numero
      time-fields.js    # Builders duracion / rango
      emotion-wheel*.js # Rueda Willcox (3 niveles) + su contenido psicológico
      ekman-wheel*.js   # Rueda Ekman (Atlas of Emotions, 2 niveles) + contenido
      emotion-wheel-visual.js  # Render SVG data-driven, común a ambas ruedas
      emotion-guided.js # Exploración guiada (árbol de decisión, tercer tab del modal)
      vendor/           # chart.umd.min.js
  escritorio/           # Solo la app de ventana. Nada del resto del paquete importa de acá.
    main.py             # Arranque pywebview; auto-backup diario; APP_DIR por plataforma;
                        #   arrancar() = main() envuelto en el reporte de errores
    widget.py           # Ventana del widget de escritorio (segunda ventana pywebview)
    tray.py             # Icono en el área de notificación (NotifyIcon vía pythonnet, solo Win)
    instancia.py        # Una sola Bitácora a la vez: lock del SO + aviso por HTTP
    notify.py           # Notificación del escritorio (toast WinRT vía PowerShell / notify-send)
    updater.py          # Auto-actualización via GitHub Releases (check/download/apply)

tests/                  # pytest; conftest.py trae los fixtures test_db y client
docs/                   # manual.html → Bitacora-Manual.pdf (tools/make_manual.ps1,
                        #   shipeado en zip/tar.gz); LEEME.txt y LEEME-Linux.txt
tools/                  # Builds (make_release*.ps1|sh, publish_release.ps1), instalador y
                        #   launcher Linux (linux/), smoke tests, make_icon.py, compare_dbs.py,
                        #   screenshots_audit.mjs (Playwright, auditoría visual de las pantallas)
  andamios/             # `hacer.ps1 nuevo ...`: ajuste.py, campo.py, ruta.py + comun.py
                        #   (leer/escribir/insertar en ancla). Ver § Convenciones
hacer.ps1               # Un solo lugar para todos los comandos; sin argumentos los lista
start.bat               # Doble clic: abre en el navegador y crea el venv la primera vez
```

**Cómo leer las rutas en este documento**: de acá para abajo, una ruta sin prefijo es **relativa a
`bitacora/`** (`app.py` = `bitacora/app.py`, `routes/day.py` = `bitacora/routes/day.py`). Las de
`tests/`, `tools/`, `docs/` y `main.py` se escriben completas. Hay tres nombres repetidos a los que
conviene prestar atención: `main.py` (el de la raíz vs. `escritorio/main.py`), `sync.py` (`sync.py`
vs. `routes/sync.py`) y `widget.py` (`escritorio/widget.py` vs. `routes/widget.py`).

⚠️ **`templates/` y `static/` tienen que estar dentro del paquete**, al lado de `app.py`:
`Flask(__name__)` las resuelve relativo al módulo. Congelada es al revés — `app.py` pasa rutas
explícitas bajo `sys._MEIPASS`, y por eso `--add-data` las deja en la **raíz** del bundle
(`bitacora/templates;templates`), no en `_MEIPASS/bitacora/`.

## Datos de usuario

| Plataforma | Carpeta de datos (`APP_DIR`) |
|------------|------------------------------|
| Windows    | `%LOCALAPPDATA%\Bitacora\` |
| Linux      | `~/.local/share/Bitacora/` |

Desde sep 2026 hay **perfiles**: la DB no está en la raíz de `APP_DIR` sino en
`perfiles/<slug>/health.db`, y el índice (`perfiles.json`) dice cuál está activo. `webview/` y
`error.log` siguen siendo del dispositivo, no del perfil.

Todos los backups (diarios + pre-operación) van a `<dir DB>/backups/` via `backup_path(prefix)` en
`conn.py`. Como esa ruta se deriva de `DB_PATH`, **cada perfil obtiene su propia carpeta de backups
sin código extra**.

Prefijos de backup:
- `health-auto-<date>` — diario automático (rotación a 7, gestionado en `bitacora/escritorio/main.py`)
- `health-preupdate-<ts>` — antes de aplicar una auto-actualización
- `health-prereset-<ts>` — antes de borrar todo
- `health-prerestore-<ts>` — antes de restaurar un backup externo
- `health-prerename-<ts>` — antes de migrar renombres de campos/opciones
- `health-preborrado-<slug>-<ts>` — antes de borrar todos los perfiles. **Este va a
  `APP_DIR/backups/`, no al del perfil**: la carpeta del perfil es justo lo que se borra
- `health-preperfiles-<ts>` — antes de mudar la DB al layout de perfiles

## Tests

```powershell
.\hacer.ps1 tests              # 482 tests, ~27s (o `pytest tests/` directo)
.\hacer.ps1 tests -k ajustes   # los argumentos pasan tal cual a pytest
```

Los tests parchean `bitacora.database.conn.DB_PATH` para usar una DB temporal. **No mockear SQLite** — los tests tocan una DB real en `tmp_path`. Correr en venv Windows normal (no WSL).

Smoke tests fuera de pytest, porque necesitan display o ventana real — todos vía
`.\hacer.ps1 smoke <cual>`:

| `smoke …` | Qué cubre |
|---|---|
| `widget` | widget + bandeja: abre ventanas de verdad y se cierra solo |
| `instancia` | lanza dos y tres Bitácoras reales y verifica que sobreviva una sola |
| `desktop` | migración de primer arranque (headless) |
| `descargas` | descargas en GTK (solo Linux) |
| `captura` | screenshot en WebKitGTK, para bugs de rendering que no se ven en Windows |

## Comandos: `hacer.ps1`

**Todos los comandos del proyecto salen de un solo lugar.** Sin argumentos los lista:

```powershell
.\hacer.ps1                          # lista todo con su descripción
.\hacer.ps1 tests -k ajustes         # los argumentos pasan tal cual
.\hacer.ps1 smoke instancia
.\hacer.ps1 build
.\hacer.ps1 publicar -Aviso "..."
```

`hacer.ps1` **no duplica lógica**: cada subcomando despacha al script de `tools/` que ya hacía el
trabajo, así que seguir llamándolos directo funciona igual. Lo único que agrega es el chequeo del
venv y la instalación de `pywebview` en `abrir` (lo que hacía `desktop.bat`).

`start.bat` se queda aparte a propósito: es el doble clic para abrir en el navegador y **crea el
venv la primera vez**, así que es también el arranque desde cero. El manual lo documenta.

Se fueron `desktop.bat`, `release.bat`, `release-linux.bat` y `publicar.bat` (eran wrappers de una
línea) y `build_exe.bat`, que llamaba a PyInstaller **sin generar `_version.py`**: el `.exe` que
armaba se quedaba sin versión y el updater no corría.

## Build y release

**Windows** — PyInstaller (`.\hacer.ps1 build` → `tools\make_release.ps1`):
Ojo: `Bitacora.exe` debe estar cerrada antes del build (`make_release.ps1` aborta si detecta el
proceso). El zip lleva la carpeta `Bitacora`, `docs/LEEME.txt` y `docs/Bitacora-Manual.pdf`; el PDF
se regenera aparte con `.\hacer.ps1 manual` (Edge headless) cuando cambia `docs/manual.html`.

⚠️ **El entry point del build es `main.py`, no el paquete**, y `--add-data` deja `templates/` y
`static/` en la **raíz** del bundle (`bitacora/templates;templates`) porque ahí las busca la rama
congelada de `create_app()`.

**Linux** — tarball con instalador (`.\hacer.ps1 build-linux` → WSL → `tools/make_release_linux.sh`):
El tarball incluye `tools/linux/instalar.sh` (detecta apt/dnf/pacman) y `tools/linux/bitacora.sh`
(launcher con env vars, ejecuta `main.py`). Copia `main.py` + el paquete `bitacora/` entero, sin
lista de módulos: una lista explícita se desactualiza sola (`updater.py` faltó desde `v2026-06-25`
y la app de Linux ni arrancaba, y por eso el CI verifica que el tarball importe).

**Publicar a GitHub Releases** (ambas plataformas): `.\hacer.ps1 publicar`.
⚠️ **Sin `-Tag`, el script busca el primer sufijo libre del día** (`.1`, `.2`, …) y avisa cuál
eligió. Antes usaba `v<fecha>` a secas y, con un release del día ya publicado, le reemplazaba los
archivos y las notas en silencio — y encima ese tag compara **menor** que el del día con sufijo
(`_version_tuple`: `(2026,9,12) < (2026,9,12,2)`), así que el release nuevo no se le ofrecía a
nadie. La rama que reemplaza sigue existiendo, pero solo se llega pasando `-Tag` a propósito.

**CI**: `.github/workflows/ci.yml` — pytest + tarball Linux como artifact, corre en push/PR a main.

## Tareas y tareas atrasadas

Una tarea pertenece a **un** día (`todos.todo_date`) y **nunca se mueve sola**: si queda sin cerrar
se queda en su fecha hasta que el usuario la mueva o la borre. Arrastrarlas automáticamente
reescribiría datos históricos sobre una suposición (mismo criterio que los renombres). Mover **a
mano** sí está bien y es la operación central del visor.

- **No existe "silenciar".** Hubo un `snoozed_until` que sacaba la tarea del aviso sin moverla, y se
  quitó: creaba tareas abiertas e invisibles a la vez (el contador marcaba 0 con pendientes de hace
  dos meses). Hoy posponer **mueve** la tarea. La columna quedó **vestigial** en las DBs de sep 2026;
  no se borra porque `init_db()` corre en cada request (`app.py`) y un `DROP COLUMN` ahí sería un
  camino destructivo por request. `test_atrasada_no_se_puede_silenciar` impide que la lógica vuelva.
- `done_at` — timestamp local del cierre; el toggle lo setea y lo borra al reabrir. Se lee solo en el
  `title` de una tarea hecha.
- `POST /tareas/<id>/mover` con `dias` ∈ `{0,1,7}` (hoy / mañana / +1 sem), **siempre relativo a
  hoy**: un `+1 sem` sobre algo de julio tiene que caer la semana que viene. Un `dias` fuera de la
  whitelist no mueve nada — mover a una fecha equivocada es peor que no hacer nada.
- Qué es "atrasada": `services.overdue_cutoff(hoy, modo, _week_start)` → con `todo_overdue_from=week`
  (default) el corte es el inicio de la semana en curso; con `day`, hoy. El corte es exclusivo.
- Avisos, en escalera por el ajuste `todo_alert` (`off` → `badge` → `modal`): contador en el navbar
  (`overdue_count`, inyectado por el context processor de `app.py`; con `off` no paga la query) y
  modal al arrancar (`#todo-modal` en `base.html`, una vez por arranque vía `sessionStorage`).
- "Empezó una semana nueva" sale de comparar el lunes actual contra la clave
  `appconfig.LAST_WEEK_SEEN_KEY` en la tabla `settings`. **Esa clave va fuera de `SETTINGS`** a
  propósito: `get_all_settings()` clampea contra `choices` solo lo que está en el esquema, así que
  una fecha ISO libre sobreviviría igual.
- El filtro de tiempo se llama `periodo` (en la URL y en el código), nunca "rango": la palabra suena
  antinatural en la UI. El default es `hoy`. `services.periodo_ventana()` devuelve `(start, end)` y es una **ventana
  exacta** — el botón lista exactamente lo que dice, sin futuro, salvo `proximas` y `todo`. El título
  del listado sale de la tercera columna de `routes.todos.PERIODOS`.
- El bloque de atrasadas ignora el período (lo viejo se avisa siempre). De los contadores del
  resumen, **"para hoy" y "próximas" son absolutos**: atarlos a la ventana los dejaba siempre en 0,
  porque la ventana termina hoy. Solo "ya hechas" es relativo al período.
- El visor **no es un tablero**. Se rechazaron, en orden, las barras de progreso semanal y los
  contadores siempre visibles (hoy viven en un `<details>` cerrado por default, con el estado en
  `localStorage`). Antes de sumar métricas, rachas o gamificación acá: preguntar.

## Perfiles y sincronización

Varias bitácoras en la misma instalación, **un archivo de DB por perfil**. Todo local: no hay
cuentas ni nada remoto, y los perfiles no protegen nada (cualquiera cambia de perfil) — son para
ordenar, no para esconder.

- El índice va en `APP_DIR/perfiles.json` y no en una tabla, porque hay que saber qué perfil abrir
  **antes** de abrir ninguna base. Guarda también un `uid` por perfil y un `dispositivo` por
  instalación, que son la identidad que va a usar el sync.
- **Cambio en caliente**: `profiles.aplicar()` rebindea `database.conn.DB_PATH`. Funciona porque
  `conn.py` lee el env `HT_DB` una sola vez al importar pero todo lo demás lee el global del módulo
  en cada llamada, y nada cachea la conexión. Es la misma técnica que usan los tests.
  Por eso `DB_PATH` **no se re-exporta** desde `database/__init__.py`: sería una copia congelada.
- Sin `HT_PERFILES` (modo navegador, tests) los perfiles se apagan solos y la app funciona como
  antes. Eso es lo que mantiene los tests viejos intactos.
- El switcher del navbar aparece **solo con más de un perfil**.
- Borrar un perfil: nunca el activo ni el último, y pide escribir `BORRAR PERFIL`.
  ⚠️ En Windows hay que `gc.collect()` antes del `rmtree`: los callers hacen `with get_db()`, que
  commitea pero **no cierra**, así que el archivo sigue lockeado hasta que el GC recoja la conexión.
  Mismo motivo en la migración, donde además borrar el original es *best-effort* y nunca aborta.

### Sincronizar dos dispositivos (`sync.py`)
El paquete es **un archivo `.db`** (un `snapshot_to` del perfil) con la identidad escrita en su
propia tabla `settings` (claves `_sync_*`, que el merge excluye). Viaja **la base entera, no un
delta**: no hay que registrar qué se sincronizó y reimportar el mismo archivo es inofensivo.

El merge se resuelve en SQL con `ATTACH`, en este orden y con estas reglas:
- **Padres antes que hijos** (`ORDEN`), porque un hijo necesita que su padre exista para traducir
  la referencia.
- **Las FK guardan enteros locales**: la misma categoría es la 1 acá y la 77 allá. Se traduce
  resolviendo el padre por su `uid` (`PADRES`). Si el padre no existe acá, la fila se saltea en vez
  de entrar con NULL y violar el NOT NULL.
- **`completions` es el único caso con otra clave única** (`UNIQUE(event_id, done_date)`): la misma
  rutina marcada el mismo día en dos máquinas tiene uid distinto pero choca. Ahí manda la clave
  natural, no el uid — es el mismo hecho.
- **`todos.position`** se recompacta después del merge: las dos máquinas la calculan con
  `MAX(position)+1` y generan las mismas.
- Los ajustes viajan con última-escritura-gana por clave (por eso `settings.updated_at`).
- El merge trabaja **siempre sobre `SYNCABLE`**, nunca sobre "todas las tablas": las 4 legacy
  (`entries`, `goals`, `custom_events`, `event_logs`) viajan en el archivo pero no se tocan.
- `analizar()` y `aplicar()` comparten los mismos `WHERE`: la vista previa y el merge no pueden
  divergir.
- El paquete subido va a una **ruta fija** (`sync-pendiente.db`, junto a la DB): así entre la previa
  y el aplicar no viaja ninguna ruta por el formulario.

### Cimientos del sync
Las 7 tablas de `SYNCABLE` tienen `uid` (las PK autoincrementales colisionan entre dispositivos) y
`updated_at`, más la tabla `deletions` para tombstones. Todo se llena con **triggers**, así que
ninguno de los 33 puntos de escritura de `database/*.py` los conoce.

- ⚠️ `updated_at` y `deleted_at` van en **UTC y con milisegundos**
  (`strftime('%Y-%m-%d %H:%M:%f','now')`), al revés que el resto de la app: son para comparar entre
  máquinas y el caso de uso es viajar a otro huso. Los milisegundos no son cosmética — con
  resolución de segundos, dos ediciones del mismo segundo empatan y "la más reciente gana" no
  dispara. Hay tests que fijan las dos cosas.
- ⚠️ El trigger de UPDATE lleva **`WHEN NEW.updated_at = OLD.updated_at`**: si el UPDATE trae su
  propia marca es el merge trayendo la versión remota y hay que respetarla. Sin esa guarda la fila
  queda diciendo "modificada ahora" y en el viaje de vuelta una edición vieja le gana a una nueva.
  Y **no usar `created_at` para ordenar entre dispositivos**: en las DBs viejas quedó en UTC y en
  las nuevas en localtime, porque `CREATE TABLE IF NOT EXISTS` nunca reescribe una tabla existente.
- ⚠️ **El orden de `init_db()` no se puede cambiar**: triggers *después* de las migraciones. SQLite
  no resuelve columnas al crear un trigger, así que al revés el `CREATE TRIGGER` sale bien y después
  explota **cada INSERT** con `no such column: uid`.
- `PRAGMA user_version` (= `SCHEMA_VERSION`) hace de guarda de `init_db()`, que corre en cada
  request: sin eso costaba 5,5 ms por página en vez de 1. **Al agregar una migración hay que subir
  `SCHEMA_VERSION`** o las DBs instaladas se saltean el paso. `reset_db()` la baja a 0.
- `updated_at` vacío significa "original, nunca modificada" y ordena antes que cualquier fecha. El
  backfill no lo rellena a propósito: haría ganar al dispositivo que migró último.

## Widget de escritorio y bandeja

Segunda ventana de pywebview **en el mismo proceso**, `frameless` + `easy_drag` + `on_top`.

- ⚠️ **A la ventana del widget se le pasa una URL string, NO el objeto Flask.** Con la app,
  `webview/window.py:194` le levanta **un servidor Bottle propio a cada ventana**. La URL se captura
  **una sola vez al arrancar** desde `principal._url_prefix` (`widget.configurar`): después no se
  puede leer de `webview.windows[0]`, porque una ventana cerrada sale de esa lista.
- `create_window` solo crea en el acto si se la llama desde un **hilo que no es el principal**
  (`webview/__init__.py:417`). Por eso el widget se abre desde el handler de `events.shown`, que
  pywebview ya corre en un hilo aparte (`webview/event.py:56`).
- **El widget sobrevive a cerrar la ventana grande**: los backends solo terminan la app cuando se
  cierra la *última* ventana. Es la razón de ser de la feature.
- ⚠️ **Una ventana destruida NO tira excepción al navegarla.** Hay que preguntarle a pywebview si
  todavía la tiene (`_principal_viva()`), o el clic en un día se pierde en silencio.
- ⚠️ **La geometría del widget va a `APP_DIR/widget.json`, nunca a `settings`**: los ajustes
  sincronizan entre máquinas y el widget aparecería corrido o fuera de pantalla en la otra.

### Una sola instancia
Abrir Bitácora estando abierta **no lanza otra**: vuelve la que ya está, y donde la dejaste.
`instancia.py` lo resuelve con dos piezas y las dos hacen falta:

- ⚠️ **Un lock del sistema operativo** (`msvcrt.locking` / `fcntl.flock`) sobre
  `APP_DIR/instancia.lock`, **no un archivo con el PID**: si la app se cuelga y la matás desde
  el administrador de tareas, el lock lo suelta el sistema, mientras que un archivo-bandera
  quedaría y la app no abriría nunca más. El handle se deja abierto a propósito — cerrarlo
  suelta el lock.
- **Un archivo con la URL** (`instancia.json`) para avisarle por HTTP a la que ya corre
  (`POST /instancia/mostrar`). No se puede saber antes: pywebview asigna un puerto al azar y
  recién se conoce en el handler de `shown`. Que el aviso falle es un caso **normal** (la otra
  puede estar arrancando todavía) y la segunda se cierra igual.
- El chequeo va **antes** de las migraciones y el auto-backup: no hay por qué pagarlos en un
  proceso que sale, y dos procesos migrando la misma base a la vez es justo lo que no se quiere.
- ⚠️ **`mostrar_principal()` no navega.** Antes hacía `load_url("/")`, que te sacaba del día que
  estabas mirando. Solo crea una ventana nueva si no quedaba ninguna.
- ⚠️ **`restore()` va solo si la ventana está minimizada**, porque fuerza `WindowState=Normal` y
  a ciegas desmaximizaría una ventana maximizada. Y el estado hay que **rastrearlo por eventos**
  (`minimized`/`restored`/`maximized`): `window.minimized` de pywebview es el flag con el que se
  creó la ventana y nunca se actualiza. En Windows `show()` es `Show()` + `Activate()`, así que
  alcanza para traerla al frente.

### Borrado: tres acciones, tres frases
| Acción | Qué hace | Frase |
|---|---|---|
| Vaciar este perfil (`/reset`) | `reset_db()` del perfil activo; los otros no se tocan | `BORRAR DATOS` |
| Eliminar un perfil (`/perfiles/borrar`) | Saca del índice + `rmtree`. Acepta el activo | `BORRAR PERFIL` |
| Borrar todos (`/perfiles/borrar-todos`) | Arrasa `perfiles/` y deja uno vacío | `BORRAR TODOS LOS PERFILES` |

⚠️ **`BORRAR TODO` ya no coincide con nada, a propósito.** Vaciaba *un* perfil pero sonaba a que
borraba todo. Dársela a la acción nueva habría hecho que el hábito de tipearla borre los tres
perfiles; dejársela a la vieja habría mantenido el cartel mintiendo. Que falle es lo único que
garantiza que un hábito viejo no dispare un borrado más grande. Hay tests en `test_routes.py` que lo
fijan para las dos acciones.

⚠️ **Borrar el perfil activo cambia de perfil ANTES de tocar los archivos** (`profiles.borrar`): en
Windows la base que se estaba usando queda lockeada hasta que el GC recoja la conexión.

### La regla de seguridad de la bandeja
`tray.iniciar()` devuelve si pudo poner el icono, y **el cierre solo se intercepta si devolvió
True**. Esconder la ventana al cerrar sin icono dejaría el programa corriendo **sin forma de
mostrarlo ni de cerrarlo** salvo el administrador de tareas. `cerrar_a_bandeja` no alcanza por sí
solo: hay tests que fijan las tres combinaciones.

En Linux `tray.iniciar()` devuelve `False` a propósito: GNOME (Fedora) no muestra iconos de bandeja
sin una extensión, así que ahí cerrar cierra. El `NotifyIcon` corre en su **propio hilo con su
propio `Application.Run()`** — válido en WinForms (un bucle por hilo) y evita tocar los internals de
pywebview para marshalear a su hilo de interfaz.

## El calendario y el widget se refrescan

Las dos ventanas poletean `GET /refresco` cada 3 s (`static/js/refresco.js`, incluido en
`base.html` **y** en `widget.html`, que es plantilla propia). Si el token cambió, recargan.

`db.token_datos()` es la ruta de la DB + el `st_mtime_ns` del `.db` y del `-wal`. Son `os.stat`,
sin SQL: no hay que saber nada del esquema y cubre gratis lo que no pasa por un INSERT de la app
(restaurar un backup, aplicar un sync, vaciar el perfil). Se sirve con la página en
`window.TOKEN_DATOS` desde el context processor, así la primera vuelta ya tiene con qué comparar.

- ⚠️ **El `-wal` no es opcional**: la app corre en `journal_mode=WAL`, así que un commit puede
  tocar solo el sidecar y dejar el `.db` con la mtime vieja. Mirando solo el `.db`, los cambios
  recién se verían en el próximo checkpoint.
- ⚠️ **`/refresco` va con `Cache-Control: no-store`**, o el WebView se lo cachea y el poleo deja
  de ver los cambios.
- ⚠️ **Poleo y no avisarle a la otra ventana con `evaluate_js`.** El aviso directo sale más corto
  pero solo anda en la app de escritorio (el mismo problema existe con dos pestañas), no cubre los
  cambios que no vienen de un POST de la otra ventana, y obliga a mantener a mano qué rutas tocan
  datos: de las 9 POST de `routes/widget.py`, **6 no cambian nada** (fijar, minimizar, cerrar,
  abrir, dia, instancia).

Dos cosas del JS que parecen de más y no lo son — las dos salieron de verlo fallar en el navegador:

- ⚠️ **Solo los campos donde se TIPEA cuentan como borrador** (`TIPEABLES`). La primera versión
  usaba "cualquier input cuyo `value` difiera del `defaultValue`", y **el calendario no se
  refrescaba nunca**: el slider de tamaño de celda se restaura de `localStorage` al cargar, así
  que su `value` siempre difiere del HTML. Un slider o un radio no son texto a medio escribir.
- ⚠️ **`refresco.js` envuelve `fetch` para ignorar las escrituras PROPIAS de la página.** Sin eso,
  tocar un switch en Ajustes (que guarda al instante) o cerrar el aviso de tareas hacía que la
  página se recargara sola a los 3 segundos. Los formularios normales no tienen el problema porque
  recargan y traen un token nuevo; los que hacen `fetch`, sí — y hoy hay cuatro (`ajustes.js`,
  `day.js`, `week.html` y el "visto" del aviso). Se envuelve `fetch` en vez de avisar desde cada
  llamador justamente para que el quinto no vuelva a traer el bug. Solo observa: la respuesta se
  devuelve intacta.

Y el guard nunca pierde el aviso: con borrador no recarga, pero al tick siguiente el token sigue
distinto y reintenta — al soltar el campo, recarga.

## La pantalla de Ajustes

Cero `<select>` entre los 16 ajustes, seis secciones colapsables y **guardado al instante**.

- **Tres controles, y cuál va dónde no es estético**: switch deslizable para los 8 que se leen como
  prendido/apagado (aunque el vocabulario cambie: `on/off`, `show/hide`, `open/collapsed`);
  segmentado para los que son **esto o aquello** (`24h/12h`, `mon/sun`, `week/day`) y para los de 3
  opciones; swatches para el tema. Un switch en "24 h" haría preguntar *"¿12 h está prendido?"*.
- ⚠️ **El switch es un `<input type="checkbox">` escondido + un `<input type="hidden">` DESPUÉS**.
  Un checkbox sin marcar no manda nada: sin el hidden, apagar un switch desde el formulario dejaría
  el ajuste en blanco en vez de apagado. El orden no es cosmético — marcado viajan los dos y
  `request.form.get()` devuelve el primero. Hay un test por switch para las dos cosas.
- ⚠️ **El botón Guardar sigue en la plantilla; lo esconde `ajustes.js`.** Si el JS se rompiera y el
  guardado al instante fuera el único camino, los ajustes quedarían **imposibles de cambiar**.
  `POST /ajustes/guardar` (todo el formulario) y `POST /ajustes/set` (uno solo, 204) comparten la
  validación en `_guardar_ajuste()` para que no puedan divergir en qué aceptan.
- ⚠️ **`show_todos`, `show_stats`, `show_export` y `todo_alert` llevan `data-recargar`**: cambian el
  navbar, que se renderiza en el servidor. Guardarlos sin recargar los persiste pero el tab no
  aparece, y se lee como que no pasó nada.
- **El tema ya no se previsualiza y confirma**: se aplica y queda. Es la consecuencia de sacar el
  botón Guardar, y el texto de la pantalla lo dice.
- El botón "Abrir el widget ahora" usa `form="abrir-widget-form"` apuntando a un `<form>` de afuera:
  anidar formularios es HTML inválido y el navegador se come el de adentro (antes estaba anidado).
- Los colores salen todos de `var()`, y el texto sobre `var(--accent)` es `#fff` **por convención
  del repo** (`.btn-primary`, `.weekday-btn`, `.todo-check`), no por contraste medido: el
  segmentado tiene que parecerse al de los días de la semana en Rutinas.
- El colapsable es `recordarColapsable()` en `static/js/colapsables.js`, compartido con el visor de
  tareas. Dos usos se toleran copiados, tres se comparten.

## Auto-actualización

`bitacora/escritorio/updater.py` + `bitacora/routes/update.py` — chequea GitHub Releases (`LDsAragon/health-tracker`) en un hilo daemon al arrancar (`check_in_background()` desde `bitacora/escritorio/main.py`). Flujo: `/update/status` → `/update/download` → `/update/progress` → `/update/apply` (backup DB → extrae asset → lanza script externo) → `/update/quit`. UI en `base.html` + `static/css/pages.css`.

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
- Los valores de las entradas se guardan como `{etiqueta: valor}` en `values_json` — por eso renombrar un campo obliga a `migrate_entry_values()` (que además re-clava las etiquetas en la tabla `charts`).

### Agregar cosas: los andamios

Las tres cosas que se agregan seguido tocan 3 o 4 archivos cada una, y **hay un comando que las
hace**: `.\hacer.ps1 nuevo ajuste | campo | ruta` (cada uno con `--help`). Dejan la suite en verde
sin tocar nada, e imprimen al terminar qué falta a mano.

| `nuevo …` | Qué toca | Qué queda a mano |
|---|---|---|
| `ajuste` | `appconfig.SETTINGS`, un control en `templates/settings.html`, la fila del manual y la lista de `tests/test_ajustes.py` | leer el ajuste donde haga falta; el `data-recargar` si cambia el navbar |
| `campo` | `fieldtypes.FIELD_TYPES`, `static/js/field-registry.js` y un builder stub en `field-blocks.js` | el cuerpo del builder; el display propio en `day.html` (opcional) |
| `ruta` | `routes/<n>.py`, `templates/<n>.html`, `tests/test_<n>.py` y las dos listas de `app.py` | el contenido de la pantalla; el enlace del navbar |

⚠️ **Insertan en anclas** (`# ANDAMIO: ...`, `{# ANDAMIO: ... #}`), y si el ancla no está —o está
dos veces— **abortan y lo dicen** en vez de improvisar. Adivinar dónde va cada cosa parseando el
archivo es la misma clase de error que ya se rechazó para los datos del usuario. Las anclas son
parte del código: no moverlas ni borrarlas.

⚠️ **La lista de controles de `tests/test_ajustes.py` está escrita a mano a propósito**: es el
tripwire del que agrega un ajuste **sin** darle control. El andamio la mantiene porque ahí el
control está garantizado; el tripwire sigue cubriendo el camino manual, que es para lo que existe.

⚠️ **Los blueprints se listan a mano en `app.py`** (`BLUEPRINTS`), sin descubrimiento automático:
PyInstaller resuelve imports estáticamente y con un `importlib` dinámico las rutas **no entrarían al
bundle**.

Hacerlo a mano sigue siendo válido; lo que hay que respetar es el conjunto de archivos de la tabla.

## Quirks conocidos

- **Linux / WebKitGTK**: exportar `PYWEBVIEW_GUI=gtk` y `WEBKIT_DISABLE_DMABUF_RENDERER=1` (lo hace `bitacora.sh`).
- **Linux / WebKitGTK**: `color-scheme: dark/light` en CSS controla el rendering de `<select>` nativos (sin esto salen con tema GTK del sistema, blanco sobre blanco en tema oscuro).
- **Linux / descargas**: `webview.settings["ALLOW_DOWNLOADS"] = True` es necesario (está en `bitacora/escritorio/main.py`); por defecto pywebview cancela descargas silenciosamente.
- **Arch / keyring**: `instalar.sh` detecta keyring sin inicializar chequeando `/etc/pacman.d/gnupg/trustdb.gpg` (no solo el directorio — el dir puede existir vacío).
- **Windows / Mark of the Web**: si el zip viajó por internet, .NET se niega a cargar `Python.Runtime.dll`. `escritorio/main.py::_unblock_dlls()` borra el stream `Zone.Identifier` de las DLLs de `_internal/` en cada arranque; el updater hace lo mismo tras copiar los archivos nuevos.
- ⚠️ **El calendario se deformaba con texto largo**: `grid-template-columns: repeat(7, 1fr)` es
  `minmax(auto, 1fr)`, y ese `auto` como mínimo **impide que la columna se encoja por debajo del
  min-content de su contenido**. Con un `white-space: nowrap` en `.chip` (rutinas y notas
  especiales), el min-content era el título entero: las columnas pasaban de 174px a **558px** y
  los últimos días de cada semana quedaban clipeados por el `overflow: hidden` de la grilla. Va
  `minmax(0, 1fr)` + `min-width: 0` en `.cal-cell` y `.cal-cell-body` (los dos tienen `auto` por
  default), y los chips envuelven con `overflow-wrap: anywhere` en vez de `nowrap`.
  El tope de líneas de todo lo que se muestra en una celda sale de **`--cal-max-lineas` en
  `.cal-grid`** (10): un solo lugar, heredado por chips y notas.
  ⚠️ `.chip-journal` vive en `pages.css`, que carga **después** de `calendar.css`: un
  `white-space` ahí le gana al de `.chip`, y por eso se lo saca de esa regla también.
- ⚠️ **Puertos que Chromium rechaza**: WebView2 y WebKitGTK se niegan a cargar una página
  servida desde una lista de ~85 puertos "no seguros" (`net/base/port_util.cc`) y muestran
  **`ERR_UNSAFE_PORT`** — la app queda en blanco, ventana y widget, hasta reiniciarla. pywebview
  sortea el puerto con `random.randint(1023, 65535)`, así que cae en uno cada ~750 arranques (pasó
  con el 1719). `escritorio/main.py::puerto_seguro()` pide uno al sistema operativo y exige
  `>= PUERTO_MINIMO` (10081, uno más que el bloqueado más alto), y se pasa por
  **`create_window(http_port=...)`, no por `webview.start()`**: con un objeto Flask la ventana
  levanta su propio servidor en `_initialize()` y ahí solo llega el de `create_window`. El widget
  no necesita nada porque reusa ese mismo servidor.
- **pywebview / localStorage**: `webview.start(private_mode=False, storage_path=...)` — sin eso pywebview borra el zoom y el tamaño de celdas al cerrar.
- **DB path en tests**: `bitacora.database.conn.DB_PATH` se parchea directamente (por string, así que un cambio de layout lo rompe ruidoso); `get_db()` lo lee en cada call.
