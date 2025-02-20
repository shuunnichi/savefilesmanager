import sys
import os
import shutil
import re
import hashlib
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                               QWidget, QInputDialog, QMessageBox, QListWidget,
                               QHBoxLayout, QAbstractItemView)  # QHBoxLayout, QAbstractItemViewを追加


class SaveFileCopier(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Save File Copier")
        self.setGeometry(100, 100, 400, 300)

        main_layout = QVBoxLayout()  # メインのレイアウト

        # ボタン用レイアウト
        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("現在のデータを保存")
        self.copy_button.clicked.connect(self.copy_save_files)
        button_layout.addWidget(self.copy_button)

        self.delete_button = QPushButton("選択したバックアップを削除")  # 削除ボタン
        self.delete_button.clicked.connect(self.delete_selected_backup)
        button_layout.addWidget(self.delete_button)

        main_layout.addLayout(button_layout)  # ボタンレイアウトをメインレイアウトに追加


        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection) # 複数選択を許可
        main_layout.addWidget(self.file_list_widget)

        container = QWidget()
        container.setLayout(main_layout)  # メインレイアウトを設定
        self.setCentralWidget(container)

        self.show_save_files()

    def dir_hash(self, dirpath):
        hasher = hashlib.md5()
        for root, _, files in os.walk(dirpath):
            for file in files:
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, dirpath)
                hasher.update(relpath.encode('utf-8'))
                try:
                    with open(filepath, 'rb') as f:
                        while True:
                            buf = f.read(4096)
                            if not buf:
                                break
                            hasher.update(buf)
                except OSError:
                    continue
        return hasher.hexdigest()

    def copy_save_files(self):
        source_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE")
        save_base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")

        os.makedirs(save_base_dir, exist_ok=True)

        if not os.path.exists(source_dir):
            QMessageBox.critical(self, "Error", f"元のセーブファイルディレクトリが見つかりません:\n{source_dir}")
            return

        while True:
            name, ok = QInputDialog.getText(self, "バックアップ名入力", "保存する名前を入力してください:")
            if not ok:
                return

            name = name.strip()
            if not name:
                QMessageBox.warning(self, "無効な名前", "名前を入力してください。")
                continue

            if re.search(r'[\\/:*?"<>|]', name):
                QMessageBox.warning(self, "無効な名前", "使用できない文字が含まれています。\n\\ / : * ? \" < > | は使えません。")
                continue

            destination_dir = os.path.join(save_base_dir, name)

            if os.path.exists(destination_dir):
                QMessageBox.warning(self, "名前重複", f"「{name}」はすでに存在します。\n別の名前を入力してください。")
                continue

            source_hash = self.dir_hash(source_dir)
            for existing_dir in os.listdir(save_base_dir):
                existing_dir_path = os.path.join(save_base_dir, existing_dir)
                if os.path.isdir(existing_dir_path):
                    if self.dir_hash(existing_dir_path) == source_hash:
                        reply = QMessageBox.question(self, "確認",
                                                     f"同じ内容のバックアップセット「{existing_dir}」が既に存在します。\nこのまま保存しますか？",
                                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.No:
                            continue
                        break

            try:
                shutil.copytree(source_dir, destination_dir)
                QMessageBox.information(self, "成功", f"セーブファイル一式をコピーしました:\n{destination_dir}")
                self.show_save_files()
                break
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"コピーに失敗しました: {e}")
                return

    def show_save_files(self):
        save_base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        self.file_list_widget.clear()

        if not os.path.exists(save_base_dir):
            QMessageBox.information(self, "情報", "UNDERTALE-SAVEfiles フォルダーが存在しません。")
            return

        items = [item for item in os.listdir(save_base_dir) if os.path.isdir(os.path.join(save_base_dir, item))]

        if not items:
            QMessageBox.information(self, "情報", "UNDERTALE-SAVEfiles フォルダーにバックアップセットがありません。")
            return

        self.file_list_widget.addItems(items)


    def delete_selected_backup(self):
        """選択されたバックアップを削除する"""
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "情報", "削除するバックアップを選択してください。")
            return

        # 確認ダイアログを表示
        reply = QMessageBox.question(self, "確認",
                                     f"{len(selected_items)} 個のバックアップを削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        save_base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        for item in selected_items:
            backup_name = item.text()
            backup_path = os.path.join(save_base_dir, backup_name)
            try:
                shutil.rmtree(backup_path)  # ディレクトリとその内容を再帰的に削除
                QMessageBox.information(self,"成功",f"{backup_name}を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました: {e}")
                return  # 失敗したらループを抜ける

        self.show_save_files()  # リストを更新


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SaveFileCopier()
    window.show()
    sys.exit(app.exec())