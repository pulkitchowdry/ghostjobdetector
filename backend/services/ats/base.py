from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import logging
from datetime import datetime

@dataclass
class ATSResult:
    exists: Optional[bool]
    confidence: float
    url: Optional[str]
    source: str
    reason: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    application_deadline: Optional[datetime] = None

class ATSAdapter(ABC):
    @abstractmethod
    async def verify(self, company: str, job_title: str) -> ATSResult:
        pass
