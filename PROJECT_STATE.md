# MiyuLauncher — Project State

Última actualización: 2026-10-23

## Versión actual

`0.1.0-dev`

## Fase actual

FASE 0 — Preparación del proyecto

## Estado general

🟡 En desarrollo

## Entorno actual

- Windows
- Python 3.14.6
- PySide6 6.12.0
- Git 2.54.0.windows.1
- Sin entorno virtual de Python por decisión del desarrollador

Las dependencias se registran en `requirements.txt`.

## Completado

- [x] Nombre del proyecto definido: MiyuLauncher
- [x] Python instalado
- [x] Git instalado y configurado
- [x] PySide6 instalado y probado
- [x] Repositorio Git local inicializado
- [x] Primer prototipo gráfico ejecutado correctamente
- [x] QApplication y QMainWindow funcionando
- [x] Repositorio remoto creado en GitHub
- [x] Primer push realizado
- [x] GitHub conectado a ChatGPT para continuar el desarrollo sobre el repositorio real

## En progreso

- [ ] Terminar la estructura versionada del proyecto
- [ ] Cerrar FASE 0

## Próximo objetivo

Comenzar FASE 1 — Core mínimo.

Primeros módulos previstos:

1. `core/system.py` — información del sistema, arquitectura y memoria.
2. `core/paths.py` — rutas administradas por MiyuLauncher.
3. `core/java.py` — detección y administración inicial de Java.
4. Detección de instalaciones/versiones de Minecraft.
5. Primer lanzamiento de Minecraft desde MiyuLauncher.

## Arquitectura prevista

```text
src/miyu_launcher/
├── auth/       # autenticación y cuentas
├── config/     # configuración del launcher
├── core/       # Minecraft, Java, Fabric, rutas y lógica principal
├── network/    # servicios remotos y estado del servidor
├── ui/         # interfaz PySide6/Qt
└── updater/    # manifests, verificación, descargas y actualizaciones
```

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
- Actualizaciones: manifest remoto + hashes SHA-256.
- Mods: sincronización automática; algunos podrán ser opcionales.
- Autenticación oficial: Microsoft/Minecraft; no se almacenarán contraseñas.

## Problemas conocidos

Ninguno actualmente.

## Última prueba realizada

`python main.py`

Resultado: la ventana principal abrió correctamente mostrando `Miyu Launcher`.

## Cómo continuar en otra conversación

1. Leer `PROJECT_STATE.md`.
2. Leer `ROADMAP.md`.
3. Revisar los últimos commits del repositorio.
4. Continuar desde `Próximo objetivo`.
