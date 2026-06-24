from backend.adapters.base_adapter import SourceAdapter


class YelpAdapter(SourceAdapter):
    def __init__(self) -> None:
        super().__init__("Yelp", "review_platform", "yelp.com", ["rating", "review", "price"])
