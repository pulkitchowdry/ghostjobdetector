from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import logging

@dataclass
class ATSResult:
    exists: Optional[bool]
    confidence: float
    url: Optional[str]
    source: str
    reason: str

class ATSAdapter(ABC):
    @abstractmethod
    async def verify(self, company: str, job_title: str) -> ATSResult:
        pass
