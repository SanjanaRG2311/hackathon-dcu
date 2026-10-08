import json
from difflib import SequenceMatcher

from .. import config
from ..models import Job, Profile

GROUPS = [
    {"project manager", "delivery lead", "programme manager", "program manager", "delivery manager", "technical project manager"},
    {"pmo", "pmo analyst", "pmo manager", "portfolio", "governance"},
    {"scrum master", "agile coach", "agile delivery"},
]

SYSTEM = (
    "You are an experienced recruiter. Score how well a job fits a candidate profile. Treat equivalent titles "
    "(e.g. Delivery Lead, Programme Manager, Project Manager) as related. Respond with JSON only: "
    '{"role_fit":0-100,"location_fit":0-100,"type_fit":0-100,"skills_fit":0-100,"final_score":0-100,'
    '"reason":"one sentence","matched_keywords":[...],"missing_skills":[...]}'
)


def _csv(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def heuristic(p: Profile, j: Job) -> dict:
    title = j.title.lower()
    wanted = [t.lower() for t in [p.role] + _csv(p.alt_titles)]
    role = max(SequenceMatcher(None, title, w).ratio() * 100 for w in wanted)
    for w in wanted:
        if w in title:
            role = 100
    for g in GROUPS:
        if any(w in g or any(x in w for x in g) for w in wanted) and any(x in title for x in g):
            role = max(role, 88)
    locs = [l.lower() for l in _csv(p.locations)]
    loc = 100 if any(l in j.location.lower() for l in locs) else (60 if "remote" in j.location.lower() else 10)
    typ = 100 if p.job_type.lower() == j.job_type.lower() else 35
    kws = _csv(p.keywords)
    text = f"{j.title} {j.description}".lower()
    hit = [k for k in kws if k.lower() in text]
    skills = int(100 * len(hit) / len(kws)) if kws else 50
    final = int(role * 0.4 + loc * 0.25 + typ * 0.15 + skills * 0.2)
    return {"role_fit": int(role), "location_fit": loc, "type_fit": typ, "skills_fit": skills, "final_score": final,
            "reason": f"Heuristic match: title fit {int(role)}%, matched {len(hit)}/{len(kws)} keywords.",
            "matched_keywords": hit, "missing_skills": [k for k in kws if k not in hit]}


def _llm(p: Profile, j: Job, log: list[str]) -> dict | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        prompt = (
            f"CANDIDATE PROFILE\nRole: {p.role}\nAlternate titles: {p.alt_titles}\nType: {p.job_type}\n"
            f"Locations: {p.locations}\nExperience: {p.experience} years\nKeywords: {p.keywords}\n"
            f"Resume:\n{p.resume_text[:3000]}\n\nJOB\nTitle: {j.title}\nCompany: {j.company}\n"
            f"Location: {j.location}\nType: {j.job_type}\nDescription:\n{j.description[:3000]}"
        )
        msg = client.messages.create(model=config.MODEL, max_tokens=500, system=SYSTEM,
                                     messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        for k in ("role_fit", "location_fit", "type_fit", "skills_fit", "final_score"):
            data[k] = max(0, min(100, int(data[k])))
        return data
    except Exception as e:
        log.append(f"LLM match failed ({type(e).__name__}), used heuristic")
        return None


def match(p: Profile, j: Job, log: list[str]) -> dict:
    return _llm(p, j, log) or heuristic(p, j)
