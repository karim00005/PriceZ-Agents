# 🏢 PriceZ Agents — Autonomous 3D Virtual AI Office & Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)](https://threejs.org/)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Desktop%20(Windows)-orange.svg)]()

> 📖 **[اضغط هنا لقراءة التوثيق والشرح الكامل باللغة العربية (Arabic Documentation)](README_AR.md)**

> **PriceZ Agents** is an open-source, full-stack autonomous AI workforce platform. It transforms standard agent workflows into a **live, interactive 3D virtual office**, enabling teams and managers to oversee, interact with, and orchestrate specialized AI employees in real-time.

---

## 🌟 Key Features

### 1. 🏢 Interactive 3D Virtual AI Office (Three.js & WebGL)
- **Live 3D Environment**: Fully rendered technology workspace featuring modern ergonomic desks, laptops, monitors, plants, glass partitions, and conference zones.
- **Dynamic Character Behaviors**: Characters automatically reflect agent execution states via real-time WebSockets:
  - **Working**: Sits at assigned desk, typing animations, glowing displays, real-time progress bars.
  - **Idle**: Walks around the office corridor, relaxes in lounge areas, or visits the coffee bar.
  - **Done / Success**: Celebratory animations with glowing status indicators.
- **Interactive Inspection Drawer**: Click any 3D employee or workstation to reveal:
  - Live agent telemetry and reasoning stream.
  - Custom name and role editor.
  - Historic task logs and deliverables.
  - Instant direct task delegation controls.

### 2. 🔔 Real-Time Browser Push Notifications & Audio Synthesis
- **Web Push Notifications**: Native desktop & browser notifications whenever:
  - An agent completes a mission (`workflow_completed`).
  - A task is handed over from one agent to another (`agent_handoff`).
- **Web Audio API Chimes**: Built-in harmonic synthesizer generating melodic feedback without external audio file dependencies.
- **One-Click Bell Toggle**: Integrated navbar control to activate or check browser notification permissions.

### 3. 👥 User Authentication & Team Management Dashboard
- **Secure Authentication**: SHA-256 + salt password hashing with persistent 30-day session management.
- **Team Management Portal**:
  - View all registered team members, their roles, avatars, and custom API key statuses.
  - Create new team members with customizable permissions (Admin, Team Lead, Software Engineer, Marketer, Viewer).
  - Modify user details, reset passwords, or deactivate accounts.
- **Per-User API Keys**: Every team member can configure and securely store their own LLM API key, isolated from other users.

### 4. ⚡ Multi-LLM Provider Engine & 14 Free OpenRouter Models
- **Supported Providers**: Google Gemini, OpenRouter, DeepSeek, Anthropic Claude, and OpenAI-compatible endpoints (Groq, Ollama, vLLM).
- **14 Pre-Configured Free OpenRouter Models** with 1-click quick-selection pills:
  1. `nvidia/nemotron-3-ultra-550b-a55b:free` *(550B flagship)*
  2. `nvidia/nemotron-3.5-super-vl:free` *(Vision & Multimodal)*
  3. `baidu/ernie-5.5-flash-preview:free` *(High-speed reasoning)*
  4. `nvidia/nemotron-3.5-lightning:free` *(Ultra-fast response)*
  5. `thinkingmachines/inkling-2-small:free` *(Lightweight)*
  6. `dots-studio/dots-3-note-preview:free` *(Summarization)*
  7. `particle-ai/particle-1:free` *(General-purpose)*
  8. `cohere/north-mini-code:free` *(Coding & software engineering)*
  9. `recursive/flint-v1.0:free` *(Logic & sequential reasoning)*
  10. `nvidia/nemotron-3-nano-omni:free` *(Nano omni multimodal)*
  11. `inclusionai/ling-3.2-flash:free` *(Multilingual & translation)*
  12. `liquid/lfm-3-1.7b:free` *(Dynamic neural architecture)*
  13. `google/gemma-4-31b-it:free` *(Google Gemma open model)*
  14. `openrouter/free` *(Intelligent automated free router)*

### 5. 🖥️ Live Project Sandbox & Multi-Device Preview
- **In-App Sandbox**: Instantly execute and preview project code (HTML, JS, CSS, Python servers) inside an embedded runner.
- **Responsive Device Viewports**: Switch between Desktop (100%), Tablet (768px), and Mobile (375px) device frames with real-time logs.

### 6. 📱 Hybrid Web & Desktop Architecture
- **Web Command Center**: Accessible via standard modern browsers on port `7432`.
- **Native Desktop App**: Built-in Windows desktop wrapper powered by `pywebview` with two-way cloud synchronization.

---

## 🏗️ System Architecture

```
PriceZ Agents Architecture
├── Frontend (static/)
│   ├── index.html          (Glassmorphic UI, modals, telemetry, preview)
│   ├── js/office-3d.js     (Three.js 3D Virtual AI Office Engine)
│   └── libs/               (Three.js, OrbitControls, TWEEN.js)
├── Backend (api/)
│   └── server.py           (FastAPI application, WebSockets, REST APIs)
├── Core Engine (core/)
│   ├── crew.py             (Orchestrator crew, multi-agent pipelines)
│   ├── agent.py            (Autonomous agent definitions & behaviors)
│   ├── agent_loop.py       (Iterative ReAct agent loop execution)
│   ├── auth.py             (Authentication, sessions & user management)
│   ├── llm_provider.py     (Unified multi-provider LLM connector)
│   ├── project_manager.py  (Workspace sandboxes & file operations)
│   └── revisions.py        (Automated commit snapshots & revisions)
├── Runtime
│   ├── main.py             (FastAPI / Uvicorn server launcher)
│   ├── desktop_app.py      (PyWebView native desktop application)
│   └── config.py           (Centralized environment configuration)
└── Storage (data/)
    ├── users.json          (Encrypted user records & personal configs)
    ├── sessions.json       (Active auth sessions)
    └── snapshots/          (Project version history)
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- Modern web browser (Chrome, Edge, Firefox, or Safari)

### 1. Clone the Repository
```bash
git clone https://github.com/karim00005/PriceZ-Agents.git
cd PriceZ-Agents
```

### 2. Set Up Virtual Environment
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration (Optional)
Copy the example environment configuration:
```bash
cp .env.example .env
```
Default port is `7432`. You can optionally supply your LLM keys in `.env` or input them directly through the web UI per user.

### 5. Launch the Server
```bash
python main.py
```
Open your browser and navigate to:
👉 **[http://localhost:7432](http://localhost:7432)**

### 6. Launch the Native Desktop App (Windows)
```bash
python desktop_app.py
```

---

## 👥 Default Credentials

The platform is pre-configured with the following default administrator account:

| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | Administrator | Full Admin Access & User Management |

*Note: You can add new team members, create custom usernames, and configure per-user LLM API keys from the **User Management** (إدارة المستخدمين) panel.*

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, WebSockets, HTTPX, Pydantic
- **3D Graphics**: Three.js, WebGL, OrbitControls, Tween.js
- **Frontend**: HTML5, Modern Vanilla JS, Tailwind CSS (CDN), Web Audio API, Web Notifications API
- **Desktop Runtime**: PyWebView (Chromium / WebView2)
- **Deployment**: Ubuntu Linux, Nginx (SSL Reverse Proxy), PM2 Process Daemon

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details. Open-source and free for developers worldwide.

---

<p align="center">
  Built with ❤️ for autonomous AI multi-agent orchestration.
</p>
