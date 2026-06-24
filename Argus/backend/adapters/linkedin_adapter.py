from backend.adapters.base_adapter import SourceAdapter


class LinkedInAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("LinkedIn", "social_profile", "linkedin.com/company", ["company", "industry", "website"])
