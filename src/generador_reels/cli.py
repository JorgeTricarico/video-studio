import os
import sys
import argparse
import subprocess
from .config import load_brand_config
from .pipeline import ReelPipeline

def run_pipeline_cli(args):
    """Ejecuta el pipeline de generación desde CLI."""
    brand_cfg = load_brand_config(args.brand)
    
    # Resolver archivo de salida
    out_file = args.out
    if not out_file:
        out_dir = os.path.join("..", "..", "01_Reels_Finales_Subtitulados")
        if not os.path.exists(out_dir):
            out_dir = os.path.join("data", "outputs")
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"Reel_Viral_{args.tema.capitalize()}.mp4")

    # Determinar video y modo de encuadre según tema
    crop_mode = "johanna"
    video_input = args.video
    start_sec = args.start
    end_sec = args.end

    if args.tema in brand_cfg.themes:
        theme_meta = brand_cfg.themes[args.tema]
        if hasattr(theme_meta, "crop_mode") and theme_meta.crop_mode:
            crop_mode = theme_meta.crop_mode
        if hasattr(theme_meta, "video_source") and theme_meta.video_source:
            # Si el usuario no pasó un video explícito por CLI
            candidate_v = os.path.join("..", "..", "02_Entrevistas_Completas", theme_meta.video_source)
            if os.path.exists(candidate_v):
                video_input = candidate_v
        if start_sec is None and hasattr(theme_meta, "start"):
            start_sec = theme_meta.start
        if end_sec is None and hasattr(theme_meta, "end"):
            end_sec = theme_meta.end

    # Iniciar pipeline
    pipeline = ReelPipeline(
        target_duration=args.dur,
        crop_mode=crop_mode,
        active_color=args.color or brand_cfg.styling.active_subtitle_color,
        enable_zooms=not args.no_zooms if args.no_zooms else brand_cfg.styling.enable_zooms,
        enable_branding=not args.no_branding if args.no_branding else brand_cfg.styling.enable_branding_badge,
        whisper_model=args.whisper_model,
        brand_config=brand_cfg
    )

    pipeline.run(
        video_input=video_input,
        output_video=out_file,
        theme_or_query=args.tema,
        hook_override=args.hook,
        start_sec=start_sec,
        end_sec=end_sec,
        cache_json="transcript_cache.json"
    )

def launch_studio(port=8501):
    """Lanza el Centro de Mando visual en Streamlit."""
    print(f"\n[*] INICIANDO CENTRO DE MANDO (STUDIO)...")
    dashboard_app = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        dashboard_app,
        "--server.port", str(port),
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false"
    ]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[!] Centro de Mando cerrado por el usuario.")

def main():
    parser = argparse.ArgumentParser(
        prog="reels",
        description="Generador Multi-Agente de Reels Virales con IA y Centro de Mando"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Comando 'run'
    parser_run = subparsers.add_parser("run", help="Generar un Reel viral")
    parser_run.add_argument("--tema", default="cristian", help="Tema del Reel o palabra clave")
    parser_run.add_argument("--video", default=os.path.join("..", "..", "02_Entrevistas_Completas", "Reel_Instagram_Simple.mp4"), help="Ruta al video de entrada")
    parser_run.add_argument("--out", default=None, help="Ruta al video de salida MP4")
    parser_run.add_argument("--dur", type=float, default=30.0, help="Duración guía en segundos")
    parser_run.add_argument("--start", type=float, default=None, help="Segundo de inicio forzado")
    parser_run.add_argument("--end", type=float, default=None, help="Segundo de fin forzado")
    parser_run.add_argument("--hook", default=None, help="Texto del gancho visual superior")
    parser_run.add_argument("--brand", default="soygarrahan", help="Perfil de marca (archivo YAML)")
    parser_run.add_argument("--color", default="amarillo", choices=["amarillo", "verde", "cian", "blanco"], help="Color activo subtítulos")
    parser_run.add_argument("--no-zooms", action="store_true", help="Desactivar zooms")
    parser_run.add_argument("--no-branding", action="store_true", help="Desactivar badge de marca")
    parser_run.add_argument("--whisper-model", default="small", help="Modelo Whisper (tiny, base, small, medium, large)")

    # Comando 'studio'
    parser_studio = subparsers.add_parser("studio", help="Lanzar el Centro de Mando visual (Dashboard)")
    parser_studio.add_argument("--port", type=int, default=8501, help="Puerto local para la web")

    # Comando 'list-themes'
    parser_themes = subparsers.add_parser("list-themes", help="Listar temas disponibles en el perfil de marca")
    parser_themes.add_argument("--brand", default="soygarrahan", help="Perfil de marca")

    args = parser.parse_args()

    if args.command == "studio":
        launch_studio(args.port)
    elif args.command == "list-themes":
        cfg = load_brand_config(args.brand)
        print(f"\n--- Temas configurados para '{cfg.brand.name}' ({args.brand}) ---")
        for k, v in cfg.themes.items():
            print(f"  • {k:12} -> [{v.start:5.1f}s - {v.end:5.1f}s] Hook: '{v.hook_text}'")
        print()
    elif args.command == "run":
        run_pipeline_cli(args)
    else:
        # Si no se pasa comando pero se llama directo, mostrar ayuda o correr por defecto
        if len(sys.argv) == 1:
            parser.print_help()
        else:
            # Compatibilidad si pasan argumentos sin subcomando
            parser_run.print_help()

if __name__ == "__main__":
    main()
