from backend.adapters.base_adapter import SourceAdapter


class BbbAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("BBB", "professional_directory", "bbb.org", ["accreditation", "rating", "complaint"])
