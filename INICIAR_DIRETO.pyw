import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "venv" / "Lib" / "site-packages"))

import main_app

main_app.main()
