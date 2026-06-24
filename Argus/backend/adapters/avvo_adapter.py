from backend.adapters.base_adapter import SourceAdapter


class AvvoAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Avvo", "legal_directory", "avvo.com", ["practice areas", "license status", "attorney"])
