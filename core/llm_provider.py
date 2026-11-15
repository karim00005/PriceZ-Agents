import asyncio
import os
import json
from typing import Optional, Dict, Any, Callable, List
import httpx
import config

OPENROUTER_FREE_MODELS: List[Dict[str, str]] = [
    {
        "id": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "name": "NVIDIA Nemotron 3 Ultra 550B",
        "provider": "NVIDIA",
        "badge": "550B فائق القوة 🔥",
        "desc": "نموذج إنفيديا العملاق فائق الدقة 550B للأبحاث والتحليل المعقد"
    },
    {
        "id": "nvidia/nemotron-3.5-super-vl:free",
        "name": "NVIDIA Nemotron 3.5 Super VL",
        "provider": "NVIDIA",
        "badge": "رؤية بصرية وفيديو 👁️",
        "desc": "تحليل متقدم للصور والرسوم البيانية والمستندات البصرية"
    },
    {
        "id": "baidu/ernie-5.5-flash-preview:free",
        "name": "Baidu ERNIE 5.5 Flash Preview",
        "provider": "Baidu",
        "badge": "استدلال فائق ⚡",
        "desc": "نموذج بايدو المتطور ERNIE 5.5 للاستجابة السريعة والمهام المتزامنة"
    },
    {
        "id": "nvidia/nemotron-3.5-lightning:free",
        "name": "NVIDIA Nemotron 3.5 Lightning",
        "provider": "NVIDIA",
        "badge": "خاطف السرعة ⚡",
        "desc": "إنتاج فوري للمخرجات مع سرعة توليد فائقة وكفاءة عالية"
    },
    {
        "id": "thinkingmachines/inkling-2-small:free",
        "name": "Thinking Machines Inkling 2 Small",
        "provider": "ThinkingMachines",
        "badge": "خفيف ورشيق 🪶",
        "desc": "نموذج خفيف مخصص للمهام الفورية والتلخيص السريع"
    },
    {
        "id": "dots-studio/dots-3-note-preview:free",
        "name": "Dots Studio Dots-3 Note Preview",
        "provider": "Dots Studio",
        "badge": "تلخيص وملاحظات 📝",
        "desc": "متخصص في استخراج الأفكار الرئيسية وتدوين الملاحظات والموجزات"
    },
    {
        "id": "particle-ai/particle-1:free",
        "name": "Particle AI Particle-1",
        "provider": "Particle AI",
        "badge": "متعدد المهام 🌐",
        "desc": "نموذج ذكي متعدد الوظائف للردود الدقيقة والتخطيط"
    },
    {
        "id": "cohere/north-mini-code:free",
        "name": "Cohere North Mini Code",
        "provider": "Cohere",
        "badge": "أكواد وبرمجة 💻",
        "desc": "متخصص في هندسة البرمجيات وكتابة الكود وتصحيح الأخطاء البرمجية"
    },
    {
        "id": "recursive/flint-v1.0:free",
        "name": "Recursive Flint v1.0",
        "provider": "Recursive",
        "badge": "منطق وتفكير 🧠",
        "desc": "تفكير منطقي متسلسل وحل المشاكل الحسابية والخطوات المعقدة"
    },
    {
        "id": "nvidia/nemotron-3-nano-omni:free",
        "name": "NVIDIA Nemotron 3 Nano Omni",
        "provider": "NVIDIA",
        "badge": "Nano أومني 🎯",
        "desc": "نموذج مدمج وسريع لمهام الأومني والتفاعل المباشر"
    },
    {
        "id": "inclusionai/ling-3.2-flash:free",
        "name": "InclusionAI Ling 3.2 Flash",
        "provider": "InclusionAI",
        "badge": "لغات وترجمة 🌍",
        "desc": "قدرات استثنائية في فهم وتوليد اللغات والترجمة الاحترافية"
    },
    {
        "id": "liquid/lfm-3-1.7b:free",
        "name": "Liquid LFM 3 1.7B",
        "provider": "Liquid AI",
        "badge": "شبكات ديناميكية 💧",
        "desc": "معمارية عصبية سائلة فائقة الكفاءة وسرعة استجابة مذهلة"
    },
    {
        "id": "google/gemma-4-31b-it:free",
        "name": "Google Gemma 4 31B IT",
        "provider": "Google",
        "badge": "Google Gemma 31B ⭐",
        "desc": "نموذج جوجل مفتوح المصدر 31B ذو كفاءة تعليمية وهندسية استثنائية"
    },
    {
        "id": "openrouter/free",
        "name": "OpenRouter Auto Free Router",
        "provider": "OpenRouter",
        "badge": "توجيه ذكي تلقائي 🔀",
        "desc": "توجيه الطلب تلقائياً إلى أفضل وأسرع نموذج مجاني متاح الآن"
    }
]

class LLMProvider:
    def __init__(
        self,
        provider: str = config.DEFAULT_PROVIDER,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.provider = provider.lower() if provider else "gemini"
        self.api_key = api_key or config.API_KEY or os.environ.get("LLM_API_KEY", "")
        self.model = model or config.DEFAULT_MODEL
        self.base_url = base_url or config.BASE_URL
        self.timeout = config.REQUEST_TIMEOUT

    def update_config(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        if provider:
            self.provider = provider.lower()
        if api_key is not None:
            self.api_key = api_key
        if model:
            self.model = model
        if base_url is not None:
            self.base_url = base_url

    async def test_connection(self) -> Dict[str, Any]:
        """
        Quickly tests the configured provider and API key with a minimal request.
        """
        if self.provider in ("mock", "simulation"):
            return {"success": True, "message": "وضع المحاكاة الذاتي جاهز ونشط بنجاح (لا يتطلب مفتاح API)."}

        if not self.api_key:
            return {"success": False, "error": "لم يتم إدخال مفتاح API Key لهذا المزود."}

        try:
            test_prompt = "Hello! Please reply with exactly: 'OK'"
            res = await asyncio.wait_for(
                self._dispatch_call(system_instruction="You are a helpful assistant.", prompt=test_prompt),
                timeout=15.0
            )
            return {"success": True, "message": f"تم الاتصال بنجاح بمزود ({self.provider}) والنموذج ({self.model}).", "sample": res[:100]}
        except asyncio.TimeoutError:
            return {"success": False, "error": f"انتهت مهلة الاتصال بمزود ({self.provider}) بعد 15 ثانية. تحقق من اتصال الإنترنت أو البروكسي."}
        except Exception as e:
            return {"success": False, "error": f"خطأ أثناء الاتصال: {str(e)}"}

    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        step_callback: Optional[Callable[[str], Any]] = None,
        agent_name: str = "Agent"
    ) -> str:
        """
        Executes call to the configured provider with strict timeout and fallback.
        """
        # If no API key or provider is simulation
        if not self.api_key or self.provider in ("mock", "simulation"):
            if step_callback:
                await step_callback(f"يعمل في الوضع التجريبي الذكي (Smart Simulation)...")
            return await self._simulate_agent_generation(agent_name, prompt, step_callback)

        if step_callback:
            await step_callback(f"جارٍ الاتصال بـ [{self.provider.upper()}] - النموذج: ({self.model})...")

        try:
            # Enforce strict asyncio timeout to prevent UI freezes
            response_text = await asyncio.wait_for(
                self._dispatch_call(system_instruction, prompt),
                timeout=self.timeout
            )
            return response_text

        except asyncio.TimeoutError:
            err_msg = f"انتهت مهلة الاستجابة ({self.timeout} ثانية) من مزود {self.provider}. جاري التبديل للمحاكي الذكي..."
            print(f"[{agent_name} Timeout] {err_msg}")
            if step_callback:
                await step_callback(err_msg)
            return await self._simulate_agent_generation(agent_name, prompt, step_callback)

        except Exception as e:
            err_msg = f"خطأ في مزود {self.provider}: {str(e)}. جاري استخدام المحاكي الذكي لتجنب تعطل الواجهة."
            print(f"[{agent_name} Error] {err_msg}")
            if step_callback:
                await step_callback(err_msg)
            return await self._simulate_agent_generation(agent_name, prompt, step_callback)

    async def _dispatch_call(self, system_instruction: str, prompt: str) -> str:
        """
        Routes the prompt to the appropriate provider handler.
        """
        if self.provider == "openrouter":
            return await self._call_openrouter(system_instruction, prompt)
        elif self.provider == "deepseek":
            return await self._call_deepseek(system_instruction, prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(system_instruction, prompt)
        elif self.provider in ("openai", "openai_compatible", "groq", "cursor"):
            return await self._call_openai_compatible(system_instruction, prompt)
        elif self.provider == "gemini":
            return await self._call_gemini(system_instruction, prompt)
        else:
            # Default to OpenRouter or OpenAI compatible if base_url is set
            if self.base_url:
                return await self._call_openai_compatible(system_instruction, prompt)
            return await self._call_gemini(system_instruction, prompt)

    # ==========================================
    # 1. OpenRouter Handler
    # ==========================================
    async def _call_openrouter(self, system_instruction: str, prompt: str) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/karim00005/PriceZ-Agents",
            "X-Title": "PriceZ Agents Command Center",
            "Content-Type": "application/json"
        }
        # Default to first free model if not specified or incomplete
        model = self.model if self.model and ("/" in self.model or ":free" in self.model) else (self.model or "nvidia/nemotron-3-ultra-550b-a55b:free")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                err_text = resp.text
                try:
                    err_json = resp.json()
                    if "error" in err_json and isinstance(err_json["error"], dict):
                        err_text = err_json["error"].get("message", err_text)
                except Exception:
                    pass
                raise RuntimeError(f"OpenRouter ({resp.status_code}): {err_text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ==========================================
    # 2. DeepSeek Handler
    # ==========================================
    async def _call_deepseek(self, system_instruction: str, prompt: str) -> str:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        model = self.model or "deepseek-chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"DeepSeek HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ==========================================
    # 3. Anthropic (Claude) Handler
    # ==========================================
    async def _call_anthropic(self, system_instruction: str, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        model = self.model or "claude-3-5-sonnet-20241022"
        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_instruction,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Anthropic HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            content = data.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return ""

    # ==========================================
    # 4. OpenAI / Groq / Cursor / Compatible Handler
    # ==========================================
    async def _call_openai_compatible(self, system_instruction: str, prompt: str) -> str:
        base = self.base_url.rstrip("/") if self.base_url else "https://api.groq.com/openai/v1"
        url = f"{base}/chat/completions" if not base.endswith("/chat/completions") else base

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        model = self.model or "llama-3.3-70b-versatile"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"API Provider HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ==========================================
    # 5. Google Gemini Direct REST Handler
    # ==========================================
    async def _call_gemini(self, system_instruction: str, prompt: str) -> str:
        model = self.model or "gemini-2.5-flash"
        # Clean model name if user gave models/prefix
        if model.startswith("models/"):
            model = model.replace("models/", "")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4
            }
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            raise RuntimeError(f"Empty response from Gemini API: {data}")

    # ==========================================
    # 6. High-Fidelity Smart Simulation Mode
    # ==========================================
    async def _simulate_agent_generation(self, agent_name: str, prompt: str, step_callback=None) -> str:
        clean_prompt = prompt.replace("\n", " ")[:120]
        if "Orchestrator" in agent_name:
            steps = [
                "تحليل المتطلبات وفهم نطاق المشروع...",
                f"تفكيك الطلب: ({clean_prompt})...",
                "رسم المعمارية التقنية وتحديد طبقات الاتصال والبيانات...",
                "صياغة المهام الذرية وتحديد معايير القبول (Acceptance Criteria)..."
            ]
            for step in steps:
                if step_callback:
                    await step_callback(step)
                await asyncio.sleep(0.9)

            return f"""# 🏛️ وثيقة المعمارية وتوزيع المهام (Architecture Blueprint)

## 1. ملخص المشروع والهدف العام
- **الهدف الأساسي:** بناء نظام متكامل ومستقر لتحقيق المطلوب: "{clean_prompt}..."
- **نمط المعمارية:** Clean Architecture / Microservice Adapter Pattern
- **التقنيات المستخدمة:** Python 3.13, Async IO, Protocol Adapters, Real-time WebSockets

## 2. الطبقات البرمجية وتدفق البيانات
1. **Device Communication Layer (بروتوكول الاتصال):** التعامل مع أجهزة البصمة والشبكات عبر بروتوكولات TCP/IP Socket و ZK-Protocol.
2. **Business & Processing Layer:** معالجة حركات الحضور والانصراف، استخراج السجلات، ومطابقة بصمات المستخدمين.
3. **API & Dispatcher Layer:** واجهات RESTful و WebSockets لبث العمليات لحظياً.

## 3. المهام المسندة للمبرمج (Tasks for Senior Coder)
- **المهمة 1:** بناء كلاس الاتصال الأساسي `ZKTecoDeviceClient` مع إعادة المحاولة التلقائية ومعالجة مهلات الشبكة (Timeouts).
- **المهمة 2:** برمجة دوال سحب سجلات الحضور (`fetch_attendance_logs`) وسحب بيانات الموظفين (`get_users`).
- **المهمة 3:** توفير واجهة برمجية FastAPI للتحكم بالأجهزة وجلب الحركات لحظياً.

## 4. معايير القبول والاعتماد (Acceptance Criteria)
- [x] عزل أخطاء الاتصال وفصل الجهاز دون إسقاط الخادم (Graceful Reconnection).
- [x] دعم التشفير والتحقق من صحة المدخلات.
- [x] توفير كود كامل وقابل للتشغيل المباشر.
"""

        elif "Coder" in agent_name:
            steps = [
                "استلام المخطط المعماري من المخطط ومراجعة معايير القبول...",
                "بناء كلاس الاتصال بالجهاز ومصفوفات السجلات...",
                "تطبيق معالجة أخطاء الشبكة والاتصال غير المتزامن (Async)...",
                "كتابة كود الإنتاج النظيف مع التوثيق الكامل..."
            ]
            for step in steps:
                if step_callback:
                    await step_callback(step)
                await asyncio.sleep(1.0)

            return f"""```python
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZKTecoBridge")

class AttendanceRecord(BaseModel):
    user_id: str = Field(..., description="رقم الموظف في جهاز البصمة")
    timestamp: datetime = Field(..., description="وقت وتاريخ حركة البصمة")
    status: int = Field(default=0, description="حالة الحركة (0: دخول، 1: خروج)")
    punch_type: str = Field(default="Fingerprint", description="نوع البصمة المستخدمة")

class DeviceConfig(BaseModel):
    ip_address: str = Field(default="192.168.1.201", description="عنوان IP لجهاز البصمة")
    port: int = Field(default=4370, description="المنفذ الافتراضي لأجهزة ZKTeco")
    timeout_sec: float = Field(default=5.0, description="مهلة الاتصال")

class ZKTecoDeviceClient:
    \"\"\"
    عميل برمجي متقدم للتواصل مع أجهزة البصمة ZKTeco عبر الشبكة المحلية.
    يدعم إعادة الاتصال التلقائي وتدفق البيانات غير المتزامن.
    \"\"\"
    def __init__(self, config: DeviceConfig):
        self.config = config
        self.is_connected = False
        self._reader = None
        self._writer = None

    async def connect(self) -> bool:
        \"\"\"فتح اتصال شبكي آمن مع ماكينة البصمة\"\"\"
        try:
            logger.info(f"محاولة الاتصال بماكينة البصمة على: {{self.config.ip_address}}:{{self.config.port}}")
            # محاكاة اتصال شبكي غير متزامن
            await asyncio.sleep(0.5)
            self.is_connected = True
            logger.info("تم الاتصال بماكينة البصمة بنجاح.")
            return True
        except Exception as e:
            logger.error(f"فشل الاتصال بماكينة البصمة: {{e}}")
            self.is_connected = False
            return False

    async def get_live_attendance(self) -> List[AttendanceRecord]:
        \"\"\"سحب حركات الحضور والانصراف المخزنة على الجهاز\"\"\"
        if not self.is_connected:
            await self.connect()

        # استخراج وتنسيق الحركات
        records = [
            AttendanceRecord(user_id="101", timestamp=datetime.now(), status=0, punch_type="Fingerprint"),
            AttendanceRecord(user_id="102", timestamp=datetime.now(), status=0, punch_type="FaceID"),
            AttendanceRecord(user_id="103", timestamp=datetime.now(), status=1, punch_type="Fingerprint"),
        ]
        return records

    async def disconnect(self):
        \"\"\"إغلاق الجلسة وتحرير الموارد بأمان\"\"\"
        self.is_connected = False
        logger.info("تم إغلاق الاتصال بماكينة البصمة.")

# مثال تشغيلي مباشر
if __name__ == "__main__":
    async def main():
        client = ZKTecoDeviceClient(DeviceConfig(ip_address="192.168.1.201"))
        if await client.connect():
            logs = await client.get_live_attendance()
            print(f"تم سحب {{len(logs)}} حركة حضور:")
            for log in logs:
                print(f" -> موظف: {{log.user_id}} | الوقت: {{log.timestamp.strftime('%H:%M:%S')}} | نوع: {{log.punch_type}}")
            await client.disconnect()

    asyncio.run(main())
```"""

        elif "Auditor" in agent_name:
            steps = [
                "فحص سلامة الكود والتحقق من معايير الأمان ومكتبات الاتصال...",
                "اختبار سيناريوهات انقطاع كابل الشبكة وإعادة الاتصال التلقائي...",
                "التحقق من صحة نماذج Pydantic ومنع حقن البيانات...",
                "مطابقة المخرجات مع معايير القبول وإصدار القرار النهائي..."
            ]
            for step in steps:
                if step_callback:
                    await step_callback(step)
                await asyncio.sleep(0.9)

            return """# 🛡️ تقرير التدقيق الأمني وضمان الجودة (QA & Security Audit)

## 1. ملخص المراجعة والقرار النهائي
- **القرار النهائي:** ✅ **معتمد للنشر (PASSED)**
- **مستوى الأمان البرمجي:** 98/100
- **تقييم جودة وتماسك الكود:** ممتاز (Production-Ready)

## 2. فحص الأمان والحماية
- **التحقق من المدخلات (Data Validation):** تم استخدام Pydantic (`AttendanceRecord` و `DeviceConfig`) لضمان صحة البيانات ومنع حقن أي قيم غير صالحة.
- **إدارة الموارد (Resource Management):** توفير دالة `disconnect` آمنة لمنع تسريب منافذ السوكت (Socket Leaks).
- **التعامل مع الشبكة:** تم ضبط مهلة اتصال محددة (`timeout_sec`) لمنع تجميد الخادم عند انقطاع الاتصال بالجهاز.

## 3. الأداء ومطابقة المتطلبات
- **نمط التشغيل غير المتزامن (Async/Await):** تم تطبيق النمط بامتياز لمنع حظر خيط التنفيذ الرئيسي.
- **تغطية معايير القبول:** تم تغطية جميع المعايير المحددة من قِبل المخطط بنجاح كامل.
"""
        else:
            return "تم إنجاز المهمة بنجاح."
