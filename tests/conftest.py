import pytest
import database as db
import app as flask_app


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Base de datos temporal aislada por test."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("database.conn.DB_PATH", db_file)
    db.init_db()
    return db_file


@pytest.fixture
def client(test_db):
    """Flask test client con DB aislada."""
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c
