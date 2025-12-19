#!/usr/bin/env python3
"""
THE OVERMAN PROTOCOL
A brutal focus enforcement system for Arch Linux / Hyprland
Based on Nietzschean philosophy and deliberate practice principles
"""

import sys
import os
import json
import random
import subprocess
import shutil
from datetime import datetime
from collections import defaultdict
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QProgressBar, QFrame, QPushButton, QTextEdit,
    QTabWidget, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor

# ==========================================
# CONFIGURATION
# ==========================================
BASE_DIR = Path.home() / ".local/share/overman"
SCREENSHOT_DIR = BASE_DIR / "screenshots"
DATA_FILE = BASE_DIR / "session_log.csv"

# Clean slate each session
if BASE_DIR.exists():
    shutil.rmtree(BASE_DIR)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Forbidden keywords (immediate kill)
FORBIDDEN = ["porn", "xxx", "sex", "pornhub", "xvideos", "facebook", 
             "twitter", "instagram", "tiktok", "reddit", "9gag"]

# Drift apps (trigger warnings)
DRIFT_APPS = ["firefox", "brave", "chrome", "chromium", "discord", "thorium"]

# Nietzschean quotes
QUOTES = [
    "Man is a rope, tied between beast and overman—a rope over an abyss.",
    "He who cannot obey himself will be commanded.",
    "You have made your way from worm to man, and much within you is still worm.",
    "The ape is a laughing-stock to man. Are you becoming a laughing-stock?",
    "Your 'desire' is not yours. It is the belly. It is the animal.",
    "What is great in man is that he is a bridge and not an end.",
    "I teach you the overman. Man is something that shall be overcome.",
    "Spirit is the life that itself cuts into life.",
    "One must still have chaos in oneself to be able to give birth to a dancing star.",
    "The belly is the reason why man does not so easily take himself for a god.",
]

MANTRAS = ["overcome myself", "i am a bridge", "command the beast", 
           "will to power", "kill the worm", "harness the drive"]


def speak(text):
    """Voice output using espeak-ng"""
    try:
        subprocess.Popen(
            ["espeak-ng", "-s", "170", "-v", "en-us", text],
            stderr=subprocess.DEVNULL
        )
    except:
        pass


# ==========================================
# WARDEN THREAD (Background Monitor)
# ==========================================
class WardenThread(QThread):
    lockout_signal = pyqtSignal(str)  # Screenshot path
    data_signal = pyqtSignal(str, str, str)  # app, title, status
    
    def __init__(self, allowed_apps):
        super().__init__()
        self.allowed = [a.strip().lower() for a in allowed_apps if a.strip()]
        self.running = True
    
    def run(self):
        audit_timer = 0
        drift_timer = 0
        
        while self.running:
            self.msleep(2000)  # Check every 2 seconds
            audit_timer += 2
            
            try:
                # Get Hyprland window data
                result = subprocess.run(
                    ["hyprctl", "activewindow", "-j"],
                    capture_output=True, text=True
                )
                data = json.loads(result.stdout)
                
                app_class = data.get("class", "").lower()
                title = data.get("title", "").lower()
                address = data.get("address", "")
                
                # IMMEDIATE KILL PROTOCOL
                if any(k in title or k in app_class for k in FORBIDDEN):
                    subprocess.run(
                        ["hyprctl", "dispatch", "closewindow", f"address:{address}"]
                    )
                    self.trigger_audit("VIOLATION DETECTED")
                    speak("Protocol violation. The animal has taken over.")
                    continue
                
                # 10-MINUTE AUDIT LOOP
                if audit_timer >= 600:
                    self.trigger_audit("10 MINUTE AUDIT")
                    audit_timer = 0
                
                # DRIFT DETECTION
                is_allowed = any(w in app_class for w in self.allowed)
                is_drift_app = any(d in app_class for d in DRIFT_APPS)
                
                status = "Productive" if is_allowed else "Drifting"
                
                if not is_allowed and is_drift_app:
                    drift_timer += 2
                    if drift_timer == 60:
                        speak(f"Focus check. You are in {app_class}.")
                    elif drift_timer > 120:
                        speak("Close the browser. Return to the goal.")
                else:
                    drift_timer = 0
                
                # Send data update
                self.data_signal.emit(app_class or "idle", title, status)
                
                # Log to CSV
                with open(DATA_FILE, 'a') as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{timestamp},{app_class},{title},{status}\n")
                
            except Exception as e:
                print(f"Warden error: {e}")
    
    def trigger_audit(self, reason):
        speak(f"{reason}. Audit initiated.")
        screenshot_path = SCREENSHOT_DIR / f"audit_{int(datetime.now().timestamp())}.png"
        subprocess.run(["grim", str(screenshot_path)])
        self.lockout_signal.emit(str(screenshot_path))


# ==========================================
# LOCKOUT WINDOW (The Audit)
# ==========================================
class LockoutWindow(QMainWindow):
    def __init__(self, img_path):
        super().__init__()
        self.setWindowTitle("EVOLUTIONARY AUDIT")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Styling
        self.setStyleSheet("background-color: #000000; border: 4px solid #ff0000;")
        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Header
        header = QLabel("AUDIT: FACE THE TRUTH")
        header.setFont(QFont("Monospace", 32, QFont.Weight.Bold))
        header.setStyleSheet("color: #ff0000;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Screenshot evidence
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(
                900, 600, Qt.AspectRatioMode.KeepAspectRatio
            )
            img_label = QLabel()
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(img_label)
        
        # Random mantra
        self.mantra = random.choice(MANTRAS)
        
        instruction = QLabel(f"TYPE TO UNLOCK: '{self.mantra}'")
        instruction.setFont(QFont("Monospace", 16))
        instruction.setStyleSheet("color: #ffffff;")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)
        
        # Input field
        self.input = QLineEdit()
        self.input.setFont(QFont("Monospace", 18))
        self.input.setStyleSheet(
            "color: #00ff00; background: #111111; "
            "border: 2px solid #ff0000; padding: 10px;"
        )
        self.input.setFixedWidth(500)
        self.input.returnPressed.connect(self.check_mantra)
        layout.addWidget(self.input, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.input.setFocus()
    
    def check_mantra(self):
        if self.input.text().strip().lower() == self.mantra:
            self.close()
        else:
            self.input.clear()
            self.input.setPlaceholderText("WRONG. THE BEAST WINS.")


# ==========================================
# OVERLAY (Time Anchor)
# ==========================================
class OverlayWindow(QMainWindow):
    def __init__(self, duration_mins):
        super().__init__()
        self.setWindowTitle("OVERLAY")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(320, 60)
        
        self.setStyleSheet(
            "background-color: rgba(0, 0, 0, 180); "
            "border: 1px solid #00ff00;"
        )
        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        label = QLabel("TIME:")
        label.setStyleSheet("color: #00ff00; font-weight: bold;")
        layout.addWidget(label)
        
        self.progress = QProgressBar()
        self.progress.setMaximum(duration_mins * 60)
        self.progress.setValue(duration_mins * 60)
        self.progress.setStyleSheet(
            "QProgressBar { border: 0px; background: #333333; }"
            "QProgressBar::chunk { background: #00ff00; }"
        )
        layout.addWidget(self.progress)


# ==========================================
# MAIN DASHBOARD
# ==========================================
class Dashboard(QMainWindow):
    def __init__(self, goal, duration, allowed_apps):
        super().__init__()
        self.setWindowTitle("OVERMAN DASHBOARD")
        self.resize(1200, 850)
        
        # Dark theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(13, 13, 13))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(200, 200, 200))
        self.setPalette(palette)
        self.setStyleSheet("background-color: #0d0d0d; color: #cccccc;")
        
        # Session data
        self.start_time = datetime.now()
        self.duration_secs = duration * 60
        self.current_secs = self.duration_secs
        self.goal = goal
        
        # Data tracking
        self.app_time = defaultdict(int)
        self.url_time = defaultdict(lambda: defaultdict(int))
        
        # Create overlay
        self.overlay = OverlayWindow(duration)
        self.overlay.show()
        
        # Start warden
        self.warden = WardenThread(allowed_apps)
        self.warden.lockout_signal.connect(self.trigger_lockout)
        self.warden.data_signal.connect(self.update_data)
        self.warden.start()
        
        # Setup UI
        self.init_ui()
        
        # Start countdown timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # LEFT PANEL
        left_panel = QVBoxLayout()
        
        # Session info
        session_frame = QFrame()
        session_frame.setStyleSheet(
            "background: #111111; border: 1px solid #333333; padding: 10px;"
        )
        session_layout = QVBoxLayout(session_frame)
        
        goal_label = QLabel(f"MISSION: {self.goal}")
        goal_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        goal_label.setStyleSheet("color: #ffffff;")
        session_layout.addWidget(goal_label)
        
        self.time_label = QLabel(f"START: {self.start_time.strftime('%H:%M')}")
        self.time_label.setStyleSheet("color: #888888;")
        session_layout.addWidget(self.time_label)
        
        self.progress = QProgressBar()
        self.progress.setMaximum(self.duration_secs)
        self.progress.setValue(self.duration_secs)
        self.progress.setStyleSheet("QProgressBar::chunk { background: #00ff00; }")
        session_layout.addWidget(self.progress)
        
        self.status_label = QLabel("STATUS: ACTIVE")
        self.status_label.setFont(QFont("Monospace", 12))
        session_layout.addWidget(self.status_label)
        
        left_panel.addWidget(session_frame)
        
        # Quote
        quote_label = QLabel(f'"{random.choice(QUOTES)}"')
        quote_label.setWordWrap(True)
        quote_label.setStyleSheet(
            "font-style: italic; color: #666666; margin-top: 20px;"
        )
        left_panel.addWidget(quote_label)
        left_panel.addStretch()
        
        main_layout.addLayout(left_panel, 1)
        
        # RIGHT PANEL (Tree View)
        right_panel = QVBoxLayout()
        
        tree_label = QLabel("TIME EXPENDITURE TREE")
        tree_label.setFont(QFont("Monospace", 14, QFont.Weight.Bold))
        tree_label.setStyleSheet("color: #00ff00;")
        right_panel.addWidget(tree_label)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["App / URL", "Time", "Status"])
        self.tree.setStyleSheet(
            "QTreeWidget { background: #0a0a0a; color: #cccccc; border: 1px solid #333; }"
            "QTreeWidget::item { padding: 5px; }"
        )
        right_panel.addWidget(self.tree)
        
        main_layout.addLayout(right_panel, 2)
    
    def update_data(self, app, title, status):
        """Update tracking data"""
        self.app_time[app] += 2
        if app in DRIFT_APPS or "firefox" in app or "chrome" in app:
            self.url_time[app][title] += 2
        
        # Update status
        self.time_label.setText(
            f"START: {self.start_time.strftime('%H:%M')} | "
            f"NOW: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.status_label.setText(f"CURRENT: {app} | STATE: {status}")
        
        if status == "Drifting":
            self.status_label.setStyleSheet("color: #ff0000; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #00ff00;")
        
        # Update tree periodically
        if random.random() < 0.1:
            self.update_tree()
    
    def update_tree(self):
        """Rebuild the time tree"""
        self.tree.clear()
        
        total_time = sum(self.app_time.values())
        
        for app, seconds in sorted(
            self.app_time.items(), key=lambda x: x[1], reverse=True
        ):
            mins, secs = divmod(seconds, 60)
            
            app_item = QTreeWidgetItem([
                app,
                f"{mins}m {secs}s",
                "✓" if any(a in app for a in self.warden.allowed) else "✗"
            ])
            
            # Add URL children if available
            if app in self.url_time:
                for url, url_secs in sorted(
                    self.url_time[app].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]:  # Top 5 URLs
                    url_mins, url_secs_rem = divmod(url_secs, 60)
                    url_item = QTreeWidgetItem([
                        url[:50],
                        f"{url_mins}m {url_secs_rem}s",
                        ""
                    ])
                    app_item.addChild(url_item)
            
            self.tree.addTopLevelItem(app_item)
        
        self.tree.expandAll()
    
    def tick(self):
        """Countdown timer"""
        if self.current_secs > 0:
            self.current_secs -= 1
            self.progress.setValue(self.current_secs)
            self.overlay.progress.setValue(self.current_secs)
        else:
            speak("Session complete.")
            self.timer.stop()
    
    def trigger_lockout(self, img_path):
        """Show audit window"""
        self.lockout = LockoutWindow(img_path)
        self.lockout.show()


# ==========================================
# PLANNER (Startup)
# ==========================================
class PlannerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PRE-FLIGHT CHECK")
        self.resize(600, 500)
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(17, 17, 17))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(238, 238, 238))
        self.setPalette(palette)
        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        
        title = QLabel("DELIBERATE PRACTICE INITIATION")
        title.setFont(QFont("Monospace", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #00ff00;")
        layout.addWidget(title)
        
        layout.addWidget(QLabel("1. Micro-Goal (Be Specific):"))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g., Write 1 IELTS essay paragraph")
        layout.addWidget(self.goal_input)
        
        layout.addWidget(QLabel("2. Duration (Minutes):"))
        self.time_input = QLineEdit("60")
        layout.addWidget(self.time_input)
        
        layout.addWidget(QLabel("3. Allowed Apps (comma separated):"))
        self.apps_input = QTextEdit()
        self.apps_input.setPlainText(
            "code, kitty, obsidian, anki, zathura, libreoffice, mpv"
        )
        self.apps_input.setMaximumHeight(80)
        layout.addWidget(self.apps_input)
        
        button = QPushButton("INITIATE PROTOCOL")
        button.setStyleSheet(
            "background: #004400; color: white; padding: 15px; "
            "font-weight: bold; border: 1px solid #00ff00;"
        )
        button.clicked.connect(self.launch)
        layout.addWidget(button)
    
    def launch(self):
        try:
            mins = int(self.time_input.text())
            goal = self.goal_input.text()
            apps = self.apps_input.toPlainText().split(',')
            
            if not goal:
                speak("Define the goal.")
                return
            
            self.dashboard = Dashboard(goal, mins, apps)
            self.dashboard.show()
            self.close()
            speak(f"Protocol engaged. Goal: {goal}")
        except:
            speak("Invalid input. Define goal and time.")


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    
    app = QApplication(sys.argv)
    app.setApplicationName("overman")
    
    planner = PlannerWindow()
    planner.show()
    
    sys.exit(app.exec())
