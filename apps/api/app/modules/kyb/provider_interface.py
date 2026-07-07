from abc import ABC, abstractmethod
from typing import Any

class KYBProvider(ABC):
    name: str

    @abstractmethod
    async def create_applicant(self, business_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def upload_document(self, applicant_id: str, document_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def start_check(self, applicant_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_check_status(self, check_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def parse_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        raise NotImplementedError
