# filepath: video_editor_cli.py
"""
================================================================================
VIDEO STUDIO • UNIVERSAL VIDEO EDITOR & PRODUCTION CLI
================================================================================
Comandos Disponibles:
  - subtitle : Subtitula cualquier video (Hormozi, minimal, boxed) con Whisper JSON/SRT.
  - cut      : Corta fragmentos con auto-alineación acústica de silencios opcional.
  - concat   : Une múltiples clips en secuencia.
  - reframe  : Convierte a 9:16 vertical (o 1:1, etc.) con fondo desenfocado (blur_bg).
  - audio    : Masteriza y normaliza la sonoridad a -14 LUFS (EBU R128).
  - inspect  : Audita calidad técnica y visual (fotogramas clave y hoja de contacto).
  - patch    : Genera placas gráficas de impacto (Motion Title Cards).
  - reel     : Ejecuta el pipeline integral de Reels por show/campaña.
================================================================================
"""
import os
import sys
import json
import argparse
from typing import List

from core import (
    VideoEditor,
    VideoCompositor,
    SubtitleEngine,
    AudioBoundaryAuditor,
    PostRenderAuditor,
    VisualInspector,
    VisualPatcher
)
from reels_production_harness import QualityGatingHarness, compact_whisper_transcript


def cmd_subtitle(args):
    print(f"[*] Subtitulando video: {args.video} con {args.transcript}...")
    out_path = args.out or f"{os.path.splitext(args.video)[0]}_subtitulado.mp4"
    res = VideoEditor.subtitle(
        video_path=args.video,
        transcript=args.transcript,
        out_path=out_path,
        style=args.style,
        font_name=args.font,
        font_size=args.font_size,
        active_color=args.color,
        y_pos=args.y,
        use_gpu=not args.no_gpu
    )
    print(json.dumps({"status": "OK", "output_video": res}, indent=2))


def cmd_cut(args):
    print(f"[*] Cortando video: {args.video} [{args.start}s - {args.end}s]...")
    out_path = args.out or f"{os.path.splitext(args.video)[0]}_cut_{int(args.start)}_{int(args.end)}.mp4"
    res = VideoEditor.cut(
        video_path=args.video,
        start_sec=args.start,
        end_sec=args.end,
        out_path=out_path,
        auto_align_silence=args.auto_align,
        copy_codecs=args.copy,
        use_gpu=not args.no_gpu
    )
    print(json.dumps({"status": "OK", "output_video": res}, indent=2))


def cmd_concat(args):
    print(f"[*] Concatenando {len(args.inputs)} videos...")
    out_path = args.out or "concat_output.mp4"
    res = VideoEditor.concat(
        video_paths=args.inputs,
        out_path=out_path,
        use_gpu=not args.no_gpu
    )
    print(json.dumps({"status": "OK", "output_video": res}, indent=2))


def cmd_reframe(args):
    print(f"[*] Re-encuadrando video a {args.aspect} (modo: {args.mode})...")
    out_path = args.out or f"{os.path.splitext(args.video)[0]}_{args.aspect.replace(':', 'x')}.mp4"
    res = VideoEditor.reframe(
        video_path=args.video,
        out_path=out_path,
        target_aspect=args.aspect,
        mode=args.mode,
        use_gpu=not args.no_gpu
    )
    print(json.dumps({"status": "OK", "output_video": res}, indent=2))


def cmd_audio(args):
    print(f"[*] Normalizando sonoridad a {args.lufs} LUFS...")
    out_path = args.out or f"{os.path.splitext(args.video)[0]}_mastered.mp4"
    res = VideoEditor.master_audio(
        video_path=args.video,
        out_path=out_path,
        target_lufs=args.lufs
    )
    print(json.dumps({"status": "OK", "output_video": res}, indent=2))


def cmd_inspect(args):
    print(f"[*] Inspeccionando técnicamente: {args.video}...")
    tech_rep = VideoEditor.inspect(args.video)
    vis_rep = None
    if args.visual:
        vis_rep = VideoEditor.inspect_visual(args.video, out_dir=args.out_dir)
    print(json.dumps({"technical": tech_rep, "visual": vis_rep}, indent=2, ensure_ascii=False))


def cmd_patch(args):
    print(f"[*] Generando placa gráfica de impacto: '{args.text}'...")
    out_path = args.out or "scratch/headline_card.png"
    res = VideoEditor.create_title_card(
        headline_text=args.text,
        category_tag=args.tag,
        out_path=out_path
    )
    print(json.dumps({"status": "OK", "output_image": res}, indent=2))


def cmd_reel(args):
    if args.mode == "preflight":
        rep = QualityGatingHarness.run_preflight(args.show, args.reel)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0 if rep["all_passed"] else 1)
    elif args.mode == "preview":
        rep = QualityGatingHarness.run_preview(args.show, args.reel)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0)
    elif args.mode == "full":
        use_gpu = not args.no_gpu
        rep = QualityGatingHarness.run_full(
            args.show,
            args.reel,
            use_gpu=use_gpu,
            dual_versions=not args.single,
            force=args.force
        )
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0 if rep.get("status") == "COMPLETED" else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Video Studio • Editor de Video Universal & Motor de Producción de Reels"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # --- SUBTITLE ---
    p_sub = subparsers.add_parser("subtitle", help="Subtitula un video con estilo viral Hormozi o minimal")
    p_sub.add_argument("--video", "-v", required=True, help="Ruta al video de entrada")
    p_sub.add_argument("--transcript", "-t", required=True, help="Ruta a Whisper JSON o SRT")
    p_sub.add_argument("--out", "-o", default=None, help="Ruta al archivo MP4 de salida")
    p_sub.add_argument("--style", default="hormozi", choices=["hormozi", "hormozi_cyan", "hormozi_green", "minimal", "boxed"], help="Estilo visual")
    p_sub.add_argument("--font", default="Arial Black", help="Fuente tipográfica")
    p_sub.add_argument("--font-size", type=int, default=58, help="Tamaño de fuente")
    p_sub.add_argument("--color", default="&H0000FFFF&", help="Color activo (amarillo, cyan, hex #RRGGBB o &H00BBGGRR&)")
    p_sub.add_argument("--y", type=int, default=1450, help="Posición vertical Y")
    p_sub.add_argument("--no-gpu", action="store_true", help="Desactivar aceleración GPU NVENC")

    # --- CUT ---
    p_cut = subparsers.add_parser("cut", help="Corta un rango de video")
    p_cut.add_argument("--video", "-v", required=True, help="Ruta al video de entrada")
    p_cut.add_argument("--start", "-s", type=float, required=True, help="Tiempo de inicio en segundos")
    p_cut.add_argument("--end", "-e", type=float, required=True, help="Tiempo de fin en segundos")
    p_cut.add_argument("--out", "-o", default=None, help="Ruta de salida")
    p_cut.add_argument("--auto-align", action="store_true", help="Auto-calibrar corte buscando valles de silencio")
    p_cut.add_argument("--copy", action="store_true", help="Copia rápida sin re-codificación (-c copy)")
    p_cut.add_argument("--no-gpu", action="store_true", help="Desactivar aceleración GPU NVENC")

    # --- CONCAT ---
    p_cat = subparsers.add_parser("concat", help="Concatena varios videos")
    p_cat.add_argument("--inputs", "-i", nargs="+", required=True, help="Lista de videos de entrada")
    p_cat.add_argument("--out", "-o", required=True, help="Ruta del video final")
    p_cat.add_argument("--no-gpu", action="store_true", help="Desactivar aceleración GPU NVENC")

    # --- REFRAME ---
    p_ref = subparsers.add_parser("reframe", help="Convierte relación de aspecto (16:9 -> 9:16 vertical, etc.)")
    p_ref.add_argument("--video", "-v", required=True, help="Ruta al video")
    p_ref.add_argument("--aspect", default="9:16", choices=["9:16", "1:1", "16:9", "4:5"], help="Relación de aspecto destino")
    p_ref.add_argument("--mode", default="blur_bg", choices=["blur_bg", "crop", "fit"], help="Modo de composición")
    p_ref.add_argument("--out", "-o", default=None, help="Ruta de salida")
    p_ref.add_argument("--no-gpu", action="store_true", help="Desactivar aceleración GPU NVENC")

    # --- AUDIO ---
    p_aud = subparsers.add_parser("audio", help="Normaliza la sonoridad a estándar -14 LUFS")
    p_aud.add_argument("--video", "-v", required=True, help="Ruta al video")
    p_aud.add_argument("--lufs", type=float, default=-14.0, help="Nivel LUFS objetivo")
    p_aud.add_argument("--out", "-o", default=None, help="Ruta de salida")

    # --- INSPECT ---
    p_ins = subparsers.add_parser("inspect", help="Audita técnicamente y visualmente un video")
    p_ins.add_argument("--video", "-v", required=True, help="Ruta al video")
    p_ins.add_argument("--visual", action="store_true", help="Generar hoja de contacto visual y métricas de imagen")
    p_ins.add_argument("--out-dir", default=None, help="Directorio para fotogramas de inspección")

    # --- PATCH ---
    p_pat = subparsers.add_parser("patch", help="Genera una placa gráfica de impacto (Motion Title Card)")
    p_pat.add_argument("--text", "-t", required=True, help="Texto titular")
    p_pat.add_argument("--tag", default="ALERTA INFORMATIVA", help="Píldora superior de categoría")
    p_pat.add_argument("--out", "-o", default="scratch/headline_card.png", help="Ruta PNG de salida")

    # --- REEL ---
    p_rel = subparsers.add_parser("reel", help="Ejecuta el pipeline de Reels por show")
    p_rel.add_argument("--show", required=True, help="ID del show en config/shows.json")
    p_rel.add_argument("--mode", default="preflight", choices=["preflight", "preview", "full"], help="Modo del harness")
    p_rel.add_argument("--reel", default=None, help="ID de reel individual (opcional)")
    p_rel.add_argument("--no-gpu", action="store_true", help="Desactivar aceleración GPU NVENC")
    p_rel.add_argument("--single", action="store_true", help="Generar solo versión subtitulada")
    p_rel.add_argument("--force", action="store_true", help="Forzar re-renderizado")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "subtitle": cmd_subtitle,
        "cut": cmd_cut,
        "concat": cmd_concat,
        "reframe": cmd_reframe,
        "audio": cmd_audio,
        "inspect": cmd_inspect,
        "patch": cmd_patch,
        "reel": cmd_reel
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
