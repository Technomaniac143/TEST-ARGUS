from backend.adapters.base_adapter import SourceAdapter


class JustdialAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Justdial", "directory", "justdial.com", ["phone", "address", "rating"])
