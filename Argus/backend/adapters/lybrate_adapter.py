from backend.adapters.base_adapter import SourceAdapter


class LybrateAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Lybrate", "healthcare_directory", "lybrate.com", ["doctor", "speciality", "clinic", "consultation"])
