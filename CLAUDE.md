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
    stats.py            # Motor de Estadísticas: build_series, grouped_series, chartable_fields,
                        #   resumen/resumen_comparado (lo anotado + la comparación),
                        #   tiempo_comparado ("Tiempo por actividad") y emociones_frecuentes
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
      confirmar.js      # Confirmaciones con la estética de la app (data-confirmar en el <form>)
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
                        #   screenshots_audit.mjs (Playwright, auditoría visual de las pantallas),
                        #   refresco_audit.mjs (que el refresco entre ventanas ande, pantalla por
                        #   pantalla) y servidor_prueba.py (la app contra una base temporal)
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
- `health-prejournal-<ts>` — antes de borrar una categoría de notas especiales (se lleva
  todas sus entradas)
- `health-preborrado-<slug>-<ts>` — antes de borrar todos los perfiles. **Este va a
  `APP_DIR/backups/`, no al del perfil**: la carpeta del perfil es justo lo que se borra
- `health-preperfiles-<ts>` — antes de mudar la DB al layout de perfiles

## Tests

```powershell
.\hacer.ps1 tests              # 826 tests, ~45s (o `pytest tests/` directo)
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

⚠️ **Los smokes se corren en las DOS plataformas**, y en Linux con el venv de WSL
(`venv-linux/bin/python tools/<smoke>.py`, con `PYWEBVIEW_GUI=gtk` y
`WEBKIT_DISABLE_DMABUF_RENDERER=1`). `smoke_desktop` aislaba solo con `LOCALAPPDATA` —la variable
de Windows— así que en Linux apuntaba a la carpeta de datos **real**; lo frenó su propio assert,
que está justamente para eso. Ahora fija las dos variables.

⚠️ **Lo del empaquetado Linux se verifica sobre una instalación de verdad**, armada desde el
tarball (`tar -xzf dist/Bitacora-linux-*.tar.gz -C $(mktemp -d)` y `./instalar.sh` con un `HOME`
temporal), nunca sobre el repo: es lo único que reproduce que allá la app corre **desde el
código**. Así salieron dos bugs que el repo no mostraba — el updater copiando a
`bitacora/escritorio/` y el `.desktop` apuntando a un icono que se había mudado al paquete.

## Comandos: `hacer.ps1`

**Todos los comandos del proyecto salen de un solo lugar.** Sin argumentos los lista:

```powershell
.\hacer.ps1                          # lista todo con su descripción
.\hacer.ps1 tests -k ajustes         # los argumentos pasan tal cual
.\hacer.ps1 smoke instancia
.\hacer.ps1 refresco                 # audita el refresco entre ventanas (levanta su servidor)
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
proceso). El zip lleva **una sola carpeta, `Bitacora`**, con el `LEEME.txt` y el
`Bitacora-Manual.pdf` **adentro**; el PDF se regenera aparte con `.\hacer.ps1 manual` (Edge
headless) cuando cambia `docs/manual.html`.

⚠️ **Todo lo que se distribuya va DENTRO de esa carpeta.** `apply_update()` toma
`extracted/Bitacora` y la espeja sobre la carpeta del ejecutable (`robocopy /MIR`), así que lo que
quede afuera **no se actualiza nunca**: el manual y el LEEME se quedaban con la versión del día en
que descomprimiste. El tarball de Linux ya lo hacía bien.
`test_el_manual_y_el_leeme_van_dentro_de_la_carpeta_que_se_espeja` lo fija para las dos
plataformas.

⚠️ **El entry point del build es `main.py`, no el paquete**, y `--add-data` deja `templates/` y
`static/` en la **raíz** del bundle (`bitacora/templates;templates`) porque ahí las busca la rama
congelada de `create_app()`.

**Linux** — tarball con instalador (`.\hacer.ps1 build-linux` → WSL → `tools/make_release_linux.sh`):
El tarball incluye `tools/linux/instalar.sh` (detecta apt/dnf/pacman) y `tools/linux/bitacora.sh`
(launcher con env vars, ejecuta `main.py`). Copia `main.py` + el paquete `bitacora/` entero, sin
lista de módulos: una lista explícita se desactualiza sola (`updater.py` faltó desde `v2026-06-25`
y la app de Linux ni arrancaba, y por eso el CI verifica que el tarball importe).

⚠️ **El tag se elige ANTES de compilar.** `publish_release.ps1` resuelve el sufijo y se lo pasa
al build (`make_release.ps1 -Version $tag`), o el `.exe` publicado llevaría un tag distinto al de
su propio release. Y **sin `-Version` —un build local— se estampa el sufijo que le tocaría al
publicarse**, sacado de los tags (`git tag -l`, con un `fetch` de mejor esfuerzo): antes ponía
`v<fecha>` a secas, que es el tag de la **primera** release del día, así que el `.exe` se hacía
pasar por una versión publicada que no era la que tenía adentro y el updater le ofrecía
"actualizar" a algo con **menos** código del recién compilado. Con el sufijo siguiente queda por
encima de todo lo publicado (`available: False`) y coincide con el tag que va a llevar cuando se
publique. Lo fijan tres tests en `tests/test_updater.py`.

**Publicar a GitHub Releases** (ambas plataformas): `.\hacer.ps1 publicar`.
⚠️ **Sin `-Tag`, el script busca el primer sufijo libre del día** (`.1`, `.2`, …) y avisa cuál
eligió. Antes usaba `v<fecha>` a secas y, con un release del día ya publicado, le reemplazaba los
archivos y las notas en silencio — y encima ese tag compara **menor** que el del día con sufijo
(`_version_tuple`: `(2026,9,12) < (2026,9,12,2)`), así que el release nuevo no se le ofrecía a
nadie. La rama que reemplaza sigue existiendo, pero solo se llega pasando `-Tag` a propósito.

**CI**: `.github/workflows/ci.yml` — pytest + tarball Linux como artifact, corre en push/PR a main.

⚠️ **El CI corre en `ubuntu-latest` y estuvo en rojo doce corridas seguidas sin que nadie lo
notara**, que es lo mismo que no tener CI. Dos causas, y las dos son la misma clase de error —un
test que falla por **plataforma** y no por comportamiento—:
- `subprocess.CREATE_NO_WINDOW` no existe fuera de Windows: los dos tests del actualizador de
  Windows llevan `skipif`.
- El CI **no instala `requirements-desktop.txt`** (pywebview necesita GTK/WebKit del sistema), así
  que los tests de la capa de ventana se saltean con `importorskip`.
Por eso el comando lleva **`-ra`**: sin él los salteados son invisibles y nadie se enteraría de
que un día se saltea media suite. Antes de dar por buena una corrida, mirar cuántos se saltearon.

**Correr la suite en Linux**: `wsl -d Ubuntu-24.04 --cd <repo> -- venv-linux/bin/python -m pytest
tests/ -q -ra` (pide `venv-linux/bin/pip install pytest` la primera vez). Ahí sí está pywebview,
así que solo se saltean los dos de Windows.

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
Las 8 tablas de `SYNCABLE` tienen `uid` (las PK autoincrementales colisionan entre dispositivos) y
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
- ⚠️ **El setup va serializado con un lock** (`schema._EN_SETUP`), y **el modo WAL se activa una
  sola vez** (`conn.activar_wal`, desde `init_db`), nunca en `get_db()`. Las dos cosas arreglan el
  mismo síntoma: **un 500 en la pantalla principal del primer arranque**, 4 de cada 10 veces. En
  el primer arranque la guarda de `user_version` todavía no está, así que la ventana grande y el
  widget —que se abre solo— entran juntos y los dos hacen el setup completo: uno moría con
  "database is locked" (cambiar el journal_mode exige que no haya otra conexión abierta, y SQLite
  **no** respeta el `busy_timeout` para eso) o con "database schema has changed" (una sentencia
  invalidada porque el otro hilo está migrando). `get_db()` sí pone un `busy_timeout`, que es lo
  que cubre dos **procesos** distintos. El lock no cuesta nada después: la guarda sale antes.
  Lo fijan `test_init_db_soporta_requests_simultaneos_en_una_base_virgen` y dos tripwires — y ⚠️
  ese test **pasa igual sin el lock**, porque con ocho hilos el que se dispara es el fallo del
  WAL; el del lock salió con doce y por eso va por tripwire.
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
- ⚠️ **Una posición guardada se valida contra los monitores, al guardarla y al abrir**
  (`posicion_visible`, con `webview.screens`). Windows le pone **(-32000, -32000)** a una ventana
  minimizada y pywebview lo dispara como un evento `moved`: **minimizar el widget una vez lo
  mandaba fuera de toda pantalla para siempre**, y como `esta_abierto()` seguía devolviendo True
  la app decía que estaba abierto mientras no se veía por ningún lado. Desenchufar el monitor
  donde vivía hacía lo mismo. Al abrir, una posición imposible se descarta y se olvida
  (`olvidar_posicion()` deja el tamaño), así la ventana nace donde la ponga el sistema.

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

### Qué muestra el widget, y qué no
- **Rutinas de hoy**, detrás del ajuste `widget_rutinas`, en la pestaña de Tareas. Se tildan desde
  ahí (`/widget/rutina/<id>/toggle`, que reusa `db.complete_event` / `db.uncomplete_event`). **Sin
  "saltear" ni nota de completado**: eso vive en la ventana grande.
- **Las notas especiales quedaron afuera a propósito.** Son formularios a medida y no entran en
  340px; el camino es el atajo de la pestaña Nota, que abre el día en la ventana grande con
  `widget.dia`, la misma ruta que ya usa el clic en un día del calendario. Decisión suya:
  *"dejando el widget compacto y pequeño"*.
- **El selector de color de la nota rápida** usa el mismo `name="color"` que el día y el
  calendario, así que pasa por `services.color_para_nota_nueva()` como todos.
- **Las tareas y las notas se editan en línea** con el lápiz (`editarEnLinea`, un solo editor
  para las dos): Enter o clic afuera guardan, Shift+Enter hace un salto y Escape cancela. Cada
  fila dice a dónde postear (`data-editar`) y con qué campo (`data-campo`). Guarda por `fetch`
  (204) y actualiza el nodo a mano, porque `refresco.js` ignora las escrituras **propias** de la
  página. Las rutinas no llevan lápiz: se editan en la ventana grande.
  ⚠️ `/widget/nota/<id>` **relee la nota para devolverle su color**: `update_note` reescribe la
  fila entera y sin eso editar el texto le apagaba el color. Las dos rutas aceptan solo lo que el
  widget **muestra** (las notas de hoy; las tareas de hoy **y las atrasadas**, que son de otros
  días).
- **"Lo de hoy" arranca colapsado** (`recordarColapsable`, el mismo helper del visor y de
  Ajustes): el widget tiene que ocupar lo mínimo. ⚠️ El `<details>` va **fuera** de la zona de
  refresco —adentro, actualizar la lista le cerraría el desplegable en la cara— y por eso el
  contador del `<summary>` necesita **su propia zona**: sin ella se quedaba con el conteo viejo
  mientras la lista sí se actualizaba, el mismo agujero que el "⚠️ Sin cerrar · N". Lo cazó
  `hacer.ps1 refresco`, no un test.

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

`db.token_datos()` sale de **datos commiteados**: la ruta de la base + un `MAX()` de los
`updated_at` de las 8 tablas de `SYNCABLE` (los llenan los triggers del sync), del `deleted_at` de
`deletions` y del `updated_at` de `settings`. Una sola consulta con subselects, armada desde
`SYNCABLE` para que no pueda quedar desfasada del esquema. Cubre gratis lo que no es un INSERT
normal: `reset_db()` deja los máximos vacíos y restaurar un backup trae otros `updated_at`.

### Los dos bugs que lo tuvieron recargándose cada 3 segundos
Se publicaron juntos en `v2026-09-12.5` y los dos daban el mismo síntoma —la app parpadeando sola—
así que conviene tener los dos presentes:

- ⚠️ **El token NO puede salir de la mtime de los archivos.** La primera versión usaba `os.stat`
  del `.db` y del `-wal`. Pero `with get_db()` deja la conexión sin referencias y CPython la
  cierra, y **al cerrarse la última conexión de una base en WAL SQLite hace checkpoint y borra el
  `-wal`**: que el archivo exista —y con qué mtime— en el momento del stat es una carrera.
  `test_el_token_no_se_mueve_entre_REQUESTS` lo fija pidiéndolo **por HTTP** varias veces, que es
  lo único que reproduce las conexiones abriéndose y cerrándose; llamarlo dos veces en el mismo
  proceso daba estable y por eso el bug pasó.
- ⚠️ **El token se embute con `| tojson`, nunca como `"{{ token_datos }}"`.** Lleva la ruta de la
  base, que en Windows tiene barras invertidas, y en un literal de JavaScript esas barras son
  escapes que desaparecen. La página guardaba un valor que **nunca** iba a coincidir con el de la
  ruta. `test_el_token_de_la_pagina_es_IGUAL_al_de_la_ruta` parsea el literal como JSON, igual que
  el navegador, y lo compara con la respuesta de `/refresco`.

### Cuándo recarga
- ⚠️ **`Cache-Control: no-store` en `/refresco`**, o el WebView se lo cachea y el poleo deja de ver
  los cambios.
- **No se recarga encima de lo que estás haciendo**: si la ventana no tiene el foco, recarga ya; si
  lo tiene, espera a que sueltes mouse y teclado 1,5 s. "Tiene el foco" solo no alcanza como regla
  —una ventana enfocada y quieta se quedaría vieja para siempre—.
- **Ni encima de algo tipeado.** Solo cuentan los campos donde se escribe (`TIPEABLES`), y
  ⚠️ **"sin tocar" NO se decide contra `defaultValue`** —el valor con el que lo renderizó el
  servidor—. Cualquier campo que el JS rellene al cargar difiere de su `defaultValue` para
  siempre, así que la ventana queda marcada "con borrador" y **no se refresca nunca**. Costó dos
  bugs: el slider de tamaño de celda del calendario (se restaura de `localStorage`) y después los
  dos campos de `date-es.js`, que dejaron **la vista del día** sin enterarse de nada de lo que
  escribías en el widget. Van las dos condiciones juntas: que el campo haya recibido un evento
  `input` de verdad (setear `.value` desde JS **no** lo dispara, que es lo que descarta lo que
  rellena la página) y que difiera del snapshot tomado al terminar de cargar (así escribir y
  volver atrás no lo deja sucio hasta la próxima recarga).
  `test_el_borrador_no_se_decide_con_defaultValue` es el tripwire.
- ⚠️ **Tener el cursor en un campo NO alcanza para ser un borrador**: tiene que haber algo
  escrito. `/search` enfoca el buscador al entrar, así que con la regla vieja —cualquier campo
  enfocado bloquea— esa pantalla tampoco se refrescaba nunca. Escribir de verdad lo cubre
  `estaSucio`, y estar por escribir, el segundo y medio de quietud. Un `<select>` abierto sí
  sigue bloqueando: recargar una lista desplegada debajo del mouse molesta.
- ⚠️ **`refresco.js` envuelve `fetch` para ignorar las escrituras PROPIAS de la página.** Sin eso,
  tocar un switch en Ajustes (que guarda al instante) o cerrar el aviso de tareas la recargaba sola
  a los 3 s. Se envuelve en vez de avisar desde cada llamador porque hoy hay cuatro (`ajustes.js`,
  `day.js`, `week.html` y el "visto" del aviso) y el quinto traería el bug de vuelta.
- Mientras está oculta no poletea, y al volver a verse chequea en el acto.
- **Corta-circuitos**: más de 3 recargas en 30 s y el poleo se corta con un `console.warn`. No
  arregla la causa, la acota — convierte "la app es inusable" en "el refresco dejó de andar".
  También se corta tras 5 fallos de red seguidos, que es lo que pasa al cerrar la app.

### Actualizar sin recargar: las zonas `data-refresco`
El `location.reload()` era la **causa de raíz** de los tres bugs de esta feature: como recargar
destruye lo que estés escribiendo, había que adivinar si estabas en el medio de algo, y esa
adivinanza era global (un campo apagaba la ventana entera), callada y permanente. Hoy el refresco
pide la misma URL y reemplaza el **contenido** de las zonas marcadas. Lo que cambia de fondo es el
costo de equivocarse: una zona que no se puede tocar queda vieja y **todas las demás se actualizan
igual**.

- ⚠️ **Se reemplaza el `innerHTML` de la zona, NUNCA el nodo.** Es lo que salva los listeners
  enganchados al contenedor: el drag & drop de tareas vive en el `<ul id="todo-list">` y resuelve
  con `closest('.todo-item')`, así que sobrevive a que cambien los `<li>` y muere si se reemplaza
  el `<ul>`. Los `onclick` inline sobreviven siempre, son atributos.
- ⚠️ **Lo activa `data-refresco-parcial` en el `<main>`, no la presencia de zonas.** El navbar
  aporta una zona a todas las pantallas (el contador de atrasadas), así que mirando zonas sueltas
  `/journal` o `/ajustes` se darían por al día porque ese contador no cambió. **Una pantalla a
  medio marcar es peor que una sin marcar**: la sin marcar recarga y queda al día.
- **Una zona en uso se saltea** (tiene el foco adentro, o un campo sucio) y las demás se
  actualizan. Si algo quedó viejo aparece el aviso, que ahí sí es raro y accionable.
- **Se recarga** —con la regla del borrador— si la página no está marcada, si falla el fetch, o
  si **el conjunto de zonas cambió**: eso es un cambio estructural (aparece el panel de rutinas o
  el de notas especiales del día, que viven dentro de un `if`) y lo granular no lo cubre.
- **Las zonas envuelven los condicionales y existen siempre** aunque queden vacías. Marcando solo
  los `<ul>`, en el widget quedaban afuera el "⚠️ Sin cerrar · N" y el "Nada anotado para hoy": la
  pestaña se daba por al día con el conteo viejo en pantalla. Por lo mismo el `<ul id="todo-list">`
  del día se renderiza sin tareas.
- **Re-inicializar lo que viva adentro** va en `window.BITACORA_REINIT` (funciones `(nodo) => {}`).
  Hoy lo usa una sola cosa: las ruedas de emociones de las notas especiales (`day.js`).
  `date-es.js` ya estaba listo (`initDateEs(root)`, y su input/change/click son delegados en
  `document`).
- Cubiertas: **día, mes, semana y las pestañas de tareas y mes del widget**. El resto recarga, que
  es lo que hacía siempre.

### ⚠️ El modo de falla es CALLADO, y por eso hay red de seguridad
Cuando esto se rompe no hay error ni señal: la ventana se ve perfecta y muestra datos viejos.
Así vivieron rotas **6 de las 14 pantallas** —todas las que tienen un campo que el JS rellena al
cargar— hasta que el usuario lo notó usando la app. Tres piezas, y las tres hacen falta:

- **Un aviso en la app.** Si hay un cambio esperando hace más de 10 s que no se puede aplicar,
  aparece una barrita *"Hay cambios nuevos · Actualizar"* (`barraAviso()` en `refresco.js`,
  `.refresco-aviso` en **`base.css`** porque la usan los dos árboles de plantillas). El botón
  recarga aunque haya un borrador: lo pidió el usuario. El corta-circuitos también la muestra.
  Convierte "la ventana quedó vieja para siempre" en algo que se ve y se resuelve con un clic.
- **`hacer.ps1 refresco`** (`tools/refresco_audit.mjs`) — recorre las 14 pantallas y prueba de
  punta a punta lo que ningún test de pytest puede: que un cambio hecho en una ventana
  **aparezca** en la otra, y que entre **sin pisar un borrador**. Levanta su propio servidor con
  base temporal (`tools/servidor_prueba.py`, que aborta si la ruta cayera en el `APP_DIR` real),
  así que no toca los datos de nadie. Necesita `npm i playwright`, igual que
  `screenshots_audit.mjs`.
  ⚠️ En una pantalla cubierta el veredicto sale de **comparar el texto de `<main>` contra lo que
  sirve el servidor**, no de "¿recargó?": es lo único que caza una parte que se quedó fuera de
  toda zona, que es el fallo callado de este diseño. Y toca una nota **y** una tarea a propósito,
  porque con un solo tipo de dato quedaban zonas sin ejercitar.
- **Tests en `tests/test_refresco.py`**, que corren siempre y sin dependencias: que **toda**
  pantalla cargue `refresco.js` y traiga el token, que ninguna quede impedida de refrescarse por
  el `autofocus`, y los dos tripwires (`defaultValue` y el aviso).

## Rutinas y recordatorios

> **Una rutina se mide. Un recordatorio avisa.**

Es la distinción que ordena la pantalla, y la frase va **en la pantalla**: la rutina es algo que
querés hacer seguido y te importa cuánto lo cumplís (de ahí el "Últimos 30 días: 12/15"); el
recordatorio es algo que pasa ese día y no querés que se te escape. El recordatorio **se tilda**
—"saludé a mi amigo"— pero **no tiene porcentaje**, porque no significaría nada. Sale de
`recurring_events.tipo` (`rutina` | `recordatorio`), y `get_completion_stats()` devuelve los
recordatorios con `applicable = 0`.

- **Los grupos** (`recurring_groups`) son las secciones plegables de la pantalla y los crea el
  usuario, dentro de cada tipo. `especial` es lo que enciende el comportamiento propio de un grupo
  —hoy solo `cumpleanos`, que trae la edad y la frecuencia anual por default—; es texto y no un
  booleano `es_cumpleanos` para que el próximo caso especial no pida otra columna.
- ⚠️ **El grupo Cumpleaños nace con `uid` y `updated_at` FIJOS** (`UID_CUMPLEANOS`,
  `MARCA_SEED`). Lo crea cada instalación por su cuenta: con un uid al azar, dos máquinas
  generarían dos grupos distintos y sincronizar dejaría **dos "Cumpleaños"**. Y la marca fija y
  vieja evita el otro extremo — con `strftime('now')` cada sync haría un update inútil que podría
  pisar el renombre de la otra máquina. Empatados, solo gana quien lo edite de verdad.
- ⚠️ **`group_id` va en `PADRES_OPCIONALES`, no en `PADRES`.** El mecanismo de `PADRES` hace un
  INNER JOIN y además exige que el padre exista, así que aplicado a una FK que puede ser NULL
  **borraría al sincronizar toda rutina sin grupo**. La versión opcional traduce con un subselect
  que da NULL si el grupo no está: la rutina entra igual, en "Sin grupo".
- **Borrar un grupo nunca borra sus rutinas** (quedan sin grupo), y un grupo `especial` no se
  puede borrar.
- ⚠️ **Un solo campo decide el grupo Y el tipo** (`donde`, con valores `g:<id>` o `sin:<tipo>`).
  Eran dos campos y podían **contradecirse**: una rutina metida en un grupo de Recordatorios
  salía en esa sección pero se comportaba como rutina. Con un solo lugar donde se decide, eso
  deja de poder pasar, y el formulario tiene un campo menos.
- **Los grupos se administran en su propia sección de la lista**, no en un panel aparte: ese
  panel los listaba una segunda vez y con cinco grupos ocupaba 982px, con 54 círculos de color y
  6 selects. El lápiz abre el formulario del grupo ahí mismo (nombre y color), y el "+ Nuevo
  grupo" vive al final de cada sección — **por eso el tipo no se pregunta: sale de dónde lo
  creaste**. ⚠️ Las acciones del summary van envueltas en un `stopPropagation`: un clic ahí
  burbujearía al `<summary>` y plegaría la sección justo cuando querés editarla.
- **El color de un grupo se elige solo** (`_color_libre`: el primero de la paleta sin usar) y se
  cambia al editar. Las nueve bolitas repetidas en cada fila eran la mitad del ruido.
- **El tipo de un grupo no se edita**: moverlo de sección arrastraría todo lo que tiene adentro
  (sus rutinas perderían el porcentaje, o al revés) y no se vio la necesidad.
- ⚠️ **Los campos de una rutina viven en el macro `campos_rutina`** (`_macros.html`), compartido
  por el alta y la edición, porque **nacieron divergiendo**: el formulario de edición se quedó sin
  ellos y, como el navegador no manda lo que el formulario no tiene, guardar cualquier cambio
  —hasta el color— le borraba a la rutina el grupo, el tipo, la antelación y el año de nacimiento.
  Un formulario que pierde datos que no estás editando es peor que uno incompleto. El macro recibe
  un sufijo para los ids (vacío en el alta, `-<id>` en cada edición) y el JS lo usa para saber
  sobre qué formulario trabaja; **el "template" del cumpleaños busca dentro de SU formulario**, o
  tocaría los radios del alta.

### La frecuencia `yearly`
⚠️ **Se repite por MES-DÍA, no por días transcurridos.** El cumpleaños se venía modelando con
`every:364`, y 364 no es un año: se corre un día por año. El "Cumple del pablo" del 5 de mayo de
2023 ya caía **el 1 de mayo en 2026**, el 26 de abril en 2030 y en **febrero** para 2078.
`test_el_viejo_every_364_si_se_corre` deja el contraste fijado para que no vuelva como
"optimización".

- El **29 de febrero se festeja el 28** en años no bisiestos: desaparecer tres de cada cuatro años
  es peor que correrlo un día. `_bisiesto()` contempla los siglos (1900 y 2100 no lo son).
- `proxima_fecha()` busca día a día hasta un año y medio en vez de tener una fórmula por
  frecuencia — es justamente en una fórmula así donde se coló el error de los 364 días.
- **La antelación vive aparte** (`avisos_proximos()`): "¿aplica hoy?" y "¿cuánto falta?" son dos
  preguntas distintas, y mezclarlas haría que un recordatorio con aviso apareciera como si el día
  fuera hoy. El que cae hoy **no** es un aviso: ese sale por el camino normal.

### Dónde se ven los recordatorios
- **En su día**, como cualquier rutina: tildables y con 🎂 si son de un grupo de cumpleaños. El
  icono sale de `grupo_especial`, que viene en el mismo SELECT de `get_recurring_events()` (LEFT
  JOIN, porque no tener grupo es válido) para que no haya una consulta por vista.
- **Lo que se viene** (la antelación) va en el **día de hoy** y en el **widget**, que son los dos
  lugares donde se mira "qué hay ahora". Aparece sin tilde: todavía no pasó, no hay nada que
  marcar como hecho.
- ⚠️ **Solo se muestra parado en HOY.** Mirando el 20 de marzo del año pasado, "en 3 días" sería
  una cuenta contra una fecha que ya pasó.
- ⚠️ **La antelación NO va al calendario ni a la semana.** Cada celda dice qué pasa **ese** día, y
  llenar los tres días previos con el mismo cumpleaños lo ensucia.
- ⚠️ El panel de rutinas del día cuelga de **`day_events or avisos`**: colgaba solo de
  `day_events`, así que un recordatorio a tres días —lo único que había para mostrar— quedaba
  invisible.

### Lo que la migración NO hace, y lo que la pantalla OFRECE
Las rutinas que ya existían quedan **exactamente como estaban** (Rutina, sin grupo, misma
frecuencia), incluido el cumpleaños mal modelado. Convertirlo es un clic del usuario en la
pantalla, no una heurística en la migración: es la misma regla que los renombres de campos.

Lo que sí hace la pantalla es **ofrecerlo**, con un aviso por rutina
(`services.sugerencias_de_arreglo`):

- **La detección es acotada y no mira el contenido**: `every:N` con N entre 360 y 366. Lo único
  que se deduce del título es si sugerir además el grupo de cumpleaños —un "cada 365 días" puede
  ser un chequeo médico, y mudarlo a Cumpleaños sería inventar—.
- El aviso dice **qué** está mal, **por qué** importa (con la fecha concreta a la que ya se
  corrió) y **exactamente qué** va a cambiar. Es amarillo y no rojo: nada está roto todavía.
- `POST /recurring/<id>/arreglar-frecuencia` cambia **lo mínimo**: la frecuencia a `yearly`, y el
  grupo solo si el usuario aceptó esa parte. El `start_date` ya tiene el mes y el día correctos
  —de ahí sale la fecha buena—, así que no se toca, ni el título, ni el color, ni el `end_date`.
- **"Dejarla como está" va a `localStorage` por `uid`**: es una preferencia de vista y no un dato,
  así que no ensucia el esquema ni viaja en el sync. Por `uid` y no por `id`, que es local a cada
  base.

## Notas especiales

Categorías (el "tipo" de nota, con sus campos) y entradas. La configuración vive en `/journal`;
el alta, la vista y la edición, en la vista del día.

- ⚠️ **El alta vive SOLO en el día.** El calendario y la semana muestran el badge de lo que
  registraste, pero no dejan cargar (`446638b`, *"vista muy cargada"*). De esa decisión quedó vivo
  todo el JS del formulario llamando a elementos que ya no existían —45 líneas por plantilla que
  nunca corrieron— y las dos pantallas serializando las categorías a JSON para nadie. Limpiado, y
  con un tripwire para que no vuelva.
- **Elegida la categoría, el selector colapsa** al chip elegido + "Cambiar", y el formulario se
  tiñe con su color. No es solo estética: con la fila entera a la vista, un clic distraído en otro
  chip reconstruía los campos y **vaciaba lo escrito**. Hoy re-elegir la misma no reconstruye,
  "Cambiar" no toca ni el hidden ni los campos, y con una sola categoría se elige sola.
- ⚠️ **Archivar afecta dónde se ESCRIBE, nunca dónde se lee.** `get_journal_categories()` filtra
  por `active` por default —lo correcto en el único lugar donde se elige una, el alta del día— y
  todo lo que lee historia pide `incluir_archivadas=True`: `chartable_fields`, `tiempo_comparado`,
  `emociones_frecuentes`, el `fieldinfo` de Estadísticas y la propia `/journal`. Al revés,
  archivar haría desaparecer meses de gráficos y de resumen sin que nada avise. Hay un tripwire.
- **Borrar una categoría se lleva todas sus notas**: snapshot previo (`health-prejournal-<ts>`) y
  el número real en la confirmación, porque "y todas sus notas" no deja saber si son dos o
  doscientas.
- ⚠️ **Quitar un campo esconde lo guardado para siempre**: la vista y la edición iteran la
  definición de la categoría, así que un valor sin campo no se ve en ningún lado. Por eso cada
  fila del editor dice cuántas notas lo usan (`journal_field_usage()`) y el ✕ sobre una con datos
  no borra: la marca con sus controles `disabled` —no viajan, y los arreglos paralelos quedan
  igual de alineados— con un aviso inline y un Deshacer. Se va recién al guardar.
- **Reordenar con ↑/↓ no es un renombre**: el `field_oldlabel[]` se mueve con su fila, así que
  `_detect_label_renames` no ve nada. Antes, meter un campo en el medio obligaba a borrar y
  recrear, que es justo lo que **no** migra.
- ⚠️ **La búsqueda confirma en Python.** El `LIKE` sobre `values_json` es solo para acotar: ese
  JSON guarda `{etiqueta: valor}`, así que un LIKE crudo devuelve toda categoría que tenga un
  campo llamado "Notas" apenas buscás "notas". Se busca lo que escribiste, no cómo se llama el
  casillero.
- **No hay validación de "nota vacía"**: una categoría sin campos es un marcador legítimo ("hoy
  medité"), y exigir contenido rompería ese uso.

## Volver de una pantalla del navbar

Las ocho pantallas que se abren desde el navbar llevan el mismo `.page-back .back-link`
("← Volver" si venís de algún lado, "← Calendario" si entraste por URL), y el navbar les pasa
`back=request.full_path`. `safe_back()` (`helpers.py`) corta cualquier URL externa.

- ⚠️ **Sin ese enlace no hay botón Y TAMPOCO Escape**: el handler global de `base.html` navega
  atrás buscando exactamente un `.page-back .back-link`. Tareas, Estadísticas y Búsqueda no lo
  tenían y quedaban sin salida, mientras las otras cinco sí. Al agregar una pantalla al navbar,
  el enlace de vuelta es parte de la pantalla.
- ⚠️ **En el visor de tareas `back` viaja DENTRO de `_filtros()`**, no como un parámetro aparte:
  así lo arrastran solos los enlaces de estado y período, el buscador y `_back_to_todos()`.
  Afuera, filtrar o mover una tarea te dejaba sin camino de vuelta.
- En `/search` el hidden del formulario **conserva** el `back` en vez de recalcularlo, o buscar
  dos veces seguidas encadenaba el volver a la búsqueda anterior.

## Confirmaciones: ninguna es del navegador

`confirm()` en la ventana de escritorio sale encabezado por **"127.0.0.1:65015 dice"**, que es lo
contrario de una app propia. Eran 16 repartidos en 8 pantallas, todos con la misma forma
(`onsubmit="return confirm('...')"` sobre un `<form>`), así que el diálogo vive en un solo lugar y
cada formulario **declara** lo suyo:

```html
<form ... data-confirmar="¿Eliminar esta tarea?" data-confirmar-ok="Eliminar"
      onsubmit="return false;">
```

- `data-confirmar` el mensaje, `data-confirmar-ok` el texto del botón —que **nombra la acción**
  ("Vaciar el perfil", "Borrar los futuros") en vez del "Aceptar" genérico que era lo único que
  podía dar el navegador—, y `data-confirmar-suave` para las dos que no destruyen nada (combinar
  datos del sync, traer tareas a hoy): el botón es rojo por defecto porque las otras catorce
  borran o reemplazan.
- ⚠️ **El `onsubmit="return false;"` es la guarda y no se puede sacar.** El `confirm()` lo ponía
  el navegador, así que aparecía aunque el JS de la app estuviera roto; con un modal propio sin
  esa guarda, un JS roto enviaría el formulario **sin preguntar nada** —y cuatro de estos borran
  datos—. Con ella, si `confirmar.js` no corre el formulario simplemente no se envía: que sin JS
  no se pueda borrar es aceptable, que borre sin preguntar no. Mismo criterio que el botón Guardar
  de Ajustes. `test_todo_formulario_con_confirmacion_lleva_la_guarda` lo fija por formulario.
- ⚠️ **Los saltos de línea van como `&#10;`**: los `\n` de los mensajes eran escapes de
  JavaScript y en un atributo HTML se verían como el texto literal `\n`.
- ⚠️ **Solo funciona bajo `base.html`**, que es donde están el modal y el script: `widget.html` es
  plantilla propia y un `data-confirmar` ahí no haría nada (con la guarda, el formulario no se
  enviaría). Hay un test que lo impide.
- Las tres frases de borrado (`BORRAR DATOS` / `BORRAR PERFIL` / `BORRAR TODOS LOS PERFILES`) son
  **otra** barrera y siguen igual: el botón nace `disabled` y lo habilita escribir la frase. El
  modal es el segundo paso, no el reemplazo.
- **Un aviso de validación NO es una confirmación**: va **inline, al lado de lo que falta
  completar**, no en un modal. Los dos casos son iguales y comparten `.form-error`: el
  `#weekday-error` de Rutinas y el `#jday-cat-error` del alta de nota especial del día. ⚠️ Los dos
  existen porque el valor viaja en un `<input type="hidden">` (los días de la semana, la categoría
  elegida con chips) y **a un hidden no le aplica `required`**: la validación es a mano, y por eso
  es fácil que vuelva como diálogo. El del día era un `alert('Seleccioná una categoría.')`.
- `test_confirmar.py` es el tripwire de que no vuelva un `confirm()`, `alert()` o `prompt()` a
  ninguna plantilla **ni a ningún `.js`**. Lee los archivos y no las rutas, así cubre los 16 sin
  tener que armar dos perfiles, un gráfico y una previa de sync para que aparezcan los botones.
  Es estricto a propósito: salta hasta con un `alert()` escrito dentro de un comentario.

## Color por defecto de las notas rápidas

`services.color_para_nota_nueva(elegido)` decide con qué color se guarda una nota nueva:
**lo que elegiste a mano siempre gana**, y si no elegiste nada manda el ajuste `nota_color`
(vacío = sin color, `aleatorio` = uno de `NOTE_COLORS`, o un color fijo).

- ⚠️ **"No elegí color" llega como string VACÍO, no como ausente**: los formularios del día, del
  calendario y del widget siempre mandan el campo `color`, con el radio de "sin color"
  (`value=""`) marcado por default. La condición es sobre el contenido, no sobre la presencia.
- **El color se guarda en la nota**, no se deriva al mostrar. Fue decisión suya y explícita:
  *"no sería sin color sino como si se hubiera elegido un color elegido aleatorio"*. La
  consecuencia aceptada es que `notes.color` deja de distinguir "no elegí" de "elegí esto" cuando
  el ajuste está activo.
- **Dos call sites y no cuatro**: `day.note_add` recibe las altas del día, del calendario **y** de
  la semana (las tres plantillas postean ahí), y `widget.nota` es el otro.
- El control en Ajustes es de **swatches**, el tercer tipo de esa pantalla (además del switch y el
  segmentado): son 11 opciones y el andamio `hacer.ps1 nuevo ajuste` no lo genera.
- ⚠️ **El formulario de alta viene con el color ya marcado** (`services.color_sugerido()`,
  inyectado como `color_sugerido` por el context processor): con `aleatorio` el color se decidía
  recién al insertar y la nota aparecía pintada de un color que nunca habías visto. Como el
  formulario ahora **manda ese color**, `color_para_nota_nueva` lo respeta por la regla de "lo
  elegido gana" — si mandara vacío, el servidor sortearía **otro** y la previsualización mentiría.
  Sortea por página, así que cada recarga (y cada nota guardada, que recarga) trae uno nuevo.
  El radio marcado por el servidor **no dispara su propio `onchange`**, así que el fondo del campo
  lo pinta un script de `base.html` al cargar; es `change` y no `input` a propósito, porque
  `input` es lo que mira `refresco.js` para saber si hay algo tipeado. El widget solo marca el
  swatch: nunca pintó el fondo, tampoco al elegir a mano.

## La pantalla de Estadísticas

Tenía tres problemas de fondo y los tres eran de diseño, no de código: **nacía vacía** (sin campos
marcados con 📈 no mostraba nada, aunque hubieras anotado todos los días durante meses),
**ignoraba casi todo lo que la app registra** (notas rápidas, tareas y la rueda de emociones no se
miraban) y **ningún número era comparativo** — un `0 / 15 · 0%` no dice si venís mejorando.

- **El bloque "Lo que anotaste" va SIEMPRE**, incluso en cero, y se arma con las funciones de rango
  que ya existían (`get_notes_range`, `get_todo_counts_range`, `get_journal_entries_range`): no
  hizo falta SQL nuevo. Es lo que hace que la pantalla cuente algo el día uno, sin configurar nada.
  "Un día con algo anotado" incluye nota, tarea o nota especial; **tildar una rutina no cuenta**:
  es cumplir algo que ya estaba planeado, no anotar.
- ⚠️ **Un delta contra un período anterior sin datos no es una mejora.** Si antes no usabas la app,
  un "▲ +23" es ruido que se lee como un logro. Sin datos previos el delta viaja `None` y la
  pantalla muestra un guion (`resumen_comparado`, `tiempo_comparado`). La adherencia usa la misma
  regla con su propia señal: se compara **solo si entonces marcabas rutinas** (alguna completion en
  el período anterior), porque si no, todas aparecerían subiendo 90 puntos contra una app vacía.
- ⚠️ **Un solo período para toda la pantalla.** `charts.range_days` sigue existiendo y se sigue
  guardando, pero **ya no decide el render**: era una segunda noción de rango y hacía que dos
  tarjetas al lado mostraran ventanas distintas sin decirlo. Cada tarjeta dice de qué período
  habla. Lo mismo con "Tiempo por actividad", que eran tres ventanas fijas (semana / mes / 90 días)
  ajenas al selector.
- Los períodos viven en `routes/main.PERIODOS`; el default son **30 días**. `mes` ("Este mes") es
  el único de largo variable —el mes calendario en curso— porque la gente piensa en meses.
  Se llama `periodo` en el código y en la UI, nunca "rango" (mismo criterio que el visor de
  tareas); el parámetro de la URL se quedó en `range=` para no romper enlaces guardados.
- ⚠️ **Las dos ruedas de emociones se cuentan por separado.** Willcox y Ekman son taxonomías
  distintas: sumar "Ira" con "Enojado" sería inventar una equivalencia que nadie definió. Se cuenta
  por **emoción base** (el primer nivel, que es la que tiene color); los matices de abajo
  dispersarían todo en frecuencia 1.
- Los colores salen de `appconfig.EMOTION_COLORS` —estaban como literales dentro de `day.html`— y
  un test los compara **contra el JS de cada rueda**: una emoción que falte ahí sale del gris de
  fallback sin que nada avise, y la estadística mentiría el color.
- **No hay rachas ni gamificación.** Se rechazaron para el visor de tareas (*"el visor no es un
  tablero"*) y acá no se sumaron sin pedirlo. Queda anotado.

## La pantalla de Ajustes

Cero `<select>` entre los 17 ajustes, seis secciones colapsables y **guardado al instante**.

- **Cuatro controles, y cuál va dónde no es estético**: switch deslizable para los 9 que se leen
  como prendido/apagado (aunque el vocabulario cambie: `on/off`, `show/hide`, `open/collapsed`);
  segmentado para los que son **esto o aquello** (`24h/12h`, `mon/sun`, `week/day`) y para los de 3
  opciones; swatches para el tema y el color de nota; y el de **medida** (tamaño de ventana), que
  es un segmentado de medidas comunes más dos números para escribir la tuya. Un switch en "24 h"
  haría preguntar *"¿12 h está prendido?"*.
- ⚠️ **`window_size` es el único ajuste sin whitelist cerrada.** Admite `maximizada`, una de
  `VENTANA_PRESETS` o una medida escrita a mano, así que trae **su propio validador** en el
  esquema (`valida: es_resolucion`) y toda la app valida por `appconfig.valor_valido()`. Eso no es
  opcional: `get_all_settings()` clampea al default lo que no está en `choices`, así que sin el
  validador elegir una medida propia y recargar la borraba. Hay un test que lo fija.
  El radio de "Otra" lleva el valor que escriben los dos números y dispara **su** `change`, así el
  guardado al instante es el mismo camino que el de los presets; sin JS quedan los presets.
- **El cambio se aplica EN CALIENTE**, no al próximo arranque: es un ajuste que se elige mirando
  la ventana. Lo hace `escritorio/widget.aplicar_tamano_principal()` desde `_guardar_ajuste`, por
  el mismo canal que ya usan las rutas del widget (`routes/widget.py` importa ese módulo, que
  degrada a no-op sin pywebview). De maximizada a una medida hay que `restore()` primero, o el
  `resize()` no se ve.
- ⚠️ **El tamaño pedido se acota a la pantalla** (`widget.medidas_ventana()`, con
  `webview.screens`): los ajustes viajan en el sync, así que una medida elegida en un monitor de
  2560 puede llegar a una máquina de 1366, y una ventana más grande que la pantalla nace con los
  bordes —y la barra de título— afuera. El cálculo vive junto al handle de la ventana grande para
  que el arranque (`main.tamano_inicial()`) y el cambio en caliente no puedan divergir.
  `maximizada` usa `create_window(maximized=True)` y deja el default como tamaño de "restaurar".
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
- ⚠️ **`available` y `can_reinstall` exigen `current_version()`**: `apply_update()` copia sobre `base_dir()`, que en dev es el repo, y en Windows con `robocopy /MIR`. Sin esa guarda, un chequeo forzado en dev habilitaría un botón que borra el repo.
- ⚠️ **`base_dir()` es la carpeta de la INSTALACIÓN, y hay UNA sola definición** (en `updater.py`;
  `escritorio/main.py` la importa). Sin congelar sube **tres** niveles, porque el módulo vive en
  `bitacora/escritorio/`. Estuvo duplicada y **divergió**: la copia del updater subía uno solo, y
  como **en Linux la app corre desde el código** (nada de PyInstaller: bundlear WebKitGTK es
  frágil) ese era el camino real allá — `apply_update` volcaba la carpeta nueva **dentro de
  `bitacora/escritorio/`** y después buscaba ahí `venv/bin/pip`, `instalar.sh` y `bitacora.sh`,
  que están en la raíz. No borraba nada (el rsync no lleva `--delete`) pero la actualización no
  se aplicaba, la app no se relanzaba y quedaba una copia anidada. Hay un tripwire que falla si
  aparece una segunda definición, y la verificación de verdad es armar una instalación desde el
  tarball en WSL y preguntarle al updater dónde copiaría.

## Convenciones de código

- Mensajes de commit en español, prefijo minúscula: `fix:`, `stats:`, `journal:`, `linux:`, etc.
- Sin `Co-Authored-By` en los commits.
- Sin comentarios que expliquen el *qué* — solo el *por qué* cuando no es obvio.
- `MESES[]` hardcodeado en `helpers.py` (no `calendar.month_name` — depende del locale del sistema).
- Renames de datos de usuario: solo con señal explícita (hidden `field_oldlabel[]` o control de UI); nunca por heurística.
- **La paleta de colores de notas, rutinas y categorías es `appconfig.NOTE_COLORS`**, inyectada como `note_colors`. Estaba repetida como literal en **seis** plantillas; también es el `choices` del ajuste `nota_color`. `test_nota_color.py` falla si vuelve a aparecer una paleta copiada (tres o más colores en una línea de una plantilla) — un color suelto sí es legítimo, como el de una categoría predefinida de `journal.html`.
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
- **Las columnas laterales arrancan en 400px** (`--day-side`), no en 300: con 300 al texto de una
  tarea le quedaban 103px y los títulos se partían en dos líneas. 400 es lo más ancho que entra
  sin achicar la card en una pantalla de 1600.
  ⚠️ **Las tres columnas se declaran siempre, incluso sin panel de rutinas.** Se probó no
  declarar la tercera cuando el panel no está —una columna vacía igual mide su ancho y corre todo
  a la izquierda— y **se revirtió por pedido del usuario**: el tema del layout del día se va a
  rehacer entero más adelante, con algo más adaptable, y mientras tanto la vista se queda como
  estaba. No volver a intentarlo suelto.
- **El panel de tareas arranca en 420px de alto** (`min-height: var(--day-alto-tareas, 420px)`).
  El mismo var en `height` y en `min-height` es lo que deja el arrastre intacto: con un alto
  elegido los dos valen lo mismo y se puede achicar; sin arrastrar, crece con las tareas y **no
  aparece scroll interno**.
- ⚠️ **`.main-day` NO lleva `max-width`**, como `.main-wide` (el calendario). Con el tope de
  1400px que tenía, en una pantalla grande el día vivía en 1400px centrados y ensanchar el panel
  solo podía robarle ancho a la card: los costados quedaban sin usar. Y las tres columnas de
  `.day-layout` son **topes `minmax(0, X)` sin ninguna `1fr`** + `justify-content: center`: con un
  `1fr` en el medio, esa columna se comía todo el sobrante y la card quedaba lejísimos del panel.
  Así el conjunto mide lo que necesita, queda centrado y el sobrante va **afuera** — que es el
  espacio que se gana al ensanchar. El tope del arrastre sale de la pantalla
  (`(ancho - CARD_MIN - gaps) / 2`, hasta 900) y no es un número fijo: con el 560 fijo que tenía
  quedaba media pantalla sin usar.
  ⚠️ **Lo que ese tope le reserva a la card es su mínimo legible (520), no sus 760.**
  Reservándole los 760, achicar la ventana se lo cobraba siempre al panel: en 1372px quedaba en
  262 y las tareas se leían **a una palabra por línea**, con scroll interno. Y se sentía
  permanente porque solo se salía de ahí con el doble clic que resetea — que es justo el estado
  que se ve bien, porque sin ancho pedido el grid achica la card y deja los paneles en su lugar.
- ⚠️ **La fila de una tarea (`.todo-row`) envuelve**: el panel es angosto por elección del
  usuario, y al mínimo las acciones —que son `flex-shrink: 0`— se salían del panel (41px afuera)
  dejando el texto en 55px, o sea cinco líneas de una palabra. Con `flex-wrap: wrap` bajan a una
  segunda línea, pegadas a la derecha con `margin-left: auto`. Es la misma solución que el visor
  `/tareas` ya usaba en su media query de ≤600px.
  ⚠️ **La base del texto es chica (70px) a propósito**: con una grande (110px) el texto tampoco
  entraba al lado del asa y el tilde y bajaba a una línea propia — tres líneas por tarea en vez
  de dos.
- ⚠️ **Los paneles del día se arrastran a lo ancho Y a lo alto**, con un helper compartido en
  `day.js` (`arrastrable({grip, eje, variable, pref, ...})`) que usan los tres agarres. El ancho es
  uno solo para los dos paneles; **el alto es de cada uno**, porque tienen contenidos muy distintos.
  Con un alto fijo el panel pasa a ser columna flex y **scrollea la lista**, no el panel: así el
  título y el "Agregar una tarea" quedan siempre a la vista. El hijo que scrollea necesita
  `min-height: 0` — un item flex no se encoge por debajo de su contenido y sin eso el `overflow-y`
  no actúa nunca.
  ⚠️ **El tope del alto va en el JS, no como `max-height` en el CSS**: un `max-height` también
  aplicaría en modo automático y a alguien con treinta tareas le aparecería un scroll interno que
  hoy no tiene. Y el tope es `alto de ventana − 40` porque `.day-side` es `position: sticky`: un
  panel más alto que la ventana deja de quedarse pegado.
- ⚠️ **El ancho del panel de tareas del día se arrastra** (`.day-side-grip`, lo maneja `day.js`,
  queda en `localStorage`; doble clic resetea). Las columnas laterales toman el ancho pedido
  (`--day-side`, 300px) y la del medio absorbe con `minmax(0, 1fr)`. **Antes eran `1fr` con la del
  medio capada en 760px y así el panel no podía crecer**: la del medio se quedaba con el espacio
  primero. El tope de lectura se mudó a `.day-card`. Dos cosas que salieron de probar el arrastre:
  se guarda el ancho **pedido** y no el medido (midiendo, cada recarga lo encogía: 402 → 354 →
  306…), y por eso mismo el arrastre es 1:1 con el mouse.
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
- **pywebview / localStorage**: `webview.start(private_mode=False, storage_path=...)` — sin eso
  pywebview borra el perfil del WebView2 al cerrar.
  ⚠️ **Pero eso NO alcanza: hoy el `localStorage` se pierde igual en cada arranque.** Vive por
  **origen**, y el origen es `http://127.0.0.1:<puerto>` con un puerto efímero distinto cada vez
  (`puerto_seguro()`, que nació para esquivar `ERR_UNSAFE_PORT`). Medido en una instalación real:
  **52 orígenes** acumulados, con `app_zoom` guardada bajo 18 de ellos, `setOpen-apariencia` bajo
  15 y `day_side_width` bajo 13. O sea que se resetean en cada arranque los colapsables
  (`setOpen-*`, `todos*Open`, `widgetNotasHoy`), el zoom, `cal_cell_height`, el ancho y alto de
  los paneles del día y el "dejarla como está" de las sugerencias de rutinas. En el navegador sí
  persisten: ahí el puerto es fijo. **Arreglo pendiente** (decisión del usuario, 2026-09-14):
  recordar el último puerto en un archivo del dispositivo y reusarlo si sigue libre. Hasta
  entonces el manual dice la verdad —"mientras la app está abierta"— en vez de prometerlo.
- **DB path en tests**: `bitacora.database.conn.DB_PATH` se parchea directamente (por string, así que un cambio de layout lo rompe ruidoso); `get_db()` lo lee en cada call.
