# ⚡ VIDEO STUDIO • Editor de Video General & Motor de Postproducción Audiovisual

**Video Studio** es una suite profesional determinista basada en Python y FFmpeg para postproducción audiovisual, edición de video general, subtitulado dinámico de alta retención (estilo Hormozi), re-encuadre vertical 9:16 y orquestación de campañas completas de Reels con certificación técnica de 5 etapas.

El motor es **completamente agnóstico de marca** y desacopla la lógica de postproducción de las campañas institucionales. La base de conocimiento y los assets de **Soy Garrahan • Hospital Garrahan** se encuentran encapsulados como un skill especializado de dominio (`soy-garrahan-production`).

---

## 🌟 Capacidades de Edición General

1. **Subtitulado Inteligente & Viral (Hormozi Style)**:
   - Sincronización palabra por palabra con pop de escala animado y cero solapamientos temporales en `libass`.
   - Presets de estilo: `hormozi` (amarillo activo pop), `hormozi_cyan`, `hormozi_green`, `minimal` (limpio inferior con sombra suave) y `boxed` (caja traslúcida).
   - Ingesta directa de Whisper JSON (completo o compacto), archivos SRT, VTT o estructuras nativas.

2. **Corte Preciso con Auto-Alineación Acústica (Silencios Limpios)**:
   - Detección automática de valles de silencio en ventanas de 50ms alrededor de los cortes para evitar palabras o consonantes truncadas.
   - Soporte para copia rápida de streams sin pérdida (`-c copy`) o re-encodeo exacto de fotogramas.

3. **Re-Encuadre de Formato (16:9 horizontal ➔ 9:16 vertical / 1:1)**:
   - Conversión de entrevistas y tomas apaisadas a formato vertical para Reels, TikTok y YouTube Shorts.
   - Modo `blur_bg` (video centrado sobre versión ampliada con desenfoque gaussiano suave), `crop` (recorte central) o `fit` (relleno proporcional).

4. **Masterización y Normalización de Sonoridad Broadcast**:
   - Normalización EBU R128 a **-14.0 LUFS** (estándar oficial de Instagram/TikTok/YouTube) manteniendo la pista de video intacta.

5. **Auditoría Técnica y Gating de 5 Etapas**:
   - Verificación de SAR 1:1, resolución 1080x1920, fotogramas por segundo (60 fps) y sonoridad.
   - Generación de pasaportes técnicos `.qa.json`.
   - Auditoría visual con métricas de luminancia, contraste, nitidez y hojas de contacto 3x2.

6. **Placas Gráficas de Impacto (Motion Title Cards)**:
   - Generación de placas verticales 1080x1920 para cubrir baches visuales o destacar citas textuales.

---

## 🚀 Uso Rápido vía CLI (`video_editor.py`)

El punto de entrada unificado es [`video_editor.py`](file:///C:/Users/admin/Desktop/Reels_Instagram_Edicion/04_Herramientas_y_Codigo/Generador_Reels/video_editor.py):

### 1. Subtitular cualquier video
```powershell
python video_editor.py subtitle --video input.mp4 --transcript whisper.json --style hormozi --color amarillo
```

### 2. Cortar un video con auto-alineación de silencios
```powershell
python video_editor.py cut --video input.mp4 --start 14.2 --end 48.5 --auto-align --out recorte.mp4
```

### 3. Convertir video horizontal (16:9) a vertical (9:16) para Reels
```powershell
python video_editor.py reframe --video input_16_9.mp4 --aspect 9:16 --mode blur_bg --out vertical.mp4
```

### 4. Normalizar sonoridad a -14.0 LUFS
```powershell
python video_editor.py audio --video video.mp4 --lufs -14.0 --out audio_mastered.mp4
```

### 5. Inspeccionar calidad técnica y visual
```powershell
python video_editor.py inspect --video video.mp4 --visual --out-dir scratch/visual_inspection
```

### 6. Generar una placa gráfica de impacto
```powershell
python video_editor.py patch --text "EL HOSPITAL NO PREGUNTA QUÉ VOTASTE" --tag "ALERTA" --out placa.png
```

---

## 🏛️ Campañas Estructuradas de Reels (`config/shows.json`)

Para campañas recurrentes con identidad declarativa (hooks, encuadres, píldoras y entrega dual):

```powershell
# 1. Pre-Flight instantáneo (<2s)
python video_editor.py reel --show <show_id> --mode preflight

# 2. Previsualización rápida de encuadre (<1.5s)
python video_editor.py reel --show <show_id> --reel <reel_id> --mode preview

# 3. Renderizado completo, entrega dual, ZIP y sincronización con Google Drive
python video_editor.py reel --show <show_id> --mode full
```

*(El harness clásico [`reels_production_harness.py`](reels_production_harness.py) se mantiene 100% operativo y compatible).*

---

## 🏥 Dominio Especializado: Soy Garrahan

Toda la identidad de marca, pautas editoriales, portavoces (Johanna Tricarico, Graciela), directivas sobre la Ley de Emergencia Pediátrica, assets de marca y destinos de Google Drive están organizados de forma modular:

- **Skill Específico para Agentes:** `soy-garrahan-production`
- **Configuración de Marca:** [`config/brands/soygarrahan.yaml`](config/brands/soygarrahan.yaml)
- **Campañas Registradas:** [`config/shows.json`](config/shows.json)
- **Diccionario Fonético Médico/Político:** [`config/dictionary.json`](config/dictionary.json)

---

## 🐍 Uso desde Python (`VideoEditor` SDK)

```python
from core import VideoEditor

# 1. Subtitular video
VideoEditor.subtitle(
    video_path="input.mp4",
    transcript="whisper.json",
    out_path="subtitulado.mp4",
    style="hormozi"
)

# 2. Cortar con valles de silencio
VideoEditor.cut(
    video_path="input.mp4",
    start_sec=10.0,
    end_sec=40.0,
    out_path="cut.mp4",
    auto_align_silence=True
)

# 3. Re-encuadrar a vertical con blur
VideoEditor.reframe(
    video_path="input.mp4",
    out_path="vertical.mp4",
    target_aspect="9:16",
    mode="blur_bg"
)

# 4. Masterizar audio
VideoEditor.master_audio(
    video_path="vertical.mp4",
    out_path="final.mp4",
    target_lufs=-14.0
)
```
