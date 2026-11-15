import json
import hashlib
import secrets
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

AVATARS = [
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=150",
    "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&q=80&w=150",
    "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?auto=format&fit=crop&q=80&w=150",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=150",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=150",
    "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=150"
]

class AuthManager:
    """
    Manages user authentication, sessions, team permissions, and per-user LLM API configs.
    Persists data in data/users.json and data/sessions.json.
    """
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.sessions_file = self.data_dir / "sessions.json"
        self.sessions: Dict[str, Dict[str, Any]] = {}  # token -> {username, created_at, expires_at}
        self.users: Dict[str, Dict[str, Any]] = {}
        self._load_users()
        self._load_sessions()

    def _hash_password(self, password: str, salt: Optional[str] = None) -> str:
        if not salt:
            salt = secrets.token_hex(8)
        hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"{salt}:{hashed}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt, hashed = stored_hash.split(":", 1)
            calc_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
            return secrets.compare_digest(calc_hash, hashed)
        except Exception:
            return False

    def _load_users(self):
        if self.users_file.exists():
            try:
                self.users = json.loads(self.users_file.read_text(encoding="utf-8"))
            except Exception:
                self.users = {}
        
        # Seed default users if empty
        if not self.users:
            self.users = {
                "admin": {
                    "username": "admin",
                    "name": "PriceZ Admin",
                    "role": "مدير النظام (Admin)",
                    "is_admin": True,
                    "is_active": True,
                    "password_hash": self._hash_password("admin123"),
                    "avatar": AVATARS[0],
                    "created_at": time.time(),
                    "last_login": time.time(),
                    "llm_config": {
                        "provider": "gemini",
                        "api_key": "",
                        "model": "gemini-2.5-flash",
                        "base_url": ""
                    }
                }
            }
            self._save_users()

    def _save_users(self):
        try:
            self.users_file.write_text(json.dumps(self.users, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[AuthManager Error] Failed to save users: {e}")

    def _load_sessions(self):
        if self.sessions_file.exists():
            try:
                data = json.loads(self.sessions_file.read_text(encoding="utf-8"))
                now = time.time()
                # Keep non-expired sessions
                self.sessions = {t: s for t, s in data.items() if s.get("expires_at", 0) > now}
            except Exception:
                self.sessions = {}

    def _save_sessions(self):
        try:
            self.sessions_file.write_text(json.dumps(self.sessions, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[AuthManager Error] Failed to save sessions: {e}")

    def is_user_admin(self, username: str) -> bool:
        u = username.strip().lower()
        if u == "admin":
            return True
        user = self.users.get(u)
        if user:
            return bool(user.get("is_admin") or "مدير" in user.get("role", ""))
        return False

    def login(self, username: str, password: str) -> Dict[str, Any]:
        username = username.strip().lower()
        user = self.users.get(username)
        if not user or not self._verify_password(password, user.get("password_hash", "")):
            return {"success": False, "error": "اسم المستخدم أو كلمة المرور غير صحيحة"}

        if not user.get("is_active", True):
            return {"success": False, "error": "تم تعطيل هذا الحساب من قبل مدير النظام"}

        # Update last login
        user["last_login"] = time.time()
        self._save_users()

        # Generate session token valid for 30 days
        token = secrets.token_hex(24)
        expires_at = time.time() + (30 * 86400)
        self.sessions[token] = {
            "username": username,
            "created_at": time.time(),
            "expires_at": expires_at
        }
        self._save_sessions()

        user_info = {
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "is_admin": self.is_user_admin(username),
            "avatar": user.get("avatar", ""),
            "has_custom_api_key": bool(user.get("llm_config", {}).get("api_key")),
            "provider": user.get("llm_config", {}).get("provider", "gemini"),
            "model": user.get("llm_config", {}).get("model", "gemini-2.5-flash")
        }

        return {
            "success": True,
            "token": token,
            "user": user_info,
            "message": f"مرحباً بك يا {user['name']}!"
        }

    def register(self, username: str, password: str, name: Optional[str] = None, role: str = "مطور ومستخدم") -> Dict[str, Any]:
        username = username.strip().lower()
        if not username or len(username) < 3:
            return {"success": False, "error": "اسم المستخدم يجب أن يكون 3 أحرف على الأقل"}
        if not password or len(password) < 4:
            return {"success": False, "error": "كلمة المرور يجب أن تكون 4 أحرف على الأقل"}
        if username in self.users:
            return {"success": False, "error": "اسم المستخدم مسجل بالفعل"}

        display_name = (name or username).strip()
        idx = len(self.users) % len(AVATARS)
        new_user = {
            "username": username,
            "name": display_name,
            "role": role,
            "is_admin": False,
            "is_active": True,
            "password_hash": self._hash_password(password),
            "avatar": AVATARS[idx],
            "created_at": time.time(),
            "last_login": time.time(),
            "llm_config": {
                "provider": "gemini",
                "api_key": "",
                "model": "gemini-2.5-flash",
                "base_url": ""
            }
        }
        self.users[username] = new_user
        self._save_users()

        return self.login(username, password)

    def list_users(self) -> List[Dict[str, Any]]:
        """Returns all registered users with public details."""
        res = []
        for u in self.users.values():
            res.append({
                "username": u["username"],
                "name": u.get("name", u["username"]),
                "role": u.get("role", "عضو"),
                "is_admin": self.is_user_admin(u["username"]),
                "is_active": u.get("is_active", True),
                "avatar": u.get("avatar", ""),
                "created_at": u.get("created_at", 0),
                "last_login": u.get("last_login", 0),
                "has_custom_api_key": bool(u.get("llm_config", {}).get("api_key")),
                "provider": u.get("llm_config", {}).get("provider", "gemini"),
                "model": u.get("llm_config", {}).get("model", "gemini-2.5-flash")
            })
        return res

    def create_user(
        self,
        creator_username: str,
        username: str,
        password: str,
        name: str,
        role: str = "مطور ومستخدم",
        is_admin: bool = False
    ) -> Dict[str, Any]:
        username = username.strip().lower()
        if not username or len(username) < 3:
            return {"success": False, "error": "اسم المستخدم يجب أن يكون 3 أحرف على الأقل"}
        if not password or len(password) < 4:
            return {"success": False, "error": "كلمة المرور يجب أن تكون 4 أحرف على الأقل"}
        if username in self.users:
            return {"success": False, "error": "اسم المستخدم مسجل بالفعل"}

        idx = len(self.users) % len(AVATARS)
        new_user = {
            "username": username,
            "name": name.strip(),
            "role": role.strip() or "مطور ومستخدم",
            "is_admin": bool(is_admin),
            "is_active": True,
            "password_hash": self._hash_password(password),
            "avatar": AVATARS[idx],
            "created_at": time.time(),
            "last_login": 0,
            "llm_config": {
                "provider": "gemini",
                "api_key": "",
                "model": "gemini-2.5-flash",
                "base_url": ""
            }
        }
        self.users[username] = new_user
        self._save_users()
        return {"success": True, "message": f"تم إنشاء المستخدم '{name}' بنجاح ✨", "user": new_user}

    def update_user(
        self,
        creator_username: str,
        target_username: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        password: Optional[str] = None,
        is_admin: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        target = target_username.strip().lower()
        user = self.users.get(target)
        if not user:
            return {"success": False, "error": "المستخدم غير موجود"}

        if name is not None and name.strip():
            user["name"] = name.strip()
        if role is not None and role.strip():
            user["role"] = role.strip()
        if password is not None and len(password.strip()) >= 4:
            user["password_hash"] = self._hash_password(password.strip())
        if is_admin is not None:
            # Root admin is always admin
            user["is_admin"] = True if target == "admin" else bool(is_admin)
        if is_active is not None:
            # Cannot deactivate root admin
            if target == "admin":
                user["is_active"] = True
            else:
                user["is_active"] = bool(is_active)

        self._save_users()
        return {"success": True, "message": f"تم تحديث بيانات المستخدم '{user['name']}' بنجاح ✅"}

    def delete_user(self, creator_username: str, target_username: str) -> Dict[str, Any]:
        target = target_username.strip().lower()
        if target == "admin":
            return {"success": False, "error": "لا يمكن حذف الحساب الرئيسي لمدير النظام (Admin)"}
        if target == creator_username.strip().lower():
            return {"success": False, "error": "لا يمكنك حذف حسابك الحالي أثناء تسجيل الدخول منه"}

        if target not in self.users:
            return {"success": False, "error": "المستخدم غير موجود"}

        # Delete user
        del self.users[target]
        self._save_users()

        # Invalidate target's sessions
        to_del = [t for t, s in self.sessions.items() if s.get("username") == target]
        for t in to_del:
            del self.sessions[t]
        self._save_sessions()

        return {"success": True, "message": f"تم حذف المستخدم '{target}' بنجاح 🗑️"}

    def get_user_by_token(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        session = self.sessions.get(token)
        if not session:
            return None
        if time.time() > session["expires_at"]:
            del self.sessions[token]
            self._save_sessions()
            return None

        username = session["username"]
        user = self.users.get(username)
        if not user or not user.get("is_active", True):
            return None

        return {
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "is_admin": self.is_user_admin(username),
            "avatar": user.get("avatar", ""),
            "has_custom_api_key": bool(user.get("llm_config", {}).get("api_key")),
            "provider": user.get("llm_config", {}).get("provider", "gemini"),
            "model": user.get("llm_config", {}).get("model", "gemini-2.5-flash")
        }

    def get_user_llm_config(self, username: str) -> Dict[str, Any]:
        user = self.users.get(username)
        if user and "llm_config" in user:
            return user["llm_config"]
        return {
            "provider": "gemini",
            "api_key": "",
            "model": "gemini-2.5-flash",
            "base_url": ""
        }

    def update_user_llm_config(
        self,
        username: str,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        user = self.users.get(username)
        if not user:
            return {"success": False, "error": "المستخدم غير موجود"}

        cfg = user.setdefault("llm_config", {})
        if provider is not None:
            cfg["provider"] = provider
        if api_key is not None:
            cfg["api_key"] = api_key.strip()
        if model is not None:
            cfg["model"] = model.strip()
        if base_url is not None:
            cfg["base_url"] = base_url.strip()

        self._save_users()
        return {
            "success": True,
            "message": "تم حفظ إعدادات الـ API الخاصة بحسابك بنجاح 💾",
            "config": {
                "provider": cfg.get("provider"),
                "has_api_key": bool(cfg.get("api_key")),
                "model": cfg.get("model")
            }
        }

