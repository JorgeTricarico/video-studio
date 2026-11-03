import os
import sys
import shutil
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
FINAL_DIR = os.path.join(PROJECT_ROOT, "01_Reels_Finales_Subtitulados")
DOCS_DIR = os.path.join(PROJECT_ROOT, "05_Documentos_Copies_y_Transcripciones", "Copys_Redes")

CAMPAIGNS_MAP = {
    "01_Campaña_Septiembre_Johanna_Antonela": {
        "files": [
            "01_Johanna_Caso_Bayron_Cancer_Auditorias.mp4",
            "02_Johanna_Caso_Cristian_15_Anos_Leches.mp4",
            "03_Johanna_No_Los_Mata_La_Enfermedad_Mata_El_Estado.mp4",
            "04_Johanna_Presupuesto_Congelado_Medicamentos_3000.mp4",
            "05_Johanna_Hospital_Publico_No_Tiene_Banderas.mp4",
            "06_Johanna_La_Prepaga_No_Alcanzo_Solo_El_Garrahan.mp4",
            "07_Johanna_Dilema_Etico_Trasplante_Sin_Medicacion.mp4",
            "08_Johanna_La_Pelea_Es_Colectiva.mp4",
            "09_Antonela_Tumor_Oido_7_Anos_Solo_Garrahan.mp4",
            "10_Antonela_Obra_Social_Ghosteo_Implante_Coclear.mp4",
            "11_Antonela_Que_El_Garrahan_Siga_Salvando_Vidas.mp4",
            "11_Antonela_Que_El_Garrahan_Siga_Salvando_Vidas_CORREGIDO.mp4",
            "12_Antonela_Ninos_Vivos_Discapacidad_Natalidad.mp4",
            "CATALOGO_Y_COPIES_SEPTIEMBRE_JOHANNA_ANTONELA.txt",
            "REELS_Septiembre_Johanna_Antonela_Completo.zip"
        ]
    },
    "02_Campaña_Octubre_Graciela_VocesDelInterior": {
        "files": [
            "01_Graciela_La_Ilusion_De_La_Prepaga_Garrahan.mp4",
            "02_Graciela_Que_Es_Soy_Garrahan_Red_Federal.mp4",
            "03_Graciela_21Oct_Cae_Ley_Emergencia_Pediatrica.mp4",
            "03_Graciela_21Oct_Cae_Ley_Emergencia_Pediatrica.qa.json",
            "04_Graciela_El_Garrahan_No_Gano_Hablo_Al_Distraido.mp4",
            "05_Graciela_15Oct_Plaza_De_Mayo_Quita_Penas.mp4",
            "CATALOGO_Y_COPIES_GRACIELA_VOCES_DEL_INTERIOR.txt",
            "REELS_Octubre_Graciela_Voces_Del_Interior_Completo.zip"
        ]
    },
    "03_Campaña_Octubre_Johanna_FMEnTransito": {
        "files": [
            "01_Johanna_Vencimiento_Ley_Pediatrica_21Oct.mp4",
            "02_Johanna_Nombre_y_Apellido_Voto_Legisladores.mp4",
            "03_Johanna_Motosierra_Garrahan_Presupuesto.mp4",
            "04_Johanna_F16_vs_Discapacidad_Yates_Lujo.mp4",
            "05_Johanna_Llamado_Familias_Pais_Caso_Nena.mp4",
            "CATALOGO_Y_COPIES_FM_EN_TRANSITO.txt",
            "REELS_Octubre_Johanna_FM_En_Transito_Completo.zip"
        ]
    },
    "04_Campaña_Octubre_Johanna_Radio10": {
        "files": [
            "01_Johanna_Nueva_Ley_Salud_Pediatrica_Nacional.mp4",
            "02_Johanna_La_Trampa_Del_Gobierno_Quisieron_Apagar_La_Lucha.mp4",
            "03_Johanna_Medicamentos_Millonarios_Caso_Bayron.mp4",
            "CATALOGO_Y_COPIES_NUEVA_LEY.txt",
            "REELS_Octubre_Johanna_Radio10_Completo.zip"
        ]
    },
    "05_Campaña_Octubre_Johanna_AM530": {
        "files": [
            "01_Johanna_Caso_Nena_Salta_DNI_Cirugia.mp4",
            "02_Johanna_Cancer_No_Espera_Auditorias_Mata.mp4",
            "03_Johanna_Sector_Privado_No_Vio_Tumor_3_Resonancias.mp4",
            "04_Johanna_Munecas_Quita_Penas_Plaza_De_Mayo.mp4",
            "05_Johanna_Caso_Cristian_Santiago_Murio_De_Hambre.mp4",
            "CATALOGO_Y_COPIES_AM530.txt",
            "REELS_Octubre_Johanna_AM530_Completo.zip"
        ]
    },
    "06_Campaña_Octubre_Johanna_Diputados_ComisionSalud": {
        "files": [
            "01_Johanna_Cuanto_Vale_La_Vida_De_Un_Nino.mp4",
            "01_Johanna_Cuanto_Vale_La_Vida_De_Un_Nino.qa.json",
            "02_Johanna_Dejen_De_Mirar_Las_Planillas.mp4",
            "02_Johanna_Dejen_De_Mirar_Las_Planillas.qa.json",
            "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio.mp4",
            "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio.qa.json",
            "04_Johanna_Vence_Ley_Emergencia_Pediatrica.mp4",
            "04_Johanna_Vence_Ley_Emergencia_Pediatrica.qa.json",
            "05_Johanna_Las_Enfermedades_No_Preguntan_Que_Votaste.mp4",
            "05_Johanna_Las_Enfermedades_No_Preguntan_Que_Votaste.qa.json",
            "06_Johanna_Detras_De_Cada_Numero_Hay_Un_Nino.mp4",
            "06_Johanna_Detras_De_Cada_Numero_Hay_Un_Nino.qa.json",
            "CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt",
            "REELS_Octubre_Johanna_Diputados_Completo.zip"
        ]
    },
    "00_Archivo_Historico_Primeros_Reels": {
        "files": [
            "Reel_Cristian.mp4",
            "Reel_Fiebre.mp4",
            "Reel_Marcha.mp4",
            "Reel_Politica.mp4",
            "Reel_Viral_Antonela_Deterioro.mp4",
            "Reel_Viral_Antonela_Discapacidad.mp4",
            "Reel_Viral_Antonela_ObraSocial.mp4",
            "Reel_Viral_Antonela_Tumor.mp4",
            "Reel_Viral_Bayron.mp4",
            "Reel_Viral_Colectiva.mp4",
            "Reel_Viral_Cristian.mp4",
            "Reel_Viral_Fiebre.mp4",
            "Reel_Viral_Futuro.mp4",
            "Reel_Viral_Hospital.mp4",
            "Reel_Viral_Marcha.mp4",
            "Reel_Viral_Medicacion.mp4",
            "Reel_Viral_Plaza.mp4",
            "Reel_Viral_Politica.mp4",
            "Reel_Viral_Prepaga.mp4",
            "Reel_Viral_Presupuesto.mp4",
            "Reel_Viral_Trasplante.mp4"
        ]
    }
}

def organize():
    print(f"[*] Organizando {FINAL_DIR} en subcarpetas por campañas...")
    
    # Asegurar copia de CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt si no está en FINAL_DIR
    dip_copies = os.path.join(DOCS_DIR, "CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt")
    target_dip_copies = os.path.join(FINAL_DIR, "CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt")
    if os.path.exists(dip_copies) and not os.path.exists(target_dip_copies):
        shutil.copy2(dip_copies, target_dip_copies)

    for camp_name, camp_data in CAMPAIGNS_MAP.items():
        camp_dir = os.path.join(FINAL_DIR, camp_name)
        os.makedirs(camp_dir, exist_ok=True)
        print(f"\n📂 Subcarpeta: {camp_name}")
        
        for fname in camp_data["files"]:
            src_file = os.path.join(FINAL_DIR, fname)
            dst_file = os.path.join(camp_dir, fname)
            
            if os.path.exists(src_file) and not os.path.isdir(src_file):
                shutil.move(src_file, dst_file)
                print(f"   [Movido] {fname} -> {camp_name}/")
            elif os.path.exists(dst_file):
                print(f"   [OK] Ya en subcarpeta: {fname}")
            else:
                # Buscar en REELS_Octubre_Johanna_Diputados si es necesario
                alt_src = os.path.join(BASE_DIR, "REELS_Octubre_Johanna_Diputados", fname)
                if os.path.exists(alt_src):
                    shutil.copy2(alt_src, dst_file)
                    print(f"   [Copiado desde render] {fname} -> {camp_name}/")
                else:
                    print(f"   [!] No encontrado: {fname}")

    print("\n[✓] Organización de carpetas completada con éxito.")

if __name__ == "__main__":
    organize()
