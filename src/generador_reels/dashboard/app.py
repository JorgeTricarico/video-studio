import os
import sys
import glob
import subprocess
import streamlit as st
from PIL import Image

# Asegurar rutas de importación
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from generador_reels.config import load_brand_config, save_brand_config
from generador_reels.pipeline import ReelPipeline
from generador_reels.agents.brand_manager import create_top_watermark_badge, create_outro_card

st.set_page_config(
    page_title="Reels Studio AI | Centro de Mando",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para look cinematográfico moderno
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00E5FF, #FE2C55, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #A0AEC0;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 700;
    }
    .brand-badge-box {
        background-color: #0F141E;
        border: 1px solid #00E5FF;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# ESTADO DE LA SESIÓN Y CONFIGURACIÓN
# -------------------------------------------------------------
if "brand_id" not in st.session_state:
    st.session_state.brand_id = "soygarrahan"

brand_cfg = load_brand_config(st.session_state.brand_id)

# -------------------------------------------------------------
# BARRA LATERAL: CONTROL DE MARCA Y SISTEMA
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Centro de Mando")
    st.markdown(f"**Organización:** `{brand_cfg.brand.name}`")
    st.markdown(f"**Usuario:** `{brand_cfg.brand.handle}`")
    
    st.divider()
    st.markdown("#### ⚙️ Parámetros del Motor")
    whisper_model = st.selectbox("Modelo de Whisper", ["tiny", "base", "small", "medium"], index=2)
    crop_mode = st.selectbox("Modo de Encuadre", ["johanna (centrado 9:16)", "completo"], index=0)
    color_sub = st.selectbox("Color Palabra Activa", ["amarillo", "cian", "verde", "blanco"], index=0)
    enable_zooms = st.checkbox("Punch-in Zooms Dinámicos", value=brand_cfg.styling.enable_zooms)
    enable_branding = st.checkbox("Watermark Superior", value=brand_cfg.styling.enable_branding_badge)
    enable_outro = st.checkbox("Outro Card al Cierre (3.2s)", value=brand_cfg.outro.enabled)
    
    st.divider()
    if st.button("📁 Abrir Carpeta de Salida en Windows"):
        out_dir = os.path.abspath(os.path.join(src_dir, "..", "01_Reels_Finales_Subtitulados"))
        if os.path.exists(out_dir):
            os.system(f'explorer.exe "{out_dir}"')
        else:
            st.warning("Carpeta aún no creada.")

# -------------------------------------------------------------
# PESTAÑAS PRINCIPALES
# -------------------------------------------------------------
st.markdown('<div class="main-title">REELS STUDIO AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Motor de Generación y Edición Automatizada de Video Vertical para Redes Sociales</div>', unsafe_allow_html=True)

tab_creator, tab_brand, tab_gallery = st.tabs([
    "🎛️ Generador de Reels",
    "🎨 Identidad de Marca y Outro",
    "📂 Biblioteca de Reels"
])

# -------------------------------------------------------------
# TAB 1: GENERADOR DE REELS
# -------------------------------------------------------------
with tab_creator:
    col_input, col_config = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("#### 1. Video Fuente")
        
        # Buscar videos disponibles en el proyecto
        possible_video_dirs = [
            os.path.join(src_dir, "..", "02_Entrevistas_Completas"),
            os.path.join(src_dir, "..", "03_Material_Original"),
            "data/inputs"
        ]
        video_files = []
        for vdir in possible_video_dirs:
            if os.path.exists(vdir):
                for ext in ("*.mp4", "*.mkv", "*.mov"):
                    video_files.extend(glob.glob(os.path.join(vdir, ext)))

        if video_files:
            video_selected = st.selectbox(
                "Seleccionar Video Disponible",
                video_files,
                format_func=lambda x: f"{os.path.basename(x)} ({os.path.basename(os.path.dirname(x))})"
            )
        else:
            video_selected = st.text_input("Ruta al archivo MP4", "")

        st.markdown("#### 2. Selección de Historia y Narrativa")
        
        # Lista de temas disponibles en la marca
        themes_list = list(brand_cfg.themes.keys())
        theme_choice = st.selectbox(
            "Elegir Historia Preconfigurada",
            ["personalizado"] + themes_list,
            format_func=lambda x: f"⭐ {brand_cfg.themes[x].title}" if x in brand_cfg.themes else "✏️ Personalizado (Elegir timestamps libres)"
        )

        if theme_choice != "personalizado":
            preset_data = brand_cfg.themes[theme_choice]
            default_hook = preset_data.hook_text
            default_start = preset_data.start
            default_end = preset_data.end
        else:
            default_hook = "TESTIMONIO VIRAL"
            default_start = 60.0
            default_end = 95.0

        hook_text = st.text_input("Gancho Visual Superior (Hook Card primeros 3s)", default_hook)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            t_start = st.number_input("Segundo de Inicio", value=float(default_start), step=1.0)
        with col_t2:
            t_end = st.number_input("Segundo de Fin (Cierre de idea)", value=float(default_end), step=1.0)

        target_duration = st.slider(
            "Duración Guía Objetivo (segundos)",
            min_value=15.0,
            max_value=90.0,
            value=35.0,
            step=5.0,
            help="El cirujano de ritmo condensará el discurso y completará la idea sin cortes abruptos."
        )

    with col_config:
        st.markdown("#### 3. Vista Previa de Identidad Gráfica")
        
        # Previsualización del badge y del outro
        top_badge_path = os.path.join(src_dir, "soygarrahan_badge.png")
        if not os.path.exists(top_badge_path):
            create_top_watermark_badge(top_badge_path, handle=brand_cfg.brand.handle)
            
        outro_card_path = os.path.join(src_dir, "outro_card.png")
        if not os.path.exists(outro_card_path):
            create_outro_card(
                outro_card_path,
                slogan_main=brand_cfg.outro.slogan_main,
                slogan_sub=brand_cfg.outro.slogan_sub,
                handle=brand_cfg.brand.handle,
                cta_text=brand_cfg.outro.cta_text
            )

        if os.path.exists(top_badge_path):
            st.markdown("**Watermark Superior (durante todo el video):**")
            st.image(top_badge_path, width=420)

        if os.path.exists(outro_card_path):
            st.markdown("**Pantalla de Cierre (últimos 3.2 segundos):**")
            st.image(outro_card_path, width=240)

        st.divider()
        out_name = st.text_input("Nombre del archivo de salida", f"Reel_Viral_{theme_choice.capitalize()}.mp4" if theme_choice != "personalizado" else "Reel_Viral_Custom.mp4")

        # BOTÓN PRINCIPAL DE GENERACIÓN
        btn_render = st.button("🚀 GENERAR REEL VIRAL CON IA", type="primary", use_container_width=True)

    # ACCIÓN DE RENDER
    if btn_render:
        if not video_selected or not os.path.exists(video_selected):
            st.error("Error: Archivo de video no encontrado.")
        else:
            out_folder = os.path.abspath(os.path.join(src_dir, "..", "01_Reels_Finales_Subtitulados"))
            os.makedirs(out_folder, exist_ok=True)
            target_out_path = os.path.join(out_folder, out_name)

            progress_bar = st.progress(0, text="Iniciando pipeline multi-agente...")
            status_placeholder = st.empty()

            try:
                # 1. Configurar pipeline
                status_placeholder.info("[1/6] Configurando agentes y cargando modelos...")
                progress_bar.progress(15, text="Extrayendo audio y transcribiendo con Whisper...")

                pipeline = ReelPipeline(
                    target_duration=target_duration,
                    crop_mode="johanna" if "johanna" in crop_mode else "completo",
                    active_color=color_sub,
                    enable_zooms=enable_zooms,
                    enable_branding=enable_branding,
                    whisper_model=whisper_model,
                    brand_config=brand_cfg
                )

                # 2. Ejecución
                progress_bar.progress(40, text="Curando momento clave y eliminando silencios...")
                status_placeholder.info("[2/6] Agentes de Curaduría y Ritmo operando...")

                final_path = pipeline.run(
                    video_input=video_selected,
                    output_video=target_out_path,
                    theme_or_query=theme_choice if theme_choice != "personalizado" else "custom",
                    hook_override=hook_text,
                    start_sec=t_start if theme_choice == "personalizado" else None,
                    end_sec=t_end if theme_choice == "personalizado" else None
                )

                progress_bar.progress(100, text="¡Reel completado con éxito!")
                status_placeholder.success(f"✅ ¡Reel generado exitosamente en: {final_path}")
                
                # Mostrar reproductor
                st.video(final_path)

            except Exception as e:
                status_placeholder.error(f"Error durante la generación: {e}")
                progress_bar.empty()

# -------------------------------------------------------------
# TAB 2: IDENTIDAD DE MARCA
# -------------------------------------------------------------
with tab_brand:
    st.markdown("### 🎨 Configuración de Marca y Pantalla Final (Outro)")
    st.markdown("Personaliza los datos de la causa u organización para que todos los Reels se generen con su identidad.")

    col_b1, col_b2 = st.columns([1, 1], gap="large")

    with col_b1:
        brand_name_input = st.text_input("Nombre de la Organización", value=brand_cfg.brand.name)
        brand_handle_input = st.text_input("Usuario de Instagram / Redes", value=brand_cfg.brand.handle)
        
        st.markdown("#### Textos del Outro (Pantalla de Cierre)")
        slogan_main_input = st.text_input("Slogan Principal", value=brand_cfg.outro.slogan_main)
        slogan_sub_input = st.text_input("Bajada / Sub-slogan", value=brand_cfg.outro.slogan_sub)
        cta_text_input = st.text_input("Llamado a la Acción (CTA)", value=brand_cfg.outro.cta_text)
        outro_dur_input = st.slider("Duración del Outro (segundos)", 2.0, 5.0, float(brand_cfg.outro.duration), 0.2)

        if st.button("💾 Guardar Configuración de Marca", type="secondary"):
            brand_cfg.brand.name = brand_name_input
            brand_cfg.brand.handle = brand_handle_input
            brand_cfg.outro.slogan_main = slogan_main_input
            brand_cfg.outro.slogan_sub = slogan_sub_input
            brand_cfg.outro.cta_text = cta_text_input
            brand_cfg.outro.duration = outro_dur_input
            
            save_brand_config(brand_cfg)
            
            # Regenerar assets
            create_top_watermark_badge(
                os.path.join(src_dir, "soygarrahan_badge.png"),
                handle=brand_handle_input
            )
            create_outro_card(
                os.path.join(src_dir, "outro_card.png"),
                slogan_main=slogan_main_input,
                slogan_sub=slogan_sub_input,
                handle=brand_handle_input,
                cta_text=cta_text_input
            )
            st.success("¡Configuración guardada y assets gráficos actualizados!")
            st.rerun()

    with col_b2:
        st.markdown("#### Vista Previa en Vivo de Assets Gráficos")
        if os.path.exists(os.path.join(src_dir, "soygarrahan_badge.png")):
            st.markdown("**Watermark Superior:**")
            st.image(os.path.join(src_dir, "soygarrahan_badge.png"), width=420)
            
        if os.path.exists(os.path.join(src_dir, "outro_card.png")):
            st.markdown("**Outro Card de Cierre:**")
            st.image(os.path.join(src_dir, "outro_card.png"), width=280)

# -------------------------------------------------------------
# TAB 3: BIBLIOTECA DE REELS
# -------------------------------------------------------------
with tab_gallery:
    st.markdown("### 📂 Reels Generados Listos para Publicar")
    
    out_folder = os.path.abspath(os.path.join(src_dir, "..", "01_Reels_Finales_Subtitulados"))
    if os.path.exists(out_folder):
        reels_list = glob.glob(os.path.join(out_folder, "*.mp4"))
        if reels_list:
            reels_list.sort(key=os.path.getmtime, reverse=True)
            
            cols = st.columns(2)
            for idx, r_path in enumerate(reels_list):
                col_target = cols[idx % 2]
                with col_target:
                    size_mb = os.path.getsize(r_path) / (1024 * 1024)
                    st.markdown(f"#### 🎬 {os.path.basename(r_path)}")
                    st.caption(f"Peso: {size_mb:.1f} MB | Ubicación: `{os.path.basename(r_path)}`")
                    st.video(r_path)
                    st.divider()
        else:
            st.info("No hay videos generados aún en la carpeta de salida.")
    else:
        st.info("Carpeta de salida no encontrada.")
