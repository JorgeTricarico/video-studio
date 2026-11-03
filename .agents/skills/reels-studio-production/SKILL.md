---
name: reels-studio-production
description: >-
  Protocolo canónico de edición de video general, subtitulado viral dinámico (Hormozi), reframing (9:16 vertical),
  auditoría técnica de 5 Gates y producción de Reels multi-marca con Video Studio Engine.
---

# VIDEO STUDIO • PROTOCOLO GENERAL DE EDICIÓN Y PRODUCCIÓN AUDIOVISUAL

Este Skill define las capacidades, comandos deterministas y directivas operativas del motor general de edición de video **Video Studio Engine**. Permite manipular cualquier video, subtitularlo con estilo viral, cortar tomas con auto-alineación acústica, re-encuadrar formatos y orquestar campañas completas de Reels.

---

## 1. Arquitectura General y Puntos de Entrada

El motor ofrece dos interfaces CLI unificadas:
- [`video_editor.py`](file:///C:/Users/admin/Desktop/Reels_Instagram_Edicion/04_Herramientas_y_Codigo/Generador_Reels/video_editor.py) (o `video_editor_cli.py`): Interfaz moderna para tareas generales y modulares.
- [`reels_production_harness.py`](file:///C:/Users/admin/Desktop/Reels_Instagram_Edicion/04_Herramientas_y_Codigo/Generador_Reels/reels_production_harness.py): Interfaz para campañas declarativas de shows con entrega dual y pasaportes QA.

### Desacoplamiento de Marca
El motor es **100% agnóstico de marca**:
- Marcas y campañas específicas se configuran en `config/brands/<marca>.yaml` o `config/shows.json`.
- Para la campaña institucional de **Soy Garrahan • Hospital Garrahan**, activa y consulta el skill especializado:
  👉 `soy-garrahan-production`.

---

## 2. Comandos de Edición General (`video_editor.py`)

### A. Subtitulado Inteligente y Viral (Hormozi Style)
Subtitula cualquier archivo MP4 con ingesta directa de transcripciones Whisper (JSON, SRT o VTT):
```powershell
python video_editor.py subtitle --video <input.mp4> --transcript <whisper.json> --style hormozi --color amarillo
```
- **Estilos Disponibles:** `hormozi` (amarillo activo pop), `hormozi_cyan`, `hormozi_green`, `minimal` (limpio inferior con sombra suave), `boxed` (caja traslúcida).
- **Parámetros Opcionales:** `--font "Arial Black"`, `--font-size 58`, `--y 1450`, `--out <salida.mp4>`.

### B. Corte Preciso y Auto-Alineación Acústica
Corta un tramo de video garantizando que no queden sílabas cortadas al inicio o al final:
```powershell
python video_editor.py cut --video <input.mp4> --start 12.5 --end 45.0 --auto-align --out <recorte.mp4>
```
- Con `--auto-align`: El motor acústico escanea valles de silencio en ventanas de 50ms antes de cortar.
- Con `--copy`: Realiza corte ultra-rápido sin pérdida por copia de stream (`-c copy`).

### C. Re-Encuadre de Formato (16:9 a 9:16 Vertical / 1:1)
Convierte videos horizontales a formato vertical para Reels/TikTok con fondo desenfocado:
```powershell
python video_editor.py reframe --video <input_16_9.mp4> --aspect 9:16 --mode blur_bg --out <vertical.mp4>
```
- **Modos:** `blur_bg` (fondo desenfocado), `crop` (recorte central), `fit` (relleno negro).
- **Aspectos:** `9:16` (1080x1920), `1:1` (1080x1080), `4:5` (1080x1350), `16:9` (1920x1080).

### D. Normalización de Sonoridad Broadcast (EBU R128)
Ajusta la sonoridad del audio a estándar de redes sociales (-14.0 LUFS) sin recomprimir el video:
```powershell
python video_editor.py audio --video <input.mp4> --lufs -14.0 --out <mastered.mp4>
```

### E. Inspección Técnica y Control de Calidad
Verifica resolución, SAR 1:1, sonoridad LUFS y genera hoja de contacto visual:
```powershell
python video_editor.py inspect --video <video.mp4> --visual --out-dir scratch/visual_inspection
```

### F. Placas Gráficas de Impacto (Motion Title Cards)
Genera placas gráficas 1080x1920 para cubrir baches de video o titulares destacados:
```powershell
python video_editor.py patch --text "TITULAR DE IMPACTO" --tag "ALERTA INFORMATIVA" --out scratch/placa.png
```

---

## 3. Orquestación de Campañas de Reels (Gating de 5 Etapas)

Para campañas declarativas definidas en `config/shows.json`:

1. **Lectura Eficiente de Transcripciones Grandes:**
   ```powershell
   python reels_production_harness.py --mode compact-transcript --input <whisper.json>
   ```
2. **Pre-Flight Check (<2s):**
   ```powershell
   python video_editor.py reel --show <show_id> --mode preflight
   ```
3. **Previsualización de Fotograma (<1.5s):**
   ```powershell
   python video_editor.py reel --show <show_id> --reel <reel_id> --mode preview
   ```
4. **Renderizado Completo y Certificación (Entrega Dual):**
   ```powershell
   python video_editor.py reel --show <show_id> --mode full
   ```
   Genera por defecto ambas versiones (`[id].mp4` y `[id]_sin_subtitulos.mp4`), audita 5 Gates, crea el paquete ZIP y sincroniza con Google Drive si la ruta configurada está montada.

---

## 4. API Python (`VideoEditor`)

Para automatizaciones dentro de scripts Python:
```python
from core import VideoEditor

# Subtitular un video
VideoEditor.subtitle(
    video_path="input.mp4",
    transcript="whisper.json",
    out_path="output.mp4",
    style="hormozi"
)

# Cortar con auto-alineación
VideoEditor.cut(
    video_path="input.mp4",
    start_sec=10.0,
    end_sec=35.0,
    out_path="cut.mp4",
    auto_align_silence=True
)

# Re-encuadrar a 9:16 vertical
VideoEditor.reframe(
    video_path="input.mp4",
    out_path="vertical.mp4",
    target_aspect="9:16",
    mode="blur_bg"
)
```
