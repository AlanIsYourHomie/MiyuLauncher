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
- [x] Detección de Windows, arquitectura y RAM confirmada
- [x] Creación de `%LOCALAPPDATA%/MiyuLauncher` confirmada
- [x] `core/java.py`
  - Java 21.0.11 detectado
  - Java 17.0.19 detectado
  - selección por versión mayor funcionando
- [x] `core/minecraft.py`
  - instalación oficial detectada en `%APPDATA%/.minecraft`
  - versiones 1.21.5 y 26.x detectadas
  - lectura de Java requerido, assets, main class, downloads y librerías
- [x] `core/version_resolver.py`
  - resolución inicial de versión y compatibilidad Java

### Java Runtime Manager — implementado, pendiente de validación local

- [x] `core/runtime.py`
  - runtime administrado en `%LOCALAPPDATA%/MiyuLauncher/runtime/java-<major>`
  - consulta de Eclipse Temurin mediante API de Adoptium
  - selección de Windows y arquitectura
  - descarga de JRE ZIP
  - barra/progreso mediante callback
  - verificación SHA-256 antes de instalar
  - extracción del runtime
  - validación posterior ejecutando `java -version`
  - metadata `miyu-runtime.json`
  - reutilización de runtime ya instalado
- [x] `tools/check_runtime.py`
  - consulta de paquete sin instalar
  - instalación opcional mediante `--install`
  - reinstalación mediante `--force`

## Decisión nueva sobre Java

MiyuLauncher administrará sus propios runtimes Java en lugar de depender del Java instalado globalmente en Windows.

Prioridad prevista:

1. Runtime administrado por MiyuLauncher para la versión mayor requerida por Minecraft.
2. Si no existe, MiyuLauncher lo descargará e instalará automáticamente.
3. El detector de Java del sistema se conservará como diagnóstico/fallback.

Ejemplos confirmados en el PC de desarrollo:

- Minecraft 1.21.5 requiere Java 21.
- Minecraft 26.x requiere Java 25.

Para reducir tamaño de descarga se utilizará Eclipse Temurin JRE cuando esté disponible, ya que el launcher solo necesita ejecutar Minecraft/Fabric.

## Próximo objetivo

1. Ejecutar `python tools/check_runtime.py 25` para confirmar que Adoptium devuelve un JRE compatible.
2. Ejecutar `python tools/check_runtime.py 25 --install` para probar descarga, SHA-256, extracción y validación.
3. Confirmar que aparece `%LOCALAPPDATA%/MiyuLauncher/runtime/java-25/bin/java.exe`.
4. Integrar el runtime administrado con `version_resolver.py` para que Java 25 pase a estar disponible automáticamente para Minecraft 26.x.
5. Retomar resolución de librerías, natives, classpath, assets y argumentos de lanzamiento.

## Arquitectura actual relevante

```text
src/miyu_launcher/
├── core/
│   ├── java.py
│   ├── minecraft.py
│   ├── paths.py
│   ├── runtime.py
│   ├── system.py
│   └── version_resolver.py
└── ui/
    └── main_window.py

tools/
├── check_java.py
├── check_minecraft.py
├── check_runtime.py
└── check_version_resolver.py
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
11. Verificar hashes de cualquier runtime o archivo administrado antes de confiar en él.

## Decisiones importantes

- Lenguaje: Python.
- GUI: PySide6 / Qt.
- Mod loader: Fabric.
- Plataforma inicial: Windows 10/11.
- Java: runtimes administrados por MiyuLauncher.
- Proveedor inicial de runtimes: Eclipse Temurin / Adoptium.
- Datos administrados: `%LOCALAPPDATA%/MiyuLauncher` en Windows.
- Actualizaciones: manifest remoto + hashes SHA-256.
- Mods: sincronización automática; algunos podrán ser opcionales.
- Autenticación oficial: Microsoft/Minecraft; no se almacenarán contraseñas.

## Problemas conocidos

- El Java Runtime Manager todavía debe probarse con una descarga real de Java 25.

## Última prueba confirmada

La instalación estándar de Minecraft fue detectada correctamente. Minecraft 1.21.5 declara Java 21 y las versiones 26.x detectadas declaran Java 25.

## Cómo continuar en otra conversación

1. Leer `PROJECT_STATE.md`.
2. Leer `ROADMAP.md`.
3. Revisar los últimos commits del repositorio.
4. Continuar desde `Próximo objetivo`.
