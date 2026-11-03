from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    probability: float = 1.0

@dataclass
class SoundbiteSelection:
    hook_text: str
    raw_start: float
    raw_end: float
    words: List[Dict] = field(default_factory=list)

@dataclass
class VideoCut:
    index: int
    start: float
    end: float
    duration: float
    timeline_start: float

@dataclass
class PacingResult:
    cuts: List[Dict]
    remapped_words: List[Dict]
    total_duration: float

@dataclass
class ReelResult:
    output_path: str
    duration: float
    speech_duration: float
    outro_duration: float
    cuts_count: int
    words_count: int
    hook_text: str
    theme: str
    render_time_sec: float
