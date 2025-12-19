import sys
import json
import subprocess
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QTextEdit, QPushButton, 
                             QProgressBar, QStackedWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap

# --- CONFIGURATION & CONSTANTS ---
MANTRA = "i command myself"
KILL_KEYWORDS = ["porn", "xxx", "facebook", "instagram", "tiktok", "reddit"]
BRUTAL_DARK = "#0d0d0d"
ACCENT_RED = "#ff4444"
ACCENT_GREEN = "#00ff41" # Matrix green

class WardenThread(QThread):
    drift_signal = pyqtSignal(str)
    audit_signal = pyqtSignal()
    update_stats = pyqtSignal(dict)

    def __init__(self, allowed_apps, total_minutes):
        super().__init__()
        self.allowed_apps = [app.strip().lower() for app in allowed_apps.split(",")]
        self.total_seconds = total_minutes * 60
        self.elapsed_seconds = 0
        self.drift_time = 0
        self.focus_time = 0
        self.is_running = True
        self.app_logs = {} # RAM-only storage

    def run(self):
        audit_counter = 0
        drift_warning_counter = 0
        
        while self.is_running and self.elapsed_seconds < self.total_seconds:
            time.sleep(2)
            self.elapsed_seconds += 2
            audit_counter += 2
            
            # Get Active Window via Hyprland
            try:
                result = subprocess.check_output(["hyprctl", "activewindow", "-j"])
                data = json.loads(result)
                window_class = data.get("class", "").lower()
                window_title = data.get("title", "").lower()
            except:
                window_class = "unknown"
                window_title = "unknown"

            # 1. Kill Protocol
            if any(key in window_title for key in KILL_KEYWORDS):
                subprocess.run(["hyprctl", "dispatch", "closewindow", f"class:{window_class}"])
                continue

            # 2. Drift Detection
            is_browser = any(b in window_class for b in ["firefox", "brave", "chrome", "thorium"])
            is_allowed = any(a in window_class for a in self.allowed_apps)

            if (is_browser and not is_allowed) or (not is_allowed and window_class != ""):
                self.drift_time += 2
                drift_warning_counter += 2
                if drift_warning_counter >= 60:
                    subprocess.Popen(["espeak-ng", "Focus check. You are drifting."])
                    drift_warning_counter = 0
            else:
                self.focus_time += 2
                drift_warning_counter = 0

            # Log app usage
            self.app_logs[window_class] = self.app_logs.get(window_class, 0) + 2

            # 3. Audit Loop (10 Minutes)
            if audit_counter >= 600:
                self.audit_signal.emit()
                audit_counter = 0

            # Update UI
            self.update_stats.emit({
                "focus": self.focus_time,
                "drift": self.drift_time,
                "logs": self.app_logs,
                "remaining": self.total_seconds - self.elapsed_seconds
            })

class Architect(QWidget):
    def __init__(self, start_callback):
        super().__init__()
        self.setWindowTitle("Pre-Flight Check")
        self.setFixedSize(400, 500)
        self.start_callback = start_callback
        self.setStyleSheet(f"background-color: {BRUTAL_DARK}; color: white; border: 2px solid {ACCENT_RED};")
        
        layout = QVBoxLayout()
        title = QLabel("WILL TO POWER: INITIALIZATION")
        title.setFont(QFont("Monospace", 14, QFont.Weight.Bold))
        
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("MICRO-GOAL (e.g., Implement Auth Logic)")
        
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("DURATION (MINUTES)")
        
        self.apps_input = QTextEdit()
        self.apps_input.setPlaceholderText("WHITELISTED CLASSES (comma separated: code, obsidian)")
        
        btn = QPushButton("ASCEND")
        btn.setStyleSheet(f"background-color: {ACCENT_RED}; color: black; font-weight: bold;")
        btn.clicked.connect(self.submit)
        
        layout.addWidget(title)
        layout.addWidget(QLabel("What is the objective?"))
        layout.addWidget(self.goal_input)
        layout.addWidget(QLabel("For how long shall you struggle?"))
        layout.addWidget(self.time_input)
        layout.addWidget(QLabel("Allowed tools:"))
        layout.addWidget(self.apps_input)
        layout.addWidget(btn)
        self.setLayout(layout)

    def submit(self):
        if self.goal_input.text() and self.time_input.text():
            self.start_callback(self.goal_input.text(), self.time_input.text(), self.apps_input.toPlainText())
            self.close()

class TimeAnchor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("overman")
        
        self.layout = QVBoxLayout()
        self.bar = QProgressBar()
        self.bar.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid {ACCENT_RED}; background-color: black; text-align: center; color: white; }}
            QProgressBar::chunk {{ background-color: {ACCENT_RED}; }}
        """)
        self.layout.addWidget(self.bar)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

    def update_bar(self, current, total):
        self.bar.setMaximum(total)
        self.bar.setValue(current)

class ShameEngine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Dashboard")
        self.setStyleSheet(f"background-color: {BRUTAL_DARK}; color: {ACCENT_GREEN}; border: 1px solid {ACCENT_GREEN};")
        
        self.layout = QHBoxLayout()
        
        # Left Panel: Psychometrics
        self.stats_panel = QVBoxLayout()
        stats = [
            ("INTELLECT: 97th Percentile", ACCENT_GREEN),
            ("OPENNESS: 99th Percentile", ACCENT_GREEN),
            ("CONSCIENTIOUSNESS: 43% (FAILURE)", ACCENT_RED),
            ("TYPE: INTP (Drifter)", "yellow")
        ]
        for text, color in stats:
            lbl = QLabel(text)
            lbl.setFont(QFont("Monospace", 12, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {color};")
            self.stats_panel.addWidget(lbl)
        
        # Right Panel: Live Charts
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5, 8))
        self.figure.patch.set_facecolor(BRUTAL_DARK)
        self.canvas = FigureCanvas(self.figure)
        
        self.layout.addLayout(self.stats_panel)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

    def refresh_charts(self, data):
        self.ax1.clear()
        self.ax2.clear()
        
        # Pie Chart
        labels = ['Focus', 'Drift']
        sizes = [data['focus'], data['drift']]
        self.ax1.pie(sizes, labels=labels, colors=[ACCENT_GREEN, ACCENT_RED], autopct='%1.1f%%', textprops={'color':"w"})
        self.ax1.set_title("SESSION WILL", color="white")
        
        # Bar Chart
        apps = list(data['logs'].keys())[-5:]
        times = list(data['logs'].values())[-5:]
        self.ax2.barh(apps, times, color=ACCENT_GREEN)
        self.ax2.set_title("RESOURCE ALLOCATION", color="white")
        self.ax2.tick_params(axis='x', colors='white')
        self.ax2.tick_params(axis='y', colors='white')
        
        self.canvas.draw()

class AuditLockout(QWidget):
    def __init__(self, unlock_callback):
        super().__init__()
        self.setWindowTitle("The Audit")
        self.unlock_callback = unlock_callback
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(f"background-color: {BRUTAL_DARK}; color: {ACCENT_RED};")
        
        self.layout = QVBoxLayout()
        self.img_label = QLabel("EVIDENCE")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.warning = QLabel("STAGNATION DETECTED. JUSTIFY YOUR EXISTENCE.")
        self.warning.setFont(QFont("Monospace", 16, QFont.Weight.Bold))
        self.warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("TYPE THE MANTRA TO RESUME CONTROL")
        self.input.setStyleSheet("font-size: 20px; padding: 10px;")
        self.input.textChanged.connect(self.check_mantra)
        
        self.layout.addWidget(self.warning)
        self.layout.addWidget(self.img_label)
        self.layout.addWidget(self.input)
        self.setLayout(self.layout)

    def show_audit(self):
        subprocess.run(["grim", "/tmp/audit.png"])
        pixmap = QPixmap("/tmp/audit.png")
        self.img_label.setPixmap(pixmap.scaled(800, 450, Qt.AspectRatioMode.KeepAspectRatio))
        self.input.clear()
        self.showFullScreen()
        self.activateWindow()

    def check_mantra(self):
        if self.input.text().lower() == MANTRA:
            self.hide()
            subprocess.run(["rm", "/tmp/audit.png"])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore() # Prevent escape

class OvermanProtocol:
    def __init__(self):
        self.architect = Architect(self.start_session)
        self.architect.show()
        
    def start_session(self, goal, duration, apps):
        self.duration_secs = int(duration) * 60
        
        self.overlay = TimeAnchor()
        self.overlay.show()
        
        self.dashboard = ShameEngine()
        self.dashboard.show()
        
        self.audit = AuditLockout(None)
        
        self.warden = WardenThread(apps, int(duration))
        self.warden.update_stats.connect(self.sync_ui)
        self.warden.audit_signal.connect(self.audit.show_audit)
        self.warden.start()

    def sync_ui(self, data):
        self.overlay.update_bar(data['remaining'], self.duration_secs)
        self.dashboard.refresh_charts(data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("overman")
    protocol = OvermanProtocol()
    sys.exit(app.exec())
