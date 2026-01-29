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
                               QPlainTextEdit, QScrollArea, QComboBox, QGroupBox)
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

/* GroupBox */
QGroupBox { 
    border: 1px solid #444; 
    border-radius: 6px; 
    margin-top: 20px; 
    padding-top: 15px;
    font-weight: bold;
    color: #DDD;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
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
        self.setFixedSize(550, 650) # Taller and wider for better layout
        
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
            self.config["transcription_mode"] = self.mode_combo.currentData()
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
        # 1. Main Layout with Scroll Area
        main_layout_outer = QVBoxLayout(self)
        main_layout_outer.setContentsMargins(0, 0, 0, 0)
        main_layout_outer.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("SettingsScroll")
        
        content_widget = QWidget()
        content_widget.setObjectName("ContentWidget")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(25)
        
        scroll.setWidget(content_widget)
        main_layout_outer.addWidget(scroll)

        # --- Section 1: Transcription ---
        grp_transcription = QGroupBox("Transcription")
        lay_transcription = QVBoxLayout(grp_transcription)
        
        # Mode
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Engine:", objectName="FieldLabel"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Parakeet (Offline)", "parakeet")
        self.mode_combo.addItem("Streaming (Real-time)", "streaming")
        self.mode_combo.setFixedWidth(200)
        current_mode = self.config.get("transcription_mode", "parakeet")
        idx = self.mode_combo.findData(current_mode)
        if idx >= 0: self.mode_combo.setCurrentIndex(idx)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        lay_transcription.addLayout(mode_row)
        
        self.content_layout.addWidget(grp_transcription)

        # --- Section 2: OpenAI ---
        grp_openai = QGroupBox("OpenAI / Translation")
        lay_openai = QVBoxLayout(grp_openai)
        
        lay_openai.addWidget(QLabel("API Key:", objectName="FieldLabel"))
        key_input_container = QHBoxLayout()
        self.api_key_input = QLineEdit(self.config.get("openai_api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        key_input_container.addWidget(self.api_key_input)
        
        self.chk_show_key = QCheckBox("Show")
        self.chk_show_key.setCursor(Qt.PointingHandCursor)
        self.chk_show_key.stateChanged.connect(self._toggle_show_key)
        key_input_container.addWidget(self.chk_show_key)
        lay_openai.addLayout(key_input_container)
        
        self.content_layout.addWidget(grp_openai)
        
        # --- Section 3: Standard Actions ---
        grp_std = QGroupBox("Standard Actions")
        lay_std = QVBoxLayout(grp_std)
        lay_std.setSpacing(10)
        
        def add_hotkey_row(layout, label, key, config_key, default_val):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setMinimumWidth(120) 
            lbl.setProperty("class", "FieldLabel")
            row.addWidget(lbl)
            
            row.addStretch()
            
            val = self.config.get(config_key, default_val)
            display = self._get_display_hotkey(val)
            
            edit = QLineEdit(display)
            edit.setReadOnly(True)
            edit.setAlignment(Qt.AlignCenter)
            edit.setProperty("class", "HotkeyDisplay")
            edit.setFixedWidth(140)
            edit.setFocusPolicy(Qt.NoFocus)
            row.addWidget(edit)
            
            row.addSpacing(10)
            
            btn = QPushButton("Change")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedWidth(80)
            btn.clicked.connect(lambda: self._open_recorder(key))
            row.addWidget(btn)
            
            layout.addLayout(row)
            return edit

        self.edit_dictation = add_hotkey_row(lay_std, "Dictation", "dictation", "hotkey", "<cmd>+<shift>+d")
        self.edit_translate = add_hotkey_row(lay_std, "Translation", "translate", "translate_hotkey", "<cmd>+<shift>+u")
        self.edit_fix = add_hotkey_row(lay_std, "Smart Fix", "fix", "fix_hotkey", "<cmd>+<shift>+e")
        
        self.content_layout.addWidget(grp_std)
        
        # --- Section 4: Custom Actions ---
        grp_custom = QGroupBox("Custom Actions")
        lay_custom_outer = QVBoxLayout(grp_custom)
        
        cust_header = QHBoxLayout()
        cust_header.addStretch()
        btn_add = QPushButton("+ Add Action")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("background-color: #2D6A4F; font-weight: bold;") 
        btn_add.clicked.connect(self._add_custom_action)
        cust_header.addWidget(btn_add)
        lay_custom_outer.addLayout(cust_header)
        
        # Container for list
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setSpacing(8)
        lay_custom_outer.addLayout(self.actions_layout)
        
        # Load Existing
        self.custom_actions = self.config.get("custom_actions", [])
        if not isinstance(self.custom_actions, list): self.custom_actions = []
        self._refresh_actions_list()
        
        self.content_layout.addWidget(grp_custom)
        
        
        # --- Section 5: Prompts ---
        grp_prompts = QGroupBox("Default Prompts")
        lay_prompts = QVBoxLayout(grp_prompts)
        
        lay_prompts.addWidget(QLabel("Translation Prompt:", objectName="FieldLabel"))
        default_trans = "Переведи этот текст на английский язык. Исправь ошибки и напиши простыми словами. Верни ТОЛЬКО перевод."
        current_trans = self.config.get("translation_prompt", default_trans)
        self.prompt_input = QPlainTextEdit(current_trans)
        self.prompt_input.setFixedHeight(60)
        lay_prompts.addWidget(self.prompt_input)
        
        lay_prompts.addWidget(QLabel("Smart Fix Prompt:", objectName="FieldLabel"))
        default_fix = "Исправь грамматические ошибки, расставь знаки препинания и улучши стиль. Не переводи. Верни ТОЛЬКО исправленный текст."
        current_fix = self.config.get("fix_prompt", default_fix)
        self.fix_prompt_input = QPlainTextEdit(current_fix)
        self.fix_prompt_input.setFixedHeight(60)
        lay_prompts.addWidget(self.fix_prompt_input)
        
        self.content_layout.addWidget(grp_prompts)
        
        self.content_layout.addStretch()

        # --- Bottom Bar ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("BottomBar")
        bottom_bar.setStyleSheet("QWidget#BottomBar { background-color: #2D2D2D; border-top: 1px solid #3A3A3A; }")
        bb_layout = QHBoxLayout(bottom_bar)
        bb_layout.setContentsMargins(20, 15, 20, 15)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("CancelButton")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFixedWidth(80)
        btn_cancel.clicked.connect(QApplication.quit)
        bb_layout.addWidget(btn_cancel)
        
        bb_layout.addStretch()
        
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setFixedWidth(120)
        btn_save.setFixedHeight(32)
        btn_save.clicked.connect(self._save_config)
        bb_layout.addWidget(btn_save)
        
        main_layout_outer.addWidget(bottom_bar)

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
    
    def _add_custom_action(self):
        """Open dialog to add new custom action"""
        dialog = ActionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            action = dialog.get_action_data()
            if action:
                self.custom_actions.append(action)
                self.config["custom_actions"] = self.custom_actions
                self._refresh_actions_list()

    def _edit_custom_action(self, action_id):
        """Edit existing custom action"""
        # Find action
        action = next((a for a in self.custom_actions if a["id"] == action_id), None)
        if not action: return
        
        dialog = ActionDialog(self, action)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_action_data()
            if new_data:
                # Update in place
                action.update(new_data)
                self.config["custom_actions"] = self.custom_actions
                self._refresh_actions_list()
    
    def _delete_custom_action(self, action_id):
        """Delete custom action"""
        confirm = QMessageBox.question(
            self, 
            "Delete Action", 
            "Are you sure you want to delete this action?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.custom_actions = [a for a in self.custom_actions if a["id"] != action_id]
            self.config["custom_actions"] = self.custom_actions
            self._refresh_actions_list()

    def _refresh_actions_list(self):
        """Re-render the actions list"""
        # Clear existing
        while self.actions_layout.count():
            child = self.actions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add items
        if not self.custom_actions:
            empty_lbl = QLabel("No custom actions defined")
            empty_lbl.setStyleSheet("color: #666666; font-style: italic; margin: 10px;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.actions_layout.addWidget(empty_lbl)
        else:
            for action in self.custom_actions:
                item = CustomActionWidget(action, self._get_display_hotkey)
                item.edit_requested.connect(self._edit_custom_action)
                item.delete_requested.connect(self._delete_custom_action)
                self.actions_layout.addWidget(item)
        
        self.actions_layout.addStretch()


class ActionDialog(QDialog):
    """Dialog to Add/Edit Custom Action"""
    def __init__(self, parent=None, action_data=None):
        super().__init__(parent)
        self.action_data = action_data or {}
        self.setWindowTitle("Edit Action" if action_data else "Add Action")
        self.setFixedSize(450, 480)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        self.setStyleSheet(STYLE_SHEET)
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Name
        layout.addWidget(QLabel("Action Name", objectName="FieldLabel"))
        self.name_input = QLineEdit(self.action_data.get("name", ""))
        self.name_input.setPlaceholderText("e.g. Summarize Text")
        layout.addWidget(self.name_input)
        
        # Hotkey
        layout.addWidget(QLabel("Hotkey", objectName="FieldLabel"))
        hk_row = QHBoxLayout()
        self.hotkey_display = QLineEdit(self.action_data.get("hotkey", ""))
        self.hotkey_display.setPlaceholderText("Click Record ->")
        self.hotkey_display.setReadOnly(True)
        self.hotkey_display.setProperty("class", "HotkeyDisplay")
        hk_row.addWidget(self.hotkey_display)
        
        btn_rec = QPushButton("Record")
        btn_rec.setFixedWidth(80)
        btn_rec.setCursor(Qt.PointingHandCursor)
        btn_rec.clicked.connect(self._record_hotkey)
        hk_row.addWidget(btn_rec)
        layout.addLayout(hk_row)
        
        self.current_hotkey_pynput = self.action_data.get("hotkey", "")
        # Update display if existing
        if self.current_hotkey_pynput:
             # Hack: Access parent helper if possible
             pass
        
        # Prompt
        layout.addWidget(QLabel("System Prompt", objectName="FieldLabel"))
        self.prompt_input = QPlainTextEdit(self.action_data.get("prompt", ""))
        self.prompt_input.setPlaceholderText("Instruction for LLM (e.g. 'Summarize this text in 3 bullet points')")
        self.prompt_input.setMinimumHeight(120)
        layout.addWidget(self.prompt_input)
        
        layout.addStretch()
        
        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        
        cancel = QPushButton("Cancel")
        cancel.setObjectName("CancelButton")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        
        save = QPushButton("Save Action")
        save.setObjectName("PrimaryButton")
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        btns.addWidget(save)
        
        layout.addLayout(btns)
        
    def _record_hotkey(self):
        # reuse global recorder
        dialog = HotkeyRecorderDialog(self, "Record Action Hotkey")
        
        rec_hk = None
        def on_rec(k): nonlocal rec_hk; rec_hk = k
        dialog.hotkey_recorded.connect(on_rec)
        
        if dialog.exec() == QDialog.Accepted and rec_hk:
            self.current_hotkey_pynput = rec_hk
            # Format for display
            display = rec_hk
            mapping = {'<cmd>': '⌘', '<shift>': '⇧', '<ctrl>': '⌃', '<alt>': '⌥'}
            for k,v in mapping.items(): display = display.replace(k,v)
            display = display.replace('+', '').upper()
            
            self.hotkey_display.setText(display)

    def _save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Please enter a name.")
            return
        if not self.current_hotkey_pynput:
            QMessageBox.warning(self, "Validation", "Please record a hotkey.")
            return
        if not self.prompt_input.toPlainText().strip():
             QMessageBox.warning(self, "Validation", "Please enter a prompt.")
             return
             
        self.accept()

    def get_action_data(self):
        import uuid
        return {
            "id": self.action_data.get("id", str(uuid.uuid4())),
            "name": self.name_input.text().strip(),
            "hotkey": self.current_hotkey_pynput,
            "prompt": self.prompt_input.toPlainText().strip()
        }


class CustomActionWidget(QFrame):
    """Row item for custom action list"""
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    
    def __init__(self, action, format_func):
        super().__init__()
        self.action_id = action["id"]
        
        self.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border-radius: 6px;
                border: 1px solid #444444;
            }
            QLabel { background: transparent; border: none; }
        """)
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Name
        name = QLabel(action["name"])
        name.setStyleSheet("font-weight: bold; color: white;")
        layout.addWidget(name)
        
        layout.addStretch()
        
        # Hotkey Pill
        hk_text = format_func(action["hotkey"])
        hk_lbl = QLabel(hk_text)
        hk_lbl.setStyleSheet("""
            background-color: #222;
            color: #AAA;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
            border: 1px solid #444;
        """)
        layout.addWidget(hk_lbl)
        
        layout.addSpacing(10)
        
        # Edit
        btn_edit = QPushButton("✎")
        btn_edit.setFixedSize(24, 24)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setToolTip("Edit")
        btn_edit.setStyleSheet("QPushButton { border: none; background: transparent; color: #AAA; } QPushButton:hover { color: white; }")
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.action_id))
        layout.addWidget(btn_edit)
        
        # Delete
        btn_del = QPushButton("×")
        btn_del.setFixedSize(24, 24)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("Delete")
        btn_del.setStyleSheet("QPushButton { border: none; background: transparent; color: #AAA; } QPushButton:hover { color: #FF5555; }")
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.action_id))
        layout.addWidget(btn_del)


def run_settings():
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_settings()
