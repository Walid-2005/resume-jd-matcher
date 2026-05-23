"""
Evaluation module for the resume-job matching system.

Runs a suite of realistic test cases through the matcher, compares
actual match levels against expected levels, and prints a summary
report with accuracy metrics and observations.

Usage:
    python -m matcher.services.evaluation
"""
import os
import sys
import time

# ── Django bootstrap ──────────────────────────────────────────────────────
# Allow running as a standalone script from the project root.
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resume_matcher.settings")

import django  # noqa: E402
django.setup()

from matcher.services.matcher import JobMatcher  # noqa: E402

# ── Score-to-level mapping ────────────────────────────────────────────────
def score_to_level(score: int) -> str:
    """Convert a numeric match score to High / Medium / Low."""
    if score >= 70:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


# ── Test cases ────────────────────────────────────────────────────────────
TEST_CASES = [
    # ------------------------------------------------------------------ 1
    {
        "name": "Software Eng resume  →  Software Eng job",
        "expected": "High",
        "resume": (
            "Software Engineer with 4 years of experience building web "
            "applications. Proficient in Python, JavaScript, React, Node.js, "
            "and PostgreSQL. Built REST APIs using Django and Flask. Deployed "
            "services on AWS with Docker and Kubernetes. Familiar with CI/CD "
            "pipelines, Git, and Agile/Scrum methodologies. Improved API "
            "response time by 35%. BSc Computer Science."
        ),
        "job": (
            "We are looking for a Software Engineer with experience in "
            "Python, JavaScript, React, and Node.js. You will design and "
            "build REST APIs, work with PostgreSQL databases, and deploy "
            "on AWS using Docker. Experience with CI/CD, Git, and Agile "
            "practices is required. 3+ years of experience preferred."
        ),
    },
    # ------------------------------------------------------------------ 2
    {
        "name": "Data Scientist resume  →  Data Science job",
        "expected": "High",
        "resume": (
            "Data Scientist with 3 years of experience in machine learning "
            "and data analysis. Skilled in Python, pandas, NumPy, "
            "scikit-learn, TensorFlow, and SQL. Built predictive models "
            "that increased revenue by 15%. Created Tableau dashboards for "
            "executive reporting. MSc Statistics. Experienced with deep "
            "learning, NLP, and computer vision projects."
        ),
        "job": (
            "Seeking a Data Scientist proficient in Python, machine "
            "learning, deep learning, and SQL. Experience with pandas, "
            "NumPy, TensorFlow or PyTorch required. Must be able to build "
            "predictive models and create data visualisations with Tableau "
            "or Power BI. NLP experience is a plus. 2-5 years of experience."
        ),
    },
    # ------------------------------------------------------------------ 3
    {
        "name": "CS graduate resume  →  Hotel front desk job",
        "expected": "Low",
        "resume": (
            "Recent Computer Science graduate. Completed coursework in "
            "algorithms, data structures, and software engineering. "
            "Proficient in Python, Java, C++, and SQL. Built a mobile app "
            "using React Native. Internship at a tech startup working on "
            "backend development with Django and PostgreSQL."
        ),
        "job": (
            "Front Desk Agent at a five-star luxury hotel. Must have "
            "hospitality experience, guest relations skills, and knowledge "
            "of reservation systems such as Opera PMS. Responsibilities "
            "include check-in, check-out, concierge services, and guest "
            "satisfaction. Customer service and multitasking are essential. "
            "Prior front desk or hotel management experience required."
        ),
    },
    # ------------------------------------------------------------------ 4
    {
        "name": "Marketing resume  →  Marketing Manager job",
        "expected": "High",
        "resume": (
            "Digital Marketing Manager with 5 years of experience. Expert "
            "in SEO, SEM, PPC, Google Ads, and email marketing. Managed "
            "social media campaigns across Facebook, Instagram, LinkedIn, "
            "and TikTok. Proficient in Adobe Photoshop, Canva, and Figma. "
            "Increased organic traffic by 60% and reduced cost per lead "
            "by 25%. Experience with CRM platforms and marketing automation."
        ),
        "job": (
            "Marketing Manager needed with experience in digital marketing, "
            "SEO, SEM, PPC, and Google Ads. Must manage social media "
            "campaigns on Facebook, Instagram, and LinkedIn. Proficiency "
            "in graphic design tools (Photoshop, Canva) required. Experience "
            "with email marketing, CRM, and marketing automation preferred. "
            "5+ years of marketing experience."
        ),
    },
    # ------------------------------------------------------------------ 5
    {
        "name": "Hospitality resume  →  Software Eng job",
        "expected": "Low",
        "resume": (
            "Hotel Front Desk Supervisor with 6 years of hospitality "
            "experience. Managed check-in and check-out operations, trained "
            "new staff, and handled guest complaints. Proficient in Opera "
            "PMS and reservation systems. Ensured guest satisfaction scores "
            "above 95%. Strong communication and multitasking skills."
        ),
        "job": (
            "Senior Software Engineer required. Must have 5+ years of "
            "experience in Python, Java, and cloud platforms (AWS or GCP). "
            "Build and maintain microservices, REST APIs, and CI/CD "
            "pipelines. Experience with Docker, Kubernetes, and SQL "
            "databases required. Agile and Scrum environment."
        ),
    },
    # ------------------------------------------------------------------ 6
    {
        "name": "Business grad resume  →  Junior Analyst job",
        "expected": "Medium",
        "resume": (
            "Recent Business Administration graduate. Coursework in "
            "accounting, financial analysis, and strategic planning. "
            "Proficient in Microsoft Excel, PowerPoint, and Word. "
            "Completed an internship analysing sales data using Excel "
            "pivot tables. Strong communication and presentation skills. "
            "Member of the university business club."
        ),
        "job": (
            "Junior Business Analyst position. Requires data analysis "
            "skills, proficiency in Excel, SQL, and Tableau. Must "
            "understand financial reporting and budgeting. Experience "
            "with Power BI or business intelligence tools preferred. "
            "Strong communication and presentation skills. 0-2 years "
            "of experience."
        ),
    },
    # ------------------------------------------------------------------ 7
    {
        "name": "Nurse resume  →  Healthcare Admin job",
        "expected": "Medium",
        "resume": (
            "Registered Nurse with 4 years of experience in patient care. "
            "Skilled in vital signs monitoring, phlebotomy, triage, and "
            "medical records management. CPR and First Aid certified. "
            "Familiar with electronic health records (EHR) and HIPAA "
            "compliance. Strong interpersonal and communication skills. "
            "BSc Nursing."
        ),
        "job": (
            "Healthcare Administrator needed. Responsibilities include "
            "managing medical records, ensuring HIPAA compliance, "
            "overseeing patient care quality, and budgeting. Proficiency "
            "in electronic health records and Microsoft Office required. "
            "Project management and leadership skills preferred. "
            "3-5 years of healthcare experience."
        ),
    },
    # ------------------------------------------------------------------ 8
    {
        "name": "Full-stack Dev resume  →  Frontend job",
        "expected": "High",
        "resume": (
            "Full-Stack Developer with 3 years of experience. Proficient "
            "in JavaScript, TypeScript, React, Angular, Node.js, and "
            "Express. Built responsive UIs with HTML, CSS, Tailwind, and "
            "Bootstrap. Experience with REST APIs, GraphQL, Git, and Agile "
            "workflows. Deployed applications on AWS using Docker. "
            "Improved page load speed by 40%."
        ),
        "job": (
            "Frontend Developer needed. Must be proficient in JavaScript, "
            "TypeScript, React, HTML, and CSS. Experience with Tailwind "
            "or Bootstrap required. Familiarity with REST APIs, Git, and "
            "Agile practices. 2+ years of frontend development experience."
        ),
    },
    # ------------------------------------------------------------------ 9
    {
        "name": "Finance resume  →  Accounting job",
        "expected": "Medium",
        "resume": (
            "Financial Analyst with 3 years of experience in investment "
            "analysis and portfolio management. Proficient in financial "
            "modeling, Excel, and Bloomberg Terminal. Created monthly "
            "financial reports and forecasting models. BSc Finance. "
            "Strong analytical skills and attention to detail."
        ),
        "job": (
            "Accountant needed. Must have experience in bookkeeping, "
            "accounts payable, accounts receivable, tax preparation, and "
            "payroll processing. Proficiency in QuickBooks and Excel "
            "required. Knowledge of financial reporting and auditing "
            "standards. CPA certification preferred. 2-4 years of "
            "accounting experience."
        ),
    },
    # ------------------------------------------------------------------ 10
    {
        "name": "Retail resume  →  Executive Assistant job",
        "expected": "Low",
        "resume": (
            "Retail Sales Associate with 2 years of experience in a "
            "clothing store. Assisted customers with product selection, "
            "handled cash register operations, and maintained store "
            "displays. Employee of the Month twice. Good teamwork and "
            "communication skills."
        ),
        "job": (
            "Executive Assistant to the CEO. Must manage complex "
            "calendars, coordinate travel, prepare board presentations, "
            "and handle confidential documents. Advanced proficiency in "
            "Microsoft Office (Excel, PowerPoint, Outlook), SharePoint, "
            "and project management tools (Asana, Trello). 3-5 years of "
            "executive support experience. Excellent writing, stakeholder "
            "management, and organisational skills required."
        ),
    },
]


# ── Runner ────────────────────────────────────────────────────────────────
def run_evaluation():
    """Execute all test cases and print a formatted report."""
    print("=" * 80)
    print("  RESUME-JOB MATCHING SYSTEM — EVALUATION REPORT")
    print("=" * 80)
    print(f"\n  Loading matcher (SentenceTransformer model) …", end=" ", flush=True)

    start_load = time.time()
    matcher = JobMatcher()
    print(f"done ({time.time() - start_load:.1f}s)\n")

    # Column widths
    col_name = 42
    col_score = 7
    col_level = 10
    col_match = 8
    col_result = 8

    header = (
        f"  {'Test Case':<{col_name}} "
        f"{'Score':>{col_score}} "
        f"{'Expected':>{col_level}} "
        f"{'Actual':>{col_match}} "
        f"{'Result':>{col_result}}"
    )
    separator = "  " + "-" * (col_name + col_score + col_level + col_match + col_result + 4)

    print(header)
    print(separator)

    results = []
    total_time = 0.0

    for i, tc in enumerate(TEST_CASES, 1):
        t0 = time.time()
        analysis = matcher.generate_full_analysis(tc["resume"], tc["job"])
        elapsed = time.time() - t0
        total_time += elapsed

        score = analysis["matchScore"]
        matched = analysis["foundSkills"]
        missing = analysis["missingSkills"]
        actual_level = score_to_level(score)
        expected_level = tc["expected"]
        correct = actual_level == expected_level

        results.append({
            "name": tc["name"],
            "score": score,
            "expected": expected_level,
            "actual": actual_level,
            "correct": correct,
            "matched_skills": matched,
            "missing_skills": missing,
            "time": elapsed,
        })

        tag = "PASS" if correct else "FAIL"
        print(
            f"  {tc['name']:<{col_name}} "
            f"{score:>{col_score}}% "
            f"{expected_level:>{col_level}} "
            f"{actual_level:>{col_match}} "
            f"{'  ' + tag:>{col_result}}"
        )

    print(separator)

    # ── Detailed breakdown ────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("  DETAILED RESULTS")
    print(f"{'=' * 80}\n")

    for r in results:
        tag = "PASS" if r["correct"] else "FAIL"
        print(f"  [{tag}] {r['name']}  —  {r['score']}%")
        print(f"       Matched skills : {', '.join(r['matched_skills'][:8]) if r['matched_skills'] else '(none)'}")
        print(f"       Missing skills : {', '.join(r['missing_skills'][:8]) if r['missing_skills'] else '(none)'}")
        print()

    # ── Summary ───────────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for r in results if r["correct"])
    failed = total - passed
    accuracy = (passed / total) * 100 if total else 0

    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"\n  Test cases       : {total}")
    print(f"  Correct          : {passed}")
    print(f"  Incorrect        : {failed}")
    print(f"  Accuracy         : {accuracy:.0f}%")
    print(f"  Total runtime    : {total_time:.1f}s")
    print(f"  Avg per case     : {total_time / total:.2f}s")

    # ── Observations ──────────────────────────────────────────────────────
    high_cases = [r for r in results if r["expected"] == "High"]
    med_cases  = [r for r in results if r["expected"] == "Medium"]
    low_cases  = [r for r in results if r["expected"] == "Low"]

    high_acc = sum(1 for r in high_cases if r["correct"]) / len(high_cases) * 100 if high_cases else 0
    med_acc  = sum(1 for r in med_cases  if r["correct"]) / len(med_cases)  * 100 if med_cases  else 0
    low_acc  = sum(1 for r in low_cases  if r["correct"]) / len(low_cases)  * 100 if low_cases  else 0

    print(f"\n  Accuracy by expected level:")
    print(f"    High   ({len(high_cases)} cases) : {high_acc:.0f}%")
    print(f"    Medium ({len(med_cases)} cases)  : {med_acc:.0f}%")
    print(f"    Low    ({len(low_cases)} cases)  : {low_acc:.0f}%")

    print("\n  Observations:")

    if high_acc == 100:
        print("    - The system reliably identifies strong matches where")
        print("      resume skills closely align with job requirements.")
    elif high_acc >= 50:
        print("    - Strong matches are mostly detected, though some high-overlap")
        print("      cases are scored lower than expected.")
    else:
        print("    - Strong matches are under-scored — the scoring weights may")
        print("      need adjustment.")

    if low_acc == 100:
        print("    - Cross-domain mismatches (e.g., tech resume vs hospitality")
        print("      job) are correctly flagged as low matches.")
    elif low_acc >= 50:
        print("    - Most cross-domain mismatches are caught, but some receive")
        print("      inflated scores from soft-skill or semantic overlap.")
    else:
        print("    - Weak matches are over-scored — semantic similarity may be")
        print("      inflating scores for unrelated domains.")

    if med_acc == 100:
        print("    - Borderline / partial-overlap cases are classified accurately.")
    elif med_acc >= 50:
        print("    - Borderline cases are partially captured; the Medium band")
        print("      (45-69%) may need tuning for edge cases.")
    else:
        print("    - The system struggles with borderline cases — consider")
        print("      adjusting the Medium score thresholds (currently 45-69%).")

    # Failed-case details
    failed_cases = [r for r in results if not r["correct"]]
    if failed_cases:
        print("\n  Misclassified cases:")
        for r in failed_cases:
            print(f"    - \"{r['name']}\": scored {r['score']}% "
                  f"(expected {r['expected']}, got {r['actual']})")
    else:
        print("\n    All test cases classified correctly.")

    print("\n" + "=" * 80)

    return accuracy, results


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_evaluation()
