"""
FRAME CONTACT SHEET GENERATOR • REELS STUDIO
Genera una hoja de contacto visual interactiva en HTML con capturas clave
de cada Reel para auditar encuadre, subtítulos y branding al instante.
"""
import os
import sys
import json

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    final_dir = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\01_Reels_Finales_Subtitulados"
    catalog_path = os.path.join(final_dir, "catalog.json")

    if not os.path.exists(catalog_path):
        print(f"[!] catalog.json no encontrado en: {catalog_path}")
        return

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    cards_html = []
    for r in catalog.get("all_reels", []):
        fn = r.get("filename", "")
        title = r.get("title", "")
        hook = r.get("hook", "")
        show = r.get("show_name", "")
        speaker = r.get("speaker", "")
        dur = r.get("specs", {}).get("duration_sec", 0)
        lufs = r.get("specs", {}).get("lufs", 0)
        thumbs = r.get("thumbnails", {})

        thumb_boxes = []
        for tag in ["1_intro", "2_subs", "3_body", "4_outro"]:
            t_info = thumbs.get(tag, {})
            path = t_info.get("path", "")
            label = t_info.get("label", tag)
            thumb_boxes.append(f'''
            <div class="thumb-box">
              <img src="{path}" alt="{label}" loading="lazy">
              <label>{label}</label>
            </div>
            ''')

        cards_html.append(f"""
        <div class="reel-card">
          <div class="reel-header">
            <div>
              <h3>{title}</h3>
              <div class="reel-meta">{show} • <strong>{speaker}</strong> • Archivo: <code>{fn}</code></div>
              {f'<div class="hook-badge">🔥 {hook}</div>' if hook else ''}
            </div>
            <div class="stats-badges">
              <span class="dur-badge">⏱️ {dur:.1f}s</span>
              <span class="lufs-badge">🔊 {lufs:.1f} LUFS</span>
            </div>
          </div>
          <div class="thumbs-grid">
            {''.join(thumb_boxes)}
          </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>QA Visual Contact Sheet • Soy Garrahan (36 Reels)</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #070b14; color: #f8fafc; padding: 24px; margin: 0; }}
    h1 {{ text-align: center; color: #00e5ff; margin-bottom: 8px; font-size: 1.8rem; font-weight: 800; }}
    .subtitle {{ text-align: center; color: #94a3b8; margin-bottom: 30px; font-size: 0.95rem; }}
    .reel-card {{ background: #0f172a; border-radius: 12px; padding: 18px; margin-bottom: 24px; border: 1px solid #1e293b; max-width: 1400px; margin-left: auto; margin-right: auto; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
    .reel-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; gap: 16px; }}
    .reel-header h3 {{ margin: 0 0 4px; font-size: 1.1rem; color: #fff; }}
    .reel-meta {{ font-size: 0.82rem; color: #94a3b8; }}
    .reel-meta code {{ background: #1e293b; padding: 2px 6px; border-radius: 4px; color: #38bdf8; }}
    .hook-badge {{ display: inline-block; background: rgba(255, 171, 0, 0.15); border: 1px solid rgba(255, 171, 0, 0.4); color: #ffab00; padding: 4px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; margin-top: 6px; }}
    .stats-badges {{ display: flex; gap: 8px; flex-shrink: 0; }}
    .dur-badge {{ background: #7c3aed; color: #fff; padding: 6px 12px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; }}
    .lufs-badge {{ background: #059669; color: #fff; padding: 6px 12px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; }}
    .thumbs-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
    .thumb-box {{ text-align: center; background: #080d1a; border-radius: 8px; overflow: hidden; padding-bottom: 8px; border: 1px solid #1e293b; }}
    .thumb-box img {{ width: 100%; aspect-ratio: 9/16; object-fit: cover; display: block; }}
    .thumb-box label {{ font-size: 0.78rem; color: #94a3b8; font-weight: 600; display: block; margin-top: 6px; }}
  </style>
</head>
<body>
  <h1>📋 Hoja de Contacto Visual • Auditoría Técnica (36 Reels)</h1>
  <p class="subtitle">Inspección instantánea de encuadre 9:16, subtítulos dinámicos Hormozi 58pt, Live Pill y tarjeta de cierre.</p>
  {"".join(cards_html)}
</body>
</html>
"""
    sheet_path = os.path.join(final_dir, "qa_contact_sheet.html")
    with open(sheet_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Hoja de contacto visual generada en: {sheet_path}")

if __name__ == "__main__":
    main()
