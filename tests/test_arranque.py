"""El arranque de la app de escritorio: que una instalación NUEVA pueda abrir.

Lo que necesita una ventana de verdad vive en tools/smoke_desktop.py; acá va lo que se puede
verificar sin display, que es justo donde se escapó el bug que estos tests fijan.
"""
import sqlite3
from pathlib import Path

import pytest

from bitacora import database as db
from bitacora import profiles
from bitacora.app import create_app
from bitacora.escritorio import main as desktop


@pytest.fixture
def instalacion_nueva(tmp_path, monkeypatch):
    """Una carpeta de datos virgen: la de una computadora donde se acaba de instalar la app."""
    monkeypatch.setattr(desktop, "APP_DIR", tmp_path)
    monkeypatch.setattr(desktop, "DB_FILE", tmp_path / "health.db")
    # Sin esto _migrate_first_run se traería la health.db del repo a la carpeta del test.
    monkeypatch.setattr(desktop, "base_dir", lambda: tmp_path / "sin-instalacion-previa")
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    # profiles.aplicar() lo rebindea; parchearlo acá es lo que lo deja como estaba al terminar.
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "health.db"))
    return tmp_path


def test_una_instalacion_nueva_puede_abrir_la_ventana(instalacion_nueva):
    """El bug de sep 2026: la ventana abre con el tamaño del ajuste `window_size`, y eso se lee
    ANTES del primer request. En una instalación nueva no había ni tablas, así que el arranque
    moría con "no such table: settings" y la app no abría NUNCA en una máquina nueva."""
    desktop.preparar_datos()

    ancho, alto, _maximizada = desktop.tamano_inicial()
    assert (ancho, alto) >= desktop.MIN_SIZE


def test_el_arranque_lee_los_ajustes_que_necesita_antes_del_primer_request(instalacion_nueva):
    """El tamaño no es el único: el ajuste de la bandeja, el del widget y el toast de tareas
    también se leen sin que haya pasado ningún request todavía."""
    desktop.preparar_datos()

    assert db.get_setting("cerrar_a_bandeja", "on") in ("on", "off")
    assert db.get_setting("widget_autostart", "off") in ("on", "off")
    assert db.get_all_settings()["window_size"]
    assert db.count_overdue_todos("2000-01-01") == 0


def test_preparar_los_datos_dos_veces_no_cambia_nada(instalacion_nueva):
    """Corre en cada arranque, incluido el de una instalación que ya tenía datos."""
    desktop.preparar_datos()
    db.set_setting("window_size", "1366x768")

    desktop.preparar_datos()

    assert db.get_setting("window_size") == "1366x768"
    assert len(__import__("bitacora.profiles", fromlist=["x"]).listar()) == 1


def test_una_instalacion_nueva_sirve_la_app(instalacion_nueva):
    """De punta a punta y sin ventana: una carpeta de datos virgen tiene que poder mostrar la
    pantalla principal y guardar algo, no solo no explotar al arrancar.

    Este NO es el tripwire del bug —pasa igual sin el fix, porque cualquier request pasa por el
    `init_db()` del before_request—: lo que cubre es que la instalación virgen sirva la app
    entera. El bug lo fijan los de arriba, que leen la base sin pasar por ningún request."""
    desktop.preparar_datos()

    cliente = create_app().test_client()
    assert cliente.get("/", follow_redirects=True).status_code == 200
    r = cliente.post("/day/2026-09-14/note/add", data={"content": "la primera nota", "color": ""},
                     follow_redirects=True)
    assert r.status_code == 200 and "la primera nota" in r.data.decode()


def test_reanuda_una_instalacion_que_quedo_a_medias(instalacion_nueva):
    """La máquina donde YA corrió la versión rota: el perfil quedó creado y su health.db quedó
    en 0 bytes (cualquier cosa que toque la ruta lo crea, aunque después falle la lectura).

    Un archivo de 0 bytes es una base SQLite válida y vacía, así que el arranque arreglado tiene
    que escribirle el esquema adentro y seguir — sin duplicar el perfil que ya estaba."""
    desktop._migrate_first_run()
    desktop._migrate_a_perfiles()
    profiles.aplicar()
    with pytest.raises(sqlite3.OperationalError):
        db.get_all_settings()                      # así moría, después de dejar el archivo
    activa = Path(db.db_path())
    assert activa.stat().st_size == 0, activa.stat().st_size

    desktop.preparar_datos()

    assert desktop.tamano_inicial()
    assert [p["nombre"] for p in profiles.listar()] == ["Principal"]
    assert create_app().test_client().get("/", follow_redirects=True).status_code == 200


def test_sin_crear_el_esquema_la_base_nueva_no_se_puede_leer(tmp_path, monkeypatch):
    """El contraste, para que se vea por qué `preparar_datos()` tiene que crear el esquema y no
    alcanza con el `init_db()` del before_request: el arranque lee antes que eso."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "virgen.db"))
    with pytest.raises(sqlite3.OperationalError):
        db.get_setting("window_size", "")
