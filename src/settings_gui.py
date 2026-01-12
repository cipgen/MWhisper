"""
MWhisper Settings GUI
Standalone PySide6 application for configuring settings
"""

import sys
import os
import json
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QCheckBox, 
                               QMessageBox, QFrame, QSpacerItem, QSizePolicy, QDialog)
from PySide6.QtCore import Qt, Signal, QObject, QSize
from PySide6.QtGui import QFont, QIcon
from pynput import keyboard

# Add src to path to import local modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_FILE = "config.json"

class HotkeyRecorderDialog(QDialog):
    hotkey_recorded = Signal(str)

    def __init__(self, parent=None, title="Record Hotkey"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        self.lbl_instruction = QLabel("Press the desired key combination\non your keyboard now...")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        self.lbl_instruction.setFont(QFont("System", 14))
        layout.addWidget(self.lbl_instruction)
        
        self.lbl_preview = QLabel("Waiting...")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setFont(QFont("System", 18, QFont.Bold))
        self.lbl_preview.setStyleSheet("color: #007AFF; padding: 10px; background: #E5F1FF; border-radius: 6px;")
        layout.addWidget(self.lbl_preview)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)
        
        self.setLayout(layout)
        self.current_modifiers = set()
        
        # Focus policy to ensure we grab keys
        self.setFocusPolicy(Qt.StrongFocus)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()
        
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Ignore isolated modifiers press (wait for combo)
        # But we need to update preview
        
        pynput_mods = []
        if modifiers & Qt.ControlModifier: pynput_mods.append("<cmd>")
        if modifiers & Qt.MetaModifier: pynput_mods.append("<ctrl>")
        if modifiers & Qt.AltModifier: pynput_mods.append("<alt>")
        if modifiers & Qt.ShiftModifier: pynput_mods.append("<shift>")
        
        # Determine main key
        # Qt.Key mapping to pynput string char
        main_key = ""
        
        # Don't capture valid modifiers as main keys
        is_mod_key = key in (Qt.Key_Control, Qt.Key_Meta, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_AltGr)
        
        if not is_mod_key:
            if 0x20 <= key <= 0x7E: # Visible ASCII
                text = event.text()
                if text:
                    main_key = text.lower()
                else:
                    # Fallback for keys without text (e.g. F-keys, special)
                    import QKeySequence
                    main_key = QKeySequence(key).toString().lower()
            else:
                 # Handle special keys if needed (F1, Escape, etc)
                 # MWhisper seems to focus on simple letter combos.
                 # Let's try to get text().
                 text = event.text()
                 if text: main_key = text.lower()
        
        self.current_modifiers = set(pynput_mods)
        
        # Update Preview
        if main_key:
            display_str = "+".join(sorted(pynput_mods) + [main_key])
            self.lbl_preview.setText(display_str)
            
            # If we have at least one modifier and a key, or just a key?
            # MWhisper logic usually expects <mod>+key.
            # But let's allow single keys if user wants (though usually bad).
            
            # Commit logic: If we have main_key, we save.
            hotkey_str = display_str # Already in format <ctrl>+<shift>+d
            self.hotkey_recorded.emit(hotkey_str)
            self.accept()
        else:
            # Just showing modifiers
            display_str = "+".join(sorted(pynput_mods)) + "..."
            self.lbl_preview.setText(display_str)

    def keyReleaseEvent(self, event):
        # Update preview on release if needed?
        pass

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MWhisper Settings")
        self.setFixedSize(500, 480) # Slightly taller
        
        self.config = self._load_config()
        self._setup_ui()
        self._center_window()

    def _center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _load_config(self) -> dict:
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", CONFIG_FILE)
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load config: {e}")
        return {}
        
    def _save_config(self):
        try:
            self.config["openai_api_key"] = self.api_key_input.text().strip()
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", CONFIG_FILE)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            QMessageBox.information(self, "Success", "Settings saved successfully!\nMWhisper will reload settings.")
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # OpenAI
        lbl_openai = QLabel("OpenAI Configuration")
        lbl_openai.setFont(QFont("System", 14, QFont.Bold))
        layout.addWidget(lbl_openai)
        
        layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit(self.config.get("openai_api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        layout.addWidget(self.api_key_input)
        
        self.chk_show_key = QCheckBox("Show API Key")
        self.chk_show_key.stateChanged.connect(self._toggle_show_key)
        layout.addWidget(self.chk_show_key)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Hotkeys
        lbl_hotkeys = QLabel("Hotkeys (Push-to-Talk)")
        lbl_hotkeys.setFont(QFont("System", 14, QFont.Bold))
        layout.addWidget(lbl_hotkeys)
        
        # Dictation
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(QLabel("Dictation:", minimumWidth=80))
        
        self.edit_dictation = QLineEdit(self._get_display_hotkey(self.config.get("hotkey", "<cmd>+<shift>+d")))
        self.edit_dictation.setReadOnly(True)
        self.edit_dictation.setAlignment(Qt.AlignCenter)
        self.edit_dictation.setStyleSheet("QLineEdit { background: #f0f0f0; color: #333; font-weight: bold; }")
        h_layout1.addWidget(self.edit_dictation)
        
        self.btn_dictation = QPushButton("Change")
        self.btn_dictation.clicked.connect(lambda: self._open_recorder("dictation"))
        h_layout1.addWidget(self.btn_dictation)
        layout.addLayout(h_layout1)
        
        # Translate
        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(QLabel("Translate:", minimumWidth=80))
        
        self.edit_translate = QLineEdit(self._get_display_hotkey(self.config.get("translate_hotkey", "<cmd>+<shift>+u")))
        self.edit_translate.setReadOnly(True)
        self.edit_translate.setAlignment(Qt.AlignCenter)
        self.edit_translate.setStyleSheet("QLineEdit { background: #f0f0f0; color: #333; font-weight: bold; }")
        h_layout2.addWidget(self.edit_translate)
        
        self.btn_translate = QPushButton("Change")
        self.btn_translate.clicked.connect(lambda: self._open_recorder("translate"))
        h_layout2.addWidget(self.btn_translate)
        layout.addLayout(h_layout2)
        
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(QApplication.quit)
        btn_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("Save Settings")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save_config)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _toggle_show_key(self, state):
        if self.chk_show_key.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            
    def _get_display_hotkey(self, pynput_str):
        mapping = {
            '<cmd>': '⌘', '<cmd_r>': '⌘',
            '<shift>': '⇧', '<shift_r>': '⇧',
            '<ctrl>': '⌃', '<ctrl_r>': '⌃',
            '<alt>': '⌥', '<alt_r>': '⌥',
        }
        parts = pynput_str.split('+')
        display = ""
        for part in parts:
            if part in mapping: display += mapping[part]
            else: display += part.upper()
        return display

    def _open_recorder(self, target_type):
        dialog = HotkeyRecorderDialog(self, f"Set {target_type.title()} Hotkey")
        # We need a slot to handle signal, or just check result after exec?
        # exec() blocks until closed.
        
        # But wait, dialog uses threading for pynput.
        # We need to ensure we get the result.
        
        current_hotkey = ""
        def on_recorded(hk):
            nonlocal current_hotkey
            current_hotkey = hk
            
        dialog.hotkey_recorded.connect(on_recorded)
        
        if dialog.exec() == QDialog.Accepted and current_hotkey:
            display = self._get_display_hotkey(current_hotkey)
            if target_type == "dictation":
                self.edit_dictation.setText(display)
                self.config["hotkey"] = current_hotkey
            else:
                self.edit_translate.setText(display)
                self.config["translate_hotkey"] = current_hotkey

def run_settings():
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_settings()
