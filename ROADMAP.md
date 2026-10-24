
---

## 2. `PROJECT_STATE.md`

Este será **importantísimo**.

```markdown
# MiyuLauncher — Project State

Última actualización: 2026-10-23

## Versión actual

0.1.0-dev

## Fase actual

FASE 0 — Preparación del proyecto

## Estado general

🟡 En desarrollo

## Entorno actual

Sistema principal de desarrollo:

- Windows
- Python 3.14.6
- PySide6 6.12.0
- Git 2.54.0.windows.1

No se utiliza entorno virtual de Python por decisión del desarrollador.

Las dependencias se registrarán en `requirements.txt`.

## Completado

- [x] Nombre del proyecto definido: MiyuLauncher
- [x] Python instalado
- [x] Git instalado y configurado
- [x] PySide6 instalado
- [x] PySide6 probado correctamente
- [x] Repositorio Git local inicializado
- [x] Estructura inicial de carpetas creada
- [x] Primer prototipo gráfico ejecutado correctamente
- [x] QApplication funcionando
- [x] QMainWindow funcionando

## En progreso

- [ ] Documentación inicial
- [ ] Primer commit
- [ ] Crear repositorio remoto en GitHub
- [ ] Conectar repositorio local con GitHub

## Próximo objetivo

Finalizar FASE 0.

Después comenzar:

FASE 1 — Núcleo mínimo del launcher.

El primer objetivo técnico será detectar el entorno del sistema y comenzar
el desarrollo del administrador de Java/Minecraft.

## Arquitectura prevista

```text
src/miyu_launcher/

auth/
    Autenticación y cuentas.

config/
    Configuración del launcher.

core/
    Minecraft, Java, Fabric, rutas y lógica principal.

network/
    Comunicación con servicios remotos y servidor.

ui/
    Interfaz gráfica Qt.

updater/
    Manifest, verificación, descargas y actualizaciones.