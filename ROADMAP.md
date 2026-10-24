# MiyuLauncher — Roadmap

Este documento contiene la hoja de ruta general de MiyuLauncher. Los números de versión son orientativos y podrán cambiar durante el desarrollo.

---

## FASE 0 — Preparación

- [x] Elegir tecnologías
- [x] Instalar Python
- [x] Instalar Git
- [x] Instalar PySide6
- [x] Crear estructura inicial
- [x] Crear primera ventana
- [x] Crear documentación base
- [x] Crear primer commit
- [x] Crear repositorio GitHub
- [x] Conectar el repositorio para trabajar sobre el proyecto real

---

## FASE 1 — Core mínimo

- Detectar sistema operativo
- Detectar arquitectura
- Detectar memoria disponible
- Administrar rutas
- Detectar Java
- Detectar instalaciones de Minecraft
- Leer versiones instaladas
- Construir primer comando de lanzamiento
- Lanzar Minecraft desde MiyuLauncher

**Hito:** Minecraft puede iniciarse desde MiyuLauncher.

---

## FASE 2 — Minecraft Manager

- Consultar versiones disponibles
- Descargar Minecraft
- Descargar libraries
- Descargar assets
- Verificar hashes
- Crear instancia independiente
- Reparar archivos faltantes

**Hito:** MiyuLauncher puede instalar Minecraft sin depender del launcher oficial.

---

## FASE 3 — Java Manager

- Detectar versión requerida
- Descargar Java Runtime
- Administrar runtimes
- Permitir Java personalizado
- Seleccionar automáticamente el runtime apropiado

**Hito:** el usuario no necesita instalar Java manualmente.

---

## FASE 4 — Autenticación

- Microsoft OAuth
- Autenticación Minecraft
- Perfil Minecraft
- Sesiones
- Renovación de tokens
- Cerrar sesión
- Selector de cuentas
- Avatar del jugador

**Hito:** Minecraft puede ejecutarse autenticado.

---

## FASE 5 — Fabric

- Consultar versiones
- Instalar Fabric Loader
- Gestionar Fabric
- Lanzar Minecraft con Fabric

---

## FASE 6 — Mod Manager

- Manifest de mods
- Mods obligatorios
- Mods opcionales
- Descarga automática
- Actualización
- Eliminación de archivos obsoletos
- SHA-256
- Descargas diferenciales

---

## FASE 7 — Content Manager

Administrar:

- configs
- resource packs
- shader packs
- archivos adicionales

Distinguir archivos administrados y preferencias personales.

---

## FASE 8 — Remote Manifest

Definir protocolo de distribución con:

- versión del pack
- Minecraft
- Fabric
- Java
- archivos
- URLs
- tamaños
- hashes
- obligatoriedad

Implementar comparación local/remota, progreso, velocidad, descargas y verificación.

---

## FASE 9 — Reparación

- Verificación rápida
- Verificación completa
- Detectar archivos corruptos
- Reparar archivos
- Restaurar instalación

---

## FASE 10 — UI definitiva

- Diseño visual
- Navegación
- Pantalla principal
- Login
- Ajustes
- Progreso
- Errores
- Animaciones
- Identidad visual

---

## FASE 11 — Noticias y eventos

- API de noticias
- Eventos
- Banners
- Changelogs
- Avisos importantes

---

## FASE 12 — Integración con el servidor

Mostrar:

- online/offline
- jugadores
- máximo
- ping
- información relevante

---

## FASE 13 — Ajustes

- RAM
- Java
- Directorios
- Preferencias
- Mods opcionales
- Configuraciones avanzadas

---

## FASE 14 — Logs y diagnóstico

- `launcher.log`
- Captura de errores
- Diagnóstico
- Exportación de información
- Logs de Minecraft

---

## FASE 15 — Manejo de errores

Contemplar:

- sin Internet
- servidor caído
- API caída
- descarga interrumpida
- disco lleno
- Java incorrecto
- archivos corruptos
- login expirado
- Fabric incompatible
- crash de Minecraft

---

## FASE 16 — Seguridad

- HTTPS
- hashes
- almacenamiento seguro de tokens
- validación de URLs
- validación de manifest
- seguridad de actualizaciones
- posible firma de manifests/releases

---

## FASE 17 — Self Updater

- comprobar versión de MiyuLauncher
- descargar actualización
- updater independiente
- reemplazar aplicación
- reiniciar launcher
- rollback ante fallos

---

## FASE 18 — Backend

Endpoints conceptuales:

- `launcher/version`
- `manifest`
- `news`
- `events`
- `server`

Almacenamiento para mods, configs, assets, actualizaciones y banners.

---

## FASE 19 — Panel administrativo

Herramientas para:

- administrar mods
- publicar versiones
- publicar noticias
- crear eventos
- subir banners
- generar manifests

---

## FASE 20 — Empaquetado

Convertir MiyuLauncher en aplicación distribuible.

Objetivo: `MiyuLauncher.exe`

El usuario no necesitará Python.

---

## FASE 21 — Instalador

Crear `MiyuLauncher-Setup.exe` con:

- instalación
- accesos directos
- menú Inicio
- desinstalación
- directorios de aplicación

---

## FASE 22 — Testing

Probar:

- PC limpia
- sin Java
- sin Minecraft
- Internet lento
- pérdida de conexión
- archivos corruptos
- actualizaciones entre versiones
- hardware diferente
- PCs de usuarios reales

---

## FASE 23 — Release Candidate

Congelar nuevas características y trabajar exclusivamente en:

- bugs
- estabilidad
- seguridad
- UX

Versiones previstas: `1.0.0-rc1`, `1.0.0-rc2`, etc.

---

## FASE 24 — MiyuLauncher 1.0

Objetivo final:

**Instalar → iniciar sesión → sincronizar → JUGAR.**

Las actualizaciones posteriores deberán ser automáticas.
