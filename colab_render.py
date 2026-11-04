"""Render project Remotion dari GitHub di Google Colab.

Cara pakai di Colab:
  !wget -q https://raw.githubusercontent.com/idinlabs-dev/render-remotion/main/colab_render.py
  %run colab_render.py

Sebelum menjalankan, pilih Runtime -> Change runtime type -> T4 GPU.
Repository public, jadi tidak perlu token GitHub.
"""
from __future__ import annotations
import io, json, os, pathlib, re, shutil, subprocess, sys, time, zipfile

# ====== UBAH BAGIAN INI JIKA PERLU ======
REPO = os.environ.get("RENDER_REPO", "idinlabs-dev/render-remotion")
BRANCH = os.environ.get("RENDER_BRANCH", "main")
PROJECT = os.environ.get("RENDER_PROJECT", "peter-episode1")
COMPOSITION = os.environ.get("RENDER_COMPOSITION", "")
CONCURRENCY = int(os.environ.get("RENDER_CONCURRENCY", "4"))
# ========================================

ROOT = pathlib.Path("/content/remotion-render")
PROJECT_ROOT = ROOT / "project"

def run(cmd, **kwargs):
    print("$", " ".join(map(str, cmd)))
    kwargs.setdefault("text", True)
    kwargs.setdefault("bufsize", 1)
    kwargs.setdefault("env", {**os.environ, "PYTHONUNBUFFERED": "1"})
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
    code = process.wait()
    if code != 0:
        raise subprocess.CalledProcessError(code, cmd)

def get_token():
    return os.environ.get("GITHUB_TOKEN", "")

def install_system():
    run(["bash", "-lc", "sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg libnss3 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libasound2t64 libxrandr2 libxkbcommon-x11-0 libxfixes3 libxcomposite1 libxdamage1 libgbm-dev libcups2 libpango-1.0-0 libcairo2 unzip curl"])
    run(["bash", "-lc", "if ! command -v node >/dev/null; then curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y -qq nodejs; fi"])

def download_project(token):
    import requests
    if ROOT.exists(): shutil.rmtree(ROOT)
    PROJECT_ROOT.mkdir(parents=True)
    url = f"https://api.github.com/repos/{REPO}/contents/projects/{PROJECT}.zip?ref={BRANCH}"
    headers = {"Accept": "application/vnd.github.raw"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(PROJECT_ROOT)
    if not (PROJECT_ROOT / "package.json").exists():
        children = [p for p in PROJECT_ROOT.iterdir() if p.name != "__MACOSX"]
        if len(children) == 1 and children[0].is_dir() and (children[0] / "package.json").exists():
            return children[0]
    if not (PROJECT_ROOT / "package.json").exists():
        raise RuntimeError("package.json tidak ditemukan dalam ZIP project")
    return PROJECT_ROOT

def detect(project_root):
    cfg = {}
    config_file = project_root / "render.json"
    if config_file.exists():
        cfg = json.loads(config_file.read_text())
    entry = cfg.get("entry", "")
    if not entry:
        for candidate in ("src/index.ts", "src/index.tsx", "src/index.js", "src/index.jsx"):
            if (project_root / candidate).exists():
                entry = candidate
                break
    if not entry:
        raise RuntimeError("Entry Remotion tidak ditemukan")
    requested = COMPOSITION or cfg.get("composition", "")
    result = subprocess.run(["npx", "remotion", "compositions", entry, "--quiet"], cwd=project_root, text=True, capture_output=True, check=True)
    ids = result.stdout.strip().splitlines()[-1].split()
    composition = requested or (ids[0] if ids else "")
    if composition not in ids:
        raise RuntimeError(f"Composition tidak valid: {composition}; pilihan: {ids}")
    return entry, composition, cfg.get("args", [])

def main():
    token = get_token()
    install_system()
    project_root = download_project(token)
    print("Project root:", project_root)
    print("\n=== INSTALL DEPENDENCY PROJECT ===", flush=True)
    run(["npm", "install", "--no-audit", "--no-fund", "--loglevel", "info"], cwd=project_root)
    print("\n=== SIAPKAN BROWSER REMOTION ===", flush=True)
    run(["npx", "remotion", "browser", "ensure"], cwd=project_root)
    entry, composition, extra = detect(project_root)
    print(f"\n=== KOMPOSISI TERPILIH: {composition} ===", flush=True)
    output = project_root / "out" / f"{PROJECT}.mp4"
    output.parent.mkdir(exist_ok=True)
    command = ["npx", "remotion", "render", entry, composition, str(output), "--codec=h264", "--gl=angle", f"--concurrency={CONCURRENCY}", "--log=verbose"] + [str(x) for x in extra]
    print("\n=== MULAI RENDER — LOG REAL-TIME ===", flush=True)
    run(command, cwd=project_root)
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("Render selesai tetapi file MP4 tidak ditemukan")
    print(f"\nSELESAI: {output} ({output.stat().st_size:,} bytes)")
    try:
        from google.colab import files
        files.download(str(output))
    except Exception:
        print("Download otomatis hanya tersedia di Google Colab.")

if __name__ == "__main__":
    main()
