from backend.offline_corpus.corpus import corpus_index
from backend.schemas.search import ParsedQuery


class CorpusIndexService:
    """Reports offline corpus coverage and support level for a parsed query."""

    def describe(self, parsed_query: ParsedQuery | None = None) -> dict[str, object]:
        return corpus_index(parsed_query)
