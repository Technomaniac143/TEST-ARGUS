from backend.schemas.extraction import ExtractedBusiness, FieldEvidence
from backend.schemas.search import ParsedQuery

SOURCE_URLS = {
    "Official Website": "https://demo.argus.local/official",
    "Google Business Profile": "https://demo.argus.local/google-business",
    "LinkedIn": "https://demo.argus.local/linkedin",
    "Yelp": "https://demo.argus.local/yelp",
    "Yellow Pages": "https://demo.argus.local/yellow-pages",
    "Professional Directory": "https://demo.argus.local/professional-directory",
    "Government License Registry": "https://demo.argus.local/license-registry",
    "Facebook": "https://demo.argus.local/facebook",
    "Industry Association": "https://demo.argus.local/industry-association",
}

QUERY_CONFIG = {
    ("cardiologists", "birmingham"): {
        "prefixes": ["Birmingham Heart", "Crestline Cardiology", "Southern Pulse", "Magic City Cardiac", "Red Mountain Heart", "Five Points Cardiology", "Homewood Heart", "Avondale Vascular"],
        "street": "Medical Center Dr",
        "city": "Birmingham",
        "state": "AL",
        "domain": "heart",
        "services": "cardiology, echocardiography, vascular screening",
        "specialties": "preventive cardiology, cardiac imaging",
        "license": "AL-MED",
        "certification": "Board Certified Cardiologist",
    },
    ("dentists", "austin"): {
        "prefixes": ["Austin Smile Studio", "Barton Springs Dental", "Lone Star Dental", "Zilker Family Dentistry", "Capital City Dental", "South Congress Smiles", "Cedar Bend Dental", "Lake Austin Dental"],
        "street": "Congress Ave",
        "city": "Austin",
        "state": "TX",
        "domain": "dental",
        "services": "general dentistry, crowns, cleanings",
        "specialties": "cosmetic dentistry, preventive care",
        "license": "TX-DDS",
        "certification": "Texas Dental Board Active License",
    },
    ("roofing contractors", "dallas"): {
        "prefixes": ["Dallas Premier Roofing", "Oak Cliff Roof Works", "Lone Star Roofing", "Deep Ellum Exteriors", "North Dallas Roofing", "White Rock Roofers", "Trinity Storm Repair", "Bishop Arts Roofing"],
        "street": "Industrial Blvd",
        "city": "Dallas",
        "state": "TX",
        "domain": "roof",
        "services": "roof repair, storm damage, inspections",
        "specialties": "commercial roofing, asphalt shingles",
        "license": "TX-RFC",
        "certification": "Certified Roofing Contractor",
    },
    ("family lawyers", "chicago"): {
        "prefixes": ["Chicago Family Law Group", "Lincoln Park Legal", "Lakefront Family Attorneys", "Loop Divorce Counsel", "Northside Family Law", "Hyde Park Legal", "Wicker Park Counsel", "Gold Coast Family Lawyers"],
        "street": "LaSalle St",
        "city": "Chicago",
        "state": "IL",
        "domain": "legal",
        "services": "family law, custody, divorce mediation",
        "specialties": "custody agreements, mediation",
        "license": "IL-BAR",
        "certification": "Illinois Bar Active Registration",
    },
    ("plumbers", "houston"): {
        "prefixes": ["Houston Reliable Plumbing", "Bayou City Plumbing", "Heights Pipe Pros", "Space City Plumbers", "Memorial Plumbing", "Montrose Drain Service", "Galleria Plumbing", "East End Pipeworks"],
        "street": "Main St",
        "city": "Houston",
        "state": "TX",
        "domain": "plumb",
        "services": "leak repair, drain cleaning, water heaters",
        "specialties": "emergency plumbing, slab leak detection",
        "license": "TX-PLB",
        "certification": "Texas Responsible Master Plumber",
    },
}

DEMO_RECORDS: dict[str, ExtractedBusiness] = {}


def supported_query_key(parsed_query: ParsedQuery) -> tuple[str, str] | None:
    key = (parsed_query.category.lower(), parsed_query.location.lower())
    if key in QUERY_CONFIG:
        return key
    return None


def demo_search_results(parsed_query: ParsedQuery) -> list[tuple[str, str, str]]:
    key = supported_query_key(parsed_query) or ("cardiologists", "birmingham")
    records = _records_for_key(key)
    return [
        (
            record.name or "Unknown business",
            record.source_url or f"demo://{key[0]}/{key[1]}/{index}",
            f"Demo intelligence profile with {len(record.evidence)} evidence receipts from source-class research.",
        )
        for index, record in enumerate(records)
    ]


def get_demo_business(url: str) -> ExtractedBusiness | None:
    return DEMO_RECORDS.get(url)


def _records_for_key(key: tuple[str, str]) -> list[ExtractedBusiness]:
    config = QUERY_CONFIG[key]
    records = [_business(config, index, key) for index in range(8)]
    records.append(_duplicate_business(config, key))
    records[2] = _conflict_business(config, 2, key)
    records[3] = _missing_website_business(config, 3, key)
    records[4] = _weak_evidence_business(config, 4, key)
    for record in records:
        if record.source_url:
            DEMO_RECORDS[record.source_url] = record
    return records


def _business(config: dict[str, str | list[str]], index: int, key: tuple[str, str]) -> ExtractedBusiness:
    name = config["prefixes"][index] if isinstance(config["prefixes"], list) else f"Business {index}"
    phone = f"205-55{index}-01{index}{index}" if config["city"] == "Birmingham" else f"214-55{index}-01{index}{index}"
    address = f"{1100 + index * 37} {config['street']}, {config['city']}, {config['state']}"
    website = f"https://{_slug(name)}.{config['domain']}.example"
    email = f"info@{_slug(name)}.{config['domain']}.example"
    url = f"demo://{key[0]}/{key[1]}/{index}"
    evidence = _strong_evidence(name, phone, address, website, email, config, index)
    return ExtractedBusiness(
        name=name,
        category=key[0],
        location=key[1],
        phone=phone,
        address=address,
        website=website,
        email=email,
        services=str(config["services"]),
        working_hours="Mon-Fri 8am-5pm",
        source_url=url,
        source_name="Demo Research Dataset",
        evidence=evidence,
    )


def _strong_evidence(name: str, phone: str, address: str, website: str, email: str, config: dict[str, str | list[str]], index: int) -> list[FieldEvidence]:
    license_value = f"{config['license']}-{7400 + index}"
    return [
        _ev("name", name, "Official Website"),
        _ev("name", name, "Google Business Profile"),
        _ev("phone", phone, "Official Website"),
        _ev("phone", phone, "Google Business Profile"),
        _ev("phone", phone, "LinkedIn"),
        _ev("address", address, "Official Website"),
        _ev("address", address, "Yelp"),
        _ev("address", address, "Yellow Pages"),
        _ev("website", website, "Google Business Profile"),
        _ev("website", website, "Professional Directory"),
        _ev("email", email, "Official Website"),
        _ev("services", str(config["services"]), "Official Website"),
        _ev("specialties", str(config["specialties"]), "Industry Association"),
        _ev("working_hours", "Mon-Fri 8am-5pm", "Google Business Profile"),
        _ev("rating", "4.8", "Google Business Profile"),
        _ev("review_count", str(80 + index * 13), "Yelp"),
        _ev("license_information", license_value, "Government License Registry"),
        _ev("license_information", license_value, "Professional Directory"),
        _ev("certifications", str(config["certification"]), "Industry Association"),
        _ev("awards", "Top Local Provider", "Professional Directory"),
        _ev("social_profiles", f"https://facebook.example/{_slug(name)}", "Facebook"),
    ]


def _duplicate_business(config: dict[str, str | list[str]], key: tuple[str, str]) -> ExtractedBusiness:
    original = _business(config, 0, key)
    duplicate = original.model_copy(deep=True)
    duplicate.name = f"{original.name} Specialists"
    duplicate.source_url = f"demo://{key[0]}/{key[1]}/duplicate"
    duplicate.evidence = [
        _ev("name", duplicate.name or "", "Yellow Pages"),
        _ev("phone", duplicate.phone or "", "Yellow Pages"),
        _ev("address", duplicate.address or "", "Yellow Pages"),
        _ev("website", duplicate.website or "", "Professional Directory"),
    ]
    return duplicate


def _conflict_business(config: dict[str, str | list[str]], index: int, key: tuple[str, str]) -> ExtractedBusiness:
    record = _business(config, index, key)
    conflict_phone = record.phone[:-2] + "99" if record.phone else "205-555-0199"
    record.evidence.append(_ev("phone", conflict_phone, "Yelp"))
    record.evidence.append(_ev("phone", conflict_phone, "Yellow Pages"))
    return record


def _missing_website_business(config: dict[str, str | list[str]], index: int, key: tuple[str, str]) -> ExtractedBusiness:
    record = _business(config, index, key)
    record.website = None
    record.evidence = [item for item in record.evidence if item.field != "website"]
    return record


def _weak_evidence_business(config: dict[str, str | list[str]], index: int, key: tuple[str, str]) -> ExtractedBusiness:
    record = _business(config, index, key)
    record.website = None
    record.email = None
    record.evidence = [
        _ev("name", record.name or "", "Yellow Pages"),
        _ev("phone", record.phone or "", "Yellow Pages"),
        _ev("address", record.address or "", "Yellow Pages"),
    ]
    return record


def _ev(field: str, value: str, source: str) -> FieldEvidence:
    return FieldEvidence(field=field, value=value, source=source, url=SOURCE_URLS[source])


def _slug(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "")
