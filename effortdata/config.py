"""Paths. Data folder precedence: argument `dir` > env EFFORT_DATA_DIR > config.yml `data_dir` > default 'data'.
Relative paths are resolved against the repository root, never against the working directory."""
import os, re
from pathlib import Path

DEFAULTS = dict(data_dir='data', tables_subdir='thesis_data_main/31-participants-2026-09-06/tables',
                export_subdir='thesis_data_main/vps-export-2026-09-28',
                uploads_glob='thesis_data_uploads*/upload-*.json.gz', cache_dir='cache')

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def config() -> dict:
    cfg = dict(DEFAULTS); f = repo_root() / 'config.yml'
    if f.exists():
        for line in f.read_text(encoding='utf-8').splitlines():
            m = re.match(r'^([A-Za-z_]+)\s*:\s*(.*?)\s*(#.*)?$', line)
            if m and m.group(2): cfg[m.group(1)] = m.group(2).strip('"\'')
    for k in cfg:
        if os.environ.get('EFFORT_' + k.upper()): cfg[k] = os.environ['EFFORT_' + k.upper()]
    return cfg

def _abs(p) -> Path:
    p = Path(p).expanduser(); return p if p.is_absolute() else repo_root() / p

def data_dir(dir=None) -> Path:
    d = _abs(dir or config()['data_dir'])
    if not d.is_dir():
        raise FileNotFoundError(f'Data folder not found: {d}. Copy the study data into <repo>/data/ (see data/README.md), '
                                'or set EFFORT_DATA_DIR / data_dir in config.yml.')
    return d.resolve()

def _sub(key, dir=None) -> Path:
    p = data_dir(dir) / config()[key]
    if not p.is_dir(): raise FileNotFoundError(f'{p} not found - see data/README.md for the expected layout.')
    return p

def tables_dir(dir=None) -> Path: return _sub('tables_subdir', dir)
def export_dir(dir=None) -> Path: return _sub('export_subdir', dir)

def cache_dir() -> Path:
    d = _abs(config()['cache_dir']); d.mkdir(parents=True, exist_ok=True); return d

def fig_dir(name) -> Path:
    """<repo>/output/<name>/ (tracked: figures only)."""
    d = repo_root() / 'output' / name; d.mkdir(parents=True, exist_ok=True); return d
