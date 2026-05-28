from flask import Flask, jsonify, request, render_template
from recommender import score_courses
from tiss import fetch_all_courses
import json
import os

app = Flask(__name__)

# ── Course cache ──────────────────────────────────────────────────────────────
# Courses are loaded once at startup and cached in memory.
# In production you would reload this nightly or on demand.
COURSES = []
CACHE_FILE = "courses_cache.json"


def load_courses():
    """
    Load courses from cache file if it exists,
    otherwise fetch from TISS API and save to cache.
    """
    global COURSES

    if os.path.exists(CACHE_FILE):
        print("Loading courses from cache...")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            COURSES = json.load(f)
        print(f"Loaded {len(COURSES)} courses from cache.")
    else:
        print("Cache not found. Fetching from TISS API...")
        COURSES = fetch_all_courses(semester="2025W")

        if COURSES:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(COURSES, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(COURSES)} courses to cache.")
        else:
            print("TISS fetch returned no courses. Using fallback dataset.")
            COURSES = get_fallback_courses()


def get_fallback_courses():
    """
    Hardcoded fallback dataset in case TISS API is unavailable.
    Based on the CourseCompass paper mock dataset.
    """
    return [
        {"id":"AI101","name":"Introduction to Machine Learning","ects":4.5,"domain":"Artificial Intelligence","difficulty":2,"language":"English","semester":"WS","prerequisites":[],"sdg":True,"sdgTags":["SDG 4","SDG 9"],"programs":["Business Informatics","Computer Science","Data Science"],"enrollment":180,"description":"Core ML algorithms and model evaluation."},
        {"id":"AI201","name":"Deep Learning","ects":4.5,"domain":"Artificial Intelligence","difficulty":3,"language":"English","semester":"SS","prerequisites":["AI101"],"sdg":True,"sdgTags":["SDG 9"],"programs":["Computer Science","Data Science"],"enrollment":120,"description":"Neural networks, CNNs, RNNs, and transformers."},
        {"id":"AI301","name":"Natural Language Processing","ects":3.0,"domain":"Artificial Intelligence","difficulty":3,"language":"English","semester":"WS","prerequisites":["AI101"],"sdg":False,"sdgTags":[],"programs":["Computer Science","Data Science"],"enrollment":95,"description":"Text processing and language models."},
        {"id":"AI501","name":"Recommender Systems","ects":3.0,"domain":"Artificial Intelligence","difficulty":2,"language":"English","semester":"SS","prerequisites":["AI101"],"sdg":True,"sdgTags":["SDG 4","SDG 10"],"programs":["Business Informatics","Computer Science","Data Science"],"enrollment":85,"description":"CF, content-based and hybrid approaches."},
        {"id":"SE101","name":"Software Architecture","ects":4.5,"domain":"Software Engineering","difficulty":2,"language":"English","semester":"WS","prerequisites":[],"sdg":False,"sdgTags":[],"programs":["Business Informatics","Computer Science","Software Engineering"],"enrollment":140,"description":"Design patterns and architectural styles."},
        {"id":"SE201","name":"Agile Development Methods","ects":3.0,"domain":"Software Engineering","difficulty":1,"language":"English","semester":"WS+SS","prerequisites":[],"sdg":False,"sdgTags":[],"programs":["Business Informatics","Software Engineering"],"enrollment":130,"description":"Scrum, Kanban, and agile project management."},
        {"id":"SE601","name":"Cloud Computing","ects":4.5,"domain":"Software Engineering","difficulty":2,"language":"English","semester":"WS+SS","prerequisites":[],"sdg":False,"sdgTags":[],"programs":["Computer Science","Business Informatics"],"enrollment":160,"description":"AWS, Azure, GCP, serverless, and microservices."},
        {"id":"ES101","name":"Technology Ethics","ects":3.0,"domain":"Ethics and Society","difficulty":1,"language":"English","semester":"WS+SS","prerequisites":[],"sdg":True,"sdgTags":["SDG 4","SDG 16"],"programs":["Business Informatics","Computer Science","Data Science","Software Engineering"],"enrollment":55,"description":"Ethical frameworks for technology development."},
        {"id":"ES401","name":"AI Ethics and Fairness","ects":3.0,"domain":"Ethics and Society","difficulty":2,"language":"English","semester":"WS","prerequisites":[],"sdg":True,"sdgTags":["SDG 4","SDG 10","SDG 16"],"programs":["Business Informatics","Computer Science","Data Science"],"enrollment":65,"description":"Bias, fairness, and accountability in AI."},
        {"id":"SU101","name":"Climate Informatics","ects":3.0,"domain":"Sustainable Engineering","difficulty":2,"language":"English","semester":"WS","prerequisites":[],"sdg":True,"sdgTags":["SDG 13","SDG 11","SDG 4"],"programs":["Business Informatics","Computer Science","Data Science"],"enrollment":48,"description":"Data-driven approaches to climate change."},
        {"id":"MS101","name":"Applied Statistics","ects":4.5,"domain":"Mathematics and Statistics","difficulty":2,"language":"English","semester":"WS","prerequisites":[],"sdg":False,"sdgTags":[],"programs":["Business Informatics","Data Science","Mathematics"],"enrollment":160,"description":"Probability, hypothesis testing, and regression."},
        {"id":"MS201","name":"Econometrics","ects":4.5,"domain":"Mathematics and Statistics","difficulty":3,"language":"English","semester":"SS","prerequisites":["MS101"],"sdg":False,"sdgTags":[],"programs":["Business Informatics","Mathematics"],"enrollment":95,"description":"Regression models, time series, and causal inference."},
        {"id":"DS101","name":"Data Visualization","ects":3.0,"domain":"Data Science","difficulty":1,"language":"English","semester":"WS+SS","prerequisites":[],"sdg":False,"sdgTags":[],"programs":["Business Informatics","Data Science","Computer Science"],"enrollment":155,"description":"Visual encoding, dashboards, and data storytelling."},
        {"id":"DS301","name":"Database Systems","ects":4.5,"domain":"Data Science","difficulty":2,"language":"English","semester":"WS+SS","prerequisites":[],"sdg":False,"sdgTags":[],"programs":["Business Informatics","Computer Science","Data Science","Software Engineering"],"enrollment":170,"description":"SQL, NoSQL, and query optimization."},
        {"id":"DS501","name":"Data Mining","ects":3.0,"domain":"Data Science","difficulty":2,"language":"English","semester":"WS","prerequisites":["MS101"],"sdg":False,"sdgTags":[],"programs":["Data Science","Business Informatics","Computer Science"],"enrollment":98,"description":"Pattern recognition, association rules, and clustering."},
    ]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the frontend."""
    return render_template("index.html")


@app.route("/api/courses", methods=["GET"])
def get_courses():
    """Return the full course catalog."""
    return jsonify({"courses": COURSES, "total": len(COURSES)})


@app.route("/api/recommend", methods=["POST"])
def recommend():
    """
    Return ranked course recommendations for a student.

    Expected JSON body:
    {
        "program": "Business Informatics",
        "completed_ids": ["AI101", "MS101"],
        "mode": "default",
        "num_results": 5
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    program = data.get("program", "")
    completed_ids = data.get("completed_ids", [])
    mode = data.get("mode", "default")
    num_results = int(data.get("num_results", 5))

    if not program:
        return jsonify({"error": "program is required"}), 400

    if mode not in ("default", "diversity"):
        return jsonify({"error": "mode must be 'default' or 'diversity'"}), 400

    num_results = max(3, min(num_results, 10))

    recommendations = score_courses(
        courses=COURSES,
        completed_ids=completed_ids,
        program=program,
        mode=mode,
    )

    return jsonify({
        "recommendations": recommendations[:num_results],
        "total_eligible": len(recommendations),
        "mode": mode,
        "program": program,
    })


@app.route("/api/refresh", methods=["POST"])
def refresh_courses():
    """
    Re-fetch courses from TISS API and update the cache.
    Call this from the admin dashboard to get fresh data.
    """
    global COURSES
    semester = request.get_json(silent=True) or {}
    sem = semester.get("semester", "2025W")

    print(f"Refreshing courses for semester {sem}...")
    fetched = fetch_all_courses(semester=sem)

    if fetched:
        COURSES = fetched
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(COURSES, f, ensure_ascii=False, indent=2)
        return jsonify({"message": f"Refreshed {len(COURSES)} courses", "total": len(COURSES)})
    else:
        return jsonify({"message": "TISS fetch failed, keeping existing courses", "total": len(COURSES)}), 500


@app.route("/api/stats", methods=["GET"])
def stats():
    """Return admin statistics about the course catalog."""
    if not COURSES:
        return jsonify({"error": "No courses loaded"}), 500

    domains = {}
    for course in COURSES:
        d = course["domain"]
        if d not in domains:
            domains[d] = {"count": 0, "total_enrollment": 0, "sdg_count": 0}
        domains[d]["count"] += 1
        domains[d]["total_enrollment"] += course["enrollment"]
        if course["sdg"]:
            domains[d]["sdg_count"] += 1

    for d in domains:
        domains[d]["avg_enrollment"] = round(
            domains[d]["total_enrollment"] / domains[d]["count"]
        )

    total_enrollment = sum(c["enrollment"] for c in COURSES)
    sdg_courses = sum(1 for c in COURSES if c["sdg"])

    return jsonify({
        "total_courses": len(COURSES),
        "sdg_courses": sdg_courses,
        "sdg_percentage": round(sdg_courses / len(COURSES) * 100),
        "avg_enrollment": round(total_enrollment / len(COURSES)),
        "domains": domains,
    })


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_courses()
    app.run(debug=True, port=5000)
