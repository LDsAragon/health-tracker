"""Perfiles locales: aislamiento, cambio en caliente y las rejas para no perder datos."""
import os

import pytest

import database as db
import profiles
import app as flask_app


@pytest.fixture
def perfiles(tmp_path, monkeypatch):
    """Raíz de perfiles aislada. monkeypatch restaura env y DB_PATH al terminar."""
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "sin-perfil.db"))
    p = profiles.crear("Principal")
    profiles.usar(p["slug"])
    return tmp_path


@pytest.fixture
def cliente(perfiles):
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


# ── El módulo ────────────────────────────────────────────────────────────────

def test_sin_raiz_los_perfiles_estan_apagados(monkeypatch):
    """Modo navegador y tests: sin HT_PERFILES nada cambia. Es lo que mantiene intactos
    los 299 tests que no saben que existen los perfiles."""
    monkeypatch.delenv("HT_PERFILES", raising=False)
    assert profiles.raiz() is None
    assert profiles.activo() is None
    assert profiles.listar() == []

def test_slug_no_escapa_de_la_raiz():
    """Un nombre con ../ o / escribiría fuera de la carpeta de datos."""
    for peligro in ("../../etc/passwd", "..", "/abs/oluto", r"C:\Windows"):
        s = profiles.slug(peligro)
        assert "/" not in s and "\\" not in s and ".." not in s

def test_slug_translitera_acentos():
    assert profiles.slug("Matías Ñandú") == "matias-nandu"

def test_crear_no_pisa_un_slug_existente(perfiles):
    a = profiles.crear("Trabajo")
    b = profiles.crear("trabajo")          # mismo slug
    assert a["slug"] != b["slug"]
    assert len({p["slug"] for p in profiles.listar()}) == len(profiles.listar())

def test_cada_perfil_tiene_uid_propio(perfiles):
    profiles.crear("Otro")
    uids = {p["uid"] for p in profiles.listar()}
    assert len(uids) == len(profiles.listar())
    assert all(len(u) == 32 for u in uids)

def test_dispositivo_es_estable(perfiles):
    assert profiles.dispositivo() == profiles.dispositivo() != ""

def test_renombrar_no_mueve_la_carpeta(perfiles):
    slug = profiles.activo()["slug"]
    ruta = profiles.db_de(slug)
    profiles.renombrar(slug, "Otro nombre")
    assert profiles.activo()["nombre"] == "Otro nombre"
    assert profiles.db_de(slug) == ruta

def test_indice_corrupto_no_tumba_la_app(perfiles):
    (perfiles / profiles.INDICE).write_text("{ esto no es json", encoding="utf-8")
    assert profiles.leer()["perfiles"] == []
    assert profiles.activo() is None


# ── Aislamiento y cambio en caliente ─────────────────────────────────────────

def test_cambiar_de_perfil_mueve_la_db(perfiles):
    a = profiles.activo()["slug"]
    b = profiles.crear("Trabajo")["slug"]
    profiles.usar(b)
    assert db.db_path() == profiles.db_de(b) != profiles.db_de(a)

def test_los_datos_no_se_cruzan(perfiles):
    a = profiles.activo()["slug"]
    db.init_db()
    db.add_note("2026-06-09", "de Principal")
    b = profiles.crear("Trabajo")["slug"]
    profiles.usar(b)
    db.init_db()
    assert db.get_notes_for_date("2026-06-09") == []
    db.add_note("2026-06-09", "de Trabajo")
    profiles.usar(a)
    assert [n["content"] for n in db.get_notes_for_date("2026-06-09")] == ["de Principal"]

def test_cada_perfil_tiene_sus_backups(perfiles):
    """backup_path deriva de la ruta de la DB: sin eso el segundo perfil pisaba los del primero."""
    db.init_db()
    uno = db.backup_path("x")
    profiles.usar(profiles.crear("Trabajo")["slug"])
    db.init_db()
    assert os.path.dirname(db.backup_path("x")) != os.path.dirname(uno)

def test_usar_un_slug_inexistente_no_hace_nada(perfiles):
    antes = db.db_path()
    assert profiles.usar("no-existe") is False
    assert db.db_path() == antes


# ── Borrado ──────────────────────────────────────────────────────────────────

def test_no_se_puede_borrar_el_unico_perfil(perfiles):
    ok, _ = profiles.borrar(profiles.activo()["slug"])
    assert not ok and len(profiles.listar()) == 1

def test_no_se_puede_borrar_el_perfil_activo(perfiles):
    profiles.crear("Trabajo")
    ok, _ = profiles.borrar(profiles.activo()["slug"])
    assert not ok and len(profiles.listar()) == 2

def test_borrar_saca_el_perfil_y_sus_archivos(perfiles):
    b = profiles.crear("Trabajo")["slug"]
    profiles.usar(b)
    db.init_db()
    ruta = profiles.db_de(b)
    profiles.usar(profiles.listar()[0]["slug"])
    ok, _ = profiles.borrar(b)
    assert ok
    assert b not in {p["slug"] for p in profiles.listar()}
    assert not os.path.exists(ruta)


# ── Rutas ────────────────────────────────────────────────────────────────────

def test_el_switcher_aparece_recien_con_dos_perfiles(cliente):
    """Con un solo perfil la app se ve igual que siempre."""
    assert b"nav-perfil" not in cliente.get("/ajustes").data
    profiles.crear("Trabajo")
    assert b"nav-perfil" in cliente.get("/ajustes").data

def test_crear_desde_la_ruta(cliente):
    cliente.post("/perfiles/crear", data={"nombre": "Trabajo"})
    assert "Trabajo" in {p["nombre"] for p in profiles.listar()}

def test_crear_sin_nombre_no_crea(cliente):
    cliente.post("/perfiles/crear", data={"nombre": "   "})
    assert len(profiles.listar()) == 1

def test_borrar_exige_la_frase(cliente):
    b = profiles.crear("Trabajo")["slug"]
    cliente.post("/perfiles/borrar", data={"slug": b, "confirm_text": "borrar perfil"})
    assert b in {p["slug"] for p in profiles.listar()}   # minúsculas no cuentan
    cliente.post("/perfiles/borrar", data={"slug": b, "confirm_text": "BORRAR PERFIL"})
    assert b not in {p["slug"] for p in profiles.listar()}

def test_cambiar_desde_la_ruta_redirige_al_inicio(cliente):
    b = profiles.crear("Trabajo")["slug"]
    r = cliente.post("/perfiles/usar", data={"slug": b})
    assert r.status_code == 302 and db.db_path() == profiles.db_de(b)


# ── Migración del layout viejo ───────────────────────────────────────────────
# Es el camino que corre en la máquina de cada usuario al actualizar.

@pytest.fixture
def appdir_viejo(tmp_path, monkeypatch):
    """APP_DIR con una health.db suelta, como antes de los perfiles."""
    import desktop
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr(desktop, "APP_DIR", tmp_path)
    monkeypatch.setattr(desktop, "DB_FILE", tmp_path / "health.db")
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "health.db"))
    db.init_db()
    db.add_note("2026-06-09", "dato de antes")
    db.add_todo("2026-06-09", "tarea de antes")
    return tmp_path


def test_migracion_conserva_todo_y_borra_el_original(appdir_viejo):
    import desktop
    antes = db.table_counts(str(appdir_viejo / "health.db"))
    desktop._migrate_a_perfiles()
    profiles.aplicar()

    assert db.table_counts(db.db_path()) == antes
    assert [n["content"] for n in db.get_notes_for_date("2026-06-09")] == ["dato de antes"]
    assert not (appdir_viejo / "health.db").exists()
    assert db.db_path() == profiles.db_de("principal")

def test_migracion_deja_backup_previo(appdir_viejo):
    import desktop
    desktop._migrate_a_perfiles()
    previos = list((appdir_viejo / "backups").glob("health-preperfiles-*.db"))
    assert len(previos) == 1
    assert db.is_valid_db(str(previos[0]))

def test_migracion_es_idempotente(appdir_viejo):
    import desktop
    desktop._migrate_a_perfiles()
    desktop._migrate_a_perfiles()
    desktop._migrate_a_perfiles()
    assert len(profiles.listar()) == 1

def test_migracion_deja_el_leeme_del_downgrade(appdir_viejo):
    """Una versión vieja instalada encima buscaría APP_DIR/health.db y arrancaría en blanco."""
    import desktop
    desktop._migrate_a_perfiles()
    texto = (appdir_viejo / "LEEME-perfiles.txt").read_text(encoding="utf-8")
    assert "perfiles" in texto and "no perdiste" in texto.lower()

def test_instalacion_nueva_sin_db_previa(tmp_path, monkeypatch):
    """Arranque limpio: crea el perfil y deja que init_db arme el esquema."""
    import desktop
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr(desktop, "APP_DIR", tmp_path)
    monkeypatch.setattr(desktop, "DB_FILE", tmp_path / "health.db")
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "health.db"))
    desktop._migrate_a_perfiles()
    profiles.aplicar()
    db.init_db()
    db.add_note("2026-06-09", "arranque limpio")
    assert [n["content"] for n in db.get_notes_for_date("2026-06-09")] == ["arranque limpio"]
