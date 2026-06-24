from backend.adapters.base_adapter import SourceAdapter


class GovernmentRegistryAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Government Registry", "government_license_registry", None, ["license", "registration", "board", "registry"])

    def query_for(self, parsed_query, target, page: int = 1) -> str:
        base = f"{parsed_query.category} {parsed_query.location} license registry registration"
        return f"{base} page {page}" if page > 1 else base
