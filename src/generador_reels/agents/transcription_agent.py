import os
import json
import subprocess
import whisper
from .ffmpeg_utils import get_ffmpeg_path, run_command_with_safety

class TranscriptionAgent:
    """
    Agente 1: Ingesta y Transcripción Fina a nivel de palabra.
    Extrae audio de alta fidelidad y utiliza Whisper para generar timestamps palabra por palabra.
    Optimizado con 'smart windowing' para transcribir segmentos en segundos en lugar de horas.
    """
    def __init__(self, model_name: str = "small"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            print(f"  [TranscriptionAgent] Cargando modelo Whisper '{self.model_name}'...")
            self._model = whisper.load_model(self.model_name)
        return self._model

    def extract_audio(self, video_path: str, output_wav: str, start: float = None, duration: float = None) -> str:
        """Extrae la pista de audio a WAV 16kHz mono para máxima precisión."""
        if os.path.exists(output_wav):
            try:
                os.remove(output_wav)
            except Exception:
                pass
            
        ffmpeg = get_ffmpeg_path()
        cmd = [ffmpeg, "-y"]
        if start is not None:
            cmd.extend(["-ss", f"{start:.3f}"])
        if duration is not None:
            cmd.extend(["-t", f"{duration:.3f}"])
        cmd.extend([
            "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            output_wav
        ])
        
        run_command_with_safety(cmd, timeout=60.0)
        return output_wav

    def transcribe(self, media_path: str, cache_json: str = None, window_start: float = None, window_end: float = None) -> dict:
        """
        Transcribe el archivo y retorna la estructura con timestamps a nivel de palabra.
        Si se especifica window_start y window_end, extrae y transcribe únicamente esa ventana
        para velocidad instantánea (segundos en lugar de minutos).
        """
        if cache_json and os.path.exists(cache_json):
            print(f"  [TranscriptionAgent] Usando transcripción en caché desde {cache_json}")
            with open(cache_json, "r", encoding="utf-8") as f:
                return json.load(f)

        # Si hay ventana definida, transcribir únicamente el fragmento necesario
        time_offset = 0.0
        temp_wav = "temp_window_audio.wav"
        
        if window_start is not None and window_end is not None:
            time_offset = max(0.0, window_start - 8.0)
            window_dur = (window_end - window_start) + 16.0
            print(f"  [TranscriptionAgent] Extrayendo ventana optimizada: [{time_offset:.1f}s -> {time_offset + window_dur:.1f}s]...")
            self.extract_audio(media_path, temp_wav, start=time_offset, duration=window_dur)
            audio_target = temp_wav
        elif media_path.lower().endswith((".mp4", ".mov", ".mkv", ".m4a", ".webm")):
            print(f"  [TranscriptionAgent] Extrayendo audio completo...")
            self.extract_audio(media_path, temp_wav)
            audio_target = temp_wav
        else:
            audio_target = media_path

        print(f"  [TranscriptionAgent] Transcribiendo con Whisper ({self.model_name}) word_timestamps=True...")
        model = self._get_model()
        result = model.transcribe(audio_target, word_timestamps=True, language="es")

        # Limpiar temporal
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass

        # Estructurar resultado y sumar time_offset para alinear al video original
        structured_data = {
            "text": result.get("text", "").strip(),
            "segments": []
        }

        for seg in result.get("segments", []):
            seg_s = round(seg.get("start", 0.0) + time_offset, 3)
            seg_e = round(seg.get("end", 0.0) + time_offset, 3)
            seg_data = {
                "id": seg.get("id"),
                "start": seg_s,
                "end": seg_e,
                "text": seg.get("text", "").strip(),
                "words": []
            }
            for w in seg.get("words", []):
                w_s = round(w.get("start", 0.0) + time_offset, 3)
                w_e = round(w.get("end", 0.0) + time_offset, 3)
                seg_data["words"].append({
                    "word": w.get("word", "").strip(),
                    "start": w_s,
                    "end": w_e,
                    "probability": round(w.get("probability", 1.0), 3)
                })
            structured_data["segments"].append(seg_data)

        if cache_json and window_start is None:
            with open(cache_json, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)
            print(f"  [TranscriptionAgent] Transcripción guardada en {cache_json}")

        return structured_data
