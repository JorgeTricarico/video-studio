---
name: soy-garrahan-production
description: >-
  Base de conocimiento de dominio, identidad visual, reglas editoriales y protocolo de producción de Reels para la campaña Soy Garrahan (Hospital Garrahan).
  Define la voz de marca, portavoces (Johanna Tricarico, Graciela), directivas sobre la Ley de Emergencia Pediátrica,
  reemplazos fonéticos médicos/políticos, assets de marca (badge y outro card) y sincronización con Google Drive.
---

# SOY GARRAHAN • SKILL DE DOMINIO Y PRODUCCIÓN AUDIOVISUAL

Este Skill encapsula todo el entendimiento institucional, contexto sociopolítico, identidad gráfica y pautas editoriales de la campaña **Soy Garrahan** (Familias y trabajadores en defensa del Hospital de Pediatría Garrahan).

---

## 1. Misión, Narrativa y Tono Editorial

### Contexto Institucional
- **El Garrahan:** Hospital pediátrico público de máxima complejidad de Argentina y referente de toda América Latina.
- **Narrativa Central:** Defensa irrestricta de la salud pública, financiamiento de medicamentos oncológicos, insumos pediátricos, trasplantes y salarios dignos de profesionales.
- **Principio Fundamental:** *"El Hospital Garrahan no te pregunta a quién votaste para salvarle la vida a tu hijo."* La causa trasciende banderías partidarias.
- **Ejes de Campaña:**
  1. **Ley de Emergencia Pediátrica:** Visibilizar los plazos de vencimiento, exigir votaciones nominales a diputados y senadores.
  2. **Contraste de Prioridades del Estado:** Compra de equipamiento militar (aviones F-16) vs. recortes en salud infantil, discapacidad y programas de asistencia (Incluir Salud, DADSE).
  3. **Testimonios Testeados en Primera Persona:** Casos reales de familias de todo el país atendidas en el Garrahan tras fallas del sistema privado o provincial.

### Portavoces Principales
- **Johanna Tricarico:** Madre referente de la comisión de familias del Garrahan. Tono firme, urgente, empático, sin medias tintas.
- **Graciela:** Testimonio federal de familias del interior.

---

## 2. Identidad Visual y Assets Canónicos

### Paleta Cromática y Tipografía
- **Cyan Eléctrico:** `#00E5FF` (Acento institucional de marca).
- **Rojo Alerta:** `#FE2C55` / `0xCC0000` (Fondo de píldoras informativas de emisión en vivo).
- **Blanco Puro:** `#FFFFFF` (Texto base de subtítulos e información).
- **Amarillo Hormozi:** `#00FFFF` en formato BGR de libass (`&H0000FFFF&`) para palabras activas habladas.
- **Tipografía:** Arial Black (`ariblk.ttf`) para subtítulos Hormozi de alto impacto y Arial Bold (`arialbd.ttf`) para banners informativos.

### Assets Gráficos Obligatorios
- **Insignia Superior (Badge):** `assets/logos/soygarrahan_badge.png`
  - Posición: Centrado horizontal `(W-w)/2`, `y=35`.
- **Placa de Cierre (Outro Card):** `assets/logos/outro_card.png`
  - Duración: 3.2 segundos con fundido suave (`fade=in:d=0.5`).
  - Slogan: *"EL GARRAHAN SALVA VIDAS • SEGUINOS Y COMPARTÍ ESTE TESTIMONIO"*.
  - Decaimiento sonoro (`afade=out:d=1.5`) y `apad`.
- **Píldora de Emisión / Titular:**
  - Posición vertical: `y=1320`.
  - Fondo: Rojo `boxcolor=0xCC0000@0.92`, texto en blanco mayúsculas, bordes de 10px.
- **Zona Segura de Subtítulos:**
  - Posición vertical: `y=1450` a `y=1460`.

---

## 3. Diccionario Fonético y Normalización (Gate 3)

La producción de Garrahan requiere auditoría estricta de términos médicos y apellidos en `config/dictionary.json`:

| Transcripción Whisper Errónea | Corrección Fonética Canónica |
| :--- | :--- |
| `garrajan`, `garrajam`, `garajan` | `Garrahan` |
| `hospital garrajan` | `Hospital Garrahan` |
| `tri cárico`, `tricarico`, `trikarico` | `Tricarico` |
| `pediatrica`, `pediatrico` | `pediátrica`, `pediátrico` |
| `f 16`, `f dieciseis`, `efedieciseis` | `F16` |
| `incluirsalud`, `incluir salud` | `Incluir Salud` |
| `inmuno supresores` | `inmunosupresores` |

> [!IMPORTANT]
> Si el Pre-Flight Check reporta un error en Gate 3, agrega el término observado en `config/dictionary.json` bajo `word_replacements` o `multiword_replacements`.

---

## 4. Shows y Campañas Registradas (`config/shows.json`)

Los perfiles de campaña oficiales de Garrahan residen en `config/shows.json`:
- `fm_en_transito`: Entrevista en vivo a Johanna Tricarico en FM En Tránsito (5 reels).
- `am530_somos_radio`: Cobertura radial en AM530 Somos Radio (5 reels).
- `radio10`: Entrevista radial matutina en Radio 10 (3 reels).
- `voces_del_interior`: Graciela y testimonios federales (5 reels).
- `septiembre_johanna_antonela`: Campaña fundacional de movilizaciones (12 reels).

---

## 5. Destino de Distribución y Google Drive

Todos los reels producidos para Soy Garrahan deben sincronizarse automáticamente con la unidad compartida oficial de Google Drive:
- **Ruta de Montaje:**
  `G:\.shortcut-targets-by-id\1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2\VIDEOS IA SOYGARRAHAN`
- **Estructura Requerida por Campaña:**
  - Versión oficial con subtítulos Hormozi y branding (`[id].mp4`).
  - Versión limpia sin subtítulos (`[id]_sin_subtitulos.mp4`).
  - Pasaportes de certificación técnica (`[id].qa.json`).
  - Catálogo de copys maestros y archivo comprimido ZIP de respaldo.
  - Catálogo central sincronizado en la raíz: `catalog.json` y visor `index.html`.

---

## 6. Comandos de Producción Canónicos

### Pre-Flight Check (<2s)
```powershell
python video_editor.py reel --show <show_id> --mode preflight
# o mediante el harness legacy:
python reels_production_harness.py --mode preflight --show <show_id>
```

### Previsualización Visual Rápida (<1.5s)
```powershell
python video_editor.py reel --show <show_id> --reel <reel_id> --mode preview
```

### Renderizado Completo, Entrega Dual y Sync con Drive
```powershell
python video_editor.py reel --show <show_id> --mode full
```
