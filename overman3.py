import sys
import os
import json
import random
import subprocess
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QProgressBar, 
                             QFrame, QPushButton, QTabWidget, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- CONFIGURATION ---
BASE_DIR = os.path.expanduser("~/.local/share/overman")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "temp_evidence")

# Ensure clean slate every restart (Privacy Requirement)
if os.path.exists(SCREENSHOT_DIR):
    shutil.rmtree(SCREENSHOT_DIR)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# HARSH NIETZSCHEAN QUOTES
QUOTES = [
    "Your intellect (97th percentile) is useless. You are failing at 43% Conscientiousness.",
    "He who cannot obey himself will be commanded. That is the nature of living creatures.",
    "The ape is an embarrassment to man. You are the ape right now.",
    "Do not talk about 'potential'. Potential is just energy doing nothing.",
    "Man is a rope tied between beast and Overman—a rope over an abyss.",
    "Burn yourself in your own flame; how could you become new if you have not first become ashes?"
]

# PERMANENTLY BANNED KEYWORDS (Triggers Immediate Kill)
FORBIDDEN = ["porn", "xxx", "sex", "facebook", "twitter", "instagram", "tiktok", "reddit", "shorts", "reels"]

# DRIFT APPS (Allowed briefly, but trigger voice alarms if focused too long)
DRIFT_APPS = ["firefox", "brave", "chrome", "chromium", "discord", "thorium"]

def speak(text):
    subprocess.Popen(["espeak-ng", "-s", "175", "-v", "en-us", text], stderr=subprocess.DEVNULL)

class WardenThread(QThread):
    lockout_trigger = pyqtSignal(str)
    data_update = pyqtSignal(str, str, dict) # App, Status, StatsDict

    def __init__(self, allowed_apps):
        super().__init__()
        self.allowed = [x.strip().lower() for x in allowed_apps if x.strip()]
        self.stats = {"Productive": 0, "Drifting": 0}
        self.app_usage = {}
        self.running = True

    def run(self):
        audit_timer = 0
        drift_timer = 0
        
        while self.running:
            self.msleep(2000) # Check every 2 seconds
            audit_timer += 2
            
            try:
                # 1. HYPRLAND QUERY
                cmd = ["hyprctl", "activewindow", "-j"]
                raw = subprocess.check_output(cmd).decode("utf-8")
                data = json.loads(raw)
                app = data.get("class", "").lower()
                title = data.get("title", "").lower()
                
                # 2. KILL PROTOCOL
                if any(k in title for k in FORBIDDEN):
                    subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{data['address']}"])
                    self.trigger_audit("PROTOCOL VIOLATION")
                    continue

                # 3. 10-MINUTE AUDIT LOOP
                if audit_timer >= 600: # 600s = 10 mins
                    self.trigger_audit("10 MINUTE AUDIT")
                    audit_timer = 0

                # 4. DRIFT DETECTION
                is_whitelisted = any(w in app for w in self.allowed)
                is_drift_risk = any(d in app for d in DRIFT_APPS)

                status = "Productive"
                if not is_whitelisted:
                    status = "Drifting"
                    if is_drift_risk:
                        drift_timer += 2
                        if drift_timer == 60: speak(f"Focus check. You are in {app}.")
                        if drift_timer > 120: speak("Close the browser. Return to the goal.")
                else:
                    drift_timer = 0

                # 5. SESSION-ONLY DATA AGGREGATION
                self.stats[status] += 2
                self.app_usage[app] = self.app_usage.get(app, 0) + 2
                self.data_update.emit(app, status, {"pie": self.stats, "bar": self.app_usage})

            except Exception:
                pass

    def trigger_audit(self, reason):
        speak(f"{reason}. Prove your focus.")
        path = os.path.join(SCREENSHOT_DIR, "evidence.png")
        subprocess.run(["grim", path])
        self.lockout_trigger.emit(path)

class LockoutWindow(QMainWindow):
    def __init__(self, img_path):
        super().__init__()
        self.setProperty("class", "overman-lockout")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet("background: #000; border: 4px solid #ff0000;")
        
        layout = QVBoxLayout()
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)

        lbl = QLabel("AUDIT: FACE REALITY")
        lbl.setFont(QFont("Monospace", 30, QFont.Weight.Bold)); lbl.setStyleSheet("color: red")
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        if os.path.exists(img_path):
            pix = QPixmap(img_path).scaled(800, 500, Qt.AspectRatioMode.KeepAspectRatio)
            img = QLabel(); img.setPixmap(pix)
            layout.addWidget(img, alignment=Qt.AlignmentFlag.AlignCenter)

        self.mantra = random.choice(["will to power", "i command myself", "kill the worm", "become the bridge"])
        layout.addWidget(QLabel(f"TYPE TO UNLOCK: '{self.mantra}'"), alignment=Qt.AlignmentFlag.AlignCenter)

        self.inp = QLineEdit()
        self.inp.setStyleSheet("font-size: 20px; padding: 10px; color: white; background: #222; border: 1px solid red;")
        self.inp.setFixedWidth(400)
        self.inp.returnPressed.connect(self.check)
        layout.addWidget(self.inp, alignment=Qt.AlignmentFlag.AlignCenter)
        self.inp.setFocus()

    def check(self):
        if self.inp.text().lower().strip() == self.mantra: self.close()

class Overlay(QMainWindow):
    def __init__(self, mins):
        super().__init__()
        self.setProperty("class", "overman-overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.resize(300, 40)
        self.setStyleSheet("background: rgba(0,0,0,0.8); border: 1px solid #00ff00;")
        
        layout = QHBoxLayout(); layout.setContentsMargins(5,0,5,0)
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)
        
        self.lbl = QLabel("TIME:"); self.lbl.setStyleSheet("color: #00ff00; font-weight: bold;")
        layout.addWidget(self.lbl)
        self.prog = QProgressBar(); self.prog.setMaximum(mins*60); self.prog.setValue(mins*60)
        self.prog.setStyleSheet("QProgressBar{border:0; background:#333} QProgressBar::chunk{background:#00ff00}")
        layout.addWidget(self.prog)

class Dashboard(QMainWindow):
    def __init__(self, goal, mins, apps):
        super().__init__()
        self.setProperty("class", "overman-app")
        self.setWindowTitle("OVERMAN DASHBOARD")
        self.resize(1000, 700)
        self.setStyleSheet("background: #0d0d0d; color: #ccc;")
        
        self.overlay = Overlay(mins)
        self.overlay.show()
        
        self.warden = WardenThread(apps)
        self.warden.lockout_trigger.connect(self.lock_screen)
        self.warden.data_update.connect(self.update_ui)
        self.warden.start()
        
        self.init_ui(goal, mins)
        self.timer = QTimer(); self.timer.timeout.connect(self.tick); self.timer.start(1000)

    def init_ui(self, goal, mins):
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # LEFT PANEL (Stats & Shame)
        left = QVBoxLayout()
        
        # PSYCHOMETRICS BOX (From your data)
        box = QFrame(); box.setStyleSheet("border: 1px solid #333; padding: 10px; background: #111;")
        bl = QVBoxLayout(box)
        bl.addWidget(self.mk_lbl("OPERATOR PSYCHOMETRICS:", "#fff"))
        bl.addWidget(self.mk_lbl("INTELLECT: 97th Percentile", "#00ff00"))
        bl.addWidget(self.mk_lbl("OPENNESS: 99th Percentile", "#00ff00"))
        bl.addWidget(self.mk_lbl("CONSCIENTIOUSNESS: 43% (FAILURE)", "#ff0000"))
        bl.addWidget(self.mk_lbl("TYPE: INTP (Drifter)", "#ffff00"))
        left.addWidget(box)

        self.time_lbl = self.mk_lbl(f"NOW: {datetime.now().strftime('%H:%M')}", "#888")
        left.addWidget(self.time_lbl)

        self.goal_lbl = self.mk_lbl(f"GOAL: {goal}", "#fff"); self.goal_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        left.addWidget(self.goal_lbl)

        self.bar = QProgressBar(); self.bar.setMaximum(mins*60); self.bar.setValue(mins*60)
        self.bar.setStyleSheet("QProgressBar::chunk{background: #00ff00}")
        left.addWidget(self.bar)

        self.status = self.mk_lbl("STATUS: ACTIVE", "#fff")
        left.addWidget(self.status)

        quote = QLabel(f"\"{random.choice(QUOTES)}\""); quote.setWordWrap(True)
        quote.setStyleSheet("font-style: italic; color: #666; margin-top: 20px;")
        left.addWidget(quote)
        left.addStretch()
        main_layout.addLayout(left, 1)

        # RIGHT PANEL (Charts)
        right = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane{border:0;} QTabBar::tab{background:#222; color:#888; padding:8px;}")
        
        self.fig1 = Figure(facecolor='#0d0d0d'); self.c1 = FigureCanvas(self.fig1)
        self.tabs.addTab(self.c1, "Focus")
        
        self.fig2 = Figure(facecolor='#0d0d0d'); self.c2 = FigureCanvas(self.fig2)
        self.tabs.addTab(self.c2, "Apps")
        
        right.addWidget(self.tabs)
        main_layout.addLayout(right, 2)

    def mk_lbl(self, t, c):
        l = QLabel(t); l.setStyleSheet(f"color: {c}; font-weight: bold;"); return l

    def update_ui(self, app, status, stats):
        self.time_lbl.setText(f"NOW: {datetime.now().strftime('%H:%M:%S')}")
        self.status.setText(f"APP: {app} | STATE: {status}")
        self.status.setStyleSheet(f"color: {'#ff0000' if status == 'Drifting' else '#00ff00'}")

        # Update Charts (Throttled)
        if random.random() < 0.2:
            self.fig1.clear()
            ax = self.fig1.add_subplot(111)
            vals = list(stats['pie'].values()); labels = list(stats['pie'].keys())
            if sum(vals) > 0: ax.pie(vals, labels=labels, colors=['#00ff00', '#ff0000'], autopct='%1.0f%%', textprops={'color':'w'})
            self.c1.draw()

            self.fig2.clear()
            ax2 = self.fig2.add_subplot(111)
            s_apps = sorted(stats['bar'].items(), key=lambda x: x[1], reverse=True)[:5]
            if s_apps:
                ax2.barh([x[0] for x in s_apps], [x[1] for x in s_apps], color='#00aaff')
                ax2.tick_params(colors='white')
            self.c2.draw()

    def tick(self):
        v = self.bar.value()
        if v > 0:
            self.bar.setValue(v-1)
            self.overlay.prog.setValue(v-1)
        else:
            self.timer.stop(); speak("Time is up.")

    def lock_screen(self, path):
        self.lock = LockoutWindow(path)
        self.lock.show()

class Planner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PRE-FLIGHT CHECK")
        self.resize(600, 400)
        self.setStyleSheet("background: #111; color: #eee;")
        
        l = QVBoxLayout(); w = QWidget(); w.setLayout(l); self.setCentralWidget(w)
        
        l.addWidget(QLabel("DEFINE MICRO-GOAL:"))
        self.g = QLineEdit(); l.addWidget(self.g)
        
        l.addWidget(QLabel("DURATION (MINS):"))
        self.t = QLineEdit("60"); l.addWidget(self.t)
        
        l.addWidget(QLabel("ALLOWED APPS (Comma Sep):"))
        self.a = QTextEdit("code, kitty, obsidian, anki, zathura, libreoffice, mpv, vlc"); self.a.setMaximumHeight(60); l.addWidget(self.a)
        
        b = QPushButton("ENGAGE"); b.setStyleSheet("background: green; padding: 10px; font-weight: bold;")
        b.clicked.connect(self.go); l.addWidget(b)

    def go(self):
        try:
            self.d = Dashboard(self.g.text(), int(self.t.text()), self.a.toPlainText().split(','))
            self.d.show(); self.close()
        except: pass

if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    app = QApplication(sys.argv)
    p = Planner()
    p.show()
    sys.exit(app.exec())
