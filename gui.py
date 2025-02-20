# gui.py
import sys
import os
import re  # logic.py に移動しても良い
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                               QWidget, QInputDialog, QMessageBox, QListWidget,
                               QHBoxLayout, QAbstractItemView)

from .logic import copy_save_files, delete_save_files, load_save_files, get_missing_files, list_backups  # .logicから
from .utils import natural_sort_key  # .utils から


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

    def copy_save(self):
        src_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE")
        dst_base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        os.makedirs(dst_base_dir, exist_ok=True)  # ディレクトリ作成

        if not os.path.exists(src_dir):
            QMessageBox.critical(self, "エラー", "UNDERTALEフォルダが見つかりません")
            return

        while True:
            name, ok = QInputDialog.getText(self, "名前入力", "バックアップ名:")
            if not ok or not name.strip():
                return
            if re.search(r'[\\/:*?"<>|]', name):
                QMessageBox.warning(self, "エラー", "使えない文字があります")
                continue

            try:
                copy_save_files(src_dir, dst_base_dir, name) # logicの関数を呼び出し
                QMessageBox.information(self, "成功", "保存しました")
                self.update_list()
                break
            except FileExistsError:
                QMessageBox.warning(self, "エラー", "名前が重複しています")
                continue
            except ValueError:
                reply = QMessageBox.question(
                    self, "確認", "同じ内容があります。保存しますか？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    try:
                        # 同じ内容でも上書き保存を許可
                        copy_save_files(src_dir, dst_base_dir, name)
                        QMessageBox.information(self, "成功", "保存しました")
                        self.update_list()
                        break
                    except Exception as e:
                        QMessageBox.critical(self, "エラー", f"失敗: {e}")
                        return
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"失敗: {e}")
                return

    def delete_save(self):
        selected = self.list_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "エラー", "選択してください")
            return

        if QMessageBox.question(
            self, "確認", f"{len(selected)}個削除しますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.No:
            return

        base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")
        try:
            deleted_names = [item.text() for item in selected]
            delete_save_files(base_dir, deleted_names) # logic の関数を呼び出し
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
        backup_path = os.path.join(
            os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles", backup_name
        )
        undertale_save_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE")


        missing_files = get_missing_files(undertale_save_path, backup_path) # logicの関数

        if missing_files:
            missing_files_str = "\n".join(missing_files)
            reply = QMessageBox.question(
                self, "確認",
                f"「{backup_name}」をロードすると、以下のファイルが失われます:\n\n"
                f"{missing_files_str}\n\nロードしますか？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        try:
            load_save_files(backup_path, undertale_save_path) # logicの関数
            QMessageBox.information(self, "成功", f"「{backup_name}」をロードしました。")

        except Exception as e:
            QMessageBox.critical(
                self, "エラー",
                f"ロードに失敗しました: {e}\n"
                f"元のセーブデータは一時退避ファイルにあります。"
            )

    def update_list(self):
        base_dir = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "UNDERTALE-SAVEfiles")

        self.list_widget.clear()
        backups = list_backups(base_dir)  # logic.py の関数を呼び出す
        backups.sort(key=natural_sort_key)  # utils.py の関数でソート
        self.list_widget.addItems(backups)