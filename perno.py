import sys
import os
import json
import random
import subprocess
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

# --- PERSONALITY DATA INJECTION ---
# Based on your report: Type 5 (Analyst), Truth-Seeker, High Intellect, LOW Execution.
USER_NAME = "Samidu"
USER_TYPE = "INTJ (RECLAIMING)" 
CRITICAL_FLAW = "Analysis Paralysis" # Type 5 weakness
STRENGTH = "97th Percentile Intellect"

# --- CONFIGURATION ---
BASE_DIR = os.path.expanduser("~/.local/share/truth_engine")
DATA_FILE = os.path.join(BASE_DIR, "execution_log.csv")
os.makedirs(BASE_DIR, exist_ok=True)

# These quotes target the "Truth-Seeker" logic and "Type 8" secondary drive [cite: 294]
TRUTH_BOMBS = [
    "Intelligence without execution is just entertainment.",
    "You are in the 99th percentile for Openness. Focus on CLOSING.",
    "Type 5 Trap: You are hoarding knowledge to avoid the fear of incompetence.",
    "You fell from 64% Conscientiousness to 43%. Fix it.",
    "Logic dictates that action is the only variable that changes reality."
]

class WardenThread(QThread):
    """
    The External Prefrontal Cortex.
    Monitors if you are 'Learning' (Passive) vs 'Doing' (Active).
    """
    drift_signal = pyqtSignal(str)

    def run(self):
        while True:
            self.msleep(5000)
            try:
                # Get active window using Hyprland (Arch Linux specific)
                cmd = ["hyprctl", "activewindow", "-j"]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                app_class = data.get("class", "").lower()
                title = data.get("title", "").lower()

                # TRUTH-SEEKER LOGIC:
                # Browsers/YouTube = "Researching" (Passive Type 5 behavior)
                # Terminals/Editors = "Building" (Active Type 8 behavior)
                
                passive_apps = ["firefox", "brave", "chrome", "zathura"]
                active_apps = ["code", "kitty", "alacritty", "obsidian", "anki"]

                if any(x in app_class for x in passive_apps):
                    # Check if actually working or just drifting
                    if "youtube" in title or "reddit" in title:
                        self.drift_signal.emit(f"DETECTED PASSIVE CONSUMPTION: {app_class}")
                
            except Exception:
                pass

class TruthDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THE TRUTH ENGINE")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #0d0d0d; color: #e0e0e0;")
        self.init_ui()
        
        self.warden = WardenThread()
        self.warden.drift_signal.connect(self.trigger_shame_protocol)
        self.warden.start()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # HEADER: IDENTITY RECLAMATION
        header = QLabel(f"OPERATOR: {USER_NAME} | TARGET: {USER_TYPE}")
        header.setFont(QFont("Monospace", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #00ff41; border-bottom: 2px solid #00ff41; padding-bottom: 10px;")
        layout.addWidget(header)

        # THE DATA REALITY CHECK
        stats_layout = QHBoxLayout()
        
        # Stat 1: The Fall
        stat_box1 = self.create_stat_box("CONSCIENTIOUSNESS", "43% (CRITICAL)", 
                                         "You dropped 21 points since August.\nYour discipline is bleeding out.")
        stats_layout.addWidget(stat_box1)

        # Stat 2: The Potential
        stat_box2 = self.create_stat_box("INTELLECT", "97th Percentile", 
                                         "Your hardware is elite.\nYour software (habits) is corrupted.")
        stats_layout.addWidget(stat_box2)

        layout.addLayout(stats_layout)

        # THE ACTION FORCER
        self.input_label = QLabel("DEFINE MICRO-OUTPUT (NOT STUDYING):")
        self.input_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.input_label)

        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g. Write 50 lines of code, NOT 'Watch Python tutorial'")
        self.goal_input.setStyleSheet("padding: 10px; font-size: 16px; background: #222; border: 1px solid #444; color: white;")
        layout.addWidget(self.goal_input)

        # PROGRESS BAR (TIME PRESSURE)
        self.timer_label = QLabel("SESSION TIME REMAINING")
        layout.addWidget(self.timer_label)
        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #ff3333; }")
        layout.addWidget(self.progress)

        # QUOTE OF REALITY
        self.quote_lbl = QLabel(random.choice(TRUTH_BOMBS))
        self.quote_lbl.setStyleSheet("font-style: italic; color: #888; font-size: 14px; margin-top: 20px;")
        self.quote_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.quote_lbl)

    def create_stat_box(self, title, value, desc):
        box = QFrame()
        box.setStyleSheet("background: #1a1a1a; border: 1px solid #333; border-radius: 5px;")
        l = QVBoxLayout(box)
        
        t = QLabel(title)
        t.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        l.addWidget(t)
        
        v = QLabel(value)
        v.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        l.addWidget(v)
        
        d = QLabel(desc)
        d.setStyleSheet("color: #ff5555; font-size: 10px;")
        d.setWordWrap(True)
        l.addWidget(d)
        
        return box

    def trigger_shame_protocol(self, msg):
        # When you drift, this window forces itself to the top
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        self.raise_()
        self.quote_lbl.setText(f"ALERT: {msg}\nYour Type 5 brain is avoiding work by 'Researching'. STOP.")
        self.quote_lbl.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")

if __name__ == "__main__":
    # Hyprland/Wayland Support
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    
    app = QApplication(sys.argv)
    window = TruthDashboard()
    window.show()
    sys.exit(app.exec())
