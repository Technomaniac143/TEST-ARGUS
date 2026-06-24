from backend.adapters.base_adapter import SourceAdapter


class SulekhaAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Sulekha", "directory", "sulekha.com", ["service", "rating", "locality"])
