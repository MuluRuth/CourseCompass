# CourseCompass

TU Wien elective course recommender system.

## Setup

```bash
# 1 — Install dependencies
pip install -r requirements.txt

# 2 — Run the app
python app.py
```

Then open http://localhost:5000 in your browser.

## Project structure

```
coursecompass/
├── app.py           ← Flask backend (routes + course cache)
├── recommender.py   ← scoring logic (S = w1*C + w2*P + w3*D)
├── tiss.py          ← TISS API fetcher and course normalizer
├── requirements.txt
└── templates/
    └── index.html   ← frontend (HTML + JS)
```

## How it works

1. On startup, `app.py` checks for `courses_cache.json`
2. If cache exists → loads from it (fast)
3. If not → fetches from TISS API and saves cache
4. Admin dashboard has a "Refresh from TISS" button to update the cache

## Scoring formula

**Relevance mode:**  S = 0.6·C + 0.4·P
**Diversity mode:**  S = 0.3·C + 0.1·P + 0.6·D

Where:
- C = content match (domain overlap with completed courses)
- P = popularity (normalized enrollment)
- D = diversity bonus (rewards unexplored domains)

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/courses | Full course catalog |
| POST | /api/recommend | Get recommendations |
| GET | /api/stats | Admin statistics |
| POST | /api/refresh | Re-fetch from TISS |
