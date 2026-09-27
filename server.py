import os
import sys
from pathlib import Path

# Add bot directory to path so all imports work seamlessly
root_dir = Path(__file__).resolve().parent
bot_dir = root_dir / "bot"
if str(bot_dir) not in sys.path:
    sys.path.insert(0, str(bot_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from bot.server import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
