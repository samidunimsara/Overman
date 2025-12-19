import sys
import os
import json
import random
import subprocess
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QProgressBar, QFrame, QPushButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- CONFIGURATION (ADJUST THESE) ---
# Apps that count as "Deep Work"
ALLOWED_APPS = ["mpv", "kitty", "obsidian", "anki", "libreoffice", "zathura"] 
# Apps that trigger immediate KILL + LOCKOUT
FORBIDDEN_KEYWORDS = ["porn", "facebook", "twitter", "instagram", "tiktok"] 
# Apps that trigger "Drift Warning" (Voice Alarm) if focused too long
DISTRACTION_APPS = ["firefox", "brave", "chrome", "discord"]

# --- PATHS ---
BASE_DIR = os.path.expanduser("~/.local/share/truthengine")
DATA_FILE = os.path.join(BASE_DIR, "session_log.csv")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "shame_snaps")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# --- NIETZSCHEAN DATA ---
QUOTES = [
    "He who cannot obey himself will be commanded.",
    "Man is a rope stretched between the animal and the Overman.",
    "Your intellect (97th percentile) is useless without execution.",
    "Build the bridge, or remain the animal.",
    "The 43% Conscientiousness score is your prison. Break it."
]

def speak(text):
    """Voice of the Warden."""
    subprocess.Popen(["espeak-ng", "-s", "160", "-v", "en-us", text], stderr=subprocess.DEVNULL)

class WardenThread(QThread):
    """
    Background process:
    1. Kills forbidden apps immediately.
    2. Warns you if you drift into browsers for too long.
    3. Logs activity for the charts.
    """
    lockout_signal = pyqtSignal(str) # Trigger lockout with screenshot path
    update_signal = pyqtSignal(str, str) # Send current app/time to GUI

    def run(self):
        drift_timer = 0
        while True:
            self.msleep(2000) # Check every 2 seconds
            try:
                # Get Window Info from Hyprland
                cmd = ["hyprctl", "activewindow", "-j"]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                app_class = data.get("class", "").lower()
                title = data.get("title", "").lower()

                # 1. KILL PROTOCOL
                if any(k in title for k in FORBIDDEN_KEYWORDS):
                    subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{data['address']}"])
                    snap_path = os.path.join(SCREENSHOT_DIR, f"shame_{datetime.now().strftime('%H%M%S')}.png")
                    subprocess.run(["grim", snap_path])
                    self.lockout_signal.emit(snap_path)
                    speak("Protocol violated. The animal has taken over.")
                    continue

                # 2. DRIFT PROTOCOL
                is_working = any(a in app_class for a in ALLOWED_APPS)
                is_distracted = any(d in app_class for d in DISTRACTION_APPS)

                if is_distracted:
                    drift_timer += 2
                    if drift_timer == 60: # 1 minute grace period
                        speak(f"Samidu, you are drifting. Close {app_class}.")
                    if drift_timer > 120: # 2 minutes -> constant nagging
                         speak("Return to the goal immediately.")
                else:
                    drift_timer = 0

                # 3. LOGGING
                status = "Productive" if is_working else "Drifting"
                self.update_signal.emit(app_class, status)
                
                # Save to CSV
                df = pd.DataFrame([{"timestamp": datetime.now(), "app": app_class, "status": status}])
                df.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False)

            except Exception:
                pass

class LockoutWindow(QMainWindow):
    """The Punishment Cell."""
    def __init__(self, img_path):
        super().__init__()
        self.setProperty("class", "truth-lockout")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet("background: black; border: 4px solid red;")
        
        layout = QVBoxLayout()
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)

        lbl = QLabel("YOU SURRENDERED TO IMPULSE")
        lbl.setFont(QFont("Impact", 40)); lbl.setStyleSheet("color: red")
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Show the screenshot of what you were doing
        if os.path.exists(img_path):
            pix = QPixmap(img_path).scaled(800, 500, Qt.AspectRatioMode.KeepAspectRatio)
            img = QLabel(); img.setPixmap(pix)
            layout.addWidget(img, alignment=Qt.AlignmentFlag.AlignCenter)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type: 'I command myself' to release")
        self.input.setStyleSheet("font-size: 20px; padding: 10px; color: white; background: #222; border: 1px solid red;")
        self.input.setFixedWidth(500)
        self.input.returnPressed.connect(self.check_mantra)
        layout.addWidget(self.input, alignment=Qt.AlignmentFlag.AlignCenter)

    def check_mantra(self):
        if self.input.text().lower() == "i command myself":
            self.close()

class PlannerWindow(QMainWindow):
    """Step 1: Deliberate Practice Setup."""
    def __init__(self):
        super().__init__()
        self.setProperty("class", "truth-engine")
        self.setWindowTitle("PRE-FLIGHT CHECK")
        self.setStyleSheet("background: #0d0d0d; color: #eee;")
        
        layout = QVBoxLayout()
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)

        title = QLabel("DELIBERATE PRACTICE INITIATION")
        title.setFont(QFont("Monospace", 16, QFont.Weight.Bold)); title.setStyleSheet("color: #00ff41")
        layout.addWidget(title)

        layout.addWidget(QLabel("1. Specific Skill to Train (Micro-Goal):"))
        self.skill_inp = QLineEdit()
        layout.addWidget(self.skill_inp)

        layout.addWidget(QLabel("2. Weakness to Target:"))
        self.weak_inp = QLineEdit()
        layout.addWidget(self.weak_inp)

        layout.addWidget(QLabel("3. Duration (Minutes):"))
        self.time_inp = QLineEdit()
        layout.addWidget(self.time_inp)

        btn = QPushButton("ENGAGE PROTOCOL")
        btn.setStyleSheet("background: #004400; color: white; padding: 15px; font-weight: bold;")
        btn.clicked.connect(self.launch_dashboard)
        layout.addWidget(btn)

    def launch_dashboard(self):
        try:
            mins = int(self.time_inp.text())
            goal = self.skill_inp.text()
            if not goal: raise ValueError
            
            self.dash = MainDashboard(mins, goal)
            self.dash.show()
            self.close()
            speak(f"Protocol engaged. Goal: {goal}")
        except:
            speak("Invalid Input. Define the goal.")

class MainDashboard(QMainWindow):
    """The Control Center."""
    def __init__(self, duration_mins, goal):
        super().__init__()
        self.setProperty("class", "truth-engine")
        self.duration_sec = duration_mins * 60
        self.goal = goal
        self.init_ui()
        
        # Start the Enforcer
        self.warden = WardenThread()
        self.warden.lockout_signal.connect(self.trigger_lockout)
        self.warden.update_signal.connect(self.update_live_data)
        self.warden.start()

        # Session Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def init_ui(self):
        self.resize(1100, 700)
        self.setStyleSheet("background-color: #0d0d0d; color: #e0e0e0;")
        central = QWidget(); self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # LEFT: STATS & TRUTH
        left = QVBoxLayout()
        
        # Profile Data (Hardcoded based on your reports)
        prof_frame = QFrame(); prof_frame.setStyleSheet("border: 1px solid #333; padding: 10px;")
        pl = QVBoxLayout(prof_frame)
        pl.addWidget(QLabel("OPERATOR STATS (DEC 2025):"))
        pl.addWidget(self.stat_row("INTELLECT", "97th Percentile", "#00ff41"))
        pl.addWidget(self.stat_row("OPENNESS", "99th Percentile", "#00ff41"))
        pl.addWidget(self.stat_row("CONSCIENTIOUSNESS", "43% (FAILURE)", "#ff3333"))
        pl.addWidget(self.stat_row("TYPE", "INTP (Regression from INTJ)", "#ffff00"))
        left.addWidget(prof_frame)

        # Current Session
        self.lbl_goal = QLabel(f"CURRENT MISSION:\n{self.goal}")
        self.lbl_goal.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.lbl_goal.setStyleSheet("color: white; margin-top: 20px;")
        left.addWidget(self.lbl_goal)

        self.progress = QProgressBar()
        self.progress.setMaximum(self.duration_sec)
        self.progress.setValue(self.duration_sec)
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #00ff41; }")
        left.addWidget(self.progress)
        
        self.lbl_status = QLabel("STATUS: AWAITING DATA")
        left.addWidget(self.lbl_status)
        
        # Quote
        quote = QLabel(f"\"{random.choice(QUOTES)}\"")
        quote.setWordWrap(True)
        quote.setStyleSheet("font-style: italic; color: #888;")
        left.addWidget(quote)
        
        layout.addLayout(left, 1)

        # RIGHT: CHARTS
        self.canvas = FigureCanvas(Figure(figsize=(5, 5), facecolor='#0d0d0d'))
        layout.addWidget(self.canvas, 2)
        self.update_chart()

    def stat_row(self, title, val, color):
        l = QLabel(f"{title}: {val}")
        l.setStyleSheet(f"color: {color}; font-weight: bold;")
        return l

    def tick(self):
        curr = self.progress.value()
        if curr > 0:
            self.progress.setValue(curr - 1)
        else:
            self.lbl_status.setText("SESSION COMPLETE")
            self.timer.stop()
            speak("Session complete. Review your progress.")

    def update_live_data(self, app, status):
        self.lbl_status.setText(f"ACTIVE: {app} | STATUS: {status}")
        if "Drifting" in status:
            self.lbl_status.setStyleSheet("color: #ff3333; font-weight: bold;")
        else:
            self.lbl_status.setStyleSheet("color: #00ff41;")
        
        # Trigger chart update occasionally
        if random.random() < 0.1: 
            self.update_chart()

    def update_chart(self):
        if not os.path.exists(DATA_FILE): return
        try:
            df = pd.read_csv(DATA_FILE)
            counts = df['status'].value_counts()
            
            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111)
            ax.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=['#00ff41', '#ff3333'],
                   textprops={'color':"w"})
            ax.set_title("WILLPOWER DISTRIBUTION", color='white')
            self.canvas.draw()
        except: pass

    def trigger_lockout(self, path):
        self.lock = LockoutWindow(path)
        self.lock.show()

if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland" # Force Wayland for Hyprland
    app = QApplication(sys.argv)
    
    # Start with the Planner
    planner = PlannerWindow()
    planner.show()
    
    sys.exit(app.exec())
