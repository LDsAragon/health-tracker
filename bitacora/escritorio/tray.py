"""Icono en el área de notificación.

Windows: NotifyIcon de WinForms vía pythonnet, que ya está instalado porque lo usa pywebview —
sin dependencias nuevas. Corre en su propio hilo con su propio bucle de mensajes, que es válido
en WinForms (uno por hilo) y evita tener que meter mano en los internals de pywebview para
marshalear al hilo de su interfaz.

Linux: no se intenta. GNOME (el escritorio por defecto de Fedora) no muestra iconos de bandeja
sin una extensión aparte, así que intentarlo daría un resultado peor que no tenerlo.

Todo va dentro de try/except: la bandeja nunca puede impedir que la app arranque.
"""
import os
import sys
import threading

_activo = False
_icono = None


def disponible() -> bool:
    """Si hay un icono puesto de verdad.

    ⚠️ Es la guarda de "cerrar = ir a la bandeja": esconder la ventana al cerrar SIN un icono
    dejaría el programa corriendo sin ninguna forma de volver a mostrarlo ni de cerrarlo.
    """
    return _activo


def _ruta_icono() -> str:
    """`static/` vive en la raíz del paquete, dos niveles arriba de este archivo.

    Congelada, PyInstaller la deja en la raíz del bundle (`--add-data`), así que ahí el
    `_MEIPASS` pelado alcanza.
    """
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "static", "icon.ico")


def iniciar(abrir_app, mostrar_widget, salir) -> bool:
    """Pone el icono. Devuelve si se pudo."""
    global _activo
    if sys.platform != "win32":
        return False
    try:
        hilo = threading.Thread(target=_correr_win, args=(abrir_app, mostrar_widget, salir),
                                daemon=True)
        hilo.start()
        # El hilo avisa por su cuenta; esperamos un toque a que levante el icono.
        for _ in range(50):
            if _activo:
                break
            threading.Event().wait(0.05)
    except Exception:
        return False
    return _activo


def _correr_win(abrir_app, mostrar_widget, salir):
    global _activo, _icono
    try:
        import clr
        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
        from System.Windows.Forms import (Application, NotifyIcon, ContextMenuStrip,
                                          ToolStripMenuItem)
        from System.Drawing import Icon

        menu = ContextMenuStrip()

        def item(texto, accion, negrita=False):
            it = ToolStripMenuItem(texto)
            it.Click += lambda s, e: _seguro(accion)
            if negrita:
                from System.Drawing import FontStyle
                it.Font = _negrita(it.Font, FontStyle)
            menu.Items.Add(it)
            return it

        item("Abrir Bitácora", abrir_app, negrita=True)
        item("Mostrar el widget", mostrar_widget)
        menu.Items.Add("-")
        item("Salir", salir)

        _icono = NotifyIcon()
        _icono.Icon = Icon(_ruta_icono())
        _icono.Text = "Bitácora"
        _icono.ContextMenuStrip = menu
        _icono.DoubleClick += lambda s, e: _seguro(abrir_app)
        _icono.Visible = True
        _activo = True

        Application.Run()          # bucle propio de este hilo
    except Exception:
        _activo = False


def _negrita(fuente, FontStyle):
    from System.Drawing import Font
    return Font(fuente, FontStyle.Bold)


def _seguro(accion):
    """Una excepción en un handler de WinForms se lleva puesto el hilo de la bandeja."""
    try:
        accion()
    except Exception:
        pass


def quitar():
    """Saca el icono. Sin esto queda el fantasma en la bandeja hasta que pasás el mouse."""
    global _activo
    _activo = False
    try:
        if _icono is not None:
            _icono.Visible = False
            _icono.Dispose()
    except Exception:
        pass
