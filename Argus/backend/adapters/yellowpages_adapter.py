from backend.adapters.base_adapter import SourceAdapter


class YellowPagesAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Yellow Pages", "directory", "yellowpages.com", ["phone", "address", "hours"])
