import sys
import asyncio

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from core.crew import OrchestratorCrew

async def test():
    events = []
    async def broadcaster(event):
        events.append(event)
        ev_type = event.get("event")
        agent = event.get("agent_id") or event.get("agent_name", "")
        status = event.get("status", "")
        details = event.get("step_details", "")
        print(f"[{ev_type}] {agent} -> {status}: {details}")

    crew = OrchestratorCrew(event_broadcaster=broadcaster)
    print("🚀 Initializing PriceZ Agents test sprint...")
    result = await crew.run("تحليل متطلبات نظام أتمتة الوكلاء الذاتية")
    print("\n✅ Sprint finished with status:", result["status"])
    print(f"Total events captured: {len(events)}")
    print(f"Created files count: {len(result.get('files_created', []))}")

if __name__ == "__main__":
    asyncio.run(test())
