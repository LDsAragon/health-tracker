"""Perfiles locales: varias bitácoras en la misma instalación, cada una en su propio archivo.

Todo local y offline. El índice vive en un JSON y no en una tabla porque hay que saber qué
perfil abrir *antes* de abrir ninguna base.

Se desactiva solo: sin `HT_PERFILES` (modo navegador, tests) hay un único perfil implícito y
`activo()` devuelve None, así que nada cambia.
"""
import json
import os
import re
import unicodedata
import uuid

import database.conn as conn

INDICE = "perfiles.json"
CARPETA = "perfiles"
DB = "health.db"
NOMBRE_MAX = 40


def raiz():
    """Carpeta de datos donde viven el índice y los perfiles. None = perfiles desactivados."""
    return os.environ.get("HT_PERFILES") or None


def _ruta_indice():
    return os.path.join(raiz(), INDICE)


def slug(nombre: str) -> str:
    """Nombre → nombre de carpeta seguro. Sin esto un nombre con / o .. escribe fuera de raíz.

    Translitera los acentos en vez de tirarlos: si no, "Matías Ñandú" quedaría "mat-as-and".
    """
    plano = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", plano.lower().strip()).strip("-")
    return s[:40] or "perfil"


def db_de(slug_: str) -> str:
    return os.path.join(raiz(), CARPETA, slug_, DB)


def leer() -> dict:
    """El índice, o uno vacío si todavía no existe / está corrupto."""
    try:
        with open(_ruta_indice(), encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("perfiles"), list):
            return d
    except (OSError, ValueError):
        pass
    return {"activo": "", "dispositivo": "", "perfiles": []}


def guardar(indice: dict):
    """Escritura atómica: un JSON a medio escribir dejaría la app sin saber qué perfil abrir."""
    os.makedirs(raiz(), exist_ok=True)
    tmp = _ruta_indice() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _ruta_indice())


def listar() -> list:
    return leer()["perfiles"] if raiz() else []


def activo() -> dict | None:
    """El perfil activo, o None si los perfiles están desactivados o el índice está vacío."""
    if not raiz():
        return None
    ind = leer()
    for p in ind["perfiles"]:
        if p["slug"] == ind.get("activo"):
            return p
    return ind["perfiles"][0] if ind["perfiles"] else None


def dispositivo() -> str:
    """Id de esta instalación. El sync lo necesita para desambiguar el origen de las filas."""
    if not raiz():
        return ""
    ind = leer()
    if not ind.get("dispositivo"):
        ind["dispositivo"] = uuid.uuid4().hex
        guardar(ind)
    return ind["dispositivo"]


def crear(nombre: str) -> dict:
    """Crea un perfil vacío y lo devuelve. El esquema lo arma init_db en el primer request."""
    nombre = (nombre or "").strip()[:NOMBRE_MAX] or "Perfil"
    ind = leer()
    usados = {p["slug"] for p in ind["perfiles"]}
    base = slug(nombre)
    s, i = base, 2
    while s in usados:
        s, i = f"{base}-{i}", i + 1
    perfil = {"slug": s, "nombre": nombre, "uid": uuid.uuid4().hex}
    os.makedirs(os.path.dirname(db_de(s)), exist_ok=True)
    ind["perfiles"].append(perfil)
    guardar(ind)
    return perfil


def renombrar(slug_: str, nombre: str):
    """Cambia solo la etiqueta: el slug (y la carpeta) quedan, para no mover archivos."""
    nombre = (nombre or "").strip()[:NOMBRE_MAX]
    if not nombre:
        return
    ind = leer()
    for p in ind["perfiles"]:
        if p["slug"] == slug_:
            p["nombre"] = nombre
    guardar(ind)


def emparejar(slug_: str, uid_remoto: str):
    """Recuerda que ese perfil de la otra máquina es el mismo que este, para no volver a
    preguntar en cada sincronización."""
    if not uid_remoto:
        return
    ind = leer()
    for p in ind["perfiles"]:
        if p["slug"] == slug_:
            p["emparejados"] = sorted(set(p.get("emparejados", [])) | {uid_remoto})
    guardar(ind)


def es_conocido(perfil: dict | None, uid_remoto: str) -> bool:
    """True si ese uid remoto es este mismo perfil o uno ya emparejado con él."""
    if not perfil or not uid_remoto:
        return True     # sin identidad de un lado u otro no hay nada que confrontar
    return uid_remoto == perfil.get("uid") or uid_remoto in perfil.get("emparejados", [])


def usar(slug_: str) -> bool:
    """Cambia el perfil activo en caliente. False si el slug no existe."""
    ind = leer()
    if slug_ not in {p["slug"] for p in ind["perfiles"]}:
        return False
    ind["activo"] = slug_
    guardar(ind)
    aplicar()
    return True


def aplicar():
    """Apunta la capa de datos al perfil activo.

    Rebindea `database.conn.DB_PATH` y no `os.environ["HT_DB"]`: conn.py lee el env una sola
    vez al importar, pero todo lo demás (get_db, backup_path, snapshot_to...) lee el global
    del módulo en cada llamada. Es la misma técnica que usan los tests.
    """
    p = activo()
    if p:
        os.makedirs(os.path.dirname(db_de(p["slug"])), exist_ok=True)
        conn.DB_PATH = db_de(p["slug"])


def borrar(slug_: str) -> tuple[bool, str]:
    """Saca el perfil del índice y borra su carpeta. No se puede borrar el activo ni el último."""
    ind = leer()
    if len(ind["perfiles"]) <= 1:
        return False, "No se puede borrar el único perfil."
    if slug_ == ind.get("activo"):
        return False, "No se puede borrar el perfil activo: cambiá a otro primero."
    if slug_ not in {p["slug"] for p in ind["perfiles"]}:
        return False, "Ese perfil no existe."
    ind["perfiles"] = [p for p in ind["perfiles"] if p["slug"] != slug_]
    guardar(ind)
    # Los callers hacen `with get_db()`, que commitea pero NO cierra, así que en Windows el
    # archivo queda lockeado hasta que el GC recoja la conexión. Sin este collect, rmtree
    # falla y el perfil queda sin índice pero con archivos en disco.
    import gc
    import shutil
    gc.collect()
    try:
        shutil.rmtree(os.path.dirname(db_de(slug_)))
    except OSError:
        return True, "El perfil se quitó, pero sus archivos no se pudieron borrar (quedaron en disco)."
    return True, "Perfil eliminado."
