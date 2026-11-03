import os
import subprocess
import json

def get_ffmpeg_path() -> str:
    """Retorna la ruta al ejecutable real de FFmpeg, evitando stubs de prueba."""
    candidate_winget = os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
    )
    if os.path.isfile(candidate_winget):
        return candidate_winget
        
    try:
        output = subprocess.check_output(["where.exe", "ffmpeg"], text=True).strip().splitlines()
        for p in output:
            p_clean = p.strip()
            if "ffmpeg-stub" not in p_clean.lower() and p_clean.lower().endswith(".exe") and os.path.isfile(p_clean):
                return p_clean
    except Exception:
        pass
        
    return "ffmpeg"

def get_ffprobe_path() -> str:
    """Retorna la ruta al ejecutable real de FFprobe."""
    candidate_winget = os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffprobe.exe"
    )
    if os.path.isfile(candidate_winget):
        return candidate_winget
        
    try:
        output = subprocess.check_output(["where.exe", "ffprobe"], text=True).strip().splitlines()
        for p in output:
            p_clean = p.strip()
            if "ffmpeg-stub" not in p_clean.lower() and p_clean.lower().endswith(".exe") and os.path.isfile(p_clean):
                return p_clean
    except Exception:
        pass
        
    return "ffprobe"

def escape_filter_path(path: str) -> str:
    """Escapa una ruta para su uso dentro de filter_complex en Windows."""
    abs_path = os.path.abspath(path).replace("\\", "/")
    if len(abs_path) > 1 and abs_path[1] == ":":
        abs_path = abs_path[0] + "\\:" + abs_path[2:]
    return abs_path

import atexit
import signal

_ACTIVE_CHILD_PIDS = set()

def kill_process_tree(pid: int):
    """Mata un proceso y todo su árbol de subprocesos en Windows usando taskkill."""
    if not pid:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:
        pass

def cleanup_all_active_processes():
    """Garantiza que al terminar o fallar Python no quede ningún subproceso huérfano."""
    for pid in list(_ACTIVE_CHILD_PIDS):
        kill_process_tree(pid)
    _ACTIVE_CHILD_PIDS.clear()

atexit.register(cleanup_all_active_processes)

def run_command_with_safety(cmd: list, timeout: float = 180.0, **kwargs) -> subprocess.CompletedProcess:
    """
    Ejecuta un comando de FFmpeg/FFprobe con protección absoluta contra procesos zombi:
    1. Registra el PID del subproceso.
    2. Aplica un timeout estricto para evitar bucles infinitos.
    3. Si falla, se cancela o excede el tiempo, ejecuta taskkill /T /F sobre todo el árbol.
    """
    kwargs.setdefault("creationflags", subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    proc = subprocess.Popen(cmd, **kwargs)
    _ACTIVE_CHILD_PIDS.add(proc.pid)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        retcode = proc.poll()
        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, cmd, output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(cmd, retcode, stdout, stderr)
    except subprocess.TimeoutExpired:
        kill_process_tree(proc.pid)
        raise TimeoutError(f"El comando excedió el tiempo límite de seguridad de {timeout}s: {' '.join(cmd[:4])}...")
    except Exception:
        kill_process_tree(proc.pid)
        raise
    finally:
        _ACTIVE_CHILD_PIDS.discard(proc.pid)

def get_media_info(filepath: str) -> dict:
    """Obtiene metadatos del video con ffprobe."""
    ffprobe = get_ffprobe_path()
    cmd = [
        ffprobe, "-v", "error",
        "-show_entries", "format=duration:stream=width,height,r_frame_rate",
        "-of", "json", filepath
    ]
    res = run_command_with_safety(cmd, timeout=30.0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return json.loads(res.stdout)

