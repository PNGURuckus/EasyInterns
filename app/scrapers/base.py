from abc import ABC, abstractmethod
from ..models import Opportunity

class BaseScraper(ABC):
    @abstractmethod
    async def fetch(self) -> list[Opportunity]:
        ...
