import os
import yaml
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class BrandInfo(BaseModel):
    id: str = "soygarrahan"
    name: str = "Soy Garrahan"
    handle: str = "@soygarrahan.ok"
    platform: str = "instagram"
    logo_file: str = "assets/logos/soygarrahan_official.png"

class OutroConfig(BaseModel):
    enabled: bool = True
    duration: float = 3.2
    slogan_main: str = "EL GARRAHAN SALVA VIDAS"
    slogan_sub: str = "Familias en defensa de la salud pública"
    cta_text: str = "SEGUINOS Y COMPARTÍ ESTE TESTIMONIO"

class StylingConfig(BaseModel):
    primary_color: str = "#00E5FF"
    accent_color: str = "#FE2C55"
    active_subtitle_color: str = "amarillo"
    subtitles_safe_zone_y: int = 1200
    enable_zooms: bool = True
    enable_branding_badge: bool = True

class ThemeConfig(BaseModel):
    title: str
    hook_text: str
    start: float
    end: float
    crop_mode: Optional[str] = "johanna"
    video_source: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)

class BrandConfig(BaseModel):
    brand: BrandInfo = Field(default_factory=BrandInfo)
    outro: OutroConfig = Field(default_factory=OutroConfig)
    styling: StylingConfig = Field(default_factory=StylingConfig)
    themes: Dict[str, ThemeConfig] = Field(default_factory=dict)

def get_base_search_paths() -> List[str]:
    """Retorna posibles directorios raíz para buscar assets y configs."""
    paths = [
        os.getcwd(),
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ]
    return list(dict.fromkeys(paths))

def find_file(rel_path: str) -> str:
    """Busca un archivo relativo en las rutas base estándar."""
    if os.path.isabs(rel_path) and os.path.exists(rel_path):
        return rel_path
    for base in get_base_search_paths():
        candidate = os.path.join(base, rel_path)
        if os.path.exists(candidate):
            return candidate
    return rel_path

def load_brand_config(brand_name_or_file: str = "soygarrahan") -> BrandConfig:
    """
    Carga la configuración de marca desde un archivo YAML.
    Busca en config/brands/{name}.yaml o ruta directa.
    """
    if not brand_name_or_file.endswith(".yaml") and not brand_name_or_file.endswith(".yml"):
        filename = f"{brand_name_or_file}.yaml"
        candidate_rel = os.path.join("config", "brands", filename)
    else:
        candidate_rel = brand_name_or_file

    full_path = find_file(candidate_rel)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return BrandConfig(**data)
    
    # Fallback predeterminado si no se encuentra archivo
    print(f"  [Config] Archivo {full_path} no encontrado, usando configuración predeterminada.")
    return BrandConfig()

def save_brand_config(config: BrandConfig, target_path: Optional[str] = None):
    """Guarda un perfil de marca en formato YAML."""
    if not target_path:
        target_path = os.path.join("config", "brands", f"{config.brand.id}.yaml")
    
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(), f, allow_unicode=True, default_flow_style=False)
