import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uvicorn
import config

if __name__ == "__main__":
    print(f"🚀 Starting PriceZ Multi-Agent Command Center at http://{config.HOST}:{config.PORT}")
    uvicorn.run("api.server:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
