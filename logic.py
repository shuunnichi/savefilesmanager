# logic.py
import os
import shutil
from .utils import simple_hash  # .utils からインポート


def copy_save_files(src_dir, dst_base_dir, name):
    """セーブファイルをコピー"""
    dst_dir = os.path.join(dst_base_dir, name)
    if os.path.exists(dst_dir):
        raise FileExistsError(f"「{name}」はすでに存在します。")

    src_hash = simple_hash(src_dir)
    for existing in os.listdir(dst_base_dir):
        existing_path = os.path.join(dst_base_dir, existing)
        if os.path.isdir(existing_path) and simple_hash(existing_path) == src_hash:
            raise ValueError(f"同じ内容のバックアップ「{existing}」が既に存在します。")

    shutil.copytree(src_dir, dst_dir)
    return dst_dir


def delete_save_files(base_dir, backup_names):
    """バックアップを削除"""
    deleted_paths = []
    for name in backup_names:
        path = os.path.join(base_dir, name)
        shutil.rmtree(path)
        deleted_paths.append(path)
    return deleted_paths

def load_save_files(backup_path, undertale_save_path):
    """バックアップをロード"""
     # 現在のUNDERTALEセーブフォルダを一時的にリネーム
    temp_backup_name = "temp_backup_" + os.path.basename(undertale_save_path)
    temp_backup_path = os.path.join(os.path.dirname(undertale_save_path), temp_backup_name)

    if os.path.exists(temp_backup_path):
        shutil.rmtree(temp_backup_path)

    os.rename(undertale_save_path, temp_backup_path)
    shutil.copytree(backup_path, undertale_save_path)
    shutil.rmtree(temp_backup_path) #一時ファイルを消す
    return undertale_save_path



def get_missing_files(undertale_save_path, backup_path):
    """ロード時に失われるファイルのリストを取得"""
    undertale_files = set(
        os.path.relpath(os.path.join(root, file), undertale_save_path)
        for root, _, files in os.walk(undertale_save_path) for file in files
    )
    backup_files = set(
        os.path.relpath(os.path.join(root, file), backup_path)
        for root, _, files in os.walk(backup_path) for file in files
    )
    return undertale_files - backup_files


def list_backups(base_dir):
    """バックアップのリストを取得"""
    if not os.path.exists(base_dir):
        return []
    return [
        item for item in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, item))
    ]