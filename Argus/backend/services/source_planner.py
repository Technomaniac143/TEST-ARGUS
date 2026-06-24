from backend.schemas.search import ParsedQuery, SourceTarget


class SourcePlannerService:
    """Builds explicit source-search targets for real public-source research."""

    def plan(self, parsed_query: ParsedQuery, max_targets: int = 5) -> list[SourceTarget]:
        category = parsed_query.category
        location = parsed_query.location
        targets = [
            SourceTarget(
                source_type="general_search",
                label="General web search",
                query=f"{category} in {location}",
            ),
            SourceTarget(
                source_type="general_search",
                label="Best local results",
                query=f"best {category} {location}",
            ),
            SourceTarget(
                source_type="official_website",
                label="Official websites",
                query=f"{category} {location} official website",
            ),
            SourceTarget(
                source_type="directory",
                label="Yellow Pages",
                query=f"site:yellowpages.com {category} {location}",
            ),
            SourceTarget(
                source_type="review_platform",
                label="Yelp",
                query=f"site:yelp.com {category} {location}",
            ),
            SourceTarget(
                source_type="social_profile",
                label="LinkedIn",
                query=f"site:linkedin.com/company {category} {location}",
            ),
        ]
        if self._is_healthcare(category):
            targets.extend(
                [
                    SourceTarget(source_type="government_license_registry", label="Board certification", query=f"{category} {location} board certified"),
                    SourceTarget(source_type="professional_directory", label="Healthgrades", query=f"site:healthgrades.com {category} {location}"),
                    SourceTarget(source_type="professional_directory", label="Zocdoc", query=f"site:zocdoc.com {category} {location}"),
                ]
            )
        if self._is_legal(category):
            targets.extend(
                [
                    SourceTarget(source_type="professional_directory", label="Avvo", query=f"site:avvo.com {category} {location}"),
                    SourceTarget(source_type="professional_directory", label="Bar association", query=f"{category} {location} bar association"),
                ]
            )
        if self._is_home_service(category):
            targets.extend(
                [
                    SourceTarget(source_type="professional_directory", label="BBB", query=f"site:bbb.org {category} {location}"),
                    SourceTarget(source_type="government_license_registry", label="License lookup", query=f"{category} {location} license"),
                ]
            )
        if self._is_india_location(location):
            targets.extend(
                [
                    SourceTarget(source_type="directory", label="Justdial", query=f"site:justdial.com {category} {location}"),
                    SourceTarget(source_type="directory", label="Sulekha", query=f"site:sulekha.com {category} {location}"),
                    SourceTarget(source_type="general_search", label="Google Business style", query=f"{category} {location} reviews phone address"),
                    SourceTarget(source_type="government_license_registry", label="India registration lookup", query=f"{category} {location} registration license"),
                ]
            )
            if self._is_healthcare(category):
                targets.extend(
                    [
                        SourceTarget(source_type="professional_directory", label="Practo", query=f"site:practo.com {category} {location}"),
                        SourceTarget(source_type="professional_directory", label="Lybrate", query=f"site:lybrate.com {category} {location}"),
                    ]
                )
            if self._is_legal(category):
                targets.extend(
                    [
                        SourceTarget(source_type="professional_directory", label="Bar Council", query=f"{category} {location} bar council enrollment"),
                        SourceTarget(source_type="professional_directory", label="Legal directories India", query=f"{category} {location} legal directory"),
                    ]
                )
            if self._is_home_service(category):
                targets.append(
                    SourceTarget(source_type="directory", label="IndiaMART", query=f"site:indiamart.com {category} {location}")
                )
            if any(term in category for term in ["school", "hospital", "restaurant"]):
                targets.append(
                    SourceTarget(source_type="professional_directory", label="IndiaFilings/MCA context", query=f"{category} {location} company registration India")
                )
        targets.extend(
            [
                SourceTarget(
                    source_type="general_search",
                    label="Nearby discovery",
                    query=f"{category} near {location}",
                ),
                SourceTarget(
                    source_type="official_website",
                    label="Official contact pages",
                    query=f"{category} {location} contact",
                ),
                SourceTarget(
                    source_type="review_platform",
                    label="Angi",
                    query=f"site:angi.com {category} {location}",
                ),
                SourceTarget(
                    source_type="social_profile",
                    label="Facebook",
                    query=f"site:facebook.com {category} {location}",
                ),
            ]
        )
        return targets[:max_targets]

    def _is_healthcare(self, category: str) -> bool:
        return any(term in category for term in ["cardiologist", "dentist", "doctor", "physician", "medical", "health"])

    def _is_legal(self, category: str) -> bool:
        return any(term in category for term in ["lawyer", "attorney", "legal", "law"])

    def _is_home_service(self, category: str) -> bool:
        return any(term in category for term in ["roof", "plumb", "contractor", "hvac", "electric"])

    def _is_india_location(self, location: str) -> bool:
        terms = [
            "india",
            "tamil nadu",
            "chennai",
            "coimbatore",
            "madurai",
            "trichy",
            "salem",
            "tirunelveli",
            "vellore",
            "erode",
            "thanjavur",
            "hosur",
        ]
        return any(term in location.lower() for term in terms)
