from typing import Dict, List

from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout

from app.extensions.custom_gui import Dialog
from app.editor.settings.main_settings_controller import MainSettingsController

class UnusedResourcesDialog(Dialog):
    def __init__(self, unused_resources: Dict[str, List[str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unused Resources")
        self.window = parent
        self.resize(800, 800)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.settings = MainSettingsController()
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)
        self.textEdit.setFontFamily(self.settings.get_code_font())
        self.textEdit.setFontPointSize(12)
        self.textEdit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.textEdit)

        layout.addWidget(self.buttonbox)

        self.unused_resources = unused_resources

        # Calculate our display
        text_body = "Delete these unused files?\n\n"
        for save_data_type, unused_files in self.unused_resources.items():
            if not unused_files:  # Don't bother displaying if no unused files of that type
                continue
            data_type_text = f"=== {save_data_type} ===\n" 
            for unused_file in unused_files:
                data_type_text += f"{unused_file}\n"
            data_type_text += "\n"
            text_body += data_type_text
        self.textEdit.setText(text_body)

    @classmethod
    def get(cls, unused_resources, parent) -> bool:
        dialog = cls(unused_resources, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return True
        else:
            return False
