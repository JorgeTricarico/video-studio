import os
import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar que src esté en el sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from generador_reels.pipeline import ReelPipeline
from generador_reels.agents import CuratorAgent

def parse_time_to_sec(time_str: str) -> float:
    """Convierte cadenas como '00:01:20' o '80' a segundos flotantes."""
    if not time_str:
        return None
    parts = time_str.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    else:
        return float(time_str)

def main():
    parser = argparse.ArgumentParser(description="Generador Multi-Agente de Reels Virales con IA")
    
    parser.add_argument(
        "--video",
        default=os.path.join("..", "..", "02_Entrevistas_Completas", "Reel_Instagram_Simple.mp4"),
        help="Ruta al video de la entrevista original"
    )
    parser.add_argument(
        "--tema",
        default="cristian",
        help="Tema del Reel (ej. 'cristian', 'fiebre', 'marcha', 'politica') o palabra clave"
    )
    parser.add_argument(
        "--dur",
        type=float,
        default=30.0,
        help="Duración objetivo del Reel en segundos (default: 30s)"
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Inicio manual del corte (ej. 00:01:01 o 61.0)"
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Fin manual del corte (ej. 00:01:36 o 96.0)"
    )
    parser.add_argument(
        "--hook",
        default=None,
        help="Texto del gancho visual superior en los primeros 3 segundos"
    )
    parser.add_argument(
        "--color",
        default="amarillo",
        choices=["amarillo", "verde", "cian", "blanco"],
        help="Color de la palabra activa en los subtítulos karaoke"
    )
    parser.add_argument(
        "--no-zooms",
        action="store_true",
        help="Desactivar los punch-in zooms dinámicos"
    )
    parser.add_argument(
        "--no-branding",
        action="store_true",
        help="Desactivar el badge de @soygarrahan.ok"
    )
    parser.add_argument(
        "--whisper-model",
        default="small",
        help="Modelo de Whisper a usar (tiny, base, small, medium, large)"
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Ruta del archivo de salida MP4"
    )

    args = parser.parse_args()

    # Si no se especifica archivo de salida, nombrar según el tema
    if not args.out:
        out_dir = os.path.join("..", "..", "01_Reels_Finales_Subtitulados")
        os.makedirs(out_dir, exist_ok=True)
        args.out = os.path.join(out_dir, f"Reel_Viral_{args.tema.capitalize()}.mp4")

    # Iniciar pipeline de agentes
    pipeline = ReelPipeline(
        target_duration=args.dur,
        crop_mode="johanna",
        active_color=args.color,
        enable_zooms=not args.no_zooms,
        enable_branding=not args.no_branding,
        whisper_model=args.whisper_model
    )

    start_sec = parse_time_to_sec(args.start)
    end_sec = parse_time_to_sec(args.end)

    pipeline.run(
        video_input=args.video,
        output_video=args.out,
        theme_or_query=args.tema,
        hook_override=args.hook,
        start_sec=start_sec,
        end_sec=end_sec,
        cache_json="transcript_cache.json"
    )

if __name__ == "__main__":
    main()
