import os
import sys
import re
import shutil

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    final_dir = os.path.join(project_root, "01_Reels_Finales_Subtitulados")
    index_path = os.path.join(final_dir, "index.html")
    gdrive_dir = r"G:\.shortcut-targets-by-id\1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2\VIDEOS IA SOYGARRAHAN"

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update pill counters and labels
    html = re.sub(r'🎬 Total Reels:\s*<strong id="metric-total">\d+</strong>', '🎬 Total Reels: <strong id="metric-total">36</strong>', html)
    html = re.sub(r'<span id="badge-total-reels">\d+ REELS DISPONIBLES</span>', '<span id="badge-total-reels">36 REELS DISPONIBLES</span>', html)
    html = re.sub(r'<span>Estudio de Reels \(\d+\)</span>', '<span>Estudio de Reels (36)</span>', html)
    html = re.sub(r'<span>Entrevistas Completas \(\d+\)</span>', '<span>Entrevistas y Fuentes (6)</span>', html)
    html = re.sub(r'<span class="pill-counter" id="pill-cnt-all">\d+</span>', '<span class="pill-counter" id="pill-cnt-all">36</span>', html)

    # 2. Add Diputados pill to campaign-pills if not present
    diputados_pill = '''          <button class="filter-pill" data-filter="diputados_comision_salud" onclick="setCampaignFilter('diputados_comision_salud')">
            🏛️ Johanna (Diputados) <span class="pill-counter">6</span>
          </button>'''
    if 'data-filter="diputados_comision_salud"' not in html:
        html = html.replace(
            '<div class="filter-pills-row" id="campaign-pills">\n          <button class="filter-pill active" data-filter="all" onclick="setCampaignFilter(\'all\')">',
            f'<div class="filter-pills-row" id="campaign-pills">\n          <button class="filter-pill active" data-filter="all" onclick="setCampaignFilter(\'all\')">\n            🎬 Todas las Campañas <span class="pill-counter" id="pill-cnt-all">36</span>\n          </button>\n{diputados_pill}'
        )

    # 3. Add Diputados showLabel in JS
    if 'showLabel = "Diputados"' not in html:
        html = html.replace(
            'else if (r.show_id === "septiembre_johanna_antonela") showLabel = "Septiembre";',
            'else if (r.show_id === "septiembre_johanna_antonela") showLabel = "Septiembre";\n        else if (r.show_id === "diputados_comision_salud") showLabel = "Diputados";'
        )

    # 4. Update initial loadDocument title
    html = html.replace(
        "loadDocument('CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt', '⭐ Catálogo Maestro Consolidado (30 Reels)');",
        "loadDocument('CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt', '⭐ Catálogo Maestro Consolidado (36 Reels)');"
    )

    # 5. Inject tab-copies, tab-interviews, tab-folders before Modal
    tabs_markup = """
  <!-- TAB 2: Centro de Copys & Documentos -->
  <div id="tab-copies" class="tab-pane">
    <div class="full-view-container">
      <div class="docs-layout">
        <!-- Sidebar de Documentos -->
        <div class="docs-sidebar">
          <h3>Archivos de Copys</h3>
          <button class="doc-item-btn active" onclick="loadDocument('CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt', '⭐ Catálogo Maestro Consolidado (36 Reels)', this)">
            <span>⭐ Catálogo Maestro Completo</span>
            <span class="doc-subtitle">Los 36 copys en un solo archivo • 50 KB</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('06_Campaña_Octubre_Johanna_Diputados_ComisionSalud/CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt', '🏛️ Johanna Tricarico • Diputados Comisión Salud (6 Reels)', this)">
            <span>🏛️ Johanna • Diputados</span>
            <span class="doc-subtitle">6 Reels • 14 Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('05_Campaña_Octubre_Johanna_AM530/CATALOGO_Y_COPIES_AM530.txt', '📻 Johanna Tricarico • Somos Radio AM 530 (5 Reels)', this)">
            <span>📻 Johanna • AM 530</span>
            <span class="doc-subtitle">5 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('02_Campaña_Octubre_Graciela_VocesDelInterior/CATALOGO_Y_COPIES_GRACIELA_VOCES_DEL_INTERIOR.txt', '🎙️ Graciela del Valle • Voces del Interior (5 Reels)', this)">
            <span>🎙️ Graciela • Voces Interior</span>
            <span class="doc-subtitle">5 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('03_Campaña_Octubre_Johanna_FMEnTransito/CATALOGO_Y_COPIES_FM_EN_TRANSITO.txt', '📻 Johanna Tricarico • FM En Tránsito (5 Reels)', this)">
            <span>📻 Johanna • FM En Tránsito</span>
            <span class="doc-subtitle">5 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('04_Campaña_Octubre_Johanna_Radio10/CATALOGO_Y_COPIES_NUEVA_LEY.txt', '🎙️ Johanna Tricarico • Radio 10 (3 Reels)', this)">
            <span>🎙️ Johanna • Radio 10</span>
            <span class="doc-subtitle">3 Reels • Octubre 2026</span>
          </button>
          <button class="doc-item-btn" onclick="loadDocument('01_Campaña_Septiembre_Johanna_Antonela/CATALOGO_Y_COPIES_SEPTIEMBRE_JOHANNA_ANTONELA.txt', '💜 Johanna & Antonela • Campaña Septiembre (12 Reels)', this)">
            <span>💜 Johanna & Antonela</span>
            <span class="doc-subtitle">12 Reels • Septiembre 2026</span>
          </button>
        </div>

        <!-- Visor del Documento -->
        <div class="docs-viewer-card">
          <div class="docs-viewer-header">
            <div>
              <h2 id="doc-active-title">⭐ Catálogo Maestro Consolidado (36 Reels)</h2>
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
        <h2 style="font-size: 1.3rem; font-weight: 800; color: #fff;">🎙️ Archivo de Emisiones y Fuentes de Origen (6 Fuentes)</h2>
        <p style="font-size: 0.84rem; color: var(--text-muted); margin-top: 4px;">
          Videos crudos y fuentes completas en máxima definición desde donde se curaron y editaron los 36 reels.
        </p>
      </div>

      <div class="interviews-grid">
        <!-- Fuente 1: Diputados Comisión de Salud -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>🏛️ H. Cámara de Diputados</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">11:36 • 48 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Johanna Tricarico • Comisión de Acción Social y Salud Pública</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">Congreso de la Nación</span>
              <span class="meta-pill">14 Octubre 2026</span>
              <span class="meta-pill">6 Reels Editados</span>
            </div>
            <p class="interview-desc">
              Intervención histórica frente a diputados de todos los bloques: carta colectiva de mamás de todo el país, vencimiento de la Ley de Emergencia Pediátrica, niños con cáncer y defensa del Garrahan.
            </p>
          </div>
        </div>

        <!-- Fuente 2: AM 530 -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>📻 Somos Radio AM 530</h3>
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
              Denuncia de auditorías que matan, el caso de la nena de Salta sin DNI, y muñecas quita penas para el 15 de octubre en Plaza de Mayo.
            </p>
          </div>
        </div>

        <!-- Fuente 3: FM En Tránsito -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>📻 FM En Tránsito</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">20:30 • 326 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Johanna Tricarico • Entrevista en Piso</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">1080p Full HD</span>
              <span class="meta-pill">Octubre 2026</span>
              <span class="meta-pill">5 Reels Editados</span>
            </div>
            <p class="interview-desc">
              El vencimiento inminente de la Ley de Salud Pediátrica el 21 de octubre, el recorte presupuestario y comparación del gasto en aviones F16 frente a discapacidad.
            </p>
          </div>
        </div>

        <!-- Fuente 4: Radio 10 -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>🎙️ Radio 10</h3>
            <span class="meta-pill" style="color: var(--cyan); border-color: var(--cyan);">17:00 • 51 MB</span>
          </div>
          <div class="interview-card-body">
            <h4 style="font-size: 0.92rem; color: #fff;">Johanna Tricarico • Comunicación en Vivo</h4>
            <div class="interview-meta-pills">
              <span class="meta-pill">Octubre 2026</span>
              <span class="meta-pill">3 Reels Editados</span>
            </div>
            <p class="interview-desc">
              Presentación formal en el Congreso del nuevo proyecto de Ley de Salud Pediátrica y Residencias Nacionales, y caso Bayron con medicamentos millonarios.
            </p>
          </div>
        </div>

        <!-- Fuente 5: Canal Cíclico -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>🎙️ Canal Cíclico</h3>
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
        </div>

        <!-- Fuente 6: Voces del Interior -->
        <div class="interview-card">
          <div class="interview-card-header">
            <h3>🎙️ Voces del Interior</h3>
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
              La perspectiva de las familias del interior del país, el falso mito de las prepagas de primera línea, la construcción de la red federal y convocatoria a Plaza de Mayo.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 4: Arquitectura del Proyecto y Carpetas -->
  <div id="tab-folders" class="tab-pane">
    <div class="full-view-container">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.3rem; font-weight: 800; color: #fff;">📁 Mapa Centralizado de Carpetas y Campañas Organizadas</h2>
        <p style="font-size: 0.84rem; color: var(--text-muted); margin-top: 4px;">
          Estructura estandarizada por campañas. Cada campaña tiene su subcarpeta con videos, pasaportes técnicos QA, catálogo de copys y paquete ZIP.
        </p>
      </div>

      <div class="folders-grid">
        <!-- Campaña 06 -->
        <div class="folder-arch-card">
          <h3><span>🏛️</span> 06_Campaña_Octubre_Johanna_Diputados_ComisionSalud</h3>
          <p class="folder-desc">
            Contiene los <strong>6 Reels</strong> de la intervención de Johanna Tricarico en la Comisión de Salud de la Cámara de Diputados de la Nación (14-Oct-2026), catálogo de copys y su archivo ZIP completo.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\01_Reels_Finales_Subtitulados\\06_Campaña_Octubre_Johanna_Diputados_ComisionSalud</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\01_Reels_Finales_Subtitulados\\\\06_Campaña_Octubre_Johanna_Diputados_ComisionSalud', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Campaña 05 -->
        <div class="folder-arch-card">
          <h3><span>📻</span> 05_Campaña_Octubre_Johanna_AM530</h3>
          <p class="folder-desc">
            Contiene los <strong>5 Reels</strong> de la entrevista a Johanna Tricarico en Somos Radio AM 530, catálogo de copys y ZIP correspondiente.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\01_Reels_Finales_Subtitulados\\05_Campaña_Octubre_Johanna_AM530</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\01_Reels_Finales_Subtitulados\\\\05_Campaña_Octubre_Johanna_AM530', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Campaña 04 -->
        <div class="folder-arch-card">
          <h3><span>🎙️</span> 04_Campaña_Octubre_Johanna_Radio10</h3>
          <p class="folder-desc">
            Contiene los <strong>3 Reels</strong> de la comunicación de Johanna Tricarico en Radio 10 sobre el nuevo proyecto de Ley Pediátrica.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\01_Reels_Finales_Subtitulados\\04_Campaña_Octubre_Johanna_Radio10</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\01_Reels_Finales_Subtitulados\\\\04_Campaña_Octubre_Johanna_Radio10', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Campaña 03 -->
        <div class="folder-arch-card">
          <h3><span>📻</span> 03_Campaña_Octubre_Johanna_FMEnTransito</h3>
          <p class="folder-desc">
            Contiene los <strong>5 Reels</strong> de la entrevista en piso en FM En Tránsito sobre el vencimiento de la Ley Pediátrica.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\01_Reels_Finales_Subtitulados\\03_Campaña_Octubre_Johanna_FMEnTransito</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\01_Reels_Finales_Subtitulados\\\\03_Campaña_Octubre_Johanna_FMEnTransito', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Campaña 02 -->
        <div class="folder-arch-card">
          <h3><span>🎙️</span> 02_Campaña_Octubre_Graciela_VocesDelInterior</h3>
          <p class="folder-desc">
            Contiene los <strong>5 Reels</strong> de Graciela del Valle Ferreira (Voces del Interior) en formato vertical nativo.
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\01_Reels_Finales_Subtitulados\\02_Campaña_Octubre_Graciela_VocesDelInterior</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\01_Reels_Finales_Subtitulados\\\\02_Campaña_Octubre_Graciela_VocesDelInterior', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>

        <!-- Campaña 01 -->
        <div class="folder-arch-card">
          <h3><span>💜</span> 01_Campaña_Septiembre_Johanna_Antonela</h3>
          <p class="folder-desc">
            Contiene los <strong>12 Reels</strong> de la campaña fundacional histórica de Septiembre (Johanna Tricarico y Antonela).
          </p>
          <div class="folder-path-box">
            <span>C:\\Users\\admin\\Desktop\\Reels_Instagram_Edicion\\01_Reels_Finales_Subtitulados\\01_Campaña_Septiembre_Johanna_Antonela</span>
            <button class="btn-doc-action" style="padding: 4px 8px; font-size: 0.72rem;" onclick="copyToClipboard('C:\\\\Users\\\\admin\\\\Desktop\\\\Reels_Instagram_Edicion\\\\01_Reels_Finales_Subtitulados\\\\01_Campaña_Septiembre_Johanna_Antonela', '✅ Ruta copiada')">Copiar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
"""

    if 'id="tab-copies"' not in html:
        target_str = '<!-- Modal de Descargas Masivas'
        if target_str in html:
            html = html.replace(target_str, f'{tabs_markup}\n\n  {target_str}', 1)
        else:
            html = html.replace('</main>\n</div>', f'</main>\n</div>\n{tabs_markup}', 1)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Hub index.html actualizado con 36 reels y 4 pestañas: {index_path}")

    # Sync index.html and catalog.json to Google Drive
    if os.path.exists(gdrive_dir):
        shutil.copy2(index_path, os.path.join(gdrive_dir, "index.html"))
        catalog_path = os.path.join(final_dir, "catalog.json")
        if os.path.exists(catalog_path):
            shutil.copy2(catalog_path, os.path.join(gdrive_dir, "catalog.json"))
        print(f"[OK] index.html y catalog.json sincronizados con Google Drive: {gdrive_dir}")

if __name__ == "__main__":
    main()
