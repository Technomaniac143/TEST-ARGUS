from backend.adapters.base_adapter import SourceAdapter


class AngiAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Angi", "review_platform", "angi.com", ["rating", "project", "home service"])
