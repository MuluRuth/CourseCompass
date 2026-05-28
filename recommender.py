def score_courses(courses, completed_ids, program, mode="default"):
    """
    Score and rank eligible courses for a given student.

    Scoring formula:
      Relevance mode:  S = 0.6*C + 0.4*P
      Diversity mode:  S = 0.3*C + 0.1*P + 0.6*D

    Where:
      C = content match (domain overlap with completed courses)
      P = popularity signal (normalized enrollment)
      D = diversity bonus (rewards unexplored domains)
    """

    # get domains of completed courses
    completed_courses = [c for c in courses if c["id"] in completed_ids]
    completed_domains = set(c["domain"] for c in completed_courses)

    # max enrollment for normalization
    max_enrollment = max((c["enrollment"] for c in courses), default=1)

    # filter out completed courses and those with unmet prerequisites
    eligible = [
        c for c in courses
        if c["id"] not in completed_ids
        and all(p in completed_ids for p in c.get("prerequisites", []))
    ]

    if not eligible:
        return []

    scored = []
    for course in eligible:

        # C — content match score
        if not completed_domains:
            # cold start: use program affiliation
            C = 0.8 if program in course.get("programs", []) else 0.3
        else:
            C = 1.0 if course["domain"] in completed_domains else 0.2

        # P — normalized popularity
        P = course["enrollment"] / max_enrollment

        # D — diversity bonus (1 if domain not yet explored, else 0.3)
        D = 1.0 if (completed_domains and course["domain"] not in completed_domains) else 0.3

        # compute final score based on mode
        if mode == "default":
            score = 0.6 * C + 0.4 * P
        else:
            score = 0.3 * C + 0.1 * P + 0.6 * D

        # cap score at 1.0
        score = min(round(score, 4), 1.0)

        # build explanation
        reasons = []
        if not completed_domains:
            if program in course.get("programs", []):
                reasons.append(f"it is recommended for {program} students")
            else:
                reasons.append("it broadens your academic profile")
        else:
            if course["domain"] in completed_domains:
                reasons.append(f"it builds on your background in {course['domain']}")
            elif mode == "diversity":
                reasons.append(f"it expands your knowledge into {course['domain']}")

        if P > 0.5:
            reasons.append("it is popular among students")

        if not reasons:
            reasons.append("it aligns with your study program")

        explanation = "Suggested because " + ", ".join(reasons) + "."

        scored.append({**course, "score": score, "explanation": explanation})

    # sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
