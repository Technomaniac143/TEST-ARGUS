from backend.adapters.base_adapter import SourceAdapter


class ProfessionalDirectoryAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Professional Directory", "professional_directory", None, ["association", "directory", "certified"])
