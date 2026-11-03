import numpy as np
import wave
import scipy.signal as signal

sr = 48000

# Notes in G major (chamamé / folk acoustic guitar)
notes = {
    'G2': 98.0, 'B2': 123.47, 'C3': 130.81, 'D3': 146.83, 'E3': 164.81,
    'F#3': 185.0, 'G3': 196.0, 'A3': 220.0, 'B3': 246.94, 'C4': 261.63,
    'D4': 293.66, 'E4': 329.63, 'F#4': 369.99, 'G4': 392.0, 'A4': 440.0, 'B4': 493.88
}

def synth_nylon_note(freq, dur=1.5):
    """Additive harmonic synthesis + physical envelope with warmth for nylon acoustic guitar"""
    t = np.linspace(0, dur, int(dur * sr), endpoint=False)
    # Harmonics of nylon string: fundamental strong, 2nd, 3rd, 4th, 5th
    sig = np.zeros_like(t)
    harmonics = [(1, 1.0, 3.2), (2, 0.65, 4.8), (3, 0.40, 6.5), (4, 0.25, 8.5), (5, 0.15, 11.0), (6, 0.08, 14.0)]
    for h, amp, decay in harmonics:
        # Slight frequency damping
        decay_rate = decay * (1.0 + (freq / 300.0) * 0.5)
        env = np.exp(-t * decay_rate)
        # initial attack (pluck impulse ~ 4ms)
        attack = 1.0 - np.exp(-t * 800.0)
        sig += amp * np.sin(2 * np.pi * (freq * h) * t) * env * attack
        
    # Add warm wooden body resonance around 100-200 Hz
    body = 0.15 * np.sin(2 * np.pi * 120.0 * t) * np.exp(-t * 5.0)
    sig += body * sig[0] if len(sig) > 0 else 0
    
    # Soft low-pass filter to sound warm like nylon guitar
    b, a = signal.butter(2, min(0.4, 2500.0 / (sr / 2)), btype='low')
    sig = signal.lfilter(b, a, sig)
    return sig.astype(np.float32)

print("[*] Pre-rendering note waveforms...")
note_cache = {name: synth_nylon_note(freq) for name, freq in notes.items()}

bpm = 110
beat_dur = 60.0 / bpm
e_dur = beat_dur / 2

# 4 measure loop: G | C | D7 | G
measures = [
    # G
    [('G2', 0.0, 0.85), ('D3', e_dur, 0.45), ('G3', e_dur*1.01, 0.5),
     ('B3', e_dur*2, 0.45), ('D4', e_dur*2.01, 0.5),
     ('D3', e_dur*3, 0.75), ('G3', e_dur*4, 0.5), ('B3', e_dur*4.01, 0.5),
     ('D4', e_dur*5, 0.45), ('G4', e_dur*5.01, 0.5)],
    # C
    [('C3', 0.0, 0.85), ('E3', e_dur, 0.45), ('G3', e_dur*1.01, 0.5),
     ('C4', e_dur*2, 0.45), ('E4', e_dur*2.01, 0.5),
     ('G3', e_dur*3, 0.75), ('C4', e_dur*4, 0.5), ('E4', e_dur*4.01, 0.5),
     ('G4', e_dur*5, 0.45), ('C4', e_dur*5.01, 0.5)],
    # D7
    [('D3', 0.0, 0.85), ('F#3', e_dur, 0.45), ('A3', e_dur*1.01, 0.5),
     ('C4', e_dur*2, 0.45), ('D4', e_dur*2.01, 0.5),
     ('A3', e_dur*3, 0.75), ('C4', e_dur*4, 0.5), ('D4', e_dur*4.01, 0.5),
     ('F#4', e_dur*5, 0.45), ('A4', e_dur*5.01, 0.5)],
    # G
    [('G2', 0.0, 0.85), ('D3', e_dur, 0.45), ('G3', e_dur*1.01, 0.5),
     ('B3', e_dur*2, 0.45), ('D4', e_dur*2.01, 0.5),
     ('B2', e_dur*3, 0.75), ('D3', e_dur*4, 0.5), ('G3', e_dur*4.01, 0.5),
     ('B3', e_dur*5, 0.45), ('D4', e_dur*5.01, 0.5)],
]

measure_dur = 6 * e_dur
loop_dur = len(measures) * measure_dur
total_dur = 125.0 # Covers full narration + outro
total_samples = int(total_dur * sr)
left = np.zeros(total_samples, dtype=np.float32)
right = np.zeros(total_samples, dtype=np.float32)

t_curr = 0.0
while t_curr < total_dur:
    for m in measures:
        for n_name, offset, vel in m:
            t = t_curr + offset
            if t >= total_dur:
                continue
            idx0 = int(t * sr)
            w = note_cache[n_name] * vel
            idx1 = min(idx0 + len(w), total_samples)
            count = idx1 - idx0
            if count > 0:
                freq = notes[n_name]
                pan = max(-0.35, min(0.35, (freq - 220.0) / 450.0))
                left[idx0:idx1] += w[:count] * (0.5 - pan)
                right[idx0:idx1] += w[:count] * (0.5 + pan)
        t_curr += measure_dur

# Stereo warm ambience delay
delay = int(0.12 * sr)
left[delay:] += right[:-delay] * 0.18
right[delay:] += left[:-delay] * 0.18

# Normalize
pk = max(np.max(np.abs(left)), np.max(np.abs(right)))
if pk > 0:
    left /= pk
    right /= pk

stereo = np.column_stack(((left * 32000).astype(np.int16), (right * 32000).astype(np.int16)))
out_path = "assets/firule/guitarra_chamame_fondo.wav"
with wave.open(out_path, "wb") as w_out:
    w_out.setnchannels(2)
    w_out.setsampwidth(2)
    w_out.setframerate(sr)
    w_out.writeframes(stereo.tobytes())

print(f"[OK] Guitar backing track generated successfully: {out_path} ({total_dur}s)")
