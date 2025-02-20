import sys
import os
import shutil
import re
import hashlib
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QInputDialog, QMessageBox, QListWidget


class SaveFileCopier(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Save File Copier")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        self.copy_button = QPushButton("現在のデータを保存")
        self.copy_button.clicked.connect(self.copy_save_files)  # メソッド名変更
        layout.addWidget(self.copy_button)

        self.file_list_widget = QListWidget()
        layout.addWidget(self.file_list_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.show_save_files()

    def dir_hash(self, dirpath):
        """ディレクトリ全体のハッシュ値を計算する (簡易版)"""
        #  注意: この方法は、ファイル名、ファイル内容、ディレクトリ構造が完全に一致する場合のみ同じハッシュ値を返します。
        #        より厳密なハッシュ計算が必要な場合は、各ファイルのハッシュ値を計算し、それらを組み合わせてハッシュ値を生成するなどの方法を検討してください。

        hasher = hashlib.md5()
        for root, _, files in os.walk(dirpath):
            for file in files:
                filepath = os.path.join(root, file)
                # ファイルパスをハッシュに追加 (相対パスを使用)
                relpath = os.path.relpath(filepath, dirpath)
                hasher.update(relpath.encode('utf-8'))
                # ファイルの内容のハッシュを追加
                try:
                    with open(filepath, 'rb') as f:
                        while True:
                            buf = f.read(4096)  # 4KB ずつ読み込む
                            if not buf:
                                break
                            hasher.update(buf)
                except OSError: # ファイルが開けないなどのエラーを無視
                    continue
        return hasher.hexdigest()

    def copy_save_files(self):
        source_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE")
        save_base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")

        # UNDERTALE-SAVEfiles フォルダを作成
        os.makedirs(save_base_dir, exist_ok=True)

        if not os.path.exists(source_dir):
            QMessageBox.critical(self, "Error", f"元のセーブファイルディレクトリが見つかりません:\n{source_dir}")
            return

        while True:
            # ユーザーにバックアップセット名を入力させる
            name, ok = QInputDialog.getText(self, "バックアップ名入力", "保存する名前を入力してください:")

            if not ok:  # キャンセルが押されたら中断
                return

            name = name.strip()
            if not name:
                QMessageBox.warning(self, "無効な名前", "名前を入力してください。")
                continue

            # ファイル名の禁止文字をチェック
            if re.search(r'[\\/:*?"<>|]', name):
                QMessageBox.warning(self, "無効な名前", "使用できない文字が含まれています。\n\\ / : * ? \" < > | は使えません。")
                continue

            destination_dir = os.path.join(save_base_dir, name)

            # 同名のバックアップセットがある場合
            if os.path.exists(destination_dir):
                QMessageBox.warning(self, "名前重複",
                                    f"「{name}」はすでに存在します。\n別の名前を入力してください。")
                continue

            # 同じ内容のバックアップセットがあるかチェック
            source_hash = self.dir_hash(source_dir)
            for existing_dir in os.listdir(save_base_dir):
                existing_dir_path = os.path.join(save_base_dir, existing_dir)
                if os.path.isdir(existing_dir_path):  # ディレクトリのみを比較対象にする
                    if self.dir_hash(existing_dir_path) == source_hash:
                        reply = QMessageBox.question(self, "確認",
                                                     f"同じ内容のバックアップセット「{existing_dir}」が既に存在します。\nこのまま保存しますか？",
                                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.No:
                            continue
                        break  # 内側のループを抜ける

            # コピー処理
            try:
                shutil.copytree(source_dir, destination_dir)
                QMessageBox.information(self, "成功", f"セーブファイル一式をコピーしました:\n{destination_dir}")
                self.show_save_files()  # ファイル一覧を更新
                break  # 外側のループを抜ける
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"コピーに失敗しました: {e}")
                return

    def show_save_files(self):
        save_base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        self.file_list_widget.clear()

        if not os.path.exists(save_base_dir):
            QMessageBox.information(self, "情報", "UNDERTALE-SAVEfiles フォルダーが存在しません。")
            return

        # ディレクトリのみをリストアップする
        items = [item for item in os.listdir(save_base_dir) if os.path.isdir(os.path.join(save_base_dir, item))]

        if not items:
            QMessageBox.information(self, "情報", "UNDERTALE-SAVEfiles フォルダーにバックアップセットがありません。")
            return

        self.file_list_widget.addItems(items)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SaveFileCopier()
    window.show()
    sys.exit(app.exec())