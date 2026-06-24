from backend.adapters.base_adapter import SourceAdapter


class OfficialWebsiteAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Official Website", "official_website", None, ["contact", "about", "services", "team"])

    def query_for(self, parsed_query, target, page: int = 1) -> str:
        base = f"{parsed_query.category} {parsed_query.location} official website contact"
        return f"{base} page {page}" if page > 1 else base
