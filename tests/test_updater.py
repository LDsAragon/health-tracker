"""Tests del updater: parseo del changelog y guardas del chequeo bajo demanda.

Nunca se le pega a la API real de GitHub: se parchea urllib.request.urlopen.
"""
import io
import json

import pytest

import updater


# ── changelog() ──────────────────────────────────────────────────────────────

# Cuerpo tal cual lo arma tools/publish_release.ps1
BODY_REAL = """## Cambios

- fix: los graficos de duracion salian en minutos crudos
- stats: resumen 'tiempo por actividad'

---
**Windows:** descomprimí el zip, entrá a la carpeta `Bitacora` y ejecutá `Bitacora.exe`.
**Linux:** descomprimí el tar.gz, entrá a la carpeta `Bitacora` y ejecutá `./instalar.sh`.
"""


def test_changelog_solo_los_bullets():
    assert updater.changelog(BODY_REAL) == [
        "fix: los graficos de duracion salian en minutos crudos",
        "stats: resumen 'tiempo por actividad'",
    ]


def test_changelog_descarta_instrucciones_de_instalacion():
    """Lo de abajo del '---' es cómo instalar a mano: adentro de la app no sirve."""
    notas = " ".join(updater.changelog(BODY_REAL))
    assert "Windows:" not in notas
    assert "instalar.sh" not in notas
    assert "## Cambios" not in notas


def test_changelog_sin_bullets_devuelve_texto():
    assert updater.changelog("## Notas\n\nArreglos varios.") == ["Arreglos varios."]


def test_changelog_vacio():
    assert updater.changelog("") == []
    assert updater.changelog(None) == []


# ── force_check() ────────────────────────────────────────────────────────────

def _fake_github(monkeypatch, tag="v2099-01-01", asset_name="Bitacora-Windows-2099-01-01.zip"):
    """Parchea urlopen para que _do_check vea un release con asset."""
    payload = {
        "tag_name": tag,
        "body": BODY_REAL,
        "assets": [{"name": asset_name,
                    "browser_download_url": "https://example.invalid/x.zip"}],
    }

    class _Resp:
        headers = {"Content-Length": "0"}

        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *a, **k: _Resp())


@pytest.fixture
def estado_limpio(monkeypatch):
    """Restaura el _state global del módulo (es singleton) al terminar."""
    original = dict(updater._state)
    yield
    updater._state.clear()
    updater._state.update(original)


def _check_sincronico(monkeypatch):
    """force_check corre en un hilo; para el test lo hacemos sincrónico."""
    monkeypatch.setattr(updater.threading, "Thread",
                        lambda target, args=(), daemon=None: type(
                            "T", (), {"start": lambda self: target(*args)})())


def test_force_check_en_dev_no_ofrece_instalar(monkeypatch, estado_limpio):
    """Sin _version.py (modo dev) apply_update copiaría sobre el repo: nunca ofrecer."""
    _fake_github(monkeypatch)
    _check_sincronico(monkeypatch)
    monkeypatch.setattr(updater, "current_version", lambda: None)

    assert updater.force_check() is True
    s = updater.get_status()
    assert s["checked"] is True
    assert s["latest"] == "v2099-01-01"     # sí informa cuál es la última
    assert s["available"] is False          # pero no la ofrece


def test_force_check_con_version_detecta_la_nueva(monkeypatch, estado_limpio):
    _fake_github(monkeypatch)
    _check_sincronico(monkeypatch)
    monkeypatch.setattr(updater, "current_version", lambda: "v2026-06-25")
    monkeypatch.setattr(updater.sys, "platform", "win32")

    assert updater.force_check() is True
    s = updater.get_status()
    assert s["available"] is True
    assert s["notes"][0].startswith("fix:")


def test_force_check_no_pisa_una_descarga_en_curso(estado_limpio):
    updater._state["downloading"] = True
    assert updater.force_check() is False
