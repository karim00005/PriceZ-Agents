import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
CONFIG_FILE = DATA_DIR / "agents_config.json"

DEFAULT_TEAM_AGENTS = [
    {
        "id": "sales",
        "name": "وكيل المبيعات والتسويق",
        "title": "Sales Agent",
        "group": "مجموعة التسويق",
        "avatar_icon": "💼",
        "anime_avatar": "sales",
        "desk_name": "مكتب المبيعات والعروض",
        "color": "blue",
        "glow": "glow-blue",
        "role": "Lead Sales & Marketing Strategist",
        "goal": "صياغة استراتيجيات المبيعات، عروض الأسعار، خطط النمو وحملات التسويق الرقمي الفعالة.",
        "skills": ["Sales Pitches", "Pricing Strategy", "Client Outreach", "Growth Hacking"],
        "tasks_count": 0,
        "desk_pos": {"x": 23, "y": 62}
    },
    {
        "id": "support",
        "name": "وكيل الدعم الفني والخدمة",
        "title": "Support Agent",
        "group": "مجموعة الدعم الفني",
        "avatar_icon": "🎧",
        "anime_avatar": "support",
        "desk_name": "مكتب الدعم وخدمة العملاء",
        "color": "sky",
        "glow": "glow-sky",
        "role": "Senior Customer Success & Support Engineer",
        "goal": "حل استفسارات ومشاكل المستخدمين، كتابة أدلة الاستخدام، ومتابعة تذاكر الدعم بدقة.",
        "skills": ["Customer Support", "Troubleshooting", "User Guides", "Issue Triage"],
        "tasks_count": 0,
        "desk_pos": {"x": 58, "y": 58}
    },
    {
        "id": "research",
        "name": "وكيل البحث والتحليل",
        "title": "Research Agent",
        "group": "مجموعة البحث والتحليل",
        "avatar_icon": "🔍",
        "anime_avatar": "research",
        "desk_name": "ممر البحث واستخبارات السوق",
        "color": "emerald",
        "glow": "glow-emerald",
        "role": "Senior Deep Market & Tech Researcher",
        "goal": "البحث المعمق في الأسواق والمنافسين، استخراج البيانات الموثوقة وصياغة دراسات الجدوى.",
        "skills": ["Deep Web Research", "Market Intelligence", "Competitor Audit", "Fact Checking"],
        "tasks_count": 0,
        "desk_pos": {"x": 42, "y": 48}
    },
    {
        "id": "content",
        "name": "وكيل صناعة المحتوى",
        "title": "Content Agent",
        "group": "مجموعة التسويق",
        "avatar_icon": "✍️",
        "anime_avatar": "content",
        "desk_name": "مكتب صناعة المحتوى والتدوين",
        "color": "purple",
        "glow": "glow-purple",
        "role": "Creative Copywriter & Content Creator",
        "goal": "كتابة المقالات الاحترافية، منشورات وسائل التواصل، وثائق المشاريع وصياغة الرسائل المؤثرة.",
        "skills": ["Copywriting", "Creative Writing", "SEO Content", "Social Media Posts"],
        "tasks_count": 0,
        "desk_pos": {"x": 80, "y": 50}
    },
    {
        "id": "report",
        "name": "وكيل التقارير والإحصائيات",
        "title": "Report Agent",
        "group": "مجموعة التقارير",
        "avatar_icon": "📊",
        "anime_avatar": "report",
        "desk_name": "مكتب التقارير ولوحات البيانات",
        "color": "indigo",
        "glow": "glow-indigo",
        "role": "Business Intelligence & Data Analyst",
        "goal": "إعداد التقارير الدورية ولوحات المعلومات الإحصائية، وتحليل مؤشرات الأداء KPIs.",
        "skills": ["BI Dashboards", "Statistical Summaries", "KPI Analytics", "Executive Briefs"],
        "tasks_count": 0,
        "desk_pos": {"x": 30, "y": 45}
    },
    {
        "id": "architect",
        "name": "المخطط والمعمار البرمجي",
        "title": "Architect & DevOps",
        "group": "مجموعة المعمارية والأكواد",
        "avatar_icon": "🏛️",
        "anime_avatar": "architect",
        "desk_name": "مكتب المعمارية البرمجية والأنظمة",
        "color": "cyan",
        "glow": "glow-cyan",
        "role": "Principal Solutions Architect & DevOps",
        "goal": "تحليل متطلبات الأنظمة، كتابة أكواد الإنتاج، فحص الأمان ونشر المشاريع على السيرفر.",
        "skills": ["System Architecture", "Full-Stack Coding", "Security Auditing", "DevOps Deploy"],
        "tasks_count": 0,
        "desk_pos": {"x": 18, "y": 42}
    }
]

def load_team_agents() -> List[Dict[str, Any]]:
    """Loads agents definitions with persistent custom user names."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    custom_map = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                custom_map = json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to read agents_config.json: {e}")

    agents = []
    for a in DEFAULT_TEAM_AGENTS:
        aid = a["id"]
        item = dict(a)
        if aid in custom_map:
            item["name"] = custom_map[aid].get("name", item["name"])
            item["title"] = custom_map[aid].get("title", item["title"])
            if "role" in custom_map[aid]:
                item["role"] = custom_map[aid]["role"]
        agents.append(item)
    return agents

def save_custom_agent_name(agent_id: str, new_name: str, new_title: Optional[str] = None, new_role: Optional[str] = None) -> bool:
    """Persists renamed employee to agents_config.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    custom_map = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                custom_map = json.load(f)
        except Exception:
            custom_map = {}

    if agent_id not in custom_map:
        custom_map[agent_id] = {}

    custom_map[agent_id]["name"] = new_name
    if new_title:
        custom_map[agent_id]["title"] = new_title
    if new_role:
        custom_map[agent_id]["role"] = new_role

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_map, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Error saving agent config] {e}")
        return False

TEAM_AGENTS_DEFINITION = load_team_agents()
