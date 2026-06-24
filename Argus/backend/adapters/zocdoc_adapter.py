from backend.adapters.base_adapter import SourceAdapter


class ZocdocAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Zocdoc", "healthcare_directory", "zocdoc.com", ["doctor", "appointment", "insurance"])
