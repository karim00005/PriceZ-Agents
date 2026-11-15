# 🏢 منصة PriceZ Agents — المكتب الافتراضي ثلاثي الأبعاد لإدارة وكلاء الذكاء الاصطناعي

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)](https://threejs.org/)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Windows%20Desktop-orange.svg)]()

> **PriceZ Agents** هو مشروع ومصدر مفتوح بالكامل (Full-Stack Open Source) يُحوّل مفهوم منصات الذكاء الاصطناعي وفرق العمل الذاتية (Autonomous AI Agents) من مجرد شاشات شات تقليدية أو جداول بيانات صماء، إلى **مكتب تقني ثلاثي الأبعاد تفاعلي وحي (Interactive 3D Virtual AI Office)** يتيح لك رؤية وإدارة وتوجيه موظفيك من الذكاء الاصطناعي وكأنك تدير فريق عمل حقيقي داخل مقر شركة برمجيات حديثة!

---

## 🌟 أبرز مميزات المشروع

### 1. 🏢 مكتب ثلاثي الأبعاد حي وتفاعلي (Three.js & WebGL)
- **بيئة عمل 3D متكاملة**: مكتب مفتوح بتصميم مستقبلي يضم مكاتب خشبية حديثة، كراسي مريحة، أجهزة لابتوب وشاشات عرض، نباتات زينة، قاعة اجتماعات زجاجية، وركن للقهوة والاستراحة (Coffee Lounge).
- **محاكاة حية لسلوكيات الموظفين (Agent Behavior Simulation)**:
  - **أثناء العمل (Working)**: يتوجه الموظف إلى مكتبه الخاص، يجلس على كرسيه، وتظهر حركة كتابته على لوحة المفاتيح مع إضاءة شاشته وشريط تقدم حي للمهمة.
  - **في وضع الانتظار (Idle)**: يتحرك الموظف ويتجول بحرية في ممرات المكتب، أو يستريح في ركن القهوة أو بجوار النوافذ المطلة على أفق المدينة.
  - **أثناء التفكير والتحليل (Thinking)**: تظهر مؤشرات تحليلية وتأثيرات ضوئية تفاعلية حول الموظف.
  - **عند إتمام المهمة (Completed)**: يومض مؤشر الإنجاز باللون الأخضر مع حركة احتفالية تدل على النجاح.
- **تحكم سلس بالكاميرا (3D Camera System)**:
  - تدوير حر (Rotate)، تقريب وتكبير (Zoom)، وتحريك المشهد (Pan).
  - كاميرات سريعة جاهزة: رؤية المكتب بالكامل، قسم البرمجة، قسم الأبحاث، قسم التسويق، وقاعة الاجتماعات.

---

### 2. 🖱️ لوحة تحكم تفاعلية للموظفين (Agent Drawer & Inspector)
- عند النقر على أي شخصية 3D في المكتب يفتح درج جانبي يعرض:
  - اسم الموظف ودوره الوظيفي.
  - حالة الموظف اللحظية والمهام الجارية مع شريط النسبة المئوية.
  - إمكانية **تعديل وتسمية أي موظف وتغيير تخصصه** بضغطة زر.
  - إرسال تكليف بمهمة جديدة فوراً (Direct Task Assignment).
  - سجل الأنشطة والمهام السابقة وسجلات التنفيذ (Execution Logs).

---

### 3. 🔔 إشعارات المتصفح الفورية والمؤثرات الصوتية (Web Push & Audio FX)
- **إشعارات سطح المكتب والمتصفح (Native Browser Push Notifications)**:
  - تنبيه فوري بصوت مميز فور انتهاء أي مهمة أو تدفق عمل كامل.
  - إشعار لحظي عند نقل المهمة تلقائياً من وكيل إلى وكيل آخر (Agent Handoff).
- **مُولّد نغمات تفاعلي (Web Audio API Synthesizer)**:
  - يعمل بدون الحاجة لأي ملفات صوتية خارجية أو استهلاك لباقة الإنترنت؛ يتم توليد النغمات برمجياً بالكامل.
- زر تفعيل/إلغاء الإشعارات بنقرة واحدة من شريط القوائم العلوي.

---

### 4. 🚀 تشغيل المشروعات لايف واستعراض الكود (Live Sandbox & Code Viewer)
- **معاينة المشروعات لايف (Live Project Preview)**:
  - إمكانية تشغيل ومعاينة صفحات الويب والتطبيقات التي يبنيها الوكلاء مباشرة داخل نافذة تفاعلية (Live iframe Sandbox).
- **مستكشف الكود (Interactive Code Explorer)**:
  - استعراض هيكل الملفات والمجلدات للكود الناتج.
  - تلوين الكود البرمجي (Syntax Highlighting) لجميع اللغات (HTML, JS, Python, SQL, CSS).
  - إمكانية نسخ وتحميل الملفات المنشأة بنقرة واحدة.

---

### 5. 👥 نظام إدارة المستخدمين والصلاحيات (Auth & Multi-User System)
- **تسجيل دخول آمن (Secure Authentication)**:
  - دعم جلسات تسجيل الدخول برمز الجلسة (Session Tokens).
  - تشفير كلمات المرور باستخدام خوارزمية SHA-256 مع التمليح العشوائي (Salt).
- **لوحة إدارة الفريق (User Management)**:
  - يستطيع المدير (Admin) إضافة مستخدمين جدد، تعديل كلمات المرور، أو تعطيل وحذف الحسابات.
- **تخصيص المفاتيح والنماذج لكل مستخدم (Per-User LLM API Keys)**:
  - يمكن لكل عضو في الفريق ضبط مفتاح الـ API الخاص به واختيار المزود المفضل له (Gemini / OpenAI / OpenRouter / Ollama) بشكل مستقل تماماً.

---

### 6. 🧠 دعم كامل لـ 14 نموذج ذكاء اصطناعي مجاني عبر OpenRouter
بالإضافة إلى Google Gemini (2.5 Flash / Pro) و OpenAI GPT-4o، يدعم النظام قائمة موسعة من أقوى النماذج المجانية العالمية عبر OpenRouter:
1. `nvidia/nemotron-3-ultra-550b-a55b:free`
2. `nvidia/nemotron-3.5-super-vl:free`
3. `baidu/ernie-5.5-flash-preview:free`
4. `nvidia/nemotron-3.5-lightning:free`
5. `thinkingmachines/inkling-2-small:free`
6. `dots-studio/dots-3-note-preview:free`
7. `particle-ai/particle-1:free`
8. `cohere/north-mini-code:free`
9. `recursive/flint-v1.0:free`
10. `nvidia/nemotron-3-nano-omni:free`
11. `inclusionai/ling-3.2-flash:free`
12. `liquid/lfm-3-1.7b:free`
13. `google/gemma-4-31b-it:free`
14. `openrouter/free`

---

### 7. 🖥️ تطبيق ديسكتوب لنظام ويندوز (Windows Desktop App)
- إمكانية تشغيل المنصة كتطبيق سطح مكتب مدمج بملء الشاشة مع نافذة أصلية عبر مكتبة `pywebview`.
- يتصل بسيرفر محلي أو سيرفر سحابي بضغطة زر واحدة.

---

## 🏗️ المعمارية والتقنيات المستخدمة (Tech Stack)

| الطبقة | التقنيات |
| :--- | :--- |
| **الخلفية (Backend)** | Python 3.10+, FastAPI, Uvicorn, WebSockets, HTTPX, Pydantic |
| **محرك الرسوميات (3D Graphics)** | Three.js, WebGL, OrbitControls, Tween.js |
| **الواجهة الأمامية (Frontend)** | Modern Vanilla JavaScript, Tailwind CSS (CDN), Web Audio API, Web Notifications API |
| **تطبيق سطح المكتب (Desktop)** | PyWebView (WebView2 / Chromium Engine) |
| **إدارة البيانات (Storage & Persistence)** | Atomic JSON Engine, Revisions Control, File Watcher |

---

## ⚡ خطوات التثبيت والتشغيل المحلي (Quick Start)

### 1. استنساخ المستودع (Clone Repository)
```bash
git clone https://github.com/karim00005/PriceZ-Agents.git
cd PriceZ-Agents
```

### 2. إنشاء بيئة عمل بايثون وتفعيلها (Virtual Environment)
```bash
# على ويندوز (Windows)
python -m venv venv
venv\Scripts\activate

# على لينكس أو ماك (Linux / macOS)
python3 -m venv venv
source venv/bin/activate
```

### 3. تثبيت المتطلبات (Install Dependencies)
```bash
pip install -r requirements.txt
```

### 4. إعداد متغيرات البيئة (Environment Variables)
قم بنسخ ملف الإعدادات التجريبي وتعديل الخيارات إذا لزم:
```bash
copy .env.example .env
```

### 5. تشغيل خادم الويب (Start Server)
```bash
python main.py
```
افتح المتصفح وتوجه إلى:
👉 **[http://localhost:7432](http://localhost:7432)**

### 6. تشغيل تطبيق الديسكتوب (Desktop App)
```bash
python desktop_app.py
```

---

## 🔑 بيانات الدخول الافتراضية (Default Credentials)

المنصة مهيأة مسبقاً بحساب المسؤول الرئيسي الافتراضي:

| اسم المستخدم (Username) | كلمة المرور (Password) | الصلاحية (Role) |
| :--- | :--- | :--- |
| `admin` | `admin123` | مدير النظام (Admin) — صلاحيات إدارية كاملة |

*ملاحظة: يمكنك تغيير كلمة المرور أو إضافة أعضاء جدد بكل سهولة من خلال زر **إدارة المستخدمين** في شريط القائمة العلوي.*

---

## 🔒 الأمان وحماية البيانات (Security & Privacy)

- **بدون أسرار مضمنة**: تم فحص المستودع بالكامل لضمان خلوه من أي مفاتيح خاصة، عناوين سيرفرات، أو بيانات اعتماد حساسة.
- **حفظ محلي مستقل**: يتم حفظ بيانات المستخدمين وإعدادات النماذج محلياً على جهازك أو سيرفرك الخاص، ولا يتم إرسال أي مفاتيح API لأي طرف ثالث.
- **تشفير كلمات المرور**: استخدام خوارزمية SHA-256 مع Random Salt لمنع هجمات Rainbow Tables.

---

## 📄 الترخيص (License)

هذا المشروع مرخص تحت رخصة **MIT License** — وهو متاح للاستخدام الشخصي والتجاري والتطوير بحرية تامة. لمزيد من التفاصيل راجع ملف [LICENSE](LICENSE).

---

⭐ إذا أعجبك المشروع، لا تنسَ ترك نجمة (Star) على المستودع في GitHub لدعم استمرار التطوير!
