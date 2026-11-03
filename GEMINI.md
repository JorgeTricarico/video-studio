# REGLAS DE OPERACIÓN PARA AGENTES FLASH (VIDEO STUDIO • GENERAL VIDEO ENGINE)

## 1. Identidad y Arquitectura Canónica
Este repositorio es un **Motor General de Edición de Video (Video Studio Engine)** con capacidades profesionales de postproducción audiovisual, subtitulado dinámico, re-encuadre vertical y orquestación de campañas de Reels con certificación de calidad:

- **Motor Principal (`core/`):**
  - `video_editor.py`: Fachada unificada (`VideoEditor`) para subtitulado, corte, re-encuadre, audio y placas.
  - `subtitle_engine.py`: Motor dinámico Hormozi / minimal / boxed (sin parpadeos en libass, pop de escala suave).
  - `video_compositor.py`: Compositor FFmpeg modular (quema de subtítulos, split 9:16, blur background, NVENC/CPU).
  - `audio_boundary_auditor.py`: Detección acústica de valles de silencio en ventanas de 50ms (Gate 2).
  - `qa_auditor.py`: Inspección de SAR 1:1, resolución, sonoridad -14 LUFS y pasaportes `.qa.json` (Gate 4).
  - `visual_inspector.py`: Métricas de nitidez, luminancia, contraste y hojas de contacto 3x2 (Gate 5).
  - `visual_patcher.py`: Placas gráficas de impacto (Motion Title Cards) para baches de video.
  - `env_config.py`: Detección de binarios WinGet FFmpeg, tipografías y perfiles de marca.
- **Configuración Declarativa (`config/`):**
  - `config/shows.json`: Definición de shows, timestamps, hooks y recortes.
  - `config/dictionary.json`: Reemplazos fonéticos (`word_replacements`, `multiword_replacements`) y `blacklist_typos`.
  - `config/brands/`: Perfiles de marca modulares (`soygarrahan.yaml`, `generic.yaml`).
- **Interfaces CLI Deterministas:**
  - `python video_editor.py <comando>`: Punto de entrada para edición modular (subtitle, cut, concat, reframe, audio, inspect, patch, reel).
  - `python reels_production_harness.py`: Harness canónico para producción de campañas de Reels.

---

## 2. Desacoplamiento de Marca: Skill Específico de Soy Garrahan
- El motor de video es **completamente agnóstico de marcas**.
- Para tareas relacionadas con la campaña de **Soy Garrahan • Hospital Garrahan** (portavoces Johanna Tricarico y Graciela, Ley de Emergencia Pediátrica, badge, outro card y sync con Google Drive), **activa y consulta siempre su skill especializado:**
  👉 **`soy-garrahan-production`**.

---

## 3. Flujo de Trabajo Obligatorio (Ciclo Rápido para Modelos Flash)

1. **Lectura Eficiente de Transcripciones:**
   Nunca leas JSONs crudos de Whisper de más de 500 líneas. Comprímelos primero:
   `python reels_production_harness.py --mode compact-transcript --input <archivo.json>`

2. **Edición Modular Rápida:**
   - **Subtitular un video:** `python video_editor.py subtitle --video <video.mp4> --transcript <whisper.json> [--style hormozi|minimal|boxed]`
   - **Cortar con auto-silencio:** `python video_editor.py cut --video <video.mp4> --start <s_ini> --end <s_fin> --auto-align`
   - **Convertir a 9:16 vertical:** `python video_editor.py reframe --video <video.mp4> --aspect 9:16 --mode blur_bg`
   - **Normalizar sonoridad:** `python video_editor.py audio --video <video.mp4> --lufs -14`

3. **Producción de Campañas de Reels (Pre-Flight Primero):**
   Antes de renderizar cualquier campaña, ejecuta siempre el Pre-Flight Check (<2s):
   `python video_editor.py reel --show <show_id> --mode preflight`

4. **Auto-Remediación (Self-Healing):**
   - Si falla **Gate 2 (Acústico)**: Lee `suggested_start` y `suggested_end` de la salida JSON y actualiza `config/shows.json`. No crees scripts en `scratch/`.
   - Si falla **Gate 3 (Lingüístico)**: Añade el término reportado en `self_healing_hint` dentro de `config/dictionary.json` y vuelve a correr `--mode preflight`.

5. **Prohibido crear scripts sueltos:**
   No crees scripts `.py` desechables en la raíz ni en `scratch/` para inspeccionar audio o subtítulos. Usa las herramientas provistas por `video_editor.py`.

6. **Entrega Dual y Sincronización Automática:**
   La ejecución de `python video_editor.py reel --show <show_id> --mode full` genera siempre por defecto ambas versiones por reel (`[id].mp4` y `[id]_sin_subtitulos.mp4`), realiza la certificación de los 5 Gates, genera el archivo ZIP y sincroniza con Google Drive si la ruta configurada está montada.
