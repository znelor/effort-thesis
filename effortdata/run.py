"""Small helpers for the figure scripts: per-script out/ folder and a results dict saved as JSON."""
import json, sys
from pathlib import Path
def out_dir(script):
    d = Path(script).resolve().parent / 'out'; d.mkdir(exist_ok=True); return d
def save_results(script, res: dict):
    f = out_dir(script) / 'results.json'; f.write_text(json.dumps(res, indent=2, default=float)); print(json.dumps(res, indent=1, default=float)[:3000])
