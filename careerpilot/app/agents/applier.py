import json

from .. import config
from ..models import Application, Match


def _template(m: Match) -> dict:
    p, j = m.profile, m.job
    skills = ", ".join(m.matched[:5]) or p.keywords
    return {
        "cv_summary": f"{p.role} with {p.experience}+ years of experience delivering {skills}. "
                      f"Focused on measurable outcomes in {j.location}.",
        "cover_letter": f"Dear {j.company} team,\n\nI am applying for the {j.title} role. My {p.experience}+ years as a "
                        f"{p.role} include {skills}, which map directly to your requirements.\n\n"
                        f"I would welcome the chance to discuss how I can contribute.\n\nKind regards",
    }


def _llm(m: Match) -> dict | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic

        p, j = m.profile, m.job
        prompt = (f"Write a tailored 3-sentence CV summary and a short cover letter (max 150 words) for this job. "
                  f"Use only facts from the candidate data. Respond with JSON only: "
                  f'{{"cv_summary":"...","cover_letter":"..."}}\n\nCandidate: {p.role}, {p.experience} years, '
                  f"keywords {p.keywords}\nResume:\n{p.resume_text[:3000]}\n\nJob: {j.title} at {j.company}\n"
                  f"{j.description[:2500]}")
        msg = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY).messages.create(
            model=config.MODEL, max_tokens=900, messages=[{"role": "user", "content": prompt}])
        t = msg.content[0].text
        return json.loads(t[t.index("{"): t.rindex("}") + 1])
    except Exception:
        return None


def draft(m: Match, db) -> Application:
    d = _llm(m) or _template(m)
    app = Application(match_id=m.id, cv_summary=d["cv_summary"], cover_letter=d["cover_letter"])
    db.add(app)
    return app
