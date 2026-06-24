from collections import Counter


class BusinessKnowledgeGraphService:
    """Builds a session-level market knowledge graph as JSON."""

    node_fields = {
        "services": ("service", "BUSINESS_HAS_SERVICE"),
        "specialties": ("specialty", "BUSINESS_HAS_SPECIALTY"),
        "certifications": ("certification", "BUSINESS_HAS_CERTIFICATION"),
        "awards": ("award", "BUSINESS_HAS_AWARD"),
    }

    def build(self, businesses: list[dict[str, object]], review_queue: list[dict[str, object]] | None = None) -> dict[str, list[dict[str, str]]]:
        nodes: dict[str, dict[str, str]] = {}
        edges: list[dict[str, str]] = []
        review_names = {str(item.get("business_name")): str(item.get("reason")) for item in review_queue or []}

        for business in businesses:
            business_id = f"business:{business.get('id')}"
            nodes[business_id] = {"id": business_id, "type": "business", "label": str(business.get("name") or "Unknown")}
            self._linked_node(nodes, edges, business_id, "city", str(business.get("location") or "unknown"), "BUSINESS_IN_CITY")
            self._linked_node(nodes, edges, business_id, "category", str(business.get("category") or "unknown"), "BUSINESS_IN_CATEGORY")
            for flag in business.get("analyst_quality_flags", []):
                self._linked_node(nodes, edges, business_id, "quality_flag", str(flag), "BUSINESS_HAS_FLAG")
            for source in sorted({str(item.get("source")) for item in business.get("evidence", []) if item.get("source")}):
                self._linked_node(nodes, edges, business_id, "source", source, "BUSINESS_SUPPORTED_BY_SOURCE")
            for field, (node_type, edge_label) in self.node_fields.items():
                for value in self._evidence_values(business, field):
                    self._linked_node(nodes, edges, business_id, node_type, value, edge_label)
            if str(business.get("name")) in review_names:
                self._linked_node(nodes, edges, business_id, "review_reason", review_names[str(business.get("name"))], "BUSINESS_REQUIRES_REVIEW")

        return {"nodes": list(nodes.values()), "edges": edges}

    def overview_terms(self, businesses: list[dict[str, object]], field: str, limit: int = 5) -> list[str]:
        counter: Counter[str] = Counter()
        for business in businesses:
            counter.update(self._evidence_values(business, field))
        return [item for item, _ in counter.most_common(limit)]

    def _linked_node(self, nodes, edges, business_id: str, node_type: str, label: str, edge_label: str) -> None:
        node_id = f"{node_type}:{self._slug(label)}"
        nodes.setdefault(node_id, {"id": node_id, "type": node_type, "label": label})
        edge = {"from": business_id, "to": node_id, "label": edge_label}
        if edge not in edges:
            edges.append(edge)

    def _evidence_values(self, business: dict[str, object], field: str) -> list[str]:
        values: list[str] = []
        for item in business.get("evidence", []):
            if item.get("field") == field:
                values.extend(part.strip() for part in str(item.get("value") or "").split(",") if part.strip())
        return list(dict.fromkeys(values))

    def _slug(self, value: str) -> str:
        return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")
