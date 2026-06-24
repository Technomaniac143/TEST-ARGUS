from backend.adapters.base_adapter import SourceAdapter


class FacebookAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Facebook", "social_profile", "facebook.com", ["page", "phone", "hours"])
