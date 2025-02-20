import sys
import os
import shutil
import re
import hashlib
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                               QWidget, QInputDialog, QMessageBox, QListWidget,
                               QHBoxLayout, QAbstractItemView)

class SaveFileCopier(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("セーブファイル管理")
        self.setGeometry(100, 100, 450, 300)

        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("保存")
        self.copy_button.clicked.connect(self.copy_save)
        button_layout.addWidget(self.copy_button)

        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_save)
        button_layout.addWidget(self.delete_button)

        self.load_button = QPushButton("ロード")
        self.load_button.clicked.connect(self.load_save)
        button_layout.addWidget(self.load_button)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.list_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.update_list()

    def simple_hash(self, dirpath):
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

    def copy_save(self):
        src_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE")
        dst_base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        os.makedirs(dst_base_dir, exist_ok=True)

        if not os.path.exists(src_dir):
            QMessageBox.critical(self, "エラー", "UNDERTALEフォルダが見つかりません")
            return

        while True:
            name, ok = QInputDialog.getText(self, "名前入力", "バックアップ名:")
            if not ok or not name.strip():
                return
            else:
                if re.search(r'[\\/:*?"<>|]', name):
                    QMessageBox.warning(self, "エラー", "使えない文字があります")
                else:
                    dst_dir = os.path.join(dst_base_dir, name)
                    if os.path.exists(dst_dir):
                        QMessageBox.warning(self, "エラー", "名前が重複しています")
                    else:
                        src_hash = self.simple_hash(src_dir)
                        found_duplicate = False
                        for existing in os.listdir(dst_base_dir):
                            existing_path = os.path.join(dst_base_dir, existing)
                            if os.path.isdir(existing_path) and self.simple_hash(existing_path) == src_hash:
                                reply = QMessageBox.question(self, "確認", "同じ内容があります。保存しますか？",
                                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes:
                                    found_duplicate = True
                                break

                        try:
                            shutil.copytree(src_dir, dst_dir)
                            QMessageBox.information(self, "成功", "保存しました")
                            self.update_list()
                            break
                        except Exception as e:
                            QMessageBox.critical(self, "エラー", f"失敗: {e}")
                            return

    def delete_save(self):
        selected = self.list_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "エラー", "選択してください")
            return

        if QMessageBox.question(self, "確認", f"{len(selected)}個削除しますか？",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No:
            return

        base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        for item in selected:
            path = os.path.join(base_dir, item.text())
            try:
                shutil.rmtree(path)
                QMessageBox.information(self, "成功", "削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"失敗: {e}")
                return

        self.update_list()


    def load_save(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "情報", "ロードするバックアップを選択してください。")
            return

        backup_name = selected_item.text()
        backup_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles", backup_name)
        undertale_save_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE")

        # バックアップとUNDERTALEフォルダのファイルリストを比較
        undertale_files = set(os.path.relpath(os.path.join(root, file), undertale_save_path)
                              for root, _, files in os.walk(undertale_save_path) for file in files)
        backup_files = set(os.path.relpath(os.path.join(root, file), backup_path)
                          for root, _, files in os.walk(backup_path) for file in files)


        missing_files = undertale_files - backup_files # UNDERTALEに存在するが、バックアップにはないファイル

        if missing_files: # 確認ダイアログ
            missing_files_str = "\n".join(missing_files)
            reply = QMessageBox.question(self, "確認",
                                         f"「{backup_name}」をロードすると、以下のファイルが失われます:\n\n"
                                         f"{missing_files_str}\n\nロードしますか？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # 現在のUNDERTALEセーブフォルダを一時的にリネーム
        temp_backup_name = "temp_backup_" + os.path.basename(undertale_save_path)
        temp_backup_path = os.path.join(os.path.dirname(undertale_save_path), temp_backup_name)

        try:
            if os.path.exists(temp_backup_path):
                shutil.rmtree(temp_backup_path)

            os.rename(undertale_save_path, temp_backup_path)
            shutil.copytree(backup_path, undertale_save_path)
            shutil.rmtree(temp_backup_path)

            QMessageBox.information(self, "成功", f"「{backup_name}」をロードしました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ロードに失敗しました: {e}\n"
                                              f"元のセーブデータは {temp_backup_path} に退避されています。")
            if os.path.exists(temp_backup_path):
                if os.path.exists(undertale_save_path):
                    shutil.rmtree(undertale_save_path)
                os.rename(temp_backup_path, undertale_save_path)


    def update_list(self):
        base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        self.list_widget.clear()
        if not os.path.exists(base_dir): return

        items = [item for item in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, item))]
        self.list_widget.addItems(items)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SaveFileCopier()
    window.show()
    sys.exit(app.exec())