from typing import Protocol, Any


class ContentExtractorProtocol(Protocol):
    def extract(self, html: str, url: str) -> Any:
        pass
