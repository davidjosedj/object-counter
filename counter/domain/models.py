from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Box:
    xmin: float
    ymin: float
    xmax: float
    ymax: float


@dataclass
class Prediction:
    class_name: str
    score: float
    box: Box

    def to_dict(self):
        return asdict(self)


@dataclass
class ObjectCount:
    object_class: str
    count: int

    def to_dict(self):
        return asdict(self)


@dataclass
class CountResponse:
    current_objects: List[ObjectCount]
    total_objects: List[ObjectCount]

    def to_dict(self):
        return asdict(self)
