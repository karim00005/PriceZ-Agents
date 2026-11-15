import asyncio
import re
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

from core.llm_provider import LLMProvider
from core.project_manager import ProjectManager
from core.memory import SessionMemory
from core.agent_loop import AutonomousAgentLoop
from core.team import TEAM_AGENTS_DEFINITION

class OrchestratorCrew:
    def __init__(
        self,
        event_broadcaster: Optional[Callable[[Dict[str, Any]], Any]] = None,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.broadcaster = event_broadcaster
        self.llm = LLMProvider(provider=provider, api_key=api_key, model=model, base_url=base_url)
        self.project_manager = ProjectManager()
        self.memory = SessionMemory()
        self.is_running = False
        self._current_run_task: Optional[asyncio.Task] = None

        # Build agents registry
        self.team_specs = TEAM_AGENTS_DEFINITION
        self.agents_state: Dict[str, Dict[str, Any]] = {
            agent["id"]: {
                **agent,
                "status": "idle",
                "character_state": "idle",
                "current_speech": "",
                "step_details": "في انتظار توجيهات المدير...",
                "active_task": "",
                "progress": 0,
                "history": []
            }
            for agent in self.team_specs
        }

    async def _broadcast(self, event_type_or_data: Any, data: Optional[Dict[str, Any]] = None):
        if not self.broadcaster:
            return

        if data is None and isinstance(event_type_or_data, dict):
            payload = {
                "event": event_type_or_data.get("event") or event_type_or_data.get("loop_event") or "agent_step",
                "timestamp": datetime.now().isoformat(),
                **event_type_or_data
            }
        else:
            payload = {
                "event": str(event_type_or_data),
                "timestamp": datetime.now().isoformat(),
                **(data or {})
            }
        await self.broadcaster(payload)

    def update_config(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.llm.update_config(provider=provider, api_key=api_key, model=model, base_url=base_url)

    async def test_connection(self) -> Dict[str, Any]:
        return await self.llm.test_connection()

    def rename_agent(self, agent_id: str, new_name: str, new_title: Optional[str] = None, new_role: Optional[str] = None) -> Dict[str, Any]:
        from core.team import save_custom_agent_name
        if agent_id in self.agents_state:
            self.agents_state[agent_id]["name"] = new_name
            if new_title:
                self.agents_state[agent_id]["title"] = new_title
            if new_role:
                self.agents_state[agent_id]["role"] = new_role
            save_custom_agent_name(agent_id, new_name, new_title, new_role)
            return {"success": True, "agent_id": agent_id, "name": new_name, "title": self.agents_state[agent_id].get("title", "")}
        return {"success": False, "error": f"Agent {agent_id} not found"}

    def get_real_stats(self, project_id: str = "default_project") -> Dict[str, Any]:
        available = sum(1 for a in self.agents_state.values() if a.get("status") == "idle")
        revisions = self.project_manager.revisions.list_revisions(project_id)
        completed = len(revisions)
        active = 1 if self.is_running else 0
        recent = []
        for r in revisions[:5]:
            recent.append({
                "title": r.get("message", "تحديث المشروع"),
                "category": "إنجاز",
                "time": r.get("timestamp", ""),
                "status": "completed"
            })
        return {
            "active_tasks": active,
            "available_agents": available,
            "completed_tasks": completed,
            "in_progress_tasks": active,
            "recent_tasks": recent
        }

    def stop(self):
        """Cancels running mission immediately"""
        if self._current_run_task and not self._current_run_task.done():
            self._current_run_task.cancel()
            self.is_running = False
            for aid in self.agents_state:
                self.agents_state[aid]["status"] = "idle"
                self.agents_state[aid]["character_state"] = "idle"
                self.agents_state[aid]["current_speech"] = ""
                self.agents_state[aid]["active_task"] = ""
                self.agents_state[aid]["progress"] = 0
            return True
        return False

    async def update_agent_telemetry(
        self,
        agent_id: str,
        status: str,
        character_state: str,
        speech: str,
        step_details: str,
        active_task: Optional[str] = None,
        progress: Optional[int] = None
    ):
        if agent_id in self.agents_state:
            self.agents_state[agent_id]["status"] = status
            self.agents_state[agent_id]["character_state"] = character_state
            self.agents_state[agent_id]["current_speech"] = speech
            self.agents_state[agent_id]["step_details"] = step_details
            if active_task is not None:
                self.agents_state[agent_id]["active_task"] = active_task
            if progress is not None:
                self.agents_state[agent_id]["progress"] = progress

        await self._broadcast("agent_office_step", {
            "agent_id": agent_id,
            "status": status,
            "character_state": character_state,
            "speech": speech,
            "step_details": step_details,
            "active_task": self.agents_state[agent_id].get("active_task", ""),
            "progress": self.agents_state[agent_id].get("progress", 0)
        })

    def _extract_target_agent(self, prompt: str, explicit_target: Optional[str]) -> (str, str):
        if explicit_target and explicit_target != "all":
            # Map legacy or common aliases
            alias_map = {
                "sales": "sales", "مبيعات": "sales", "تسويق": "sales",
                "support": "support", "دعم": "support", "خدمة": "support",
                "research": "research", "بحث": "research", "تحليل": "research",
                "content": "content", "محتوى": "content", "كتابة": "content",
                "report": "report", "تقارير": "report", "تقرير": "report",
                "architect": "architect", "معمار": "architect", "تخطيط": "architect",
                "backend": "architect", "مبرمج": "architect", "كود": "architect",
                "frontend": "content", "واجهات": "content",
                "database": "research", "بيانات": "research",
                "auditor": "report", "أمان": "report",
                "devops": "architect", "نشر": "architect"
            }
            return alias_map.get(explicit_target.lower(), explicit_target.lower()), prompt

        # Check for @mentions in prompt
        match = re.match(r"^@(\w+)\s*(.*)", prompt, re.DOTALL)
        if match:
            mention = match.group(1).lower()
            clean_prompt = match.group(2).strip()
            mention_map = {
                "sales": "sales", "مبيعات": "sales", "تسويق": "sales",
                "support": "support", "دعم": "support", "خدمة": "support",
                "research": "research", "بحث": "research", "تحليل": "research",
                "content": "content", "محتوى": "content", "كتابة": "content",
                "report": "report", "تقارير": "report", "تقرير": "report",
                "architect": "architect", "معمار": "architect", "تخطيط": "architect",
                "backend": "architect", "مبرمج": "architect", "كود": "architect",
                "frontend": "content", "واجهات": "content",
                "database": "research", "بيانات": "research",
                "auditor": "report", "أمان": "report",
                "devops": "architect", "نشر": "architect"
            }
            if mention in mention_map:
                return mention_map[mention], clean_prompt

        return "all", prompt

    async def run(
        self,
        user_request: str,
        session_id: str = "default_session",
        project_id: str = "default_project",
        target_agent: Optional[str] = "all"
    ) -> Dict[str, Any]:
        """
        Runs the full autonomous studio pipeline or targeted individual agent loop.
        """
        self.is_running = True
        actual_target, clean_request = self._extract_target_agent(user_request, target_agent)
        
        self.memory.add_user_message(session_id, user_request)
        context_prompt = self.memory.get_context_prompt(session_id)
        tools = self.project_manager.get_tools(project_id)
        ws_dir = self.project_manager.get_workspace_dir(project_id)

        await self._broadcast("workflow_started", {
            "user_request": user_request,
            "target_agent": actual_target,
            "session_id": session_id,
            "project_id": project_id,
            "status": "started"
        })

        results = {
            "user_request": user_request,
            "target_agent": actual_target,
            "session_id": session_id,
            "project_id": project_id,
            "architecture": None,
            "files_created": [],
            "status": "in_progress"
        }

        try:
            # ==============================================================
            # CASE A: TARGETED SINGLE AGENT DELEGATION
            # ==============================================================
            if actual_target != "all":
                agent_spec = next((a for a in self.team_specs if a["id"] == actual_target), None)
                if agent_spec:
                    await self.update_agent_telemetry(
                        agent_id=actual_target,
                        status="working",
                        character_state="typing",
                        speech=f"أمرك يا فندم! تلقيت التكليف المباشر وسأبدأ فوراً...",
                        step_details=f"تنفيذ التكليف المباشر: {clean_request[:60]}...",
                        active_task=clean_request[:50],
                        progress=20
                    )

                    single_loop = AutonomousAgentLoop(
                        agent_id=actual_target,
                        agent_name=agent_spec["name"],
                        role=agent_spec["role"],
                        tools=tools,
                        llm=self.llm,
                        event_callback=self._broadcast
                    )
                    res = await single_loop.run(task_goal=clean_request, context=context_prompt)
                    results["deliverable"] = res.get("summary", "")

                    # Record in history
                    if actual_target in self.agents_state:
                        self.agents_state[actual_target]["history"].append({
                            "task": clean_request,
                            "summary": res.get("summary", ""),
                            "time": datetime.now().strftime("%I:%M %p")
                        })

                    await self.update_agent_telemetry(
                        agent_id=actual_target,
                        status="done",
                        character_state="celebrating",
                        speech="تم إنجاز التكليف المباشر وحفظ المخرجات بنجاح يا مدير!",
                        step_details="اكتمل تنفيذ التكليف الفردي بنجاح.",
                        progress=100
                    )

                    await self._broadcast("agent_completed", {
                        "agent_id": actual_target,
                        "agent_name": agent_spec["name"],
                        "task": clean_request[:60],
                        "message": f"أنجز {agent_spec['name']} تكليفه بنجاح!"
                    })

            # ==============================================================
            # CASE B: FULL COMPANY SPRINT (NET AGENT TEAM IN HARMONY)
            # ==============================================================
            else:
                # 1. Architect & DevOps Agent: Analyzes & designs solution
                await self.update_agent_telemetry(
                    agent_id="architect",
                    status="working",
                    character_state="thinking",
                    speech="أهلاً يا فندم! جاري تحليل الطلب ورسم الهيكل المعماري والتقني...",
                    step_details="تحليل طلب المدير وهيكلة المهام للمكتب الافتراضي...",
                    active_task="صياغة الهيكل المعماري وخطة العمل",
                    progress=35
                )
                arch_loop = AutonomousAgentLoop(
                    agent_id="architect",
                    agent_name="المخطط والمعمار البرمجي",
                    role="Principal Solutions Architect",
                    tools=tools,
                    llm=self.llm,
                    event_callback=self._broadcast
                )
                arch_res = await arch_loop.run(
                    task_goal=f"صياغة معمارية كاملة لطلب المستخدم وبناء الهيكل الأساسي: {clean_request}",
                    context=context_prompt
                )
                results["architecture"] = arch_res.get("summary", "")
                await self.update_agent_telemetry(
                    agent_id="architect",
                    status="done",
                    character_state="talking",
                    speech="تم تجهيز الهيكل المعماري وخطة المهام للفريق!",
                    step_details="اكتملت المعمارية وتم توزيعها على الوكلاء.",
                    progress=100
                )

                # Broadcast handoff from architect to research
                await self._broadcast("agent_handoff", {
                    "from_agent": "architect",
                    "from_agent_name": self.agents_state["architect"]["name"],
                    "to_agent": "research",
                    "to_agent_name": self.agents_state["research"]["name"],
                    "task": "البحث المتقدم وتحليل المتطلبات والمنافسين",
                    "message": f"تم نقل المهمة وتسليم الهيكل المعماري من {self.agents_state['architect']['name']} إلى {self.agents_state['research']['name']}"
                })
                await asyncio.sleep(0.3)

                # 2. Research Agent: Deep market, competitors & specs research
                await self.update_agent_telemetry(
                    agent_id="research",
                    status="working",
                    character_state="typing",
                    speech="جاري استخراج البيانات والمصادر ومراجعة أفضل الممارسات...",
                    step_details="تحليل البيانات واستخراج المواصفات الفنية والتنافسية...",
                    active_task="البحث المتقدم وتحليل المتطلبات والمنافسين",
                    progress=50
                )
                research_loop = AutonomousAgentLoop(
                    agent_id="research",
                    agent_name="وكيل البحث والتحليل",
                    role="Senior Deep Market & Tech Researcher",
                    tools=tools,
                    llm=self.llm,
                    event_callback=self._broadcast
                )
                res_out = await research_loop.run(
                    task_goal=f"إجراء فحص وبحث دقيق ومواصفات لمتطلبات: {clean_request}",
                    context=results["architecture"]
                )
                results["research"] = res_out.get("summary", "")
                await self.update_agent_telemetry(
                    agent_id="research",
                    status="done",
                    character_state="celebrating",
                    speech="تم توثيق نتائج البحث وتغذية الفريق بالبيانات الدقيقة!",
                    step_details="اكتمل تقرير البحث التحليلي.",
                    progress=100
                )

                # Broadcast handoff from research to content
                await self._broadcast("agent_handoff", {
                    "from_agent": "research",
                    "from_agent_name": self.agents_state["research"]["name"],
                    "to_agent": "content",
                    "to_agent_name": self.agents_state["content"]["name"],
                    "task": "كتابة المحتوى والتوثيق والملفات الأساسية",
                    "message": f"تم نقل المهمة وتسليم نتائج البحث من {self.agents_state['research']['name']} إلى {self.agents_state['content']['name']}"
                })
                await asyncio.sleep(0.3)

                # 3. Content Agent: Generates content, docs and implementation
                await self.update_agent_telemetry(
                    agent_id="content",
                    status="working",
                    character_state="typing",
                    speech="أقوم بصياغة المحتوى، التوثيق، وواجهات العمل المكتملة...",
                    step_details="كتابة التوثيق والملفات التنفيذية للمشروع...",
                    active_task="كتابة المحتوى والتوثيق والملفات الأساسية",
                    progress=65
                )
                content_loop = AutonomousAgentLoop(
                    agent_id="content",
                    agent_name="وكيل صناعة المحتوى",
                    role="Creative Copywriter & Content Creator",
                    tools=tools,
                    llm=self.llm,
                    event_callback=self._broadcast
                )
                cont_out = await content_loop.run(
                    task_goal=f"بناء المحتوى الشامل والملفات التنفيذية لـ: {clean_request}",
                    context=results["architecture"]
                )
                results["content"] = cont_out.get("summary", "")
                await self.update_agent_telemetry(
                    agent_id="content",
                    status="done",
                    character_state="celebrating",
                    speech="تمت صياغة الوثائق والمحتوى والملفات بنجاح!",
                    step_details="تم حفظ ملفات المحتوى في مساحة العمل.",
                    progress=100
                )

                # Broadcast handoff from content to sales
                await self._broadcast("agent_handoff", {
                    "from_agent": "content",
                    "from_agent_name": self.agents_state["content"]["name"],
                    "to_agent": "sales",
                    "to_agent_name": self.agents_state["sales"]["name"],
                    "task": "إعداد خطة المبيعات والنمو",
                    "message": f"تم نقل المهمة وتسليم ملفات المحتوى من {self.agents_state['content']['name']} إلى {self.agents_state['sales']['name']}"
                })
                await asyncio.sleep(0.3)

                # 4. Sales Agent: Formulates commercial & growth strategy
                await self.update_agent_telemetry(
                    agent_id="sales",
                    status="working",
                    character_state="typing",
                    speech="جاري صياغة خطة المبيعات ونماذج التسعير والوصول للعملاء...",
                    step_details="تطوير استراتيجية المبيعات والتسعير...",
                    active_task="إعداد خطة المبيعات والنمو",
                    progress=80
                )
                sales_loop = AutonomousAgentLoop(
                    agent_id="sales",
                    agent_name="وكيل المبيعات والتسويق",
                    role="Lead Sales & Marketing Strategist",
                    tools=tools,
                    llm=self.llm,
                    event_callback=self._broadcast
                )
                sales_out = await sales_loop.run(
                    task_goal=f"صياغة خطة تسويق ومبيعات واقتراحات تسعير لـ: {clean_request}",
                    context=results["architecture"]
                )
                results["sales"] = sales_out.get("summary", "")
                await self.update_agent_telemetry(
                    agent_id="sales",
                    status="done",
                    character_state="celebrating",
                    speech="خطة المبيعات جاهزة لتحقيق أعلى قيمة وعائد!",
                    step_details="تم إنجاز استراتيجية المبيعات بنجاح.",
                    progress=100
                )

                # Broadcast handoff from sales to support
                await self._broadcast("agent_handoff", {
                    "from_agent": "sales",
                    "from_agent_name": self.agents_state["sales"]["name"],
                    "to_agent": "support",
                    "to_agent_name": self.agents_state["support"]["name"],
                    "task": "إعداد دليل الدعم الفني وحلول المشاكل",
                    "message": f"تم نقل المهمة وتسليم خطة التسويق من {self.agents_state['sales']['name']} إلى {self.agents_state['support']['name']}"
                })
                await asyncio.sleep(0.3)

                # 5. Support Agent: Prepares user support & FAQ troubleshooting
                await self.update_agent_telemetry(
                    agent_id="support",
                    status="working",
                    character_state="typing",
                    speech="أقوم بإعداد دليل الأسئلة الشائعة وتدفق خدمة العملاء...",
                    step_details="صياغة دليل الدعم الفني وتجربة المستخدم...",
                    active_task="إعداد دليل الدعم الفني وحلول المشاكل",
                    progress=90
                )
                support_loop = AutonomousAgentLoop(
                    agent_id="support",
                    agent_name="وكيل الدعم الفني والخدمة",
                    role="Senior Customer Success & Support Engineer",
                    tools=tools,
                    llm=self.llm,
                    event_callback=self._broadcast
                )
                sup_out = await support_loop.run(
                    task_goal=f"إعداد دليل الدعم وخدمة العملاء والأسئلة الشائعة لـ: {clean_request}",
                    context=results["architecture"]
                )
                results["support"] = sup_out.get("summary", "")
                await self.update_agent_telemetry(
                    agent_id="support",
                    status="done",
                    character_state="celebrating",
                    speech="دليل خدمة العملاء والدعم الفني مكتمل وجاهز!",
                    step_details="تم إنجاز ملفات الدعم الفني.",
                    progress=100
                )

                # Broadcast handoff from support to report
                await self._broadcast("agent_handoff", {
                    "from_agent": "support",
                    "from_agent_name": self.agents_state["support"]["name"],
                    "to_agent": "report",
                    "to_agent_name": self.agents_state["report"]["name"],
                    "task": "توليد التقرير التنفيذي الشامل",
                    "message": f"تم نقل المهمة وتسليم ملفات الدعم من {self.agents_state['support']['name']} إلى {self.agents_state['report']['name']}"
                })
                await asyncio.sleep(0.3)

                # 6. Report Agent: Aggregates KPIs, metrics & final executive report
                await self.update_agent_telemetry(
                    agent_id="report",
                    status="working",
                    character_state="thinking",
                    speech="جاري جمع كافة المخرجات وتلخيص التقرير التنفيذي الشامل للمدير...",
                    step_details="توليد تقرير الإنجاز ومؤشرات الأداء...",
                    active_task="توليد التقرير التنفيذي الشامل",
                    progress=98
                )
                report_loop = AutonomousAgentLoop(
                    agent_id="report",
                    agent_name="وكيل التقارير والإحصائيات",
                    role="Business Intelligence & Data Analyst",
                    tools=tools,
                    llm=self.llm,
                    event_callback=self._broadcast
                )
                rep_out = await report_loop.run(
                    task_goal="توليد تقرير إنجاز تنفيذي شامل يوضح ما تم إنجازه وروابط الملفات وإحصائيات التنفيذ.",
                    context=str(results)
                )
                results["report"] = rep_out.get("summary", "")
                await self.update_agent_telemetry(
                    agent_id="report",
                    status="done",
                    character_state="celebrating",
                    speech="التقرير التنفيذي الشامل جاهز للعرض على شاشة المدير! 📊",
                    step_details="اكتمل التقرير التنفيذي وتم اعتماده.",
                    progress=100
                )

            # Refresh and commit automatic revision snapshot
            files_list = self.project_manager.list_project_files(project_id)
            results["files_created"] = files_list
            commit_msg = clean_request[:60] if len(clean_request) > 5 else "تحديث آلي بواسطة Net Agent"
            author = actual_target if actual_target != "all" else "Net Agent Team"
            snapshot = self.project_manager.revisions.create_snapshot(project_id, ws_dir, commit_msg, author)

            # Update memory & deliverables
            self.memory.update_deliverables(session_id, results)

            # Finalize
            results["status"] = "completed"
            await self._broadcast("workflow_completed", {
                "results": results,
                "project_id": project_id,
                "session_id": session_id,
                "files_count": len(files_list),
                "snapshot_id": snapshot.get("id"),
                "task_name": clean_request[:60],
                "message": f"اكتملت جميع مراحل المهمة بنجاح: {clean_request[:60]}"
            })

            return results

        except asyncio.CancelledError:
            print("[Mission Cancelled] User stopped current run.")
            await self._broadcast("workflow_cancelled", {"message": "تم إيقاف المهمة بواسطة المدير."})
            results["status"] = "cancelled"
            return results
        except Exception as e:
            print(f"[Mission Error] {e}")
            import traceback
            traceback.print_exc()
            await self._broadcast("workflow_error", {"error": str(e)})
            results["status"] = "failed"
            results["error"] = str(e)
            return results
        finally:
            self.is_running = False
            self._current_run_task = None
