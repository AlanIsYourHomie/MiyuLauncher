# MiyuLauncher — Project State

Última actualización: 2026-10-23

## Versión actual

`0.1.0-dev`

## Fase actual

FASE 1 — Core mínimo

## Estado general

🟡 En desarrollo

## Entorno actual

- Windows
- Python 3.14.6
- PySide6 6.12.0
- Git 2.54.0.windows.1
- Sin entorno virtual de Python por decisión del desarrollador

Las dependencias se registran en `requirements.txt`.

## FASE 0 — Completada

- [x] Nombre del proyecto definido: MiyuLauncher
- [x] Python instalado
- [x] Git instalado y configurado
- [x] PySide6 instalado y probado
- [x] Repositorio Git local inicializado
- [x] Primer prototipo gráfico ejecutado correctamente
- [x] Repositorio remoto creado en GitHub
- [x] Primer push realizado
- [x] GitHub conectado a ChatGPT
- [x] README, ROADMAP y PROJECT_STATE organizados
- [x] Estructura modular inicial creada

## FASE 1 — En progreso

### Implementado y validado localmente

- [x] `core/system.py`
  - sistema operativo
  - versión de Windows
  - arquitectura
  - máquina/procesador
  - RAM física total en Windows
- [x] `core/paths.py`
  - raíz administrada en `%LOCALAPPDATA%/MiyuLauncher`
  - instancia
  - runtime
  - cache
  - downloads
  - logs
- [x] `ui/main_window.py`
  - ventana separada del punto de entrada
  - muestra información básica detectada
  - botón JUGAR deshabilitado temporalmente
- [x] `main.py` reducido a punto de entrada de la aplicación
- [x] La versión modular abre correctamente en el PC de desarrollo
- [x] Detección de Windows, arquitectura y RAM confirmada
- [x] Creación de `%LOCALAPPDATA%/MiyuLauncher` confirmada

### Implementado, pendiente de validación local

- [x] `core/java.py`
  - búsqueda mediante `PATH`
  - búsqueda mediante `JAVA_HOME`
  - búsqueda en directorios comunes de Java para Windows
  - ejecución segura de `java -version`
  - lectura de versión y versión mayor
  - eliminación de rutas duplicadas
  - selección de una instalación Java preferida
- [x] `tools/check_java.py`
  - utilidad temporal para comprobar detección de Java desde consola

## Próximo objetivo

1. Ejecutar `python tools/check_java.py` en el PC de desarrollo.
2. Confirmar qué instalaciones y versiones de Java detecta.
3. Corregir casos de detección si fuera necesario.
4. Mostrar el Java seleccionado en la interfaz.
5. Después comenzar la detección de instalaciones/versiones de Minecraft.

## Arquitectura actual

```text
src/miyu_launcher/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── java.py
│   ├── paths.py
│   └── system.py
└── ui/
    ├── __init__.py
    └── main_window.py

tools/
└── check_java.py
```

Las carpetas `auth`, `config`, `network` y `updater` se incorporarán a Git cuando contengan sus primeros módulos reales.

## Principios del proyecto

1. Mantener una arquitectura modular.
2. Evitar concentrar la lógica en `main.py`.
3. Separar UI y lógica del launcher.
4. Registrar dependencias en `requirements.txt`.
5. Usar Git durante todo el desarrollo.
6. Mantener este archivo actualizado después de cada hito importante.
7. El usuario final no debería necesitar conocimientos sobre Java, Fabric o mods.
8. MiyuLauncher debe poder reparar instalaciones dañadas.
9. Descargar solo los archivos necesarios cuando sea posible.
10. Mantener Minecraft en una instancia administrada separada de `.minecraft` cuando lleguemos a esa fase.

## Decisiones importantes

- Lenguaje: Python.
- GUI: PySide6 / Qt.
- Mod loader: Fabric.
- Plataforma inicial: Windows 10/11.
- Java: a largo plazo, runtime administrado por MiyuLauncher.
- Datos administrados: `%LOCALAPPDATA%/MiyuLauncher` en Windows.
- Actualizaciones: manifest remoto + hashes SHA-256.
- Mods: sincronización automática; algunos podrán ser opcionales.
- Autenticación oficial: Microsoft/Minecraft; no se almacenarán contraseñas.

## Problemas conocidos

Ninguno confirmado actualmente.

## Última prueba confirmada

`python main.py` abre correctamente la versión modular y muestra la información del sistema esperada.

## Cómo continuar en otra conversación

1. Leer `PROJECT_STATE.md`.
2. Leer `ROADMAP.md`.
3. Revisar los últimos commits del repositorio.
4. Continuar desde `Próximo objetivo`.
