import sys, os, json, random, subprocess, shutil, pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QProgressBar, 
                             QFrame, QPushButton, QTabWidget, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- DIRECTORIES (Volatile Session) ---
BASE_DIR = os.path.expanduser("~/.local/share/overman")
EVIDENCE_DIR = os.path.join(BASE_DIR, "session_evidence")
if os.path.exists(BASE_DIR): shutil.rmtree(BASE_DIR)
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# --- CONFIGURATION ---
BANNED_KEYWORDS = ["porn", "xxx", "sex", "facebook", "instagram", "tiktok", "reddit", "shorts", "reels"]
DRIFT_KEYWORDS = ["youtube", "twitch", "discord", "twitter"]

def speak(text):
    subprocess.Popen(["espeak-ng", "-s", "175", "-v", "en-us", text], stderr=subprocess.DEVNULL)

class WardenThread(QThread):
    """The External Prefrontal Cortex: Monitors, Kills, and Audits."""
    lockout_signal = pyqtSignal(str) # Path to screenshot
    update_signal = pyqtSignal(dict) # Data for charts

    def __init__(self, allowed_apps):
        super().__init__()
        self.allowed = [x.strip().lower() for x in allowed_apps if x.strip()]
        self.stats = {"Productive": 1, "Drifting": 0}
        self.app_log = {} # Track time per app/title

    def run(self):
        audit_timer = 0
        drift_voice_timer = 0
        while True:
            self.msleep(2000) # Check every 2 seconds
            audit_timer += 2
            
            try:
                # Query Hyprland for active window
                res = subprocess.check_output(["hyprctl", "activewindow", "-j"]).decode("utf-8")
                data = json.loads(res)
                app = data.get("class", "Idle").lower()
                title = data.get("title", "No Title").lower()

                # 1. THE IRON WARDEN (KILL PROTOCOL)
                if any(k in title for k in BANNED_KEYWORDS) or any(k in app for k in BANNED_KEYWORDS):
                    subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{data['address']}"])
                    self.trigger_lockout("IMMEDIATE VIOLATION DETECTED")
                    continue

                # 2. THE 10-MINUTE AUDIT
                if audit_timer >= 600:
                    self.trigger_lockout("10-MINUTE AUDIT")
                    audit_timer = 0

                # 3. DRIFT WARNING (Voice Alarm)
                is_allowed = any(a in app for a in self.allowed)
                status = "Productive" if is_allowed else "Drifting"
                
                if not is_allowed:
                    drift_voice_timer += 2
                    if drift_voice_timer == 60: speak(f"Focus check. You are in {app}.")
                    if drift_voice_timer > 120: speak("Return to the goal immediately.")
                else:
                    drift_voice_timer = 0

                # 4. LOGGING (RAM ONLY)
                self.stats[status] += 2
                self.app_log[f"{app}: {title[:30]}"] = self.app_log.get(f"{app}: {title[:30]}", 0) + 2
                self.update_signal.emit({"pie": self.stats, "bar": self.app_log, "current_app": app, "status": status})

            except Exception: pass

    def trigger_lockout(self, reason):
        speak(f"{reason}. Evidence captured.")
        path = os.path.join(EVIDENCE_DIR, f"audit_{datetime.now().strftime('%H%M%S')}.png")
        subprocess.run(["grim", path])
        self.lockout_signal.emit(path)

class LockoutWindow(QMainWindow):
    """The Fullscreen Prison."""
    def __init__(self, path):
        super().__init__()
        self.setProperty("class", "overman-lockout")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet("background: black; border: 10px solid #ff0000;")
        
        layout = QVBoxLayout()
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)
        
        lbl = QLabel("AUDIT: YOUR ANIMAL STATE"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Impact", 50)); lbl.setStyleSheet("color: red; margin-bottom: 20px;")
        layout.addWidget(lbl)

        img = QLabel(); img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setPixmap(QPixmap(path).scaled(1000, 700, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(img)

        self.mantra = random.choice(["i command myself", "will to power", "kill the worm", "i am a bridge"])
        prompt = QLabel(f"TYPE TO RELEASE: '{self.mantra}'")
        prompt.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(prompt, alignment=Qt.AlignmentFlag.AlignCenter)

        self.inp = QLineEdit()
        self.inp.setStyleSheet("font-size: 30px; background: #111; color: white; border: 2px solid red; padding: 10px;")
        self.inp.setFixedWidth(600)
        self.inp.returnPressed.connect(self.check)
        layout.addWidget(self.inp, alignment=Qt.AlignmentFlag.AlignCenter)
        self.inp.setFocus()

    def check(self):
        if self.inp.text().lower().strip() == self.mantra: self.close()

class Overlay(QMainWindow):
    """The Time-Blindness Clock."""
    def __init__(self, mins):
        super().__init__()
        self.setProperty("class", "overman-overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.resize(320, 50)
        self.setStyleSheet("background: rgba(0,0,0,0.9); border-right: 5px solid #00ff00;")
        
        layout = QHBoxLayout(); layout.setContentsMargins(10,0,10,0)
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)
        
        self.time_lbl = QLabel("00:00")
        self.time_lbl.setStyleSheet("color: #00ff00; font-family: Monospace; font-size: 20px; font-weight: bold;")
        layout.addWidget(self.time_lbl)
        
        self.p = QProgressBar(); self.p.setMaximum(mins*60); self.p.setValue(mins*60)
        self.p.setStyleSheet("QProgressBar{background:#222; border:0; height:10px;} QProgressBar::chunk{background:#00ff00}")
        layout.addWidget(self.p)

class Dashboard(QMainWindow):
    """The Command Center."""
    def __init__(self, goal, mins, allowed):
        super().__init__()
        self.setWindowTitle("OVERMAN DASHBOARD")
        self.setProperty("class", "overman-app")
        self.resize(1100, 800)
        self.setStyleSheet("background: #050505; color: #f0f0f0;")
        
        self.total_secs = mins * 60
        self.curr_secs = self.total_secs
        
        self.ov = Overlay(mins); self.ov.show()
        self.warden = WardenThread(allowed)
        self.warden.lockout_signal.connect(lambda p: LockoutWindow(p).show())
        self.warden.update_signal.connect(self.update_ui)
        self.warden.start()

        self.init_ui(goal)
        self.timer = QTimer(); self.timer.timeout.connect(self.tick); self.timer.start(1000)

    def init_ui(self, goal):
        cw = QWidget(); self.setCentralWidget(cw)
        layout = QHBoxLayout(cw)

        # --- LEFT: SHAME MIRROR ---
        left = QVBoxLayout()
        mirror = QFrame(); mirror.setStyleSheet("background: #111; border: 1px solid #333; padding: 20px;")
        ml = QVBoxLayout(mirror)
        ml.addWidget(self.mk_lbl("IDENTITY: SAMIDU", "#888"))
        ml.addWidget(self.mk_lbl("INTELLECT: 97th %", "#00ff00"))
        ml.addWidget(self.mk_lbl("CONSCIENTIOUSNESS: 43% (FAILURE)", "#ff0000"))
        ml.addWidget(self.mk_lbl("ORGANIZATION: 9th % (CHAOS)", "#ff0000"))
        left.addWidget(mirror)

        self.g_lbl = QLabel(f"MISSION: {goal.upper()}")
        self.g_lbl.setFont(QFont("Impact", 24)); self.g_lbl.setStyleSheet("color: #00ff00; margin-top: 25px;")
        left.addWidget(self.g_lbl)

        self.status = QLabel("STATUS: MONITORING ACTIVE")
        self.status.setFont(QFont("Monospace", 14))
        left.addWidget(self.status)
        
        self.clock_lbl = QLabel("ELAPSED: 00:00:00")
        self.clock_lbl.setFont(QFont("Monospace", 18))
        left.addWidget(self.clock_lbl)

        left.addStretch()
        layout.addLayout(left, 2)

        # --- RIGHT: VISUAL EVIDENCE ---
        right = QVBoxLayout(); tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane{border:0;} QTabBar::tab{background:#111; padding:10px; color:#aaa;} QTabBar::tab:selected{background:#222; color:white;}")
        
        self.fig1 = Figure(facecolor='#050505'); self.c1 = FigureCanvas(self.fig1)
        self.fig2 = Figure(facecolor='#050505'); self.c2 = FigureCanvas(self.fig2)
        tabs.addTab(self.c1, "WILLPOWER RATIO"); tabs.addTab(self.c2, "TIME LOG (PER URL/APP)")
        
        right.addWidget(tabs); layout.addLayout(right, 3)

    def mk_lbl(self, t, c):
        l = QLabel(t); l.setStyleSheet(f"color: {c}; font-weight: bold; font-size: 15px;"); return l

    def update_ui(self, data):
        self.status.setText(f"NOW: {data['current_app'].upper()} ({data['status'].upper()})")
        self.status.setStyleSheet(f"color: {'#ff0000' if data['status'] == 'Drifting' else '#00ff00'}")
        
        # Throttled Chart Refresh
        if random.random() < 0.2:
            self.fig1.clear(); ax1 = self.fig1.add_subplot(111)
            ax1.pie(data['pie'].values(), labels=data['pie'].keys(), autopct='%1.1f%%', colors=['#00ff00', '#ff0000'], textprops={'color':'w'})
            self.c1.draw()

            self.fig2.clear(); ax2 = self.fig2.add_subplot(111)
            # Sort app usage to show top 8
            sorted_apps = sorted(data['bar'].items(), key=lambda x: x[1], reverse=True)[:8]
            if sorted_apps:
                ax2.barh([x[0] for x in sorted_apps], [x[1] for x in sorted_apps], color='#00aaff')
                ax2.tick_params(colors='w', labelsize=8)
            self.c2.draw()

    def tick(self):
        self.curr_secs -= 1
        elapsed = self.total_secs - self.curr_secs
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.clock_lbl.setText(f"ELAPSED: {h:02}:{m:02}:{s:02}")
        
        rem_m, rem_s = self.curr_secs // 60, self.curr_secs % 60
        self.ov.time_lbl.setText(f"{rem_m:02}:{rem_s:02}")
        self.ov.p.setValue(self.curr_secs)
        
        if self.curr_secs <= 0:
            self.timer.stop(); speak("Session Complete. Analysis ends.")

class Planner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PRE-FLIGHT"); self.resize(600, 500); self.setStyleSheet("background:#111; color:#eee;")
        l = QVBoxLayout(); w = QWidget(); w.setLayout(l); self.setCentralWidget(w)
        
        l.addWidget(QLabel("DEFINE MICRO-GOAL (SPECIFIC):"))
        self.g = QLineEdit(); l.addWidget(self.g)
        l.addWidget(QLabel("DURATION (MINUTES):"))
        self.t = QLineEdit("60"); l.addWidget(self.t)
        l.addWidget(QLabel("ALLOWED APPS (Comma separated):"))
        self.a = QTextEdit("code, kitty, obsidian, zathura, mpv, libreoffice"); self.a.setMaximumHeight(100); l.addWidget(self.a)
        
        btn = QPushButton("ENGAGE OVERMAN PROTOCOL")
        btn.setStyleSheet("background:#004400; font-weight:bold; padding:15px; border:1px solid #00ff00;")
        btn.clicked.connect(self.go); l.addWidget(btn)

    def go(self):
        try:
            self.d = Dashboard(self.g.text(), int(self.t.text()), self.a.toPlainText().split(','))
            self.d.show(); self.close(); speak(f"Protocol Engaged. Focus on {self.g.text()}")
        except: pass

if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    app = QApplication(sys.argv)
    p = Planner(); p.show()
    sys.exit(app.exec())
