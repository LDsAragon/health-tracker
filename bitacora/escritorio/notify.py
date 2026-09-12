"""Notificaciones del escritorio. Best-effort: si el canal no está, no pasa nada."""
import base64
import shutil
import subprocess
import sys

_CREATE_NO_WINDOW = 0x08000000

# Bitácora no registra un AppUserModelID en el menú Inicio, así que el toast se emite con el
# de Windows PowerShell (que sí está instalado): con un AUMID inexistente Windows lo descarta
# sin mostrar nada. Contrapartida: la notificación se atribuye a "Windows PowerShell".
_AUMID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"

_PS_TOAST = """
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
$tpl = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
    [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$txt = $tpl.GetElementsByTagName('text')
$txt.Item(0).AppendChild($tpl.CreateTextNode('{title}')) | Out-Null
$txt.Item(1).AppendChild($tpl.CreateTextNode('{body}')) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($tpl)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{aumid}').Show($toast)
"""


def _ps_lit(s: str) -> str:
    """Texto para un string literal de PowerShell (comilla simple duplicada)."""
    return s.replace("'", "''")


def _notify_win(title: str, body: str) -> bool:
    script = _PS_TOAST.format(title=_ps_lit(title), body=_ps_lit(body), aumid=_AUMID)
    # -EncodedCommand (UTF-16LE en base64) evita pelear con el quoting de la línea de comandos.
    subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
         "-EncodedCommand", base64.b64encode(script.encode("utf-16-le")).decode("ascii")],
        creationflags=_CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def _notify_linux(title: str, body: str) -> bool:
    if not shutil.which("notify-send"):
        return False
    subprocess.Popen(
        ["notify-send", "-a", "Bitácora", title, body],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def notify(title: str, body: str) -> bool:
    """Muestra una notificación del sistema. False si no se pudo (nunca levanta)."""
    try:
        if sys.platform == "win32":
            return _notify_win(title, body)
        if sys.platform.startswith("linux"):
            return _notify_linux(title, body)
    except Exception:
        pass
    return False
