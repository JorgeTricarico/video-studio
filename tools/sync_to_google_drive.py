import os
import shutil
import sys

# Forzar codificación UTF-8 para stdout en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DRIVE_ROOT = r"G:\.shortcut-targets-by-id\1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2\VIDEOS IA SOYGARRAHAN"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

FINAL_REELS_DIR = os.path.join(PROJECT_ROOT, "01_Reels_Finales_Subtitulados")
DOCS_DIR = os.path.join(PROJECT_ROOT, "05_Documentos_Copies_y_Transcripciones", "Copys_Redes")

CAMPAIGNS = [
    {
        "folder_name": "01_Campaña_Septiembre_Johanna_Antonela",
        "old_drive_name": "REELS_1_Septiembre_Johanna_Antonella",
        "copy_file": "CATALOGO_Y_COPIES_SEPTIEMBRE_JOHANNA_ANTONELA.txt",
        "reels": [
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
            "12_Antonela_Ninos_Vivos_Discapacidad_Natalidad.mp4"
        ]
    },
    {
        "folder_name": "02_Campaña_Octubre_Graciela_VocesDelInterior",
        "old_drive_name": None,
        "copy_file": "CATALOGO_Y_COPIES_GRACIELA_VOCES_DEL_INTERIOR.txt",
        "reels": [
            "01_Graciela_La_Ilusion_De_La_Prepaga_Garrahan.mp4",
            "02_Graciela_Que_Es_Soy_Garrahan_Red_Federal.mp4",
            "03_Graciela_21Oct_Cae_Ley_Emergencia_Pediatrica.mp4",
            "04_Graciela_El_Garrahan_No_Gano_Hablo_Al_Distraido.mp4",
            "05_Graciela_15Oct_Plaza_De_Mayo_Quita_Penas.mp4"
        ]
    },
    {
        "folder_name": "03_Campaña_Octubre_Johanna_FMEnTransito",
        "old_drive_name": "REELS_Octubre_Johanna_FM_En_Transito_Completo",
        "copy_file": "CATALOGO_Y_COPIES_FM_EN_TRANSITO.txt",
        "reels": [
            "01_Johanna_Vencimiento_Ley_Pediatrica_21Oct.mp4",
            "02_Johanna_Nombre_y_Apellido_Voto_Legisladores.mp4",
            "03_Johanna_Motosierra_Garrahan_Presupuesto.mp4",
            "04_Johanna_F16_vs_Discapacidad_Yates_Lujo.mp4",
            "05_Johanna_Llamado_Familias_Pais_Caso_Nena.mp4"
        ]
    },
    {
        "folder_name": "04_Campaña_Octubre_Johanna_Radio10",
        "old_drive_name": None,
        "copy_file": "CATALOGO_Y_COPIES_NUEVA_LEY.txt",
        "reels": [
            "01_Johanna_Nueva_Ley_Salud_Pediatrica_Nacional.mp4",
            "02_Johanna_La_Trampa_Del_Gobierno_Quisieron_Apagar_La_Lucha.mp4",
            "03_Johanna_Medicamentos_Millonarios_Caso_Bayron.mp4"
        ]
    },
    {
        "folder_name": "05_Campaña_Octubre_Johanna_AM530",
        "old_drive_name": None,
        "copy_file": "CATALOGO_Y_COPIES_AM530.txt",
        "reels": [
            "01_Johanna_Caso_Nena_Salta_DNI_Cirugia.mp4",
            "02_Johanna_Cancer_No_Espera_Auditorias_Mata.mp4",
            "03_Johanna_Sector_Privado_No_Vio_Tumor_3_Resonancias.mp4",
            "04_Johanna_Munecas_Quita_Penas_Plaza_De_Mayo.mp4",
            "05_Johanna_Caso_Cristian_Santiago_Murio_De_Hambre.mp4"
        ]
    },
    {
        "folder_name": "06_Campaña_Octubre_Johanna_Diputados_ComisionSalud",
        "old_drive_name": None,
        "copy_file": "CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt",
        "reels": [
            "01_Johanna_Cuanto_Vale_La_Vida_De_Un_Nino.mp4",
            "01_Johanna_Cuanto_Vale_La_Vida_De_Un_Nino_sin_subtitulos.mp4",
            "02_Johanna_Dejen_De_Mirar_Las_Planillas.mp4",
            "02_Johanna_Dejen_De_Mirar_Las_Planillas_sin_subtitulos.mp4",
            "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio.mp4",
            "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio_sin_subtitulos.mp4",
            "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio_v2.mp4",
            "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio_v2_sin_subtitulos.mp4",
            "04_Johanna_Vence_Ley_Emergencia_Pediatrica.mp4",
            "04_Johanna_Vence_Ley_Emergencia_Pediatrica_sin_subtitulos.mp4",
            "05_Johanna_Las_Enfermedades_No_Preguntan_Que_Votaste.mp4",
            "05_Johanna_Las_Enfermedades_No_Preguntan_Que_Votaste_sin_subtitulos.mp4",
            "06_Johanna_Detras_De_Cada_Numero_Hay_Un_Nino.mp4",
            "06_Johanna_Detras_De_Cada_Numero_Hay_Un_Nino_sin_subtitulos.mp4",
            "07_Johanna_No_Discuten_Dinero_Deciden_Vida_De_Un_Nino.mp4",
            "07_Johanna_No_Discuten_Dinero_Deciden_Vida_De_Un_Nino_sin_subtitulos.mp4",
            "08_Johanna_Nuestros_Hijos_No_Entran_En_Un_Excel.mp4",
            "08_Johanna_Nuestros_Hijos_No_Entran_En_Un_Excel_sin_subtitulos.mp4"
        ]
    }
]

def main():
    print(f"[*] Verificando acceso a Google Drive:")
    print(f"    Ruta: {DRIVE_ROOT}")
    if not os.path.exists(DRIVE_ROOT):
        print(f"[!] Error: La ruta de Google Drive no existe o no esta montada.")
        sys.exit(1)

    print("\n=======================================================")
    print("   SINCRONIZANDO 30 REELS LISTOS PARA REPRODUCIR")
    print("   (SIN ARCHIVOS ZIP • CARPETAS ESTANDARIZADAS)")
    print("=======================================================\n")

    total_synced = 0

    for camp in CAMPAIGNS:
        target_dir = os.path.join(DRIVE_ROOT, camp["folder_name"])
        old_dir = os.path.join(DRIVE_ROOT, camp["old_drive_name"]) if camp["old_drive_name"] else None

        # Si existe carpeta antigua con nombre anterior, renombrarla o migrarla
        if old_dir and os.path.exists(old_dir) and not os.path.exists(target_dir):
            print(f"[*] Renombrando carpeta existente: '{camp['old_drive_name']}' -> '{camp['folder_name']}'")
            try:
                os.rename(old_dir, target_dir)
            except Exception as e:
                print(f"    No se pudo renombrar directamente ({e}), creando carpeta destino...")
                os.makedirs(target_dir, exist_ok=True)
        else:
            os.makedirs(target_dir, exist_ok=True)

        print(f"\n[CAMPANA] {camp['folder_name']}")

        # Limpiar cualquier archivo .zip dentro de la carpeta en Drive (cumpliendo instrucción del usuario)
        for f in os.listdir(target_dir):
            if f.endswith(".zip"):
                zip_path = os.path.join(target_dir, f)
                print(f"  [!] Eliminando archivo ZIP no deseado en Drive: {f}")
                try:
                    os.remove(zip_path)
                except Exception as e:
                    print(f"      Error al eliminar ZIP: {e}")

        # Limpiar video pesado antiguo de 376 MB si existía
        huge_file = os.path.join(target_dir, "11_Antonela_Que_El_Garrahan_Siga_Salvando_Vidas.mp4")
        if os.path.exists(huge_file) and os.path.getsize(huge_file) > 100 * 1024 * 1024:
            print(f"  [!] Removiendo render pesado desactualizado de 376 MB...")
            try:
                os.remove(huge_file)
            except Exception as e:
                print(f"      Error: {e}")

        # Copiar / sincronizar reels
        for r_fn in camp["reels"]:
            src_mp4 = os.path.join(FINAL_REELS_DIR, r_fn)
            dst_mp4 = os.path.join(target_dir, r_fn)

            # Caso especial: Reel 11 de Antonela en Septiembre
            if r_fn == "11_Antonela_Que_El_Garrahan_Siga_Salvando_Vidas.mp4":
                corr_src = os.path.join(FINAL_REELS_DIR, "11_Antonela_Que_El_Garrahan_Siga_Salvando_Vidas_CORREGIDO.mp4")
                if os.path.exists(corr_src):
                    src_mp4 = corr_src

            if not os.path.exists(src_mp4):
                alt_src = os.path.join(FINAL_REELS_DIR, camp["folder_name"], r_fn)
                if os.path.exists(alt_src):
                    src_mp4 = alt_src

            if not os.path.exists(src_mp4):
                print(f"  [!] Archivo local no encontrado: {r_fn}")
                continue

            src_size = os.path.getsize(src_mp4)
            needs_copy = True

            if os.path.exists(dst_mp4):
                dst_size = os.path.getsize(dst_mp4)
                if abs(src_size - dst_size) < 1024:
                    needs_copy = False
                    print(f"  [OK] Ya sincronizado: {r_fn} ({src_size / (1024*1024):.1f} MB)")

            if needs_copy:
                print(f"  [+] Copiando a Drive: {r_fn} ({src_size / (1024*1024):.1f} MB)...")
                shutil.copy2(src_mp4, dst_mp4)

            src_qa = os.path.splitext(src_mp4)[0] + ".qa.json"
            dst_qa = os.path.join(target_dir, os.path.splitext(r_fn)[0] + ".qa.json")
            if os.path.exists(src_qa):
                if not os.path.exists(dst_qa) or os.path.getsize(src_qa) != os.path.getsize(dst_qa):
                    shutil.copy2(src_qa, dst_qa)

            total_synced += 1

        # Copiar archivo de copys de la campaña
        copy_src = os.path.join(DOCS_DIR, camp["copy_file"])
        if os.path.exists(copy_src):
            dst_copy = os.path.join(target_dir, camp["copy_file"])
            shutil.copy2(copy_src, dst_copy)
            print(f"  [OK] Archivo de Copys sincronizado: {camp['copy_file']}")

    # En la raíz de Google Drive, copiar el Catálogo Maestro Consolidado
    master_copy_src = os.path.join(DOCS_DIR, "CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt")
    if os.path.exists(master_copy_src):
        dst_master = os.path.join(DRIVE_ROOT, "CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt")
        shutil.copy2(master_copy_src, dst_master)
        print(f"\n[OK] Catálogo Maestro Consolidado copiado a la raíz de Google Drive.")

    # Crear una guía rápida LEEME en la raíz de Google Drive
    readme_drive = os.path.join(DRIVE_ROOT, "LEEME_GUIA_DE_VIDEOS_Y_COPIES.txt")
    with open(readme_drive, "w", encoding="utf-8") as f:
        f.write("""================================================================================
VIDEOS OFICIALES IA • COLECTIVO SOY GARRAHAN
COLECCIÓN CONSOLIDADA: 30 REELS LISTOS PARA REPRODUCIR Y PUBLICAR
================================================================================

Este directorio de Google Drive contiene los 30 videos finales de la campaña
nacional en defensa del Hospital Garrahan y la salud pediátrica, organizados
por campaña para visualización y descarga directa (sin archivos ZIP).

ESTRUCTURA DE CARPETAS:
--------------------------------------------------------------------------------
1. 01_Campaña_Septiembre_Johanna_Antonela (12 Reels)
   - Testimonios de Johanna Tricarico y Antonela (Canal Cíclico).
   - Incluye archivo: CATALOGO_Y_COPIES_SEPTIEMBRE_JOHANNA_ANTONELA.txt

2. 02_Campaña_Octubre_Graciela_VocesDelInterior (5 Reels)
   - Entrevista federal de Graciela del Valle Ferreira (Voces del Interior).
   - Incluye archivo: CATALOGO_Y_COPIES_GRACIELA_VOCES_DEL_INTERIOR.txt

3. 03_Campaña_Octubre_Johanna_FMEnTransito (5 Reels)
   - Entrevista a Johanna Tricarico en piso de FM En Tránsito 93.9.
   - Incluye archivo: CATALOGO_Y_COPIES_FM_EN_TRANSITO.txt

4. 04_Campaña_Octubre_Johanna_Radio10 (3 Reels)
   - Presentación de la Ley de Salud Pediátrica en Radio 10.
   - Incluye archivo: CATALOGO_Y_COPIES_NUEVA_LEY.txt

5. 05_Campaña_Octubre_Johanna_AM530 (5 Reels)
   - Entrevista urgente en Somos Radio AM 530 (caso nena de Salta y DNI).
   - Incluye archivo: CATALOGO_Y_COPIES_AM530.txt

CATÁLOGO MAESTRO:
En la raíz de este directorio se encuentra el archivo:
⭐_CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt con los textos, ganchos visuales
y hashtags listos para copiar y pegar en Instagram, TikTok o WhatsApp.

ESPECIFICACIONES TÉCNICAS:
- Formato: Vertical 9:16 (1080x1920) a 60 FPS
- Audio: Calibrado a estándar broadcast (-14 LUFS EBU R128)
- Subtítulos: Dinámicos estilo Hormozi dentro de la Safe Zone de Instagram
================================================================================
""")
    print("[OK] Guía rápida LEEME_GUIA_DE_VIDEOS_Y_COPIES.txt creada en Google Drive.")

    print("\n=======================================================")
    print(f"[OK] ¡SINCRONIZACIÓN Y REORGANIZACIÓN EN GOOGLE DRIVE FINALIZADA!")
    print(f"     Total de videos verificados: {total_synced} reels.")
    print(f"     Ruta: {DRIVE_ROOT}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
