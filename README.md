# Bitácora

Calendario personal de hábitos, registros y emociones. App de escritorio para Windows y Linux — sin internet, sin cuentas, todo en tu máquina.

---

## Qué podés registrar

- **Rutinas** — actividades que querés marcar día a día (ejercicio, medicación, sueño, lo que sea). Podés definir en qué días aplican y cuáles son obligatorias.
- **Notas rápidas** — texto libre con color opcional, tipo post-it.
- **Notas especiales** — formularios con campos a medida: escala 1-5, sí/no, opciones, duración, rango horario, rueda de emociones.
- **To-dos** — tareas con fecha; se pueden mover entre días.
- **Estadísticas** — resumen de tiempo por actividad en la semana, el mes o los últimos 90 días.

Los datos viven en una base SQLite local. No hay servidor, no hay nube.

---

## Descargar e instalar

Bajá la versión más reciente desde [Releases](https://github.com/LDsAragon/health-tracker/releases/latest).

### Windows

1. Descargá `Bitacora-Windows-<fecha>.zip` y descomprimilo en una carpeta local, por ejemplo `C:\Bitacora`.
   > Evitá carpetas sincronizadas (OneDrive, Dropbox): pueden "des-descargar" archivos y romper la app.
2. Entrá a la carpeta `Bitacora` y hacé doble clic en `Bitacora.exe`.
3. **Si Windows muestra "Windows protegió tu equipo"** (pantalla azul de SmartScreen): tocá **Más información** → **Ejecutar de todas formas**. Pasa porque la app no está firmada digitalmente; es normal.
4. Para un acceso directo: clic derecho sobre `Bitacora.exe` → Enviar a → Escritorio.

Tus datos se guardan en `%LOCALAPPDATA%\Bitacora\health.db` (independiente de dónde tengas la app).

### Linux

Requiere Ubuntu 22.04+ / Debian 12+ / Mint 21+, Fedora, o Arch/Manjaro.

```bash
# Descomprimí el tar.gz
tar -xzf Bitacora-linux-<fecha>.tar.gz -C ~/

# Entrá a la carpeta y corré el instalador (pide contraseña una sola vez)
cd ~/Bitacora
./instalar.sh
```

Después buscá **Bitácora** en el menú de aplicaciones, o corré `./bitacora.sh` desde la carpeta.

Tus datos se guardan en `~/.local/share/Bitacora/health.db`.

---

## Actualizar a una nueva versión

Los datos están separados de la app, así que actualizar es reemplazar la carpeta de la app sin tocar nada más.

**Windows:**
1. Cerrá Bitácora si está abierta.
2. Descargá el nuevo zip y descomprimilo en la misma carpeta (o borrá la carpeta vieja y extraé de cero).
3. Abrí `Bitacora.exe` — la app migra la base de datos automáticamente si hay cambios de esquema.

**Linux:**
```bash
# Descomprimí el nuevo tar.gz (encima de la carpeta existente, o borrá y extraé)
tar -xzf Bitacora-linux-<fecha>.tar.gz -C ~/
cd ~/Bitacora
./instalar.sh   # solo si hay dependencias nuevas; no hace daño correrlo de nuevo
```

---

## Tus datos y backups

- Todo está en tu máquina. Sin internet, sin cuentas, sin nube.
- Para hacer un backup: abrí la pestaña **Datos** en la app → **Descargar backup**. El archivo `.db` es la base SQLite completa; guardalo donde quieras.
- Para restaurar: **Datos** → **Restaurar backup** → elegís el archivo.
- La app también hace un backup automático diario (guarda los últimos 7) en la misma carpeta donde vive la base de datos.

---

## Manual de uso

El manual completo en PDF viene incluido en el zip/tar.gz del release (`Bitacora-Manual.pdf`).
