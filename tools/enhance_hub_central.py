import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "..", "..", "01_Reels_Finales_Subtitulados", "index.html")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Inyectar estilos CSS para las nuevas pestañas y vistas antes de </style>
css_additions = """
    /* Main Navigation Tab Bar */
    .main-tabs-nav {
      background: #060a14;
      border-bottom: 1px solid var(--surface-border);
      padding: 0 24px;
      position: sticky;
      top: 64px;
      z-index: 80;
    }

    .tabs-wrapper {
      max-width: 1680px;
      margin: 0 auto;
      display: flex;
      gap: 8px;
      overflow-x: auto;
    }

    .nav-tab-btn {
      background: transparent;
      border: none;
      border-bottom: 3px solid transparent;
      color: var(--text-dim);
      padding: 13px 20px;
      font-size: 0.88rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .nav-tab-btn:hover {
      color: var(--text);
      background: rgba(255, 255, 255, 0.03);
    }

    .nav-tab-btn.active {
      color: var(--cyan);
      border-bottom-color: var(--cyan);
      background: rgba(0, 229, 255, 0.06);
    }

    .tab-pane {
      display: none;
    }

    .tab-pane.active {
      display: block;
    }

    /* Views Layout (Full width container for Copies, Interviews, Folders) */
    .full-view-container {
      max-width: 1680px;
      margin: 0 auto;
      padding: 24px 24px 60px;
      min-height: 75vh;
    }

    /* Documents View */
    .docs-layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 24px;
      align-items: start;
    }

    .docs-sidebar {
      background: var(--bg-card);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-md);
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .docs-sidebar h3 {
      font-size: 0.82rem;
      font-weight: 800;
      color: var(--cyan);
      text-transform: uppercase;
      margin-bottom: 4px;
      letter-spacing: 0.5px;
    }

    .doc-item-btn {
      background: #090e1b;
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-sm);
      color: var(--text);
      padding: 12px 14px;
      text-align: left;
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: all 0.15s ease;
    }

    .doc-item-btn:hover {
      border-color: var(--cyan);
      background: rgba(0, 229, 255, 0.06);
    }

    .doc-item-btn.active {
      border-color: var(--cyan);
      background: rgba(0, 229, 255, 0.12);
      color: var(--cyan);
    }

    .doc-item-btn .doc-subtitle {
      font-size: 0.72rem;
      color: var(--text-dim);
      font-weight: 500;
    }

    .docs-viewer-card {
      background: var(--bg-card);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-md);
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .docs-viewer-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--surface-border);
    }

    .docs-viewer-header h2 {
      font-size: 1.15rem;
      font-weight: 800;
      color: #fff;
    }

    .docs-actions {
      display: flex;
      gap: 10px;
    }

    .btn-doc-action {
      background: #0c1424;
      border: 1px solid var(--border-accent);
      color: var(--cyan);
      padding: 8px 14px;
      border-radius: var(--radius-sm);
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      text-decoration: none;
      transition: all 0.15s ease;
    }

    .btn-doc-action:hover {
      background: rgba(0, 229, 255, 0.12);
      border-color: var(--cyan);
    }

    .btn-doc-action.primary {
      background: linear-gradient(135deg, var(--primary), #b065c0);
      color: #fff;
      border: none;
    }

    .btn-doc-action.primary:hover {
      background: linear-gradient(135deg, #a85cb8, #bd73ce);
    }

    .doc-content-box {
      background: #050811;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius-sm);
      padding: 20px;
      font-family: 'Consolas', 'Menlo', 'Monaco', monospace;
      font-size: 0.84rem;
      line-height: 1.6;
      color: #e2e8f0;
      max-height: 65vh;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }

    /* Interviews View */
    .interviews-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 24px;
    }

    .interview-card {
      background: var(--bg-card);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-md);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: all 0.2s ease;
    }

    .interview-card:hover {
      border-color: var(--cyan);
      transform: translateY(-2px);
      box-shadow: 0 10px 25px rgba(0, 229, 255, 0.1);
    }

    .interview-card-header {
      background: #080d1a;
      padding: 16px 20px;
      border-bottom: 1px solid var(--surface-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .interview-card-header h3 {
      font-size: 0.95rem;
      font-weight: 800;
      color: #fff;
    }

    .interview-card-body {
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      flex: 1;
    }

    .interview-meta-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .meta-pill {
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      background: #0a1122;
      border: 1px solid var(--surface-border);
      color: var(--text-muted);
    }

    .interview-desc {
      font-size: 0.82rem;
      color: var(--text);
      line-height: 1.5;
    }

    .interview-card-footer {
      padding: 14px 20px;
      background: #060a14;
      border-top: 1px solid var(--surface-border);
      display: flex;
      gap: 10px;
    }

    /* Folders Architecture View */
    .folders-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
      gap: 20px;
    }

    .folder-arch-card {
      background: var(--bg-card);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-md);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .folder-arch-card h3 {
      font-size: 0.98rem;
      font-weight: 800;
      color: var(--cyan);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .folder-path-box {
      background: #050811;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 6px;
      padding: 10px 14px;
      font-family: monospace;
      font-size: 0.78rem;
      color: var(--yellow);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      word-break: break-all;
    }

    .folder-desc {
      font-size: 0.82rem;
      color: var(--text-muted);
      line-height: 1.5;
    }
"""

if "/* Main Navigation Tab Bar */" not in html:
    html = html.replace("</style>", f"{css_additions}\n</style>")

# 2. Inyectar barra de navegación de pestañas después de </section> (summary-strip)
tabs_nav_markup = """
  <!-- Main Navigation Tabs -->
  <nav class="main-tabs-nav">
    <div class="tabs-wrapper">
      <button class="nav-tab-btn active" data-tab="tab-reels" onclick="switchMainTab('tab-reels')">
        <span>🎬</span>
        <span>Estudio de Reels (30)</span>
      </button>
      <button class="nav-tab-btn" data-tab="tab-copies" onclick="switchMainTab('tab-copies')">
        <span>📝</span>
        <span>Copys & Documentos</span>
      </button>
      <button class="nav-tab-btn" data-tab="tab-interviews" onclick="switchMainTab('tab-interviews')">
        <span>🎙️</span>
        <span>Entrevistas Completas (5)</span>
      </button>
      <button class="nav-tab-btn" data-tab="tab-folders" onclick="switchMainTab('tab-folders')">
        <span>📁</span>
        <span>Estructura del Proyecto</span>
      </button>
    </div>
  </nav>
"""

if "<!-- Main Navigation Tabs -->" not in html:
    html = html.replace("</section>", f"</section>\n{tabs_nav_markup}")

# 3. Envolver <main class="studio-container"> en <div id="tab-reels" class="tab-pane active">
if '<div id="tab-reels" class="tab-pane active">' not in html:
    html = html.replace('<main class="studio-container">', '<div id="tab-reels" class="tab-pane active">\n  <main class="studio-container">')
    html = html.replace('</main>', '</main>\n</div>')

# 4. Agregar vistas para Copies, Entrevistas y Carpetas antes de <!-- Technical Modal for ZIP Packs -->
extra_views_markup = """
  <!-- TAB 2: Centro de Copys & Documentos -->
  <div id="tab-copies" class="tab-pane">
    <div class="full-view-container">
      <div class="docs-layout">
        <!-- Sidebar de Documentos -->
        <div class="docs-sidebar">
          <h3>Archivos de Copys</h3>
          <button class="doc-item-btn active" onclick="loadDocument('CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt', '⭐ Catálogo Maestro Consolidado (30 Reels)', this)">
            <span>⭐ Catálogo Maestro Completo</span>
            <span class="doc-subtitle">Los 30 copys en un solo archivo • 45 KB</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('CATALOGO_Y_COPIES_AM530.txt', '📻 Johanna Tricarico • Somos Radio AM 530 (5 Reels)', this)">
            <span>📻 Johanna • AM 530</span>
            <span class="doc-subtitle">5 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('CATALOGO_Y_COPIES_GRACIELA_VOCES_DEL_INTERIOR.txt', '🎙️ Graciela del Valle • Voces del Interior (5 Reels)', this)">
            <span>🎙️ Graciela • Voces Interior</span>
            <span class="doc-subtitle">5 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('CATALOGO_Y_COPIES_FM_EN_TRANSITO.txt', '📻 Johanna Tricarico • FM En Tránsito (5 Reels)', this)">
            <span>📻 Johanna • FM En Tránsito</span>
            <span class="doc-subtitle">5 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('CATALOGO_Y_COPIES_NUEVA_LEY.txt', '🎙️ Johanna Tricarico • Radio 10 (3 Reels)', this)">
            <span>🎙️ Johanna • Radio 10</span>
            <span class="doc-subtitle">3 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('CATALOGO_Y_COPIES_SEPTIEMBRE_JOHANNA_ANTONELA.txt', '💜 Johanna & Antonela • Campaña Septiembre (12 Reels)', this)">
            <span>💜 Johanna & Antonela</span>
            <span class="doc-subtitle">12 Reels • Septiembre 2026</span>
          </button>
        </div>

        <!-- Visor del Documento -->
        <div class="docs-viewer-card">
          <div class="docs-viewer-header">
            <div>
              <h2 id="doc-active-title">⭐ Catálogo Maestro Consolidado (30 Reels)</h2>
              <p style="font-size: 0.8rem; color: var(--text-dim); margin-top: 4px;" id="doc-active-filename">CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt</p>
            </div>
            <div class="docs-actions">
              <button class="btn-doc-action primary" onclick="copyActiveDoc()">
                <span>📋 Copiar Todo el Texto</span>
              </button>
              <a href="CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt" download id="btn-doc-download" class="btn-doc-action">
                <span>⬇️ Descargar .TXT</span>
              </a>
            </div>
          </div>
          <pre class="doc-content-box" id="doc-display-content">Cargando documento...</pre>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 3: Entrevistas Completas Originales -->
  <div id="tab-interviews" class="tab-pane">
    <div class="full-view-container">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.3rem; font-weight: 800; color: #fff;">🎙️ Archivo de Entrevistas Completas de Origen</h2>
        <p style="font-size: 0.84rem; color: var(--text-muted); margin-top: 4px;">
          Videos crudos y emisiones completas en máxima definición desde donde se curaron y editaron los 30 reels.
        </p>
      </div>

      <div class="interviews-grid">
        <!-- Entrevista 1: AM 530 -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>Somos Radio AM 530</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">10:01 • 150 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Johanna Tricarico • Colectivo Soy Garrahan</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">1080p Full HD</span>
              <span class="meta-pill">Octubre 2026</span>
              <span class="meta-pill">5 Reels Editados</span>
            </div>
            <p class="interview-desc">
              Denuncia sobre el caso de la nena de Salta a quien le suspendieron la cirugía por falta de DNI, la burocracia en medicamentos oncológicos, la excelencia del Garrahan y las muñecas Quita Penas.
            </p>
          </div>
          <div class="interview-card-footer">
            <a href="entrevistas_fuente/Entrevista_Johanna_AM530.mp4" download class="btn-doc-action" style="flex: 1; justify-content: center;">
              ⬇️ Descargar Video (150 MB)
            </a>
          </div>
        </div>

        <!-- Entrevista 2: FM En Tránsito -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>FM En Tránsito 93.9</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">20:00 • 226 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Johanna Tricarico • En Piso de Radio</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">720p HD</span>
              <span class="meta-pill">Octubre 2026</span>
              <span class="meta-pill">5 Reels Editados</span>
            </div>
            <p class="interview-desc">
              Vencimiento del 21 de octubre de la ley de emergencia pediátrica, el contraste entre el gasto en aviones de combate F16 vs discapacidad, y marcha junto a Madres de Plaza de Mayo.
            </p>
          </div>
          <div class="interview-card-footer">
            <a href="entrevistas_fuente/Entrevista_Johanna_FMEnTransito.mp4" download class="btn-doc-action" style="flex: 1; justify-content: center;">
              ⬇️ Descargar Video (226 MB)
            </a>
          </div>
        </div>

        <!-- Entrevista 3: Radio 10 -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>Radio 10</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">09:30 • 51 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Johanna Tricarico • Enlace Radial</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">720p HD</span>
              <span class="meta-pill">Octubre 2026</span>
              <span class="meta-pill">3 Reels Editados</span>
            </div>
            <p class="interview-desc">
              Presentación formal en el Congreso del nuevo proyecto de Ley de Salud Pediátrica y Residencias Nacionales, y caso Bayron con medicamentos millonarios.
            </p>
          </div>
          <div class="interview-card-footer">
            <a href="entrevistas_fuente/Entrevista_Johanna_Radio10.mp4" download class="btn-doc-action" style="flex: 1; justify-content: center;">
              ⬇️ Descargar Video (51 MB)
            </a>
          </div>
        </div>

        <!-- Entrevista 4: Canal Cíclico -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>Canal Cíclico</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">31:12 • 353 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Antonela • Testimonio en Estudio</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">1080p Full HD</span>
              <span class="meta-pill">Septiembre 2026</span>
              <span class="meta-pill">4 Reels Editados</span>
            </div>
            <p class="interview-desc">
              Testimonio desgarrador de 7 años recorriendo médicos privados sin diagnóstico, abandono de la obra social con el implante coclear y resolución quirúrgica en el Hospital Garrahan.
            </p>
          </div>
          <div class="interview-card-footer">
            <a href="entrevistas_fuente/Entrevista_Antonela_Ciclico.mp4" download class="btn-doc-action" style="flex: 1; justify-content: center;">
              ⬇️ Descargar Video (353 MB)
            </a>
          </div>
        </div>

        <!-- Entrevista 5: Voces del Interior -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>Voces del Interior</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">10:20 • 171 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Graciela del Valle Ferreira • Videollamada</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">Formato Vertical</span>
              <span class="meta-pill">Octubre 2026</span>
              <span class="meta-pill">5 Reels Editados</span>
            </div>
            <p class="interview-desc">
              La perspectiva de las familias del interior del país, el falso mito de las prepagas de primera línea, la construcción de la red federal y convocatoria a Plaza de Mayo el 15 de octubre.
            </p>
          </div>
          <div class="interview-card-footer">
            <a href="entrevistas_fuente/Entrevista_Graciela_VocesDelInterior.mp4" download class="btn-doc-action" style="flex: 1; justify-content: center;">
              ⬇️ Descargar Video (171 MB)
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 4: Arquitectura del Proyecto y Carpetas -->
  <div id="tab-folders" class="tab-pane">
    <div class="full-view-container">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.3rem; font-weight: 800; color: #fff;">📁 Mapa Centralizado de Carpetas y Organización</h2>
        <p style="font-size: 0.84rem; color: var(--text-muted); margin-top: 4px;">
          Estructura estandarizada del proyecto. Cada elemento tiene una ubicación única y sin duplicaciones.
        </p>
      </div>

      <!-- Lanzador Destacado -->
      <div style="background: linear-gradient(135deg, rgba(0, 229, 255, 0.12), rgba(168, 85, 247, 0.12)); border: 1px solid var(--cyan); border-radius: var(--radius-md); padding: 20px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
          <h3 style="color: #fff; font-size: 1.05rem; font-weight: 800; display: flex; align-items: center; gap: 8px;">
            <span>🚀</span> Acceso Directo de 1 Clic: ACCEDER_CENTRO_DE_CONTROL.bat
          </h3>
          <p style="color: var(--text-muted); font-size: 0.84rem; margin-top: 6px;">
            Ubicado en la carpeta principal del proyecto. Inicia el servidor web, abre este Hub y da menú rápido para abrir cualquier carpeta en Windows Explorer.
          </p>
        </div>
        <button class="btn-doc-action primary" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\ACCEDER_CENTRO_DE_CONTROL.bat', '✅ Ruta del lanzador copiada')">
          📋 Copiar Ruta del Lanzador
        </button>
      </div>

      <div class="folders-grid">
        <!-- Carpeta 01 -->
        <div class="folder-arch-card">
          <h3><span>🎬</span> 01_Reels_Finales_Subtitulados</h3>
          <p class="folder-desc">
            Contenedor maestro de los <strong>30 Reels Finales</strong> en 1080x1920 a 60 FPS, este Hub Web interactivo (index.html), catálogo técnico (catalog.json) y la subcarpeta <strong>CAMPANAS_ORGANIZADAS</strong> para navegar las 5 campañas por separado sin consumir espacio extra.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\01_Reels_Finales_Subtitulados</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\01_Reels_Finales_Subtitulados', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Carpeta 02 -->
        <div class="folder-arch-card">
          <h3><span>🎙️</span> 02_Entrevistas_Completas</h3>
          <p class="folder-desc">
            Contiene los 5 videos de emisiones completas originales descargados de YouTube y WhatsApp en máxima definición (AM 530, FM En Tránsito, Radio 10, Canal Cíclico y Voces del Interior).
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\02_Entrevistas_Completas</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\02_Entrevistas_Completas', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Carpeta 03 -->
        <div class="folder-arch-card">
          <h3><span>🎞️</span> 03_Material_Original</h3>
          <p class="folder-desc">
            Archivos brutos de cámara, audios aislados y material audiovisual de apoyo institucional del colectivo Soy Garrahan.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\03_Material_Original</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\03_Material_Original', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Carpeta 04 -->
        <div class="folder-arch-card">
          <h3><span>⚙️</span> 04_Herramientas_y_Codigo</h3>
          <p class="folder-desc">
            Pipeline de producción automatizada en Python: motor de transcripción Whisper, filtros FFmpeg, analizador de audio EBU R128, generador ASS Karaoke y herramientas de control de calidad.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\04_Herramientas_y_Codigo\\Generador_Reels</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\04_Herramientas_y_Codigo\\\\Generador_Reels', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Carpeta 05 -->
        <div class="folder-arch-card">
          <h3><span>📝</span> 05_Documentos_Copies_y_Transcripciones</h3>
          <p class="folder-desc">
            Centro de texto del proyecto: subcarpetas <strong>Copys_Redes</strong> (todos los copys individuales y el consolidado maestro), <strong>Transcripciones_Completas</strong> (archivos VTT, JSON Whisper y textos limpios) y <strong>Documentacion_Proyecto</strong>.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\05_Documentos_Copies_y_Transcripciones</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\05_Documentos_Copies_y_Transcripciones', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Carpeta 06 -->
        <div class="folder-arch-card">
          <h3><span>📦</span> 06_Paquetes_ZIP_Descargables</h3>
          <p class="folder-desc">
            Los 5 paquetes ZIP oficiales comprimidos de cada campaña, listos para enviar por Google Drive, subir a la nube o compartir con la comunidad de familias y colaboradores.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\06_Paquetes_ZIP_Descargables</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\06_Paquetes_ZIP_Descargables', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
"""

if "<!-- TAB 2: Centro de Copys & Documentos -->" not in html:
    html = html.replace('<!-- Modal for ZIP Packs -->', f"{extra_views_markup}\n  <!-- Modal for ZIP Packs -->")

# 5. Agregar funciones JavaScript para las pestañas y el visor de documentos
js_functions = """
    // Manejo de Pestañas Principales
    function switchMainTab(tabId) {
      document.querySelectorAll('.main-tabs-nav .nav-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
      });
      document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === tabId);
      });

      if (tabId === 'tab-copies' && !window.hasLoadedInitialDoc) {
        loadDocument('CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt', '⭐ Catálogo Maestro Consolidado (30 Reels)');
        window.hasLoadedInitialDoc = true;
      }
    }

    let currentLoadedDocText = "";

    async function loadDocument(filename, title, btnElement) {
      if (btnElement) {
        document.querySelectorAll('.docs-sidebar .doc-item-btn').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
      }

      document.getElementById('doc-active-title').textContent = title;
      document.getElementById('doc-active-filename').textContent = filename;
      document.getElementById('btn-doc-download').href = filename;
      const display = document.getElementById('doc-display-content');
      display.textContent = "Cargando documento...";

      try {
        const res = await fetch(filename);
        if (!res.ok) throw new Error("No se pudo cargar el archivo");
        const text = await res.text();
        currentLoadedDocText = text;
        display.textContent = text;
      } catch (err) {
        display.textContent = `⚠️ Error al cargar el documento ${filename}: ${err.message}`;
      }
    }

    function copyActiveDoc() {
      if (!currentLoadedDocText) {
        showToast("⚠️ No hay texto para copiar.");
        return;
      }
      copyToClipboard(currentLoadedDocText, "✅ ¡Documento completo copiado al portapapeles!");
    }
"""

if "function switchMainTab" not in html:
    html = html.replace("window.addEventListener('DOMContentLoaded', initStudio);", f"{js_functions}\n    window.addEventListener('DOMContentLoaded', initStudio);")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("[OK] Hub Web centralizado actualizado con éxito con 4 pestañas integradas.")
