# filepath: core/env_config.py
import os
import glob
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

# Directorio raíz del repositorio Generador_Reels
REPO_ROOT = Path(__file__).resolve().parent.parent
# Directorio padre del workspace general (si existe estructura superior)
WORKSPACE_ROOT = REPO_ROOT.parent.parent if (REPO_ROOT.parent.parent / "02_Entrevistas_Completas").exists() else REPO_ROOT


def resolve_binary(bin_name: str) -> str:
    """Resuelve dinámicamente la ruta de ffmpeg o ffprobe en WinGet, PATH o variables de entorno."""
    env_key = f"{bin_name.upper()}_PATH"
    if os.environ.get(env_key) and os.path.exists(os.environ[env_key]):
        return os.environ[env_key]

    # Búsqueda automática en paquetes de WinGet (independiente de la versión)
    winget_pattern = os.path.expandvars(
        rf"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\{bin_name}.exe"
    )
    matches = sorted(glob.glob(winget_pattern), reverse=True)
    if matches:
        return matches[0]

    which_path = shutil.which(bin_name)
    if which_path and "stub" not in which_path.lower():
        return which_path

    return which_path or bin_name


def resolve_asset(relative_path: str) -> str:
    """Busca un asset en el repositorio local, workspace padre o Downloads."""
    if not relative_path:
        return ""
    p = Path(relative_path)
    if p.is_absolute() and p.exists():
        return str(p)

    candidates = [
        REPO_ROOT / relative_path,
        WORKSPACE_ROOT / relative_path,
        REPO_ROOT / p.name,
        WORKSPACE_ROOT / p.name,
        Path.home() / "Downloads" / p.name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())
    return str((REPO_ROOT / relative_path).resolve())


def resolve_font(font_name: str = "arial") -> str:
    """Busca fuentes comunes en Windows Fonts o fuentes del sistema."""
    font_name_lower = font_name.lower().replace(" ", "").replace("_", "")
    font_map = {
        "arial": "arial.ttf",
        "arialbold": "arialbd.ttf",
        "arialblack": "ariblk.ttf",
        "impact": "impact.ttf",
        "montserrat": "Montserrat-Bold.ttf",
        "inter": "Inter-Bold.ttf"
    }
    target_file = font_map.get(font_name_lower, f"{font_name}.ttf")
    windows_font = Path("C:/Windows/Fonts") / target_file
    if windows_font.exists():
        return str(windows_font).replace("\\", "/")
    
    # Fallback genérico a Arial Bold en Windows
    fallback = Path("C:/Windows/Fonts/arialbd.ttf")
    if fallback.exists():
        return str(fallback).replace("\\", "/")
    return "Arial"


def load_brand_config(brand_name_or_file: str = "soygarrahan") -> Dict[str, Any]:
    """
    Carga la configuración de marca desde config/brands/<brand>.yaml o .json.
    Si no existe, devuelve una configuración genérica predeterminada.
    """
    if not brand_name_or_file:
        brand_name_or_file = "generic"

    # Si es ruta directa
    direct_path = Path(brand_name_or_file)
    if direct_path.exists():
        target_path = direct_path
    else:
        # Buscar en config/brands/
        clean_name = brand_name_or_file.replace(".yaml", "").replace(".yml", "").replace(".json", "")
        cand_yaml = REPO_ROOT / "config" / "brands" / f"{clean_name}.yaml"
        cand_yml = REPO_ROOT / "config" / "brands" / f"{clean_name}.yml"
        cand_json = REPO_ROOT / "config" / "brands" / f"{clean_name}.json"
        if cand_yaml.exists():
            target_path = cand_yaml
        elif cand_yml.exists():
            target_path = cand_yml
        elif cand_json.exists():
            target_path = cand_json
        else:
            target_path = None

    if target_path and target_path.exists():
        if target_path.suffix.lower() in [".yaml", ".yml"] and yaml is not None:
            with open(target_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        elif target_path.suffix.lower() == ".json" or yaml is None:
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)

    # Configuración por defecto genérica si no existe archivo
    return {
        "brand": {"id": "generic", "name": "Video Studio Default", "handle": "", "logo_file": None},
        "outro": {"enabled": False, "duration": 0.0},
        "styling": {
            "primary_color": "#FFFFFF",
            "accent_color": "#00E5FF",
            "active_subtitle_color": "amarillo",
            "subtitles_safe_zone_y": 1450,
            "enable_branding_badge": False
        }
    }


FFMPEG_BIN = resolve_binary("ffmpeg")
FFPROBE_BIN = resolve_binary("ffprobe")
BADGE_PNG = resolve_asset("assets/logos/soygarrahan_badge.png")
OUTRO_PNG = resolve_asset("assets/logos/outro_card.png")
DICT_PATH = str((REPO_ROOT / "config" / "dictionary.json").resolve())
SHOWS_PATH = str((REPO_ROOT / "config" / "shows.json").resolve())
TAILSCALE_EXE = shutil.which("tailscale") or r"C:\Program Files\Tailscale\tailscale.exe"
GDRIVE_DIR = r"G:\.shortcut-targets-by-id\1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2\VIDEOS IA SOYGARRAHAN"
