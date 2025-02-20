# utils.py
import re
import hashlib
import os

def natural_sort_key(s):
    """自然順ソート用のキー関数"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]


def simple_hash(dirpath):
    """ディレクトリの簡易ハッシュ計算"""
    hasher = hashlib.md5()
    for root, _, files in os.walk(dirpath):
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, dirpath)
            hasher.update(relpath.encode('utf-8'))
            try:
                with open(filepath, 'rb') as f:
                    while chunk := f.read(4096):
                        hasher.update(chunk)
            except OSError:
                pass
    return hasher.hexdigest()