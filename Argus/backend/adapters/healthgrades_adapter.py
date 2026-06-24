from backend.adapters.base_adapter import SourceAdapter


class HealthgradesAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Healthgrades", "healthcare_directory", "healthgrades.com", ["specialities", "certifications", "hospital"])
