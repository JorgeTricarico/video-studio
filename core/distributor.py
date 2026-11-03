import os
import shutil
import zipfile
import subprocess
import time
from typing import List, Dict, Any
from .env_config import TAILSCALE_EXE, GDRIVE_DIR

class Distributor:
    """
    Coordinador de Distribución y Entrega Multi-dispositivo.
    """
    @staticmethod
    def sync_to_google_drive(source_dir: str, campaign_folder_name: str) -> Dict[str, Any]:
        """
        Sincroniza una carpeta de campaña local con Google Drive.
        """
        if not os.path.exists(GDRIVE_DIR):
            print(f"[!] Google Drive no montado o inaccesible en {GDRIVE_DIR}")
            return {"success": False, "reason": "Drive no montado"}

        dest_dir = os.path.join(GDRIVE_DIR, campaign_folder_name)
        os.makedirs(dest_dir, exist_ok=True)
        copied = []

        print(f"[*] Sincronizando a Google Drive: {dest_dir}")
        for item in os.listdir(source_dir):
            src_p = os.path.join(source_dir, item)
            dst_p = os.path.join(dest_dir, item)
            if os.path.isfile(src_p):
                if not os.path.exists(dst_p) or os.path.getsize(src_p) != os.path.getsize(dst_p):
                    shutil.copy2(src_p, dst_p)
                    copied.append(item)
                    print(f"  [Drive] Copiado: {item}")
                else:
                    print(f"  [Drive] Ya actualizado: {item}")

        print(f"[OK] Sincronización a Drive completada: {len(copied)} archivos transferidos.")
        return {
            "success": True,
            "destination": dest_dir,
            "copied_count": len(copied),
            "copied_files": copied
        }
    @staticmethod
    def package_show(show_profile: Dict[str, Any], base_project_dir: str, final_dir: str) -> str:
        show_dir = os.path.join(base_project_dir, show_profile["output_dir"])
        zip_path = os.path.join(show_dir, show_profile["zip_name"])
        dest_zip = os.path.join(final_dir, show_profile["zip_name"])

        print(f"Empaquetando: {show_profile['name']} -> {show_profile['zip_name']}")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in show_profile["reels"]:
                mp4_path = os.path.join(show_dir, r["filename"])
                if os.path.exists(mp4_path):
                    zf.write(mp4_path, arcname=r["filename"])
                    print(f"  + {r['filename']}")

            for extra in os.listdir(show_dir):
                if extra.startswith("CATALOGO") or extra == "index.html":
                    zf.write(os.path.join(show_dir, extra), arcname=extra)
                    print(f"  + {extra}")

        shutil.copy2(zip_path, dest_zip)
        return dest_zip

    @staticmethod
    def sync_to_tailscale(files: List[str], target_device: str = "moto-g24-power:") -> bool:
        if not os.path.exists(TAILSCALE_EXE):
            print(f"Tailscale no encontrado en: {TAILSCALE_EXE}")
            return False

        existing = [f for f in files if os.path.exists(f)]
        if not existing:
            print("No hay archivos para sincronizar.")
            return False

        cmd = [TAILSCALE_EXE, "file", "cp"] + existing + [target_device]
        print(f"Transfiriendo {len(existing)} archivos a {target_device}...")
        t0 = time.time()
        res = subprocess.run(cmd)
        elapsed = time.time() - t0
        if res.returncode == 0:
            print(f"  [OK] Transferencia completada en {elapsed:.1f}s.")
            return True
        else:
            print(f"  [ERROR] Falló la transferencia (código {res.returncode}).")
            return False
