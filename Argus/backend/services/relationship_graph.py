from collections import Counter, defaultdict


class RelationshipGraphService:
    """Builds a lightweight market relationship graph without an external graph DB."""

    def build(self, businesses: list[dict[str, object]], clusters: list[dict[str, object]]) -> dict[str, object]:
        nodes: dict[str, dict[str, object]] = {}
        edges: list[dict[str, object]] = []

        for business in businesses:
            bid = self._business_id(business)
            nodes[bid] = {"id": bid, "type": "business", "label": business.get("name") or "Business"}
            self._connect_values(nodes, edges, bid, "service", self._values(business, "services"), "SHARES_SERVICE")
            self._connect_values(nodes, edges, bid, "specialty", self._values(business, "specialties"), "SHARES_SPECIALTY")
            self._connect_values(nodes, edges, bid, "certification", self._values(business, "certifications"), "SHARES_CERTIFICATION")
            self._connect_single(nodes, edges, bid, "city", str(business.get("location") or ""), "IN_SAME_CITY")
            self._connect_single(nodes, edges, bid, "category", str(business.get("category") or ""), "IN_CATEGORY")
            self._connect_single(nodes, edges, bid, "cluster", str(business.get("market_cluster") or "Unassigned"), "IN_SAME_CLUSTER")
            for flag in business.get("analyst_quality_flags", []):
                self._connect_single(nodes, edges, bid, "quality_flag", str(flag), "HAS_QUALITY_FLAG")
            for outlier in business.get("outliers", []):
                self._connect_single(nodes, edges, bid, "review_reason", str(outlier.get("outlier_reason") or ""), "HAS_REVIEW_REASON")

        name_to_id = {str(business.get("name") or ""): self._business_id(business) for business in businesses}
        for business in businesses:
            left = self._business_id(business)
            for item in business.get("similar_businesses", [])[:3]:
                right_name = str(item.get("business_name") or "")
                right = name_to_id.get(right_name)
                if right in nodes:
                    edges.append({"from": left, "to": right, "type": "SIMILAR_TO", "label": "SIMILAR_TO", "weight": item.get("score", 0)})

        metrics = self.network_metrics(businesses, edges)
        ecosystem = self.ecosystem_summary(businesses, clusters, metrics)
        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "centrality_metrics": metrics["centrality_metrics"],
            "similar_pairs": metrics["similar_pairs"],
            "ecosystem_summary": ecosystem,
        }

    def network_metrics(self, businesses: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, object]:
        degree = Counter()
        top_relationship: dict[str, str] = {}
        for edge in edges:
            if str(edge.get("from", "")).startswith("business:"):
                degree[str(edge["from"])] += 1
                top_relationship.setdefault(str(edge["from"]), str(edge.get("type", "")))
            if str(edge.get("to", "")).startswith("business:"):
                degree[str(edge["to"])] += 1
        centrality = []
        for business in businesses:
            bid = self._business_id(business)
            shared_services = len(self._values(business, "services"))
            centrality.append(
                {
                    "business_name": business.get("name"),
                    "centrality_score": degree[bid],
                    "degree_score": degree[bid],
                    "top_relationship": top_relationship.get(bid, "IN_SAME_CITY"),
                    "shared_services_count": shared_services,
                    "shared_specialties_count": len(self._values(business, "specialties")),
                    "shared_certifications_count": len(self._values(business, "certifications")),
                    "source_overlap": len({e.get("source") for e in business.get("evidence", [])}),
                }
            )
            business["centrality_score"] = degree[bid]
            business["top_relationship"] = top_relationship.get(bid, "IN_SAME_CITY")
            business["shared_services_count"] = shared_services
        centrality = sorted(centrality, key=lambda item: item["centrality_score"], reverse=True)
        similar_pairs = self._similar_pairs(businesses)
        return {
            "centrality_metrics": centrality,
            "similar_pairs": similar_pairs,
            "most_connected_business": centrality[0]["business_name"] if centrality else None,
            "most_isolated_business": centrality[-1]["business_name"] if centrality else None,
            "most_similar_pair": similar_pairs[0] if similar_pairs else {},
            "most_unique_business": centrality[-1]["business_name"] if centrality else None,
        }

    def ecosystem_summary(
        self,
        businesses: list[dict[str, object]],
        clusters: list[dict[str, object]],
        metrics: dict[str, object],
    ) -> dict[str, object]:
        return {
            "clusters": [{"name": c.get("cluster_name"), "count": c.get("cluster_metrics", {}).get("count", 0)} for c in clusters],
            "shared_services": self._common(businesses, "services"),
            "dominant_specialties": self._common(businesses, "specialties"),
            "dominant_certifications": self._common(businesses, "certifications"),
            "most_common_flags": Counter(flag for b in businesses for flag in b.get("analyst_quality_flags", [])).most_common(5),
            "most_connected_nodes": metrics.get("centrality_metrics", [])[:5],
            "outliers": {b.get("name"): b.get("outliers", []) for b in businesses if b.get("outliers")},
            "most_connected_business": metrics.get("most_connected_business"),
            "most_isolated_business": metrics.get("most_isolated_business"),
            "most_similar_pair": metrics.get("most_similar_pair"),
            "most_unique_business": metrics.get("most_unique_business"),
        }

    def _connect_values(self, nodes, edges, business_id: str, node_type: str, values: set[str], edge_type: str) -> None:
        for value in values:
            self._connect_single(nodes, edges, business_id, node_type, value, edge_type)

    def _connect_single(self, nodes, edges, business_id: str, node_type: str, value: str, edge_type: str) -> None:
        if not value:
            return
        node_id = f"{node_type}:{value.lower().replace(' ', '-')}"
        nodes.setdefault(node_id, {"id": node_id, "type": node_type, "label": value})
        edges.append({"from": business_id, "to": node_id, "type": edge_type, "label": edge_type})

    def _business_id(self, business: dict[str, object]) -> str:
        return f"business:{business.get('id') or business.get('name')}"

    def _values(self, business: dict[str, object], field: str) -> set[str]:
        values = set()
        for item in business.get("evidence", []):
            if item.get("field") == field:
                values.update(part.strip() for part in str(item.get("value") or "").split(",") if part.strip())
        return values

    def _common(self, businesses: list[dict[str, object]], field: str) -> list[str]:
        counter = Counter(value for business in businesses for value in self._values(business, field))
        return [value for value, _count in counter.most_common(5)]

    def _similar_pairs(self, businesses: list[dict[str, object]]) -> list[dict[str, object]]:
        seen = set()
        pairs = []
        for business in businesses:
            left = str(business.get("name") or "")
            for item in business.get("similar_businesses", [])[:3]:
                right = str(item.get("business_name") or "")
                key = tuple(sorted([left, right]))
                if not right or key in seen:
                    continue
                seen.add(key)
                pairs.append({"business_a": left, "business_b": right, "score": item.get("score", 0)})
        return sorted(pairs, key=lambda item: item["score"], reverse=True)
