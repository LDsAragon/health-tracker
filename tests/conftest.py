import pytest
from bitacora import database as db
from bitacora import app as flask_app


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Base de datos temporal aislada por test, y **vacía de categorías**.

    Desde que la app trae tres categorías de fábrica (`plantillas.DE_FABRICA`), una base recién
    creada ya no está vacía. Casi todos los tests son sobre comportamiento y arman sus propios
    datos, así que arrancar con tres categorías ajenas les cambiaría los conteos y el `[0]` de
    cada consulta sin agregar nada.

    Lo que el sembrado sí hace —cuándo corre, con qué uid y que no resucite lo borrado— se prueba
    en `tests/test_semilla.py`, que crea su base a mano justamente para verlo.
    """
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", db_file)
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM journal_categories")
        conn.execute("DELETE FROM deletions")          # sin tombstones de algo que nadie borró
    return db_file


@pytest.fixture
def client(test_db):
    """Flask test client con DB aislada."""
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c
