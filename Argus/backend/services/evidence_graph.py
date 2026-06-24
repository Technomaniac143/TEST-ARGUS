from backend.models.business import Business
from backend.models.conflict import Conflict
from backend.models.evidence import Evidence
from backend.utils.text import normalize_text


class EvidenceGraphService:
    """Builds lightweight evidence graph JSON from persisted receipts."""

    def build(
        self,
        business: Business,
        evidence: list[Evidence],
        conflicts: list[Conflict],
    ) -> dict[str, list[dict[str, str]]]:
        nodes: dict[str, dict[str, str]] = {}
        edges: list[dict[str, str]] = []
        business_id = f"business:{business.id}"
        nodes[business_id] = {"id": business_id, "type": "business", "label": business.name or "Unknown business"}

        for item in evidence:
            field_id = f"field:{business.id}:{item.field}"
            value_id = f"value:{business.id}:{item.field}:{normalize_text(item.value)}"
            source_id = f"source:{business.id}:{normalize_text(item.source)}"
            nodes.setdefault(field_id, {"id": field_id, "type": "field", "label": self._label(item.field)})
            nodes.setdefault(value_id, {"id": value_id, "type": "value", "label": item.value})
            nodes.setdefault(source_id, {"id": source_id, "type": "source", "label": item.source})
            self._edge(edges, business_id, field_id, "HAS_FIELD")
            self._edge(edges, field_id, value_id, "HAS_VALUE")
            self._edge(edges, value_id, source_id, "SUPPORTED_BY")

        for conflict in conflicts:
            conflict_id = f"conflict:{business.id}:{conflict.field}:{normalize_text(conflict.value1)}:{normalize_text(conflict.value2)}"
            left_id = f"value:{business.id}:{conflict.field}:{normalize_text(conflict.value1)}"
            right_id = f"value:{business.id}:{conflict.field}:{normalize_text(conflict.value2)}"
            nodes.setdefault(conflict_id, {"id": conflict_id, "type": "conflict", "label": f"{self._label(conflict.field)} conflict"})
            nodes.setdefault(left_id, {"id": left_id, "type": "value", "label": conflict.value1})
            nodes.setdefault(right_id, {"id": right_id, "type": "value", "label": conflict.value2})
            self._edge(edges, conflict_id, left_id, "INVOLVES")
            self._edge(edges, conflict_id, right_id, "INVOLVES")
            self._edge(edges, left_id, right_id, "CONFLICTS_WITH")

        return {"nodes": list(nodes.values()), "edges": edges}

    def _edge(self, edges: list[dict[str, str]], source: str, target: str, label: str) -> None:
        edge = {"from": source, "to": target, "label": label}
        if edge not in edges:
            edges.append(edge)

    def _label(self, value: str) -> str:
        return value.replace("_", " ").title()
