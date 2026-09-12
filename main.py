"""Punto de entrada de Bitácora.

Sin argumentos abre la ventana nativa; con `--navegador` levanta el servidor y abre el browser.
Es el archivo que empaqueta PyInstaller y el que ejecutan `start.bat` y el launcher de Linux.

Los imports van DENTRO de cada función a propósito: el camino de la ventana chequea primero si
ya hay otra Bitácora corriendo, y una segunda instancia que se va a cerrar en el acto no tiene
por qué pagar el import de Flask ni de pywebview.
"""
import sys


def navegador():
    """Mismo Flask, sin pywebview. Los datos quedan al lado del código, no en appdata."""
    import threading
    import webbrowser

    from bitacora import database as db
    from bitacora.app import app

    db.init_db()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False, port=5000)


def ventana():
    from bitacora.escritorio.main import arrancar
    arrancar()


if __name__ == "__main__":
    navegador() if "--navegador" in sys.argv else ventana()
