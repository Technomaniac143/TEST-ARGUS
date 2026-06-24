from backend.adapters.base_adapter import SourceAdapter


class PractoAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Practo", "healthcare_directory", "practo.com", ["doctor", "speciality", "experience", "clinic", "timings"])
