# SPDX-License-Identifier: GPL-3.0-only

import subprocess
import sys
from pathlib import Path


command = [sys.executable, "-m", "pytest", "-q", "--tb=short"]
result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
Path("pytest-diagnostic.txt").write_text(result.stdout, encoding="utf-8")
print("\n".join(result.stdout.splitlines()[-160:]))
raise SystemExit(result.returncode)
