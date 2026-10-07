#!/usr/bin/env python3
"""學生專案環境檢查（只讀，不安裝、不下載、不改任何檔案）。

檢查三件事：
  1. Python 套件：能讀 PDF、能寫 Word（python-docx）
  2. ComfyUI：本機有沒有安裝、連線埠 8188 有沒有開、有沒有生圖模型
  3. 其他：Ollama 地端模型（只列出，供參考）

只用標準函式庫，所以即使套件沒裝也能跑。
用法：python check_env.py [--json]
"""
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

MODEL_EXTS = {".safetensors", ".ckpt", ".gguf", ".pt", ".pth", ".sft"}
# 生圖（含影片）模型通常放在這幾個資料夾
MODEL_DIRS = ["checkpoints", "diffusion_models", "unet"]


def has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def check_python():
    result = {"version": sys.version.split()[0], "executable": sys.executable}
    pdf_readers = [m for m in ("fitz", "pypdf", "pdfplumber", "PyPDF2") if has_module(m)]
    result["pdf_read"] = {"ok": bool(pdf_readers), "found": pdf_readers,
                          "install": "pymupdf"}
    result["word_write"] = {"ok": has_module("docx"), "install": "python-docx"}
    result["pillow"] = {"ok": has_module("PIL"), "install": "pillow"}
    return result


def candidate_roots():
    """ComfyUI 常見安裝位置（不遞迴掃整顆硬碟，避免太慢）。"""
    home = Path(os.path.expanduser("~"))
    roots = []
    env = os.environ.get("COMFYUI_PATH")
    if env:
        roots.append(Path(env))
    names = ["ComfyUI", "ComfyUI_windows_portable", "ComfyUI_windows_portable\\ComfyUI",
             "ComfyUI-aki-v1.6", "ComfyUI-aki-v1.7"]
    bases = [Path("C:/"), Path("D:/"), Path("E:/"), home, home / "Desktop",
             home / "Documents", home / "Downloads"]
    for b in bases:
        for n in names:
            roots.append(b / n)
            roots.append(b / n / "ComfyUI")
    # ComfyUI 桌面版會在 config.json 記錄 basePath
    for cfg in (Path(os.environ.get("APPDATA", "")) / "ComfyUI" / "config.json",
                home / "AppData" / "Roaming" / "ComfyUI" / "config.json"):
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            for key in ("basePath", "base_path"):
                if data.get(key):
                    roots.append(Path(data[key]))
        except Exception:
            pass
    seen, out = set(), []
    for r in roots:
        key = str(r).lower()
        if key in seen:
            continue
        seen.add(key)
        # 判斷條件：有 main.py 與 models 資料夾，或有 models 資料夾與 custom_nodes
        if r.is_dir() and ((r / "main.py").exists() or (r / "custom_nodes").is_dir()) \
                and (r / "models").is_dir():
            out.append(r)
    return out


def list_models(root):
    found = []
    for d in MODEL_DIRS:
        folder = root / "models" / d
        if not folder.is_dir():
            continue
        for p in folder.rglob("*"):
            if p.is_file() and p.suffix.lower() in MODEL_EXTS:
                try:
                    gb = round(p.stat().st_size / 1024 ** 3, 2)
                except OSError:
                    gb = None
                found.append({"folder": d, "name": p.name, "size_gb": gb})
    return found


def port_open(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def comfy_http(url):
    """連得上就回報版本與顯卡（只讀 /system_stats）。"""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/system_stats", timeout=3) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        sysinfo = data.get("system", {})
        devices = [d.get("name") for d in data.get("devices", [])]
        return {"reachable": True, "comfyui_version": sysinfo.get("comfyui_version"),
                "devices": devices}
    except Exception as e:
        return {"reachable": False, "error": type(e).__name__}


def check_comfyui():
    result = {"installed_paths": [], "models": [], "server": None}
    for root in candidate_roots():
        result["installed_paths"].append(str(root))
        result["models"].extend(list_models(root))
    url = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
    host_port = url.split("//")[-1].split("/")[0]
    host, _, port = host_port.partition(":")
    port = int(port) if port.isdigit() else 80
    if port_open(host or "127.0.0.1", port):
        result["server"] = {"url": url, **comfy_http(url)}
    else:
        result["server"] = {"url": url, "reachable": False}
    result["has_image_model"] = bool(result["models"])
    return result


def check_ollama():
    exe = shutil.which("ollama")
    if not exe:
        return {"installed": False}
    try:
        out = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=10,
                             encoding="utf-8", errors="replace").stdout
        names = [ln.split()[0] for ln in out.strip().splitlines()[1:] if ln.strip()]
    except Exception:
        names = []
    return {"installed": True, "models": names}


def main():
    report = {"python": check_python(), "comfyui": check_comfyui(), "ollama": check_ollama()}
    if "--json" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    py, cf, ol = report["python"], report["comfyui"], report["ollama"]
    mark = lambda ok: "[OK] " if ok else "[缺] "
    print("== Python ==")
    print(f"  版本 {py['version']}（{py['executable']}）")
    print("  " + mark(py["pdf_read"]["ok"]) + "讀取 PDF："
          + (", ".join(py["pdf_read"]["found"]) if py["pdf_read"]["ok"]
             else "沒有任何 PDF 套件（建議安裝 pymupdf）"))
    print("  " + mark(py["word_write"]["ok"]) + "寫入 Word：python-docx"
          + ("" if py["word_write"]["ok"] else "（需安裝 python-docx）"))
    print("  " + mark(py["pillow"]["ok"]) + "圖片處理（選用）：pillow")
    print("== ComfyUI ==")
    if cf["installed_paths"]:
        for p in cf["installed_paths"]:
            print(f"  [OK] 找到安裝資料夾：{p}")
    else:
        print("  [未偵測] 常見位置都沒找到 ComfyUI（可能裝在別處，或在學校主機上跑）")
    srv = cf["server"]
    if srv.get("reachable"):
        print(f"  [OK] 連線成功：{srv['url']}"
              + (f"（版本 {srv.get('comfyui_version')}）" if srv.get("comfyui_version") else "")
              + (f"，顯卡：{', '.join(srv['devices'])}" if srv.get("devices") else ""))
    else:
        print(f"  [未連線] {srv['url']} 沒有回應（ComfyUI 沒開，或位址不是這個）")
    if cf["models"]:
        print(f"  [OK] 找到 {len(cf['models'])} 個模型檔：")
        for m in cf["models"][:15]:
            size = f"{m['size_gb']} GB" if m["size_gb"] is not None else "?"
            print(f"       {m['folder']}/{m['name']}（{size}）")
        if len(cf["models"]) > 15:
            print(f"       …還有 {len(cf['models']) - 15} 個")
    elif cf["installed_paths"]:
        print("  [缺] 有 ComfyUI 但 checkpoints／diffusion_models／unet 裡沒有模型檔")
    print("== Ollama（地端語言模型，僅供參考）==")
    if ol["installed"]:
        print("  [OK] 已安裝；模型：" + (", ".join(ol["models"]) or "（無）"))
    else:
        print("  [未偵測] 沒有安裝")


if __name__ == "__main__":
    main()
