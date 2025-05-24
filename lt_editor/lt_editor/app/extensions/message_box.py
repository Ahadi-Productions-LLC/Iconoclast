from typing import Optional
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import Qt

def show_info_message(title: str, text: str, detailed_text: Optional[str] = None, parent=None):
    show_custom_message_box(QMessageBox.Information, title, text, detailed_text, parent)

def show_warning_message(title: str, text: str, detailed_text: Optional[str] = None, parent=None):
    show_custom_message_box(QMessageBox.Warning, title, text, detailed_text, parent)

def show_error_message(title: str, text: str, detailed_text: Optional[str] = None, parent=None):
    show_custom_message_box(QMessageBox.Critical, title, text, detailed_text, parent)

class CustomMessageBox(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.icon_label = QLabel(self)
        self.text_label = QLabel(self)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.icon_label)
        hlayout.addWidget(self.text_label)
        layout.addLayout(hlayout)

        self.detailed_text_label = QTextEdit(self)
        self.detailed_text_label.setWordWrapMode(True)
        self.detailed_text_label.setReadOnly(True)
        layout.addWidget(self.detailed_text_label)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        self.buttonbox.accepted.connect(self.accept)
        layout.addWidget(self.buttonbox)

    def setDetailedText(self, text: str):
        self.detailed_text_label.setText(text)
        self.detailed_text_label.show()

    def setText(self, text: str):
        self.text_label.setText(text)

    def setIcon(self, icon: QMessageBox.Icon):
        self.icon_label.setPixmap(QMessageBox().standardIcon(icon))

def show_custom_message_box(alert_level: QMessageBox.Icon, title: str, text: str, detailed_text: Optional[str] = None, parent=None):
    msg_box = CustomMessageBox(parent)
    msg_box.setIcon(alert_level)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    if detailed_text:
        msg_box.setDetailedText(detailed_text)
    msg_box.exec_()
