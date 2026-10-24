<<<<<<< HEAD
```markdown
# MiyuLauncher — Roadmap

Este documento contiene la hoja de ruta general de MiyuLauncher.

Los números de versión son orientativos y podrán cambiar durante el desarrollo.
=======
# MiyuLauncher — Roadmap

Este documento contiene la hoja de ruta general de MiyuLauncher. Los números de versión son orientativos y podrán cambiar durante el desarrollo.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

---

## FASE 0 — Preparación

- [x] Elegir tecnologías
- [x] Instalar Python
- [x] Instalar Git
- [x] Instalar PySide6
<<<<<<< HEAD
- [x] Crear estructura
- [x] Crear primera ventana
- [ ] Crear documentación
- [ ] Crear primer commit
- [ ] Crear repositorio GitHub
=======
- [x] Crear estructura inicial
- [x] Crear primera ventana
- [x] Crear documentación base
- [x] Crear primer commit
- [x] Crear repositorio GitHub
- [x] Conectar el repositorio para trabajar sobre el proyecto real
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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

<<<<<<< HEAD
Hito: Minecraft puede iniciarse desde MiyuLauncher.
=======
**Hito:** Minecraft puede iniciarse desde MiyuLauncher.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

---

## FASE 2 — Minecraft Manager

- Consultar versiones disponibles
- Descargar Minecraft
- Descargar libraries
- Descargar assets
- Verificar hashes
- Crear instancia independiente
- Reparar archivos faltantes

<<<<<<< HEAD
Hito: MiyuLauncher puede instalar Minecraft sin depender del launcher oficial.
=======
**Hito:** MiyuLauncher puede instalar Minecraft sin depender del launcher oficial.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

---

## FASE 3 — Java Manager

- Detectar versión requerida
- Descargar Java Runtime
- Administrar runtimes
- Permitir Java personalizado
<<<<<<< HEAD
- Seleccionar automáticamente runtime apropiado

Hito: el usuario no necesita instalar Java manualmente.
=======
- Seleccionar automáticamente el runtime apropiado

**Hito:** el usuario no necesita instalar Java manualmente.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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

<<<<<<< HEAD
Hito: Minecraft puede ejecutarse autenticado.
=======
**Hito:** Minecraft puede ejecutarse autenticado.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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

<<<<<<< HEAD
Definir protocolo de distribución.

El manifest contendrá:
=======
Definir protocolo de distribución con:
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

- versión del pack
- Minecraft
- Fabric
- Java
- archivos
- URLs
- tamaños
- hashes
- obligatoriedad

<<<<<<< HEAD
Implementar:

- comparación local/remota
- progreso
- velocidad
- descargas
- verificación
=======
Implementar comparación local/remota, progreso, velocidad, descargas y verificación.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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
<<<<<<< HEAD
- navegación
- pantalla principal
- login
- ajustes
- progreso
- errores
- animaciones
- identidad visual
=======
- Navegación
- Pantalla principal
- Login
- Ajustes
- Progreso
- Errores
- Animaciones
- Identidad visual
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

---

## FASE 11 — Noticias y eventos

- API de noticias
<<<<<<< HEAD
- eventos
- banners
- changelogs
- avisos importantes

---

## FASE 12 — Integración servidor
=======
- Eventos
- Banners
- Changelogs
- Avisos importantes

---

## FASE 12 — Integración con el servidor
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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
<<<<<<< HEAD
- directorios
- preferencias
- mods opcionales
- configuraciones avanzadas
=======
- Directorios
- Preferencias
- Mods opcionales
- Configuraciones avanzadas
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

---

## FASE 14 — Logs y diagnóstico

<<<<<<< HEAD
- launcher.log
- captura de errores
- diagnóstico
- exportación de información
- logs de Minecraft
=======
- `launcher.log`
- Captura de errores
- Diagnóstico
- Exportación de información
- Logs de Minecraft
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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

<<<<<<< HEAD
Endpoints previstos conceptualmente:

- launcher/version
- manifest
- news
- events
- server

Almacenamiento para:

- mods
- configs
- assets
- actualizaciones
- banners
=======
Endpoints conceptuales:

- `launcher/version`
- `manifest`
- `news`
- `events`
- `server`

Almacenamiento para mods, configs, assets, actualizaciones y banners.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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

<<<<<<< HEAD
Objetivo:

`MiyuLauncher.exe`
=======
Objetivo: `MiyuLauncher.exe`
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

El usuario no necesitará Python.

---

## FASE 21 — Instalador

<<<<<<< HEAD
Crear:

`MiyuLauncher-Setup.exe`

Funciones:
=======
Crear `MiyuLauncher-Setup.exe` con:
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

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

<<<<<<< HEAD
Congelar nuevas características.

Trabajar exclusivamente en:
=======
Congelar nuevas características y trabajar exclusivamente en:
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

- bugs
- estabilidad
- seguridad
- UX

<<<<<<< HEAD
Versiones:

- 1.0.0-rc1
- 1.0.0-rc2
- etc.
=======
Versiones previstas: `1.0.0-rc1`, `1.0.0-rc2`, etc.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f

---

## FASE 24 — MiyuLauncher 1.0

Objetivo final:

<<<<<<< HEAD
Instalar
→ iniciar sesión
→ sincronizar
→ JUGAR.

Las actualizaciones posteriores deberán ser automáticas.
=======
**Instalar → iniciar sesión → sincronizar → JUGAR.**

Las actualizaciones posteriores deberán ser automáticas.
>>>>>>> c75cd589522cd6c9353ac9d40d24a21c764c782f
