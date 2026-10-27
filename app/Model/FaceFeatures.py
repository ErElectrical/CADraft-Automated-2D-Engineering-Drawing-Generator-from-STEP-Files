from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Feature:
    feature_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    face_ids: list[int] = field(default_factory=list)
    confidence: float = 1.0