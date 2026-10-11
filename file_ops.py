# -*- coding: utf-8 -*-
import os
import shutil
import time
import zipfile
import hashlib

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".3gp", ".webm"}
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
DOC_EXT = {".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"}
ARCHIVE_EXT = {".zip", ".rar", ".7z", ".tar", ".gz"}

TRASH_DIR_NAME = ".nasser_trash"


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["ب", "ك.ب", "م.ب", "غ.ب"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ت.ب"


def file_category(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    if ext in IMAGE_EXT:
        return "صور"
    if ext in VIDEO_EXT:
        return "فيديو"
    if ext in AUDIO_EXT:
        return "صوتيات"
    if ext in DOC_EXT:
        return "مستندات"
    if ext in ARCHIVE_EXT:
        return "أرشيف"
    return "أخرى"


def list_dir(path: str, show_hidden: bool = False, sort_by: str = "name", reverse: bool = False):
    entries = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                if not show_hidden and entry.name.startswith("."):
                    continue
                try:
                    stat = entry.stat()
                except OSError:
                    continue
                entries.append({
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": entry.is_dir(follow_symlinks=False),
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                })
    except OSError:
        return []

    key_map = {
        "name": lambda e: e["name"].lower(),
        "size": lambda e: e["size"],
        "date": lambda e: e["mtime"],
        "type": lambda e: os.path.splitext(e["name"])[1].lower(),
    }
    key_fn = key_map.get(sort_by, key_map["name"])
    entries.sort(key=lambda e: (not e["is_dir"], key_fn(e)), reverse=reverse)
    return entries


def search_files(root: str, query: str, by_ext: str = None, show_hidden: bool = False, max_results: int = 500):
    results = []
    query_lower = query.lower() if query else ""
    for dirpath, dirnames, filenames in os.walk(root):
        if not show_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            filenames = [f for f in filenames if not f.startswith(".")]
        for name in filenames:
            if by_ext and not name.lower().endswith(by_ext.lower()):
                continue
            if query_lower and query_lower not in name.lower():
                continue
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0
            results.append({"name": name, "path": full, "size": size})
            if len(results) >= max_results:
                return results
    return results


def create_folder(parent: str, name: str) -> str:
    new_path = os.path.join(parent, name)
    os.makedirs(new_path, exist_ok=False)
    return new_path


def create_text_file(parent: str, name: str, content: str = "") -> str:
    new_path = os.path.join(parent, name)
    with open(new_path, "w", encoding="utf-8") as f:
        f.write(content)
    return new_path


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_text_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def rename_item(path: str, new_name: str) -> str:
    parent = os.path.dirname(path)
    new_path = os.path.join(parent, new_name)
    os.rename(path, new_path)
    return new_path


def copy_item(src: str, dst_dir: str) -> str:
    name = os.path.basename(src.rstrip("/"))
    dst = os.path.join(dst_dir, name)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return dst


def move_item(src: str, dst_dir: str) -> str:
    name = os.path.basename(src.rstrip("/"))
    dst = os.path.join(dst_dir, name)
    shutil.move(src, dst)
    return dst


def _trash_dir(storage_root: str) -> str:
    t = os.path.join(storage_root, TRASH_DIR_NAME)
    os.makedirs(t, exist_ok=True)
    return t


def move_to_trash(path: str, storage_root: str) -> str:
    trash = _trash_dir(storage_root)
    name = os.path.basename(path.rstrip("/"))
    stamp = str(int(time.time()))
    dst = os.path.join(trash, f"{stamp}__{name}")
    shutil.move(path, dst)
    return dst


def list_trash(storage_root: str):
    trash = _trash_dir(storage_root)
    items = []
    for entry in os.scandir(trash):
        orig_name = entry.name.split("__", 1)[-1] if "__" in entry.name else entry.name
        items.append({"path": entry.path, "name": entry.name, "original_name": orig_name})
    return items


def restore_from_trash(trash_path: str, restore_dir: str) -> str:
    base = os.path.basename(trash_path)
    orig_name = base.split("__", 1)[-1] if "__" in base else base
    dst = os.path.join(restore_dir, orig_name)
    shutil.move(trash_path, dst)
    return dst


def permanent_delete(path: str):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def empty_trash(storage_root: str):
    trash = _trash_dir(storage_root)
    for entry in os.scandir(trash):
        permanent_delete(entry.path)


def zip_items(paths, dst_zip_path: str) -> str:
    with zipfile.ZipFile(dst_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            if os.path.isdir(p):
                base = os.path.dirname(p.rstrip("/"))
                for dirpath, _, filenames in os.walk(p):
                    for fn in filenames:
                        full = os.path.join(dirpath, fn)
                        arcname = os.path.relpath(full, base)
                        zf.write(full, arcname)
            else:
                zf.write(p, os.path.basename(p))
    return dst_zip_path


def unzip_file(zip_path: str, dst_dir: str) -> str:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dst_dir)
    return dst_dir


def file_hash(path: str, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(root: str, show_hidden: bool = False):
    by_size = {}
    for dirpath, dirnames, filenames in os.walk(root):
        if not show_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            filenames = [f for f in filenames if not f.startswith(".")]
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            by_size.setdefault(size, []).append(full)

    duplicates = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_hash = {}
        for p in paths:
            try:
                h = file_hash(p)
            except OSError:
                continue
            by_hash.setdefault(h, []).append(p)
        for h, group in by_hash.items():
            if len(group) > 1:
                duplicates.append(group)
    return duplicates


def disk_usage(path: str):
    total, used, free = shutil.disk_usage(path)
    return {
        "total": total,
        "used": used,
        "free": free,
        "total_h": human_size(total),
        "used_h": human_size(used),
        "free_h": human_size(free),
    }
