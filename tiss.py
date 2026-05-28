import requests

BASE_URL = "https://tiss.tuwien.ac.at/api"

ORG_UNITS = ["E194", "E193", "E192", "E188", "E185"]

DOMAIN_MAP = {
    "machine learning": "Artificial Intelligence",
    "deep learning": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "neural": "Artificial Intelligence",
    "nlp": "Artificial Intelligence",
    "computer vision": "Artificial Intelligence",
    "recommender": "Artificial Intelligence",
    "software": "Software Engineering",
    "agile": "Software Engineering",
    "devops": "Software Engineering",
    "distributed": "Software Engineering",
    "testing": "Software Engineering",
    "cloud": "Software Engineering",
    "ethics": "Ethics and Society",
    "privacy": "Ethics and Society",
    "fairness": "Ethics and Society",
    "digital inclusion": "Ethics and Society",
    "sustainable": "Sustainable Engineering",
    "climate": "Sustainable Engineering",
    "green": "Sustainable Engineering",
    "energy": "Sustainable Engineering",
    "statistics": "Mathematics and Statistics",
    "econometrics": "Mathematics and Statistics",
    "linear algebra": "Mathematics and Statistics",
    "stochastic": "Mathematics and Statistics",
    "operations research": "Mathematics and Statistics",
    "signal": "Electrical Engineering",
    "embedded": "Electrical Engineering",
    "wireless": "Electrical Engineering",
    "data": "Data Science",
    "database": "Data Science",
    "visualization": "Data Science",
    "mining": "Data Science",
    "big data": "Data Science",
}

SDG_KEYWORDS = {
    "SDG 4": ["education", "learning", "quality", "skill"],
    "SDG 9": ["innovation", "infrastructure", "industry", "technology"],
    "SDG 10": ["inclusion", "inequality", "diversity", "fairness"],
    "SDG 11": ["sustainable cities", "urban", "community"],
    "SDG 12": ["consumption", "production", "sustainable", "green"],
    "SDG 13": ["climate", "carbon", "environment", "energy"],
    "SDG 16": ["justice", "institution", "privacy", "ethics", "governance"],
}


def get_courses_by_orgunit(org_code, semester="2025W"):
    url = f"{BASE_URL}/course/orgUnit/{org_code}"
    params = {"semester": semester}
    cookies = {"TISS_AUTH": "08057e41dbfbabd8f0696440338a0be557e8f69ff9a040e9f196c22747fe5d22"}

    try:
        response = requests.get(url, params=params, cookies=cookies, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        response.raise_for_status()
        data = response.json()
        return data.get("courses", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching org unit {org_code}: {e}")
        return []


def get_course_details(course_number, semester="2025W"):
    url = f"{BASE_URL}/course/{course_number}-{semester}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching course {course_number}: {e}")
        return {}


def guess_domain(title, description=""):
    text = (title + " " + description).lower()
    for keyword, domain in DOMAIN_MAP.items():
        if keyword in text:
            return domain
    return "Data Science"


def guess_sdg_tags(title, description=""):
    text = (title + " " + description).lower()
    tags = []
    for sdg, keywords in SDG_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            tags.append(sdg)
    return tags[:3]


def normalize_course(raw, semester="2025W"):
    title = raw.get("title", {})
    name = title.get("en") or title.get("de") or "Unknown Course"
    number = raw.get("courseNumber", "")
    ects = float(raw.get("ects", 3.0) or 3.0)
    lang = raw.get("teachingLanguage", "German")
    language = "English" if "en" in str(lang).lower() else "German"
    enrollment = int(raw.get("maxParticipants", 50) or 50)
    desc_raw = raw.get("description", {})
    description = desc_raw.get("en") or desc_raw.get("de") or ""
    sem_type = semester[-1]
    semester_label = "WS" if sem_type == "W" else "SS"
    domain = guess_domain(name, description)
    sdg_tags = guess_sdg_tags(name, description)
    return {
        "id": number,
        "name": name,
        "ects": round(ects, 1),
        "domain": domain,
        "difficulty": 2,
        "language": language,
        "semester": semester_label,
        "prerequisites": [],
        "sdg": len(sdg_tags) > 0,
        "sdgTags": sdg_tags,
        "programs": ["Business Informatics", "Computer Science"],
        "enrollment": enrollment,
        "description": description[:120] + "..." if len(description) > 120 else description,
    }


def fetch_all_courses(semester="2025W"):
    all_courses = []
    seen_ids = set()
    for org_code in ORG_UNITS:
        print(f"Fetching courses from org unit {org_code}...")
        raw_courses = get_courses_by_orgunit(org_code, semester)
        for raw in raw_courses:
            number = raw.get("courseNumber", "")
            if number and number not in seen_ids:
                seen_ids.add(number)
                course = normalize_course(raw, semester)
                all_courses.append(course)
    print(f"Total courses fetched: {len(all_courses)}")
    return all_courses