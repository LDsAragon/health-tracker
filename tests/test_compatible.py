"""El zip compatible de Windows: Python embebido + Edge en modo app, sin binarios propios.

Es para las máquinas con Smart App Control, que bloquea todo lo que no venga firmado. Lo de
punta a punta (que el zip arranque, que la ventana abra y que cerrarla apague el servidor) se
verificó a mano sobre el build; acá queda fijado lo que se puede romper sin que nadie lo vea.
"""
import pathlib
import subprocess
import sys
import time

import pytest

from bitacora.escritorio import compatible, updater

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _leer(ruta):
    return (RAIZ / ruta).read_text(encoding="utf-8")


ASSETS = [
    {"name": "Bitacora-Windows-2026-10-11.zip", "browser_download_url": "normal"},
    {"name": "Bitacora-Compatible-v2026-10-11.zip", "browser_download_url": "compatible"},
    {"name": "Bitacora-linux-2026-10-11.tar.gz", "browser_download_url": "linux"},
]


# ── Cada instalación baja SU zip ─────────────────────────────────────────────

@pytest.mark.parametrize("orden", [ASSETS, ASSETS[::-1]])
def test_cada_canal_elige_su_asset(orden):
    assert updater.elegir_asset(orden, "win32", "normal")["browser_download_url"] == "normal"
    assert updater.elegir_asset(orden, "win32", "compatible")["browser_download_url"] == "compatible"
    assert updater.elegir_asset(orden, "linux", "normal")["browser_download_url"] == "linux"


def test_las_instalaciones_YA_REPARTIDAS_no_pueden_bajar_el_compatible():
    """⚠️ Las versiones viejas, ya instaladas en las máquinas de la gente, eligen con esta regla
    exacta y no se pueden cambiar. Si el zip compatible la cumpliera, una instalación normal
    podría bajarlo y espejarlo encima de su carpeta: se quedaría sin Bitacora.exe."""
    regla_vieja = lambda n: "windows" in n.lower() and n.endswith(".zip")
    nombre = updater.PREFIJO_COMPATIBLE + "v2026-10-11.zip"
    assert not regla_vieja(nombre)
    ps = _leer("tools/make_release_compatible.ps1")
    assert r'$zip = "$root\dist\Bitacora-Compatible-$Version.zip"' in ps
    assert updater.PREFIJO_COMPATIBLE == "Bitacora-Compatible-"


def test_sin_version_el_canal_es_el_normal():
    assert updater.canal() == "normal"     # en dev no hay _version.py


solo_windows = pytest.mark.skipif(sys.platform != "win32",
                                  reason="prueba el lanzamiento del actualizador en Windows")


@solo_windows
@pytest.mark.parametrize("canal, espera, no_espera", [
    ("compatible", ["pythonw.exe", "--compatible"], ["Bitacora.exe"]),
    ("normal", ["Bitacora.exe"], ["pythonw.exe"]),
])
def test_despues_de_actualizar_se_relanza_con_lo_que_tiene(monkeypatch, tmp_path,
                                                          canal, espera, no_espera):
    """El compatible no tiene Bitacora.exe: relanzarlo así dejaría la app cerrada después de
    actualizarse, sin ningún aviso."""
    import tempfile
    monkeypatch.setattr(updater.os.environ, "get",
                        lambda k, d=None: str(tmp_path) if k == "LOCALAPPDATA" else d)
    monkeypatch.setattr(updater, "canal", lambda: canal)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: object())
    updater._launch_win(tmp_path / "src", tmp_path / "dst", 1234)
    script = (tmp_path / "bitacora_updater.ps1").read_text(encoding="utf-8")
    for s in espera:
        assert s in script
    for s in no_espera:
        assert s not in script


def test_al_salir_para_actualizar_se_cierra_la_ventana(client, monkeypatch):
    """Sin esto la ventana de Edge queda abierta sobre un servidor muerto, y al relanzarse
    aparece otra al lado."""
    import threading
    cerradas, salida = [], []
    monkeypatch.setattr(updater, "al_salir", [lambda: cerradas.append(1),
                                              lambda: 1 / 0,      # una que falla no frena
                                              lambda: cerradas.append(2)])
    monkeypatch.setattr("bitacora.routes.update.os._exit", lambda c: salida.append(c))

    class _Inmediato:
        def __init__(self, _t, f): self.f = f
        def start(self): self.f()
    monkeypatch.setattr(threading, "Timer", _Inmediato)
    client.post("/update/quit")
    assert cerradas == [1, 2] and salida == [0]


# ── Cuándo se apaga el servidor ──────────────────────────────────────────────

class _Proc:
    def __init__(self, dura): self.dura = dura
    def wait(self): compatible.time.sleep(self.dura)


def test_cerrar_la_ventana_apaga_el_servidor(monkeypatch):
    monkeypatch.setattr(compatible, "ENTREGA", 0.05)
    monkeypatch.setattr(compatible, "SIN_PEDIDOS", 3600)
    inicio = time.monotonic()
    compatible._esperar(_Proc(0.1))
    assert time.monotonic() - inicio < 1


def test_si_edge_le_paso_la_ventana_a_otro_proceso_espera_los_pedidos(monkeypatch):
    """⚠️ Con nuestro perfil ya abierto en otro Edge, el proceso lanzado sale en el acto y la
    ventana sigue abierta. Apagar el servidor ahí la dejaría muerta: manda el último pedido."""
    ahora = [0.0]
    esperas = []

    def dormir(s):
        esperas.append(s)
        ahora[0] += s
    monkeypatch.setattr(compatible.time, "monotonic", lambda: ahora[0])
    monkeypatch.setattr(compatible.time, "sleep", dormir)
    monkeypatch.setattr(compatible, "_ultimo_pedido", 0.0)
    compatible._esperar(_Proc(0))
    # Volvió recién cuando el último pedido quedó viejo, no cuando salió el proceso.
    assert sum(esperas) >= compatible.SIN_PEDIDOS


def test_sin_edge_queda_en_el_navegador(monkeypatch):
    abiertas = []
    monkeypatch.setattr(compatible.webbrowser, "open", abiertas.append)
    assert compatible.abrir_ventana(None, "http://127.0.0.1:1", "x") is None
    assert abiertas == ["http://127.0.0.1:1"]


def test_edge_va_con_un_perfil_propio(monkeypatch, tmp_path):
    """Con el perfil del usuario, el lanzamiento le pasa la ventana a su Edge abierto y el
    proceso sale en el acto: el servidor no sabría cuándo apagarse."""
    lanzado = {}
    monkeypatch.setattr(compatible.subprocess, "Popen",
                        lambda args: lanzado.setdefault("args", args))
    monkeypatch.setattr("bitacora.escritorio.main.tamano_inicial", lambda: (900, 700, False))
    compatible.abrir_ventana("msedge.exe", "http://127.0.0.1:1", tmp_path)
    args = lanzado["args"]
    assert "--app=http://127.0.0.1:1" in args
    assert f"--user-data-dir={tmp_path / 'edge'}" in args
    assert "--window-size=900,700" in args


# ── El arranque y el build ───────────────────────────────────────────────────

def test_el_modo_compatible_usa_el_MISMO_arranque_que_la_ventana():
    """Un arranque repetido a mano diverge del real: ya pasó dos veces con los smokes."""
    src = _leer("bitacora/escritorio/compatible.py")
    assert "escritorio.preparar_entorno()" in src
    assert "escritorio.preparar_datos()" in src
    assert "instancia.tomar()" in src
    assert 'elif "--compatible" in sys.argv:' in _leer("main.py")


def test_el_build_compatible_verifica_que_TODO_venga_firmado():
    """Es la única garantía del zip: un binario sin firma y Smart App Control lo bloquea."""
    ps = _leer("tools/make_release_compatible.ps1")
    assert "Get-AuthenticodeSignature" in ps
    assert "-Include *.exe, *.dll, *.pyd" in ps
    assert '.Status -ne "Valid"' in ps
    assert 'CANAL = `"compatible`"' in ps
    # Corre con Windows PowerShell 5.1: sin BOM, lee el archivo como ANSI.
    assert ps.isascii()


def test_lo_que_se_distribuye_va_dentro_de_la_carpeta_que_se_espeja():
    ps = _leer("tools/make_release_compatible.ps1")
    assert r'$out = "$root\dist\compatible\Bitacora"' in ps
    assert r'Copy-Item "$root\docs\LEEME-Compatible.txt" "$out\LEEME.txt"' in ps
    assert r'"$out\Bitacora.bat"' in ps
    assert "Compress-Archive -Path $out" in ps


def test_el_release_arma_y_publica_el_compatible():
    assert "make_release_compatible.ps1" in _leer("tools/make_release.ps1")
    pub = _leer("tools/publish_release.ps1")
    assert r'$zipc = "dist\Bitacora-Compatible-$tag.zip"' in pub
    assert pub.count("$zipc") >= 3      # se chequea, y va en el create y en el upload
