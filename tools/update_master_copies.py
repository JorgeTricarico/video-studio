import os
import sys

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    copys_dir = os.path.join(project_root, "05_Documentos_Copies_y_Transcripciones", "Copys_Redes")
    final_dir = os.path.join(project_root, "01_Reels_Finales_Subtitulados")
    gdrive_dir = r"G:\.shortcut-targets-by-id\1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2\VIDEOS IA SOYGARRAHAN"

    # Order of campaigns
    campaign_files = [
        ("1. CAMPAÑA SEPTIEMBRE: Johanna Tricarico & Antonela (12 Reels)", "CATALOGO_Y_COPIES_SEPTIEMBRE_JOHANNA_ANTONELA.txt"),
        ("2. CAMPAÑA OCTUBRE: Graciela del Valle Ferreira • Voces del Interior (5 Reels)", "CATALOGO_Y_COPIES_GRACIELA_VOCES_DEL_INTERIOR.txt"),
        ("3. CAMPAÑA OCTUBRE: Johanna Tricarico • FM En Transito (5 Reels)", "CATALOGO_Y_COPIES_FM_EN_TRANSITO.txt"),
        ("4. CAMPAÑA OCTUBRE: Johanna Tricarico • Radio 10 (3 Reels)", "CATALOGO_Y_COPIES_NUEVA_LEY.txt"),
        ("5. CAMPAÑA OCTUBRE: Johanna Tricarico • Somos Radio AM 530 (5 Reels)", "CATALOGO_Y_COPIES_AM530.txt"),
        ("6. CAMPAÑA OCTUBRE: Johanna Tricarico • Comisión de Salud Diputados (6 Reels)", "CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt"),
    ]

    header = """================================================================================
CATALOGO MAESTRO CONSOLIDADO DE COPIES • COLECTIVO SOY GARRAHAN
36 REELS OFICIALES PARA INSTAGRAM, TIKTOK Y WHATSAPP
Coleccion Completa Septiembre - Octubre 2026
================================================================================

INDICE GENERAL DE CAMPAÑAS:
--------------------------------------------------------------------------------
1. CAMPAÑA SEPTIEMBRE: Johanna Tricarico & Antonela (12 Reels)
2. CAMPAÑA OCTUBRE: Graciela del Valle Ferreira • Voces del Interior (5 Reels)
3. CAMPAÑA OCTUBRE: Johanna Tricarico • FM En Transito (5 Reels)
4. CAMPAÑA OCTUBRE: Johanna Tricarico • Radio 10 (3 Reels)
5. CAMPAÑA OCTUBRE: Johanna Tricarico • Somos Radio AM 530 (5 Reels)
6. CAMPAÑA OCTUBRE: Johanna Tricarico • Comisión de Salud Diputados (6 Reels)
--------------------------------------------------------------------------------
Duracion Total Acumulada: 30.8 Minutos • Audio: -14 LUFS • Formato: 1080x1920 (9:16)
================================================================================

Hashtags oficiales sugeridos para todas las publicaciones:
#SoyGarrahan #GarrahanSalvaVidas #SaludPublica #ElGarrahanNoSeToca #Garrahan
Instagram oficial: @soygarrahan.ok
================================================================================
"""

    consolidated_sections = [header]

    for title, fname in campaign_files:
        fpath = os.path.join(copys_dir, fname)
        if not os.path.exists(fpath):
            print(f"[!] Warning: {fpath} not found")
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
        
        banner = f"\n\n{'='*80}\n{title.upper()}\n{'='*80}\n\n"
        consolidated_sections.append(banner + content)

    full_master_text = "\n".join(consolidated_sections) + "\n"

    target_paths = [
        os.path.join(final_dir, "CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt"),
        os.path.join(copys_dir, "CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt"),
    ]
    if os.path.exists(gdrive_dir):
        target_paths.append(os.path.join(gdrive_dir, "CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt"))

    for tp in target_paths:
        with open(tp, "w", encoding="utf-8") as f:
            f.write(full_master_text)
        print(f"[OK] Actualizado catálogo maestro: {tp} ({len(full_master_text)} bytes)")

if __name__ == "__main__":
    main()
