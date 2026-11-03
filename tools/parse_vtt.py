import re
import os

vtt_path = "assets/am530_subs.es.vtt"
out_path = "assets/am530_dialogue_clean.txt"

with open(vtt_path, "r", encoding="utf-8") as f:
    text = f.read()

cues = re.findall(r"(\d\d:\d\d:\d\d\.\d+)\s*-->\s*(\d\d:\d\d:\d\d\.\d+)[^\n]*\n(.*?)(?=\n\n|\Z)", text, re.DOTALL)

clean_cues = []
for start, end, body in cues:
    cleaned = re.sub(r"<[^>]+>", "", body).strip()
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    if lines:
        t_line = " ".join(lines)
        if not clean_cues or clean_cues[-1][2] != t_line:
            clean_cues.append((start[:8], end[:8], t_line))

blocks = []
curr_start = None
curr_end = None
curr_text = []

def to_sec(ts):
    p = [float(x) for x in ts.split(":")]
    return p[0]*3600 + p[1]*60 + p[2]

for s, e, t in clean_cues:
    if curr_start is None:
        curr_start = s
    curr_end = e
    curr_text.append(t)
    if to_sec(s) - to_sec(curr_start) >= 20:
        # Deduplicate consecutive identical words in curr_text
        combined = " ".join(curr_text)
        words = combined.split()
        dedup_words = []
        for w in words:
            if not dedup_words or dedup_words[-1].lower() != w.lower():
                dedup_words.append(w)
            elif len(dedup_words) >= 2 and dedup_words[-2].lower() == w.lower():
                pass
        final_text = " ".join(dedup_words)
        blocks.append(f"[{curr_start} --> {curr_end}] ({to_sec(curr_start):.1f}s - {to_sec(curr_end):.1f}s)\n{final_text}")
        curr_start = None
        curr_text = []

if curr_text:
    combined = " ".join(curr_text)
    blocks.append(f"[{curr_start} --> {curr_end}] ({to_sec(curr_start):.1f}s - {to_sec(curr_end):.1f}s)\n{combined}")

with open(out_path, "w", encoding="utf-8") as out:
    out.write("\n\n".join(blocks))

print(f"Total blocks generated: {len(blocks)}")
