# MiyuLauncher

MiyuLauncher es un launcher personalizado de Minecraft Java Edition desarrollado principalmente para un servidor privado entre amigos.

El objetivo es proporcionar una experiencia sencilla para los jugadores, automatizando la preparación y mantenimiento de la instalación necesaria para entrar al servidor.

## Objetivos principales

MiyuLauncher pretende administrar automáticamente:

- Minecraft Java Edition
- Java Runtime
- Fabric Loader
- Mods requeridos por el servidor
- Mods QoL
- Configuraciones
- Resource packs
- Actualizaciones del modpack
- Noticias y eventos del servidor
- Estado del servidor
- Actualizaciones del propio launcher

La intención es que el usuario final tenga que hacer lo mínimo posible:

1. Instalar MiyuLauncher.
2. Iniciar sesión.
3. Pulsar JUGAR.

## Tecnologías

- Python 3.14+
- PySide6 / Qt
- Git
- Fabric

## Estado

MiyuLauncher se encuentra actualmente en desarrollo inicial.

Versión actual: `0.1.0-dev`

## Plataformas

Inicialmente:

- Windows 10
- Windows 11

El soporte para otros sistemas operativos podrá estudiarse posteriormente.

## Estructura

```text
MiyuLauncher/
├── assets/
├── src/
│   └── miyu_launcher/
│       ├── auth/
│       ├── config/
│       ├── core/
│       ├── network/
│       ├── ui/
│       └── updater/
├── tests/
├── tools/
├── main.py
├── PROJECT_STATE.md
├── ROADMAP.md
└── requirements.txt