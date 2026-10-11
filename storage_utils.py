# -*- coding: utf-8 -*-
import os

try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.storage import primary_external_storage_path
    ON_ANDROID = True
except ImportError:
    ON_ANDROID = False


def get_storage_root() -> str:
    if ON_ANDROID:
        try:
            return primary_external_storage_path()
        except Exception:
            pass
    return os.path.expanduser("~")


def request_storage_permissions(callback=None):
    if not ON_ANDROID:
        if callback:
            callback(True)
        return
    perms = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]

    def _on_result(permissions, grants):
        ok = all(grants)
        if callback:
            callback(ok)

    request_permissions(perms, _on_result)


def has_storage_permission() -> bool:
    if not ON_ANDROID:
        return True
    try:
        return check_permission(Permission.READ_EXTERNAL_STORAGE) and check_permission(
            Permission.WRITE_EXTERNAL_STORAGE
        )
    except Exception:
        return False
