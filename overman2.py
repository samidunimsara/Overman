import sys
import os
import json
import random
import subprocess
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QProgressBar, 
                             QFrame, QPushButton, QTabWidget, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- GLOBAL CONFIG ---
BASE_DIR = os.path.expanduser("~/.local/share/overman")
DATA_FILE = os.path.join(BASE_DIR, "session_history.csv")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "audit_evidence")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Default forbidden keywords (Always active - The "Porn" Blocker)
FORBIDDEN_KEYWORDS = ["porn", "facebook", "twitter", "instagram", "tiktok", "reddit", "xxx"]
# Drifting triggers voice alarm
DRIFT_APPS = ["firefox", "brave", "chrome", "discord"]

NIETZSCHE_QUOTES = [
    "He who cannot obey himself will be commanded.",
    "Man is a rope stretched between the animal and the Overman.",
    "Your intellect (97th percentile) is useless without execution.",
    "The 43% Conscientiousness score is your prison. Break it.",
    "What is the ape to man? A laughingstock or a painful embarrassment.",
    "You must be ready to burn yourself in your own flame.",
    "I teach you the Overman. Man is something that shall be overcome."
]

def speak(text):
    """The Voice of the Warden."""
    subprocess.Popen(["espeak-ng", "-s", "170", "-v", "en-us", text], stderr=subprocess.DEVNULL)

# --- WORKER THREAD (THE WARDEN) ---
class WardenThread(QThread):
    lockout_signal = pyqtSignal(str)     # Trigger Audit Window
    update_signal = pyqtSignal(str, str) # Send data to Dashboard

    def __init__(self, allowed_apps_list):
        super().__init__()
        self.allowed_apps = [a.strip().lower() for a in allowed_apps_list if a.strip()]
        self.running = True

    def run(self):
        drift_timer = 0
        audit_timer = 0 
        
        while self.running:
            self.msleep(2000) # Poll every 2 seconds
            audit_timer += 2
            
            try:
                # 1. GET HYPRLAND WINDOW DATA
                cmd = ["hyprctl", "activewindow", "-j"]
                output = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(output)
                app_class = data.get("class", "").lower()
                title = data.get("title", "").lower()

                # 2. IMMEDIATE KILL PROTOCOL (Forbidden Keywords)
                if any(k in title for k in FORBIDDEN_KEYWORDS):
                    subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{data['address']}"])
                    self.trigger_audit("VIOLATION DETECTED")
                    continue

                # 3. THE 10-MINUTE MANDATORY AUDIT
                if audit_timer >= 600: # 10 Minutes
                    self.trigger_audit("10 MINUTE CHECK")
                    audit_timer = 0

                # 4. DRIFT DETECTION (Voice Warning)
                # If app is NOT in Allowed Apps, it counts as drift
                is_allowed = any(a in app_class for a in self.allowed_apps)
                
                if not is_allowed:
                    drift_timer += 2
                    if drift_timer == 60: # 1 min grace
                        speak(f"Samidu, focus. You are in {app_class}.")
                    elif drift_timer > 120:
                        speak("Drift detected. Return to the goal.")
                else:
                    drift_timer = 0

                # 5. DATA LOGGING
                status = "Productive" if is_allowed else "Drifting"
                self.update_signal.emit(app_class, status)
                
                df = pd.DataFrame([{
                    "timestamp": datetime.now(), 
                    "app": app_class, 
                    "status": status,
                    "is_allowed": is_allowed
                }])
                df.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False)

            except Exception:
                pass

    def trigger_audit(self, reason):
        speak(f"{reason}. Audit initiated.")
        snap_path = os.path.join(SCREENSHOT_DIR, f"audit_{datetime.now().strftime('%H%M%S')}.png")
        subprocess.run(["grim", snap_path])
        self.lockout_signal.emit(snap_path)

# --- UI: THE LOCKOUT (AUDIT) ---
class LockoutWindow(QMainWindow):
    def __init__(self, img_path):
        super().__init__()
        self.setProperty("class", "overman-lockout")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet("background: black; border: 4px solid red;")
        
        layout = QVBoxLayout()
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)

        lbl = QLabel("AUDIT IN PROGRESS: FACE THE TRUTH")
        lbl.setFont(QFont("Impact", 40)); lbl.setStyleSheet("color: red")
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Show evidence of what you were doing
        if os.path.exists(img_path):
            pix = QPixmap(img_path).scaled(900, 600, Qt.AspectRatioMode.KeepAspectRatio)
            img = QLabel(); img.setPixmap(pix)
            layout.addWidget(img, alignment=Qt.AlignmentFlag.AlignCenter)

        # Random Nietzsche Quote for the Audit
        self.target_phrase = random.choice(["I am a bridge", "Will to power", "Kill the worm", "Command myself"])
        
        q_lbl = QLabel(f"TYPE TO UNLOCK: '{self.target_phrase}'")
        q_lbl.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(q_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.input = QLineEdit()
        self.input.setStyleSheet("font-size: 24px; padding: 10px; color: white; background: #222; border: 1px solid red;")
        self.input.setFixedWidth(500)
        self.input.returnPressed.connect(self.check_mantra)
        layout.addWidget(self.input, alignment=Qt.AlignmentFlag.AlignCenter)
        self.input.setFocus()

    def check_mantra(self):
        if self.input.text().lower().strip() == self.target_phrase.lower():
            self.close()

# --- UI: THE OVERLAY (FLOATING TIMER) ---
class OverlayWindow(QMainWindow):
    def __init__(self, duration_mins):
        super().__init__()
        self.setProperty("class", "overman-overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.resize(350, 60)
        self.setStyleSheet("background: rgba(0,0,0,0.8); border: 1px solid #00ff41;")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10,0,10,0)
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)

        self.lbl = QLabel("REMAINING:")
        self.lbl.setStyleSheet("color: #00ff41; font-weight: bold;")
        layout.addWidget(self.lbl)

        self.prog = QProgressBar()
        self.prog.setMaximum(duration_mins * 60)
        self.prog.setValue(duration_mins * 60)
        self.prog.setStyleSheet("QProgressBar {border: 0px; background: #333; height: 10px;} QProgressBar::chunk {background: #00ff41;}")
        layout.addWidget(self.prog)

# --- UI: THE DASHBOARD (MAIN) ---
class Dashboard(QMainWindow):
    def __init__(self, goal, duration, allowed_apps):
        super().__init__()
        self.setWindowTitle("OVERMAN DASHBOARD")
        self.setProperty("class", "overman-app")
        self.resize(1100, 800)
        self.setStyleSheet("background-color: #0d0d0d; color: #e0e0e0;")
        
        self.start_time = datetime.now().strftime("%H:%M")
        
        self.overlay = OverlayWindow(duration)
        self.overlay.show()
        
        self.warden = WardenThread(allowed_apps)
        self.warden.lockout_signal.connect(self.trigger_lockout)
        self.warden.update_signal.connect(self.update_live_data)
        self.warden.start()

        self.setup_ui(goal, duration)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def setup_ui(self, goal, duration):
        central = QWidget(); self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # --- LEFT PANEL: STATS & LOGIC ---
        left = QVBoxLayout()
        
        # 1. PERSONALITY REPORT DATA (The "Shame" Box)
        report_box = QFrame(); report_box.setStyleSheet("border: 1px solid #333; padding: 10px; background: #111;")
        rl = QVBoxLayout(report_box)
        rl.addWidget(QLabel("OPERATOR PSYCHOMETRICS (FROM PDF):"))
        rl.addWidget(self.mk_stat("INTELLECT", "97th Percentile", "#00ff41"))
        rl.addWidget(self.mk_stat("OPENNESS", "99th Percentile", "#00ff41"))
        rl.addWidget(self.mk_stat("CONSCIENTIOUSNESS", "43% (FAILURE)", "#ff3333"))
        rl.addWidget(self.mk_stat("TYPE", "INTP (Drifter)", "#ffff00"))
        left.addWidget(report_box)

        # 2. SESSION STATUS
        self.time_lbl = QLabel(f"START: {self.start_time} | NOW: {self.start_time}")
        self.time_lbl.setStyleSheet("color: #888; font-size: 14px;")
        left.addWidget(self.time_lbl)

        self.lbl_goal = QLabel(f"MISSION: {goal}")
        self.lbl_goal.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_goal.setStyleSheet("color: white; margin-top: 10px;")
        left.addWidget(self.lbl_goal)

        self.main_prog = QProgressBar()
        self.main_prog.setMaximum(duration * 60)
        self.main_prog.setValue(duration * 60)
        self.main_prog.setStyleSheet("QProgressBar::chunk {background-color: #00ff41;}")
        left.addWidget(self.main_prog)

        self.lbl_status = QLabel("STATUS: INITIALIZING...")
        self.lbl_status.setFont(QFont("Monospace", 12))
        left.addWidget(self.lbl_status)
        
        quote = QLabel(f"\"{random.choice(NIETZSCHE_QUOTES)}\"")
        quote.setWordWrap(True)
        quote.setStyleSheet("font-style: italic; color: #888; margin-top: 20px;")
        left.addWidget(quote)
        
        left.addStretch()
        layout.addLayout(left, 3)

        # --- RIGHT PANEL: CHARTS ---
        right = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 0; } QTabBar::tab { background: #222; color: #888; padding: 10px; } QTabBar::tab:selected { background: #444; color: white; }")
        
        # Tab 1: Productivity Pie
        self.fig1 = Figure(figsize=(5, 4), facecolor='#0d0d0d')
        self.canvas1 = FigureCanvas(self.fig1)
        self.tabs.addTab(self.canvas1, "Focus Ratio")

        # Tab 2: App Usage Bar
        self.fig2 = Figure(figsize=(5, 4), facecolor='#0d0d0d')
        self.canvas2 = FigureCanvas(self.fig2)
        self.tabs.addTab(self.canvas2, "App Usage")

        right.addWidget(self.tabs)
        layout.addLayout(right, 4)

    def mk_stat(self, k, v, c):
        l = QLabel(f"{k}: {v}"); l.setStyleSheet(f"color: {c}; font-weight: bold;"); return l

    def update_live_data(self, app, status):
        now_time = datetime.now().strftime("%H:%M:%S")
        self.time_lbl.setText(f"START: {self.start_time} | NOW: {now_time}")
        self.lbl_status.setText(f"CURRENT: {app} | STATE: {status}")
        self.lbl_status.setStyleSheet(f"color: {'#ff3333' if status=='Drifting' else '#00ff41'}")
        
        if random.random() < 0.1: self.refresh_charts()

    def refresh_charts(self):
        if not os.path.exists(DATA_FILE): return
        try:
            df = pd.read_csv(DATA_FILE)
            
            # Pie Chart
            self.fig1.clear()
            ax1 = self.fig1.add_subplot(111)
            counts = df['status'].value_counts()
            ax1.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=['#00ff41', '#ff3333'], textprops={'color':"w"})
            ax1.set_title("WILLPOWER", color='white')
            self.canvas1.draw()

            # Bar Chart
            self.fig2.clear()
            ax2 = self.fig2.add_subplot(111)
            app_counts = df['app'].value_counts().head(5)
            ax2.barh(app_counts.index, app_counts.values, color='#00aaff')
            ax2.tick_params(colors='white', labelcolor='white')
            ax2.set_title("TOP APPS", color='white')
            self.canvas2.draw()
        except: pass

    def tick(self):
        curr = self.main_prog.value()
        if curr > 0:
            self.main_prog.setValue(curr - 1)
            self.overlay.prog.setValue(curr - 1)
            # Color change for urgency
            if curr < 300: # Last 5 mins
                self.overlay.setStyleSheet("background: rgba(0,0,0,0.8); border: 2px solid red;")
        else:
            self.lbl_status.setText("SESSION COMPLETE")
            speak("Session complete.")
            self.timer.stop()

    def trigger_lockout(self, path):
        self.lock = LockoutWindow(path)
        self.lock.show()

# --- UI: THE ARCHITECT (STARTUP) ---
class PlannerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PRE-FLIGHT CHECK")
        self.setProperty("class", "overman-app")
        self.resize(600, 500)
        self.setStyleSheet("background: #0d0d0d; color: #eee;")
        
        layout = QVBoxLayout()
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)

        l = QLabel("STEP 1: DELIBERATE PRACTICE PARAMETERS"); l.setStyleSheet("color: #00ff41; font-weight: bold; font-size: 16px;")
        layout.addWidget(l)

        layout.addWidget(QLabel("1. Micro-Goal (Be Specific):"))
        self.goal_in = QLineEdit()
        self.goal_in.setPlaceholderText("e.g. Write 1 essay paragraph about Education")
        layout.addWidget(self.goal_in)

        layout.addWidget(QLabel("2. Duration (Minutes):"))
        self.time_in = QLineEdit("60")
        layout.addWidget(self.time_in)

        layout.addWidget(QLabel("3. Allowed Apps (Comma separated):"))
        # Default apps pre-filled for IELTS study
        self.apps_in = QTextEdit("code, kitty, obsidian, anki, zathura, libreoffice, mpv")
        self.apps_in.setMaximumHeight(80)
        layout.addWidget(self.apps_in)

        btn = QPushButton("INITIATE PROTOCOL")
        btn.setStyleSheet("background: #004400; padding: 15px; font-weight: bold; border: 1px solid #00ff41; margin-top: 20px;")
        btn.clicked.connect(self.launch)
        layout.addWidget(btn)

    def launch(self):
        try:
            m = int(self.time_in.text())
            g = self.goal_in.text()
            apps = self.apps_in.toPlainText().split(',')
            if not g: raise ValueError
            
            self.dash = Dashboard(g, m, apps)
            self.dash.show()
            self.close()
            speak(f"Protocol engaged. Goal: {g}")
        except:
            speak("Error. Define goal and time.")

if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    app = QApplication(sys.argv)
    plan = PlannerWindow()
    plan.show()
    sys.exit(app.exec())
