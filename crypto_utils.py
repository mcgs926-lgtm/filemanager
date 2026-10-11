# -*- coding: utf-8 -*-
import os
import json
import base64
import hashlib
import hmac
import secrets

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

APP_DIR = os.path.join(os.path.expanduser("~"), ".nasser_fm")
CONFIG_PATH = os.path.join(APP_DIR, "config.dat")
PBKDF2_ITER = 200_000
SALT_SIZE = 16
IV_SIZE = 16
KEY_SIZE = 32

DEFAULT_MASTER_PASSWORD = "nasser2025"


def ensure_app_dir():
    if not os.path.isdir(APP_DIR):
        os.makedirs(APP_DIR, exist_ok=True)


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITER,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


def _pad(data: bytes) -> bytes:
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len]) * pad_len


def _unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("بيانات تالفة أو كلمة السر غير صحيحة")
    return data[:-pad_len]


def encrypt_bytes(plain: bytes, password: str) -> bytes:
    salt = secrets.token_bytes(SALT_SIZE)
    iv = secrets.token_bytes(IV_SIZE)
    key = _derive_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(_pad(plain)) + encryptor.finalize()
    mac = hmac.new(key, salt + iv + ct, hashlib.sha256).digest()
    return salt + iv + mac + ct


def decrypt_bytes(blob: bytes, password: str) -> bytes:
    salt = blob[:SALT_SIZE]
    iv = blob[SALT_SIZE:SALT_SIZE + IV_SIZE]
    mac = blob[SALT_SIZE + IV_SIZE:SALT_SIZE + IV_SIZE + 32]
    ct = blob[SALT_SIZE + IV_SIZE + 32:]
    key = _derive_key(password, salt)
    expected_mac = hmac.new(key, salt + iv + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("كلمة السر غير صحيحة أو الملف تالف")
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    return _unpad(padded)


def encrypt_file(src_path: str, password: str, dst_path: str = None) -> str:
    with open(src_path, "rb") as f:
        data = f.read()
    blob = encrypt_bytes(data, password)
    if dst_path is None:
        dst_path = src_path + ".nlock"
    with open(dst_path, "wb") as f:
        f.write(blob)
    if dst_path != src_path:
        os.remove(src_path)
    return dst_path


def decrypt_file(src_path: str, password: str, dst_path: str = None) -> str:
    with open(src_path, "rb") as f:
        blob = f.read()
    data = decrypt_bytes(blob, password)
    if dst_path is None:
        if src_path.endswith(".nlock"):
            dst_path = src_path[:-6]
        else:
            dst_path = src_path + ".dec"
    with open(dst_path, "wb") as f:
        f.write(data)
    if dst_path != src_path:
        os.remove(src_path)
    return dst_path


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITER)


def load_config() -> dict:
    ensure_app_dir()
    if not os.path.isfile(CONFIG_PATH):
        salt = secrets.token_bytes(SALT_SIZE)
        pw_hash = _hash_password(DEFAULT_MASTER_PASSWORD, salt)
        cfg = {
            "salt": base64.b64encode(salt).decode("ascii"),
            "hash": base64.b64encode(pw_hash).decode("ascii"),
            "theme": "dark",
            "show_hidden": False,
            "favorites": [],
            "recent": [],
        }
        save_config(cfg)
        return cfg
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict):
    ensure_app_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False)


def verify_master_password(password: str) -> bool:
    cfg = load_config()
    salt = base64.b64decode(cfg["salt"])
    expected = base64.b64decode(cfg["hash"])
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, expected)


def set_master_password(new_password: str):
    cfg = load_config()
    salt = secrets.token_bytes(SALT_SIZE)
    pw_hash = _hash_password(new_password, salt)
    cfg["salt"] = base64.b64encode(salt).decode("ascii")
    cfg["hash"] = base64.b64encode(pw_hash).decode("ascii")
    save_config(cfg)
