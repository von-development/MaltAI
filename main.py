import uvicorn
import sys
from pathlib import Path

# Add the project root to Python path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from backend.api.routes import app

if __name__ == "__main__":
    uvicorn.run("backend.api.routes:app", host="127.0.0.1", port=8000, reload=True) 