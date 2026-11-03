"""
=============================================================================
REELS STUDIO CLI • HOSPITAL GARRAHAN
Orquestador Unificado de Producción de Video Reels (9:16)
=============================================================================
Comandos disponibles:
  python studio.py list
  python studio.py render --show <fm_en_transito|radio_10> [--reel <num> | --all]
  python studio.py audit
  python studio.py package
  python studio.py sync
=============================================================================
"""

import os
import sys
import json
import argparse
import subprocess
import shutil
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
SHOWS_CONFIG = os.path.join(CONFIG_DIR, "shows.json")
BASE_PROJECT_DIR = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion"
FINAL_DIR = os.path.join(BASE_PROJECT_DIR, "01_Reels_Finales_Subtitulados")
TAILSCALE_EXE = r"C:\Program Files\Tailscale\tailscale.exe"

from reels_production_harness import (
    SubtitleEngine,
    TextQualityAssurance,
    AudioBoundaryAuditor,
    VideoEvaluator,
    PostRenderAuditor,
    FFMPEG,
    FFPROBE,
    BADGE_PNG,
    OUTRO_PNG
)

def load_shows() -> dict:
    with open(SHOWS_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def cmd_list(args):
    shows = load_shows()
    print("\n" + "="*75)
    print("SHOWS Y REELS CONFIGURADOS EN REELS STUDIO")
    print("="*75)
    for show_key, show in shows.items():
        print(f"\n[PROGRAMA] {show['name']} (ID: {show_key})")
        print(f"  Fuente: {show['source_video']}")
        print(f"  Carpeta: {show['output_dir']}")
        print("  Reels:")
        for idx, r in enumerate(show["reels"], 1):
            if "slices" in r:
                dur = sum(s["end"] - s["start"] for s in r["slices"])
                times_str = " + ".join(f"{s['start']:.1f}-{s['end']:.1f}s" for s in r["slices"])
            else:
                dur = r["end"] - r["start"]
                times_str = f"{r['start']:.1f}s -> {r['end']:.1f}s"
            print(f"    [{idx}] {r['title']}")
            print(f"        Hook: {r['hook']} | Rango: {times_str} ({dur:.1f}s)")
            print(f"        Archivo: {r['filename']}")
    print("\n" + "="*75)

def cmd_audit(args):
    print("\n" + "="*75)
    print("AUDITORIA INTEGRAL DE CALIDAD (QA TECNICO + LINGUISTICO)")
    print("="*75)
    
    mp4_files = [f for f in os.listdir(FINAL_DIR) if f.endswith(".mp4") and ("Johanna" in f or "0" in f)]
    if not mp4_files:
        print(f"No se encontraron videos en {FINAL_DIR}")
        return

    print(f"Auditando {len(mp4_files)} videos en: {FINAL_DIR}\n")
    all_ok = True

    for f in sorted(mp4_files):
        p = os.path.join(FINAL_DIR, f)
        qa = PostRenderAuditor.audit_reel(p)
        status_tag = "[PASS]" if qa["status"] == "APROBADO" else "[FAIL]"
        if qa["status"] != "APROBADO":
            all_ok = False
        print(f"{status_tag} {f}")
        print(f"       Res: {qa['width']}x{qa['height']} | SAR: {qa['sar']} | FPS: {qa['fps']} | Audio: {qa['lufs']} LUFS -> {qa['status']}")

    print("\n" + "-"*75)
    if all_ok:
        print("[RESULTADO] Todos los videos cumplen al 100% con los estandares de broadcast e Instagram.")
    else:
        print("[RESULTADO] Se detectaron observaciones en algunos archivos.")
    print("="*75 + "\n")

def cmd_package(args):
    print("\n" + "="*75)
    print("EMPAQUETANDO ARCHIVOS ZIP DE PRODUCCION")
    print("="*75)
    import zipfile
    shows = load_shows()
    
    for show_key, show in shows.items():
        show_dir = os.path.join(BASE_PROJECT_DIR, show["output_dir"])
        zip_path = os.path.join(show_dir, show["zip_name"])
        dest_zip = os.path.join(FINAL_DIR, show["zip_name"])
        
        print(f"\nEmpaquetando: {show['name']} -> {show['zip_name']}")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in show["reels"]:
                mp4_path = os.path.join(show_dir, r["filename"])
                if os.path.exists(mp4_path):
                    zf.write(mp4_path, arcname=r["filename"])
                    print(f"  + {r['filename']}")
            
            # Buscar catalogos o index.html
            for extra in os.listdir(show_dir):
                if extra.startswith("CATALOGO") or extra == "index.html":
                    zf.write(os.path.join(show_dir, extra), arcname=extra)
                    print(f"  + {extra}")
                    
        shutil.copy2(zip_path, dest_zip)
        print(f"  -> Copiado a unificada: {dest_zip}")
        
    print("\n[OK] Paquetes ZIP listos y actualizados.")
    print("="*75 + "\n")

def cmd_sync(args):
    print("\n" + "="*75)
    print("SINCRONIZANDO CON DISPOSITIVO MOVIL (Tailscale P2P)")
    print("="*75)
    if not os.path.exists(TAILSCALE_EXE):
        print(f"Tailscale no encontrado en: {TAILSCALE_EXE}")
        return

    shows = load_shows()
    target_files = []
    
    # Agregar los ZIPs
    for show in shows.values():
        zp = os.path.join(FINAL_DIR, show["zip_name"])
        if os.path.exists(zp):
            target_files.append(zp)
            
    # Agregar los MP4s individuales
    for show in shows.values():
        for r in show["reels"]:
            mp4 = os.path.join(FINAL_DIR, r["filename"])
            if os.path.exists(mp4):
                target_files.append(mp4)

    target_device = "moto-g24-power:"
    print(f"Dispositivo destino: {target_device}")
    print(f"Archivos a transferir ({len(target_files)}):")
    for tf in target_files:
        print(f"  - {os.path.basename(tf)}")

    cmd = [TAILSCALE_EXE, "file", "cp"] + target_files + [target_device]
    print("\nIniciando transferencia Tailscale...")
    t0 = time.time()
    res = subprocess.run(cmd)
    elapsed = time.time() - t0
    if res.returncode == 0:
        print(f"\n[OK] Transferencia completada con exito en {elapsed:.1f}s!")
    else:
        print(f"\n[ERROR] Fallo la transferencia (codigo {res.returncode})")
    print("="*75 + "\n")

def cmd_render(args):
    shows = load_shows()
    if args.show not in shows:
        print(f"Show '{args.show}' no reconocido. Opciones: {list(shows.keys())}")
        return

    show = shows[args.show]
    if args.show == "fm_en_transito":
        import render_fmentransito_reels as r_fm
        if args.reel:
            sys.argv = ["render_fmentransito_reels.py", str(args.reel)]
        else:
            sys.argv = ["render_fmentransito_reels.py"]
        r_fm.render_all()
    elif args.show == "radio_10":
        import build_and_render_all
        print("[OK] Render de Radio 10 ejecutado.")

def main():
    parser = argparse.ArgumentParser(description="Reels Studio - Hospital Garrahan")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    subparsers.add_parser("list", help="Lista los shows y reels configurados")
    subparsers.add_parser("audit", help="Audita la calidad de los reels renderizados")
    subparsers.add_parser("package", help="Reconstruye los paquetes ZIP")
    subparsers.add_parser("sync", help="Sincroniza con moto-g24-power via Tailscale")

    render_parser = subparsers.add_parser("render", help="Renderiza reels")
    render_parser.add_argument("--show", required=True, choices=["fm_en_transito", "radio_10"], help="Show a renderizar")
    render_parser.add_argument("--reel", type=int, help="Numero de reel especifico (1..N)")
    render_parser.add_argument("--all", action="store_true", help="Renderizar todos los reels del show")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "list":
        cmd_list(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "package":
        cmd_package(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "render":
        cmd_render(args)

if __name__ == "__main__":
    main()
