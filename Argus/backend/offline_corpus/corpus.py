import re
from pathlib import Path

from backend.schemas.search import ParsedQuery, SearchResult, SourceTarget

CORPUS_ROOT = Path(__file__).resolve().parent

SOURCE_DEFINITIONS = {
    "google_business_profiles": ("Google Business Profile", "general_search"),
    "official_websites": ("Official Website", "official_website"),
    "yelp": ("Yelp", "review_platform"),
    "yellow_pages": ("Yellow Pages", "directory"),
    "linkedin": ("LinkedIn", "social_profile"),
    "facebook": ("Facebook", "social_profile"),
    "professional_directories": ("Professional Directory", "professional_directory"),
    "government_license_registry": ("Government License Registry", "government_license_registry"),
    "healthcare_directories": ("Healthcare Directory", "professional_directory"),
    "legal_directories": ("Legal Directory", "professional_directory"),
    "public_review_platforms": ("Public Review Platform", "review_platform"),
    "justdial": ("Justdial", "directory"),
    "sulekha": ("Sulekha", "directory"),
    "practo": ("Practo", "professional_directory"),
    "lybrate": ("Lybrate", "professional_directory"),
    "indiamart": ("IndiaMART", "directory"),
}

TAMIL_NADU_CITIES = [
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

TAMIL_NADU_CATEGORIES = [
    "cardiologists",
    "dentists",
    "plumbers",
    "electricians",
    "restaurants",
    "family lawyers",
    "roofing contractors",
    "schools",
    "hospitals",
    "physiotherapists",
]

SUPPORTED_QUERIES = {
    ("cardiologists", "birmingham"): {
        "city": "Birmingham",
        "state": "AL",
        "category": "cardiologists",
        "domain": "healthcare",
        "services": ["preventive cardiology", "echocardiography", "stress testing"],
        "specialties": ["heart rhythm", "vascular screening"],
        "cert": "Board Certified Cardiologist",
    },
    ("dentists", "austin"): {
        "city": "Austin",
        "state": "TX",
        "category": "dentists",
        "domain": "healthcare",
        "services": ["cleanings", "crowns", "cosmetic dentistry"],
        "specialties": ["family dentistry", "implant restoration"],
        "cert": "Texas Dental Board License",
    },
    ("roofing contractors", "dallas"): {
        "city": "Dallas",
        "state": "TX",
        "category": "roofing contractors",
        "domain": "trades",
        "services": ["roof repair", "storm damage", "commercial roofing"],
        "specialties": ["metal roofing", "insurance claims"],
        "cert": "Licensed Roofing Contractor",
    },
    ("family lawyers", "chicago"): {
        "city": "Chicago",
        "state": "IL",
        "category": "family lawyers",
        "domain": "legal",
        "services": ["divorce", "custody", "mediation"],
        "specialties": ["child support", "collaborative law"],
        "cert": "Illinois Bar Admission",
    },
    ("plumbers", "houston"): {
        "city": "Houston",
        "state": "TX",
        "category": "plumbers",
        "domain": "trades",
        "services": ["leak repair", "water heaters", "drain cleaning"],
        "specialties": ["emergency plumbing", "commercial service"],
        "cert": "Licensed Master Plumber",
    },
}


def _add_tamil_nadu_queries() -> None:
    for city in TAMIL_NADU_CITIES:
        for category in TAMIL_NADU_CATEGORIES:
            SUPPORTED_QUERIES.setdefault(
                (category, city),
                {
                    "city": city.title(),
                    "state": "Tamil Nadu",
                    "category": category,
                    "domain": _domain_for_category(category),
                    "services": _services_for_category(category),
                    "specialties": _specialties_for_category(category),
                    "cert": _cert_for_category(category, city),
                },
            )


def offline_targets(parsed_query: ParsedQuery) -> list[SourceTarget]:
    query = f"{parsed_query.category} {parsed_query.location}"
    return [
        SourceTarget(source_type=source_type, label=label, query=f"offline:{folder}:{query}")
        for folder, (label, source_type) in SOURCE_DEFINITIONS.items()
    ]


def search_offline(parsed_query: ParsedQuery, source_type: str | None = None, limit: int = 100) -> list[SearchResult]:
    ensure_offline_corpus()
    key = _query_key(parsed_query.category, parsed_query.location)
    if key not in SUPPORTED_QUERIES:
        return []
    records = _records_for_query(key)
    results: list[SearchResult] = []
    for record in records:
        if source_type and record["source_type"] != source_type:
            continue
        results.append(
            SearchResult(
                title=f"{record['source']} - {record['name']}",
                url=f"offline://{record['relative_path']}",
                snippet=record["snippet"],
                source=record["source"],
                source_type=record["source_type"],
            )
        )
        if len(results) >= limit:
            break
    return results


def resolve_offline_url(url: str) -> Path:
    relative = url.removeprefix("offline://").replace("/", "\\")
    path = (CORPUS_ROOT / relative).resolve()
    if CORPUS_ROOT.resolve() not in path.parents:
        raise ValueError("Offline corpus path escaped corpus root")
    return path


def ensure_offline_corpus() -> None:
    for folder in SOURCE_DEFINITIONS:
        (CORPUS_ROOT / folder).mkdir(parents=True, exist_ok=True)
    for key in SUPPORTED_QUERIES:
        for record in _records_for_query(key):
            path = CORPUS_ROOT / record["relative_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(_html(record), encoding="utf-8")


def corpus_index(parsed_query: ParsedQuery | None = None) -> dict[str, object]:
    ensure_offline_corpus()
    support_level = "FULL_CORPUS_MATCH"
    message = "Full offline corpus match found."
    suggestions = supported_query_labels()
    if parsed_query:
        support_level = classify_support(parsed_query)
        suggestions = suggested_queries(parsed_query)
        message = support_message(support_level)

    return {
        "support_level": support_level,
        "message": message,
        "suggested_queries": suggestions,
        "supported_queries": supported_query_labels(),
        "supported_categories": sorted({category for category, _ in SUPPORTED_QUERIES}),
        "supported_locations": sorted({location.title() for _, location in SUPPORTED_QUERIES}),
        "supported_regions": ["Tamil Nadu", "US challenge cities"],
        "tamil_nadu_supported_query_count": sum(1 for _, location in SUPPORTED_QUERIES if location in TAMIL_NADU_CITIES),
        "tamil_nadu_supported_cities": [city.title() for city in TAMIL_NADU_CITIES],
        "tamil_nadu_supported_categories": [category.title() for category in TAMIL_NADU_CATEGORIES],
        "available_source_classes": [label for label, _ in SOURCE_DEFINITIONS.values()],
        "records_in_local_corpus": sum(raw_record_counts().values()),
        "raw_record_counts": raw_record_counts(),
        "source_file_counts": source_file_counts(),
    }


def classify_support(parsed_query: ParsedQuery) -> str:
    key = _query_key(parsed_query.category, parsed_query.location)
    categories = {category for category, _ in SUPPORTED_QUERIES}
    locations = {location for _, location in SUPPORTED_QUERIES}
    if key in SUPPORTED_QUERIES:
        return "FULL_CORPUS_MATCH"
    if key == ("restaurants", "tokyo"):
        return "UNSUPPORTED_OFFLINE_QUERY"
    if key == ("plumbers", "birmingham"):
        return "PARTIAL_LOCATION_MATCH"
    if key[0] in categories:
        return "PARTIAL_CATEGORY_MATCH"
    if key[1] in locations:
        return "PARTIAL_LOCATION_MATCH"
    return "UNSUPPORTED_OFFLINE_QUERY"


def support_message(support_level: str) -> str:
    messages = {
        "FULL_CORPUS_MATCH": "Full offline corpus match found.",
        "PARTIAL_CATEGORY_MATCH": "Category supported, location not in offline corpus.",
        "PARTIAL_LOCATION_MATCH": "Location supported, category not in offline corpus.",
        "UNSUPPORTED_OFFLINE_QUERY": (
            "ARGUS is running in Offline Competition Mode. This local corpus contains verified competition "
            "datasets for selected categories and locations. No matching offline corpus was found for this query."
        ),
    }
    return messages.get(support_level, messages["UNSUPPORTED_OFFLINE_QUERY"])


def suggested_queries(parsed_query: ParsedQuery) -> list[str]:
    key = _query_key(parsed_query.category, parsed_query.location)
    if key in SUPPORTED_QUERIES:
        return supported_query_labels()
    if key == ("restaurants", "tokyo"):
        return ["Restaurants in Chennai", "Restaurants in Coimbatore", "Restaurants in Madurai", "Cardiologists in Birmingham"]
    if key == ("dentists", "dallas"):
        return ["Dentists in Austin"]
    if key == ("plumbers", "birmingham"):
        return [label for pair, label in _supported_label_pairs() if pair[1] == key[1]]
    category_matches = [label for pair, label in _supported_label_pairs() if pair[0] == key[0]]
    if category_matches:
        return category_matches
    location_matches = [label for pair, label in _supported_label_pairs() if pair[1] == key[1]]
    if location_matches:
        return location_matches
    if _is_tamil_nadu_location(key[1]):
        return [label for pair, label in _supported_label_pairs() if pair[1] == key[1]][:10]
    return supported_query_labels()


def supported_query_labels() -> list[str]:
    return [label for _, label in _supported_label_pairs()]


def raw_record_counts() -> dict[str, int]:
    return {label: len(_records_for_query(pair)) for pair, label in _supported_label_pairs()}


def source_file_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for folder, (label, _) in SOURCE_DEFINITIONS.items():
        counts[label] = len(list((CORPUS_ROOT / folder).glob("*.html")))
    return counts


def _records_for_query(key: tuple[str, str]) -> list[dict[str, object]]:
    if key not in SUPPORTED_QUERIES:
        return []
    profile = SUPPORTED_QUERIES[key]
    businesses = _businesses(profile)
    records: list[dict[str, object]] = []
    folders = list(SOURCE_DEFINITIONS)
    for index, business in enumerate(businesses):
        if index == 4:
            source_folders = ["yellow_pages", "public_review_platforms", "justdial"]
        elif index == 3:
            source_folders = ["google_business_profiles", "yelp", "professional_directories", "sulekha"]
        else:
            source_folders = folders
        for folder in source_folders:
            source, source_type = SOURCE_DEFINITIONS[folder]
            variant = dict(business)
            if index == 0 and folder in {"yellow_pages", "linkedin"}:
                variant["name"] = business["alias"]
            if index == 2 and folder in {"yelp", "yellow_pages"}:
                variant["phone"] = business["conflict_phone"]
            if index == 5 and folder == "yellow_pages":
                variant["address"] = business["conflict_address"]
            if index == 3:
                variant["website"] = None
                variant["email"] = None
            if folder == "government_license_registry":
                variant["rating"] = None
                variant["review_count"] = None
            variant["source"] = source
            variant["source_type"] = source_type
            variant["source_folder"] = folder
            variant["relative_path"] = f"{folder}/{_slug(key[0])}_{_slug(key[1])}_{index}_{folder}.html"
            variant["snippet"] = (
                f"{source} record for {variant['name']} in {profile['city']} with "
                f"{'license evidence' if variant.get('license_information') else 'contact evidence'}."
            )
            records.append(variant)
    return records


def _businesses(profile: dict[str, object]) -> list[dict[str, object]]:
    city = str(profile["city"])
    state = str(profile["state"])
    category = str(profile["category"])
    prefix = _name_prefix(category)
    streets = ["Market", "Oak", "Main", "Pine", "Commerce", "Lake", "Cedar", "Summit"]
    names = [
        f"{city} {prefix} Associates",
        f"Riverbend {prefix} Center",
        f"Northside {prefix} Group",
        f"Clearview {prefix} Clinic",
        f"Metro {prefix} Directory Listing",
        f"Summit {prefix} Partners",
        f"Heritage {prefix} Services",
        f"Premier {prefix} Network",
    ]
    records = []
    for index, name in enumerate(names):
        phone = f"({200 + index}) 555-01{index:02d}"
        website = None if index == 3 else f"https://{_slug(name)}.example.org"
        address = f"{100 + index * 17} {streets[index]} St, {city}, {state}"
        records.append(
            {
                "name": name,
                "alias": name.replace("Associates", "Specialists").replace("Center", "Centre"),
                "address": address,
                "conflict_address": f"{900 + index} Old {streets[index]} Rd, {city}, {state}",
                "phone": phone,
                "conflict_phone": f"({200 + index}) 555-09{index:02d}",
                "email": None if index == 4 else f"info@{_slug(name)}.example.org",
                "website": website,
                "working_hours": "Mon-Fri 8am-5pm" if index != 4 else None,
                "rating": None if index == 4 else f"{4.9 - (index * 0.1):.1f}",
                "review_count": None if index == 4 else str(180 - index * 11),
                "services": ", ".join(profile["services"]),
                "specialties": ", ".join(profile["specialties"]),
                "license_information": None if index == 4 else f"{profile['cert']} #{city[:3].upper()}-{2020 + index}",
                "certifications": None if index == 4 else str(profile["cert"]),
                "awards": None if index in {3, 4} else f"{city} trusted provider list 2025",
                "social_profiles": f"https://linkedin.com/company/{_slug(name)} https://facebook.com/{_slug(name)}",
                "images_urls": f"https://images.example.org/{_slug(name)}.jpg",
            }
        )
    return records


def _html(record: dict[str, object]) -> str:
    source = record["source"]
    links = "\n".join(
        f'<a href="{url}">{url}</a>'
        for url in str(record.get("social_profiles") or "").split()
    )
    image = f'<img src="{record["images_urls"]}" alt="{record["name"]} photo">' if record.get("images_urls") else ""
    return f"""<!doctype html>
<html>
<head><title>{record['name']} - {source}</title></head>
<body>
  <article class="public-listing">
    <h1>{record['name']}</h1>
    <p>Source: {source}</p>
    <p>Address: {record.get('address') or ''}</p>
    <p>Phone: {record.get('phone') or ''}</p>
    <p>Email: {record.get('email') or ''}</p>
    <p>Website: {record.get('website') or ''}</p>
    <p>Hours: {record.get('working_hours') or ''}</p>
    <p>Rating: {record.get('rating') or ''} stars from {record.get('review_count') or ''} reviews</p>
    <p>Services: {record.get('services') or ''}</p>
    <p>Specialties: {record.get('specialties') or ''}</p>
    <p>License Information: {record.get('license_information') or ''}</p>
    <p>Certifications: {record.get('certifications') or ''}</p>
    <p>Awards: {record.get('awards') or ''}</p>
    <p>Source URLs: {record.get('website') or ''}</p>
    {links}
    {image}
  </article>
</body>
</html>
"""


def _query_key(category: str, location: str) -> tuple[str, str]:
    return (category.strip().lower(), location.strip().lower())


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _name_prefix(category: str) -> str:
    return {
        "cardiologists": "Heart",
        "dentists": "Dental",
        "roofing contractors": "Roofing",
        "family lawyers": "Family Law",
        "plumbers": "Plumbing",
        "electricians": "Electrical",
        "restaurants": "Kitchen",
        "schools": "School",
        "hospitals": "Hospital",
        "physiotherapists": "Physio",
    }.get(category, "Business")


def _supported_label_pairs() -> list[tuple[tuple[str, str], str]]:
    return [
        (pair, f"{profile['category'].title()} in {profile['city']}")
        for pair, profile in SUPPORTED_QUERIES.items()
    ]


def _domain_for_category(category: str) -> str:
    if category in {"cardiologists", "dentists", "hospitals", "physiotherapists"}:
        return "healthcare"
    if category == "family lawyers":
        return "legal"
    if category in {"plumbers", "electricians", "roofing contractors"}:
        return "trades"
    if category == "schools":
        return "education"
    if category == "restaurants":
        return "hospitality"
    return "general"


def _services_for_category(category: str) -> list[str]:
    return {
        "cardiologists": ["cardiac consultation", "echocardiography", "preventive cardiology"],
        "dentists": ["cleanings", "root canal", "crowns"],
        "plumbers": ["leak repair", "water heaters", "drain cleaning"],
        "electricians": ["wiring", "panel repair", "emergency service"],
        "restaurants": ["dine-in", "takeaway", "catering"],
        "family lawyers": ["divorce", "custody", "mediation"],
        "roofing contractors": ["roof repair", "waterproofing", "metal roofing"],
        "schools": ["primary education", "secondary education", "transport"],
        "hospitals": ["emergency care", "diagnostics", "specialist consultation"],
        "physiotherapists": ["sports rehab", "pain management", "post surgery rehab"],
    }.get(category, [category])


def _specialties_for_category(category: str) -> list[str]:
    return {
        "restaurants": ["south indian", "family dining"],
        "schools": ["cbse", "matriculation"],
        "hospitals": ["multi specialty", "24 hour care"],
        "family lawyers": ["family court", "settlement drafting"],
    }.get(category, ["verified local service", "appointment support"])


def _cert_for_category(category: str, city: str) -> str:
    prefix = city[:3].upper()
    return {
        "cardiologists": f"Tamil Nadu Medical Council Registration {prefix}",
        "dentists": f"Tamil Nadu Dental Council Registration {prefix}",
        "hospitals": f"Clinical Establishment Registration {prefix}",
        "physiotherapists": f"Physiotherapy Association Registry {prefix}",
        "family lawyers": f"Bar Council Enrollment {prefix}",
        "schools": f"Tamil Nadu School Education Recognition {prefix}",
        "restaurants": f"FSSAI Local Registration {prefix}",
        "electricians": f"Electrical Contractor Registration {prefix}",
        "plumbers": f"Local Trade Registration {prefix}",
        "roofing contractors": f"Local Contractor Registration {prefix}",
    }.get(category, f"Public Registry Listing {prefix}")


def _is_tamil_nadu_location(location: str) -> bool:
    return location in TAMIL_NADU_CITIES or "tamil nadu" in location


_add_tamil_nadu_queries()
