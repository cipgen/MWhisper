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
                               QMessageBox, QFrame, QSpacerItem, QSizePolicy, QDialog,
                               QPlainTextEdit, QScrollArea)
from PySide6.QtCore import Qt, Signal, QObject, QSize
from PySide6.QtGui import QFont, QIcon

CONFIG_FILE = "config.json"

# Dark Matte / Apple Matte Stylesheet
STYLE_SHEET = """
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #E0E0E0;
}

/* Main Window */
QWidget#SettingsWindow {
    background-color: #262626; /* Dark Matte Gray */
}
QWidget#ContentWidget {
    background-color: #262626;
}

/* Scroll Area */
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #262626;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #4A4A4A;
    min-height: 20px;
    border-radius: 5px;
}

/* Typography */
QLabel.SectionTitle {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 600;
    margin-top: 10px;
    margin-bottom: 5px;
}
QLabel.FieldLabel {
    color: #B0B0B0;
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 2px;
}

/* Inputs */
QLineEdit, QPlainTextEdit {
    background-color: #1A1A1A; /* Darker input background */
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
    color: #FFFFFF;
    selection-background-color: #4A90E2;
}
QLineEdit:focus, QPlainTextEdit:focus {
    background-color: #1A1A1A;
    border: 1px solid #FFFFFF; /* White Glow */
    /* Qt stylesheets don't support true box-shadow "glow" easily without graphics effects, 
       but a white border simulates the high-contrast focus state of the mock. */
}

/* Hotkey Pills */
QLineEdit.HotkeyDisplay {
    background-color: #333333;
    border: 1px solid #444444;
    border-radius: 12px; /* Pill shape */
    color: #E0E0E0;
    font-weight: 600;
    min-height: 24px;
}

/* Buttons */
QPushButton {
    background-color: #3A3A3A;
    border: 1px solid #4A4A4A;
    border-radius: 5px;
    padding: 5px 8px;
    color: #E0E0E0;
}
QPushButton:hover {
    background-color: #454545;
}
QPushButton:pressed {
    background-color: #2A2A2A;
}

/* Primary Button (Save) */
QPushButton#PrimaryButton {
    background-color: #4A4A4A; /* Dark button as per mock, maybe slightly lighter */
    border: 1px solid #5A5A5A;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover {
    background-color: #555555;
}

/* Cancel Button */
QPushButton#CancelButton {
    background-color: transparent;
    border: none;
    color: #A0A0A0;
}
QPushButton#CancelButton:hover {
    color: #FFFFFF;
}
"""

class HotkeyRecorderDialog(QDialog):
    hotkey_recorded = Signal(str)

    def __init__(self, parent=None, title="Record Hotkey"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 220)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        
        self.setStyleSheet(STYLE_SHEET)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        self.lbl_instruction = QLabel("Press key combination...")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        self.lbl_instruction.setProperty("class", "SectionTitle")
        self.lbl_instruction.setStyleSheet("color: #B0B0B0; font-size: 14px;")
        layout.addWidget(self.lbl_instruction)
        
        self.lbl_preview = QLabel("Waiting...")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setFont(QFont("System", 24, QFont.Bold))
        self.lbl_preview.setStyleSheet("""
            color: #FFFFFF; 
            padding: 15px; 
            background: #1A1A1A; 
            border: 1px solid #FFFFFF;
            border-radius: 10px;
        """)
        layout.addWidget(self.lbl_preview)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("CancelButton")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)
        
        self.setLayout(layout)
        self.current_modifiers = set()
        self.setFocusPolicy(Qt.StrongFocus)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()
        
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        pynput_mods = []
        if modifiers & Qt.ControlModifier: pynput_mods.append("<cmd>")
        if modifiers & Qt.MetaModifier: pynput_mods.append("<ctrl>")
        if modifiers & Qt.AltModifier: pynput_mods.append("<alt>")
        if modifiers & Qt.ShiftModifier: pynput_mods.append("<shift>")
        
        main_key = ""
        is_mod_key = key in (Qt.Key_Control, Qt.Key_Meta, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_AltGr)
        
        if not is_mod_key:
            if 0x20 <= key <= 0x7E:
                text = event.text()
                if text:
                    main_key = text.lower()
                else:
                    import QKeySequence
                    main_key = QKeySequence(key).toString().lower()
            else:
                 text = event.text()
                 if text: main_key = text.lower()
        
        self.current_modifiers = set(pynput_mods)
        
        if main_key:
            display_str = "+".join(sorted(pynput_mods) + [main_key])
            self.lbl_preview.setText(display_str)
            hotkey_str = display_str
            self.hotkey_recorded.emit(hotkey_str)
            self.accept()
        else:
            display_str = "+".join(sorted(pynput_mods)) + "..."
            self.lbl_preview.setText(display_str)

    def keyReleaseEvent(self, event):
        pass

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MWhisper Settings")
        self.setObjectName("SettingsWindow")
        self.setFixedSize(520, 580) # Slightly wider, same height, no scroll needed
        
        self.setStyleSheet(STYLE_SHEET)
        
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
            self.config["translation_prompt"] = self.prompt_input.toPlainText().strip()
            self.config["fix_prompt"] = self.fix_prompt_input.toPlainText().strip()
            
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", CONFIG_FILE)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            # No notification as requested by user
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def _setup_ui(self):
        # Main layout - NO SCROLL AREA
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(12)
        
        # --- Section 1: OpenAI ---
        lbl_openai = QLabel("OpenAI Configuration")
        lbl_openai.setProperty("class", "SectionTitle")
        main_layout.addWidget(lbl_openai)
        
        lbl_key = QLabel("API Key")
        lbl_key.setProperty("class", "FieldLabel")
        main_layout.addWidget(lbl_key)
        
        key_input_container = QHBoxLayout()
        self.api_key_input = QLineEdit(self.config.get("openai_api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        key_input_container.addWidget(self.api_key_input)
        
        self.chk_show_key = QCheckBox("Show")
        self.chk_show_key.setCursor(Qt.PointingHandCursor)
        self.chk_show_key.stateChanged.connect(self._toggle_show_key)
        key_input_container.addWidget(self.chk_show_key)
        
        main_layout.addLayout(key_input_container)
        
        main_layout.addSpacing(5)
        
        # --- Section 2: Prompts ---
        
        # Translation
        trans_lbl = QLabel("Translation Prompt")
        trans_lbl.setProperty("class", "FieldLabel")
        main_layout.addWidget(trans_lbl)
        
        default_trans = "Переведи этот текст на английский язык. Исправь ошибки и напиши простыми словами. Верни ТОЛЬКО перевод."
        current_trans = self.config.get("translation_prompt", default_trans)
        self.prompt_input = QPlainTextEdit(current_trans)
        self.prompt_input.setPlaceholderText("Enter your translation instructions here...")
        self.prompt_input.setFixedHeight(50) # Very compact
        main_layout.addWidget(self.prompt_input)
        
        # Smart Fix
        fix_lbl = QLabel("Smart Fix Prompt")
        fix_lbl.setProperty("class", "FieldLabel")
        main_layout.addWidget(fix_lbl)
        
        default_fix = "Исправь грамматические ошибки, расставь знаки препинания и улучши стиль. Не переводи. Верни ТОЛЬКО исправленный текст."
        current_fix = self.config.get("fix_prompt", default_fix)
        self.fix_prompt_input = QPlainTextEdit(current_fix)
        self.fix_prompt_input.setPlaceholderText("Enter instructions for grammar and style fixes...")
        self.fix_prompt_input.setFixedHeight(50) # Very compact
        main_layout.addWidget(self.fix_prompt_input)
        
        main_layout.addSpacing(10)
        
        # --- Section 3: Hotkeys ---
        lbl_hk = QLabel("Hotkeys (Push-to-Talk)")
        lbl_hk.setProperty("class", "SectionTitle")
        main_layout.addWidget(lbl_hk)
        
        def add_hotkey_row(label, key, config_key, default_val):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setMinimumWidth(100) 
            lbl.setProperty("class", "FieldLabel")
            row.addWidget(lbl)
            
            row.addStretch()
            
            val = self.config.get(config_key, default_val)
            display = self._get_display_hotkey(val)
            
            edit = QLineEdit(display)
            edit.setReadOnly(True)
            edit.setAlignment(Qt.AlignCenter)
            edit.setProperty("class", "HotkeyDisplay")
            edit.setFixedWidth(100) # Give it space
            edit.setFocusPolicy(Qt.NoFocus)
            row.addWidget(edit)
            
            # WIDER GAP
            row.addSpacing(10)
            
            btn = QPushButton("Change")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedWidth(75) # Wider button for "Change" text
            btn.clicked.connect(lambda: self._open_recorder(key))
            row.addWidget(btn)
            
            main_layout.addLayout(row)
            return edit

        self.edit_dictation = add_hotkey_row("Dictation", "dictation", "hotkey", "<cmd>+<shift>+d")
        self.edit_translate = add_hotkey_row("Translation", "translate", "translate_hotkey", "<cmd>+<shift>+u")
        self.edit_fix = add_hotkey_row("Smart Fix", "fix", "fix_hotkey", "<cmd>+<shift>+e")
        
        main_layout.addStretch()
        
        # --- Bottom Bar ---
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("CancelButton")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFixedWidth(80)
        btn_cancel.clicked.connect(QApplication.quit)
        btn_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setFixedHeight(32)
        btn_save.clicked.connect(self._save_config)
        btn_layout.addWidget(btn_save)
        
        main_layout.addLayout(btn_layout)

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
            elif target_type == "translate":
                self.edit_translate.setText(display)
                self.config["translate_hotkey"] = current_hotkey
            elif target_type == "fix":
                self.edit_fix.setText(display)
                self.config["fix_hotkey"] = current_hotkey

def run_settings():
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_settings()
