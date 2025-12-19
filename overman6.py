import sys, os, json, random, subprocess, shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QProgressBar, 
                             QFrame, QPushButton, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- DIRECTORIES ---
BASE_DIR = os.path.expanduser("~/.local/share/overman")
EVIDENCE_DIR = os.path.join(BASE_DIR, "session_evidence")
if os.path.exists(BASE_DIR): shutil.rmtree(BASE_DIR)
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# --- CONFIG ---
FORBIDDEN = ["porn", "xxx", "sex", "facebook", "instagram", "tiktok", "reddit", "shorts", "reels"]

def speak(text):
    subprocess.Popen(["espeak-ng", "-s", "175", "-v", "en-us", text], stderr=subprocess.DEVNULL)

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0: return f"{h}h {m}m"
    return f"{m}m {s}s"

class WardenThread(QThread):
    lockout_signal = pyqtSignal(str)
    # Emits hierarchical data and summary stats
    data_signal = pyqtSignal(dict, dict) 

    def __init__(self, allowed_list):
        super().__init__()
        self.allowed = [x.strip().lower() for x in allowed_list if x.strip()]
        self.stats = {"Productive": 1, "Drifting": 0}
        # Hierarchy: { app_class: { "total": secs, "subs": { title: secs } } }
        self.hierarchy = {}
        self.total_tracked_secs = 0

    def run(self):
        audit_timer = 0
        drift_voice_timer = 0
        while True:
            self.msleep(2000)
            audit_timer += 2
            try:
                # 1. HYPRLAND POLL
                res = subprocess.check_output(["hyprctl", "activewindow", "-j"]).decode("utf-8")
                data = json.loads(res)
                app = data.get("class", "Idle")
                title = data.get("title", "No Active Window")
                
                # Normalize names for grouping
                app_key = app if app else "Idle"
                title_key = title if title else "Default"

                # 2. BANNED CHECK
                if any(k in title.lower() for k in FORBIDDEN):
                    subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{data['address']}"])
                    self.trigger_lockout("IMMEDIATE VIOLATION")
                    continue

                # 3. 10-MIN AUDIT
                if audit_timer >= 600:
                    self.trigger_lockout("10-MINUTE AUDIT")
                    audit_timer = 0

                # 4. HIERARCHY LOGGING
                self.total_tracked_secs += 2
                if app_key not in self.hierarchy:
                    self.hierarchy[app_key] = {"total": 0, "subs": {}}
                
                self.hierarchy[app_key]["total"] += 2
                self.hierarchy[app_key]["subs"][title_key] = self.hierarchy[app_key]["subs"].get(title_key, 0) + 2

                # 5. WILLPOWER LOGGING
                is_ok = any(a in app_key.lower() for a in self.allowed)
                status = "Productive" if is_ok else "Drifting"
                self.stats[status] += 2
                
                if not is_ok:
                    drift_voice_timer += 2
                    if drift_voice_timer == 60: speak(f"Focus check. You are in {app_key}.")
                else: drift_voice_timer = 0

                self.data_signal.emit(self.hierarchy, self.stats)

            except Exception: pass

    def trigger_lockout(self, reason):
        speak(f"{reason}. Evidence captured.")
        path = os.path.join(EVIDENCE_DIR, f"audit_{datetime.now().strftime('%H%M%S')}.png")
        subprocess.run(["grim", path])
        self.lockout_signal.emit(path)

class LockoutWindow(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.setProperty("class", "overman-lockout")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet("background: black; border: 5px solid red;")
        
        l = QVBoxLayout(); w = QWidget(); w.setLayout(l); self.setCentralWidget(w)
        lbl = QLabel("AUDIT: THE ANIMAL IS LOOSE"); lbl.setFont(QFont("Impact", 45)); lbl.setStyleSheet("color: red")
        l.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        img = QLabel(); img.setPixmap(QPixmap(path).scaled(900, 600, Qt.AspectRatioMode.KeepAspectRatio))
        l.addWidget(img, alignment=Qt.AlignmentFlag.AlignCenter)

        self.mantra = random.choice(["i command myself", "will to power", "kill the worm", "bridge to overman"])
        prompt = QLabel(f"TYPE TO RELEASE: '{self.mantra}'")
        prompt.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        l.addWidget(prompt, alignment=Qt.AlignmentFlag.AlignCenter)

        self.inp = QLineEdit()
        self.inp.setStyleSheet("font-size: 26px; background: #222; color: white; border: 1px solid red; padding: 10px;")
        self.inp.setFixedWidth(500); self.inp.returnPressed.connect(self.check); l.addWidget(self.inp, alignment=Qt.AlignmentFlag.AlignCenter)
        self.inp.setFocus()

    def check(self):
        if self.inp.text().lower().strip() == self.mantra: self.close()

class Overlay(QMainWindow):
    def __init__(self, mins):
        super().__init__()
        self.setProperty("class", "overman-overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.resize(320, 50); self.setStyleSheet("background: rgba(0,0,0,0.9); border-right: 4px solid #00ff00;")
        
        layout = QHBoxLayout(); w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)
        self.lbl = QLabel("00:00"); self.lbl.setStyleSheet("color:#00ff00; font-family:Monospace; font-size:18px; font-weight:bold;")
        self.p = QProgressBar(); self.p.setMaximum(mins*60); self.p.setValue(mins*60)
        self.p.setStyleSheet("QProgressBar{background:#222; border:0; height:8px;} QProgressBar::chunk{background:#00ff00}")
        layout.addWidget(self.lbl); layout.addWidget(self.p)

class Dashboard(QMainWindow):
    def __init__(self, goal, mins, allowed):
        super().__init__()
        self.setWindowTitle("OVERMAN DASHBOARD")
        self.setProperty("class", "overman-app"); self.resize(1200, 900)
        self.setStyleSheet("background: #050505; color: #f0f0f0;")
        
        self.total_secs = mins * 60
        self.curr_secs = self.total_secs
        
        self.ov = Overlay(mins); self.ov.show()
        self.warden = WardenThread(allowed)
        self.warden.lockout_signal.connect(lambda p: LockoutWindow(p).show())
        self.warden.data_signal.connect(self.update_ui)
        self.warden.start()

        self.init_ui(goal)
        self.timer = QTimer(); self.timer.timeout.connect(self.tick); self.timer.start(1000)

    def init_ui(self, goal):
        cw = QWidget(); self.setCentralWidget(cw)
        layout = QHBoxLayout(cw)

        # --- LEFT: IDENTITY & GOALS ---
        left = QVBoxLayout()
        mirror = QFrame(); mirror.setStyleSheet("background:#111; border:1px solid #333; padding:15px;")
        ml = QVBoxLayout(mirror)
        ml.addWidget(self.mk_lbl("INTELLECT: 97th %", "#00ff00"))
        ml.addWidget(self.mk_lbl("CONSCIENTIOUSNESS: 43% (FAILURE)", "#ff0000"))
        left.addWidget(mirror)

        self.g_lbl = QLabel(f"MISSION: {goal.upper()}")
        self.g_lbl.setFont(QFont("Impact", 22)); self.g_lbl.setStyleSheet("color:#00ff00; margin-top:20px;")
        self.g_lbl.setWordWrap(True); left.addWidget(self.g_lbl)

        self.clock = QLabel("ELAPSED: 00:00:00"); self.clock.setFont(QFont("Monospace", 18))
        left.addWidget(self.clock)

        self.status = QLabel("STATUS: MONITORING ACTIVE"); self.status.setStyleSheet("color:#888;")
        left.addWidget(self.status)

        left.addStretch(); layout.addLayout(left, 1)

        # --- RIGHT: THE ANALYTICS TREE & CHART ---
        right = QVBoxLayout()
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane{border:0;} QTabBar::tab{background:#111; padding:12px; color:#aaa;} QTabBar::tab:selected{background:#222; color:white;}")
        
        # 1. HIERARCHY TREE
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Activity Name", "Duration"])
        self.tree.setStyleSheet("QTreeWidget{background:#0a0a0a; color:#eee; border:1px solid #333;} QHeaderView::section{background:#222; color:white;}")
        self.tree.setColumnWidth(0, 450)
        tabs.addTab(self.tree, "DEEP ANALYTICS")

        # 2. WILLPOWER PIE
        self.fig = Figure(facecolor='#050505'); self.canvas = FigureCanvas(self.fig)
        tabs.addTab(self.canvas, "WILLPOWER DISTRIBUTION")

        right.addWidget(tabs); layout.addLayout(right, 2)

    def mk_lbl(self, t, c):
        l = QLabel(t); l.setStyleSheet(f"color: {c}; font-weight: bold; font-size: 14px;"); return l

    def update_ui(self, hierarchy, stats):
        # Update Status
        self.status.setText(f"TRACKING: {sum(stats.values())}s TOTAL")

        # Update Tree
        self.tree.clear()
        total_time_str = format_time(sum(stats.values()))
        root = QTreeWidgetItem(self.tree, [f"Today History", total_time_str])
        root.setExpanded(True)
        
        for app, data in sorted(hierarchy.items(), key=lambda x: x[1]['total'], reverse=True):
            app_item = QTreeWidgetItem(root, [f"├── {app}", format_time(data['total'])])
            for sub, sub_time in sorted(data['subs'].items(), key=lambda x: x[1], reverse=True):
                QTreeWidgetItem(app_item, [f"    └── {sub[:50]}...", format_time(sub_time)])

        # Update Pie Chart (Throttled)
        if random.random() < 0.2:
            self.fig.clear(); ax = self.fig.add_subplot(111)
            ax.pie(stats.values(), labels=stats.keys(), autopct='%1.1f%%', colors=['#00ff00', '#ff0000'], textprops={'color':'w'})
            ax.set_title("FOCUS VS DRIFT", color='w')
            self.canvas.draw()

    def tick(self):
        self.curr_secs -= 1
        elapsed = self.total_secs - self.curr_secs
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.clock.setText(f"ELAPSED: {h:02}:{m:02}:{s:02}")
        
        rem_m, rem_s = self.curr_secs // 60, self.curr_secs % 60
        self.ov.lbl.setText(f"{rem_m:02}:{rem_s:02}")
        self.ov.p.setValue(self.curr_secs)
        
        if self.curr_secs <= 0:
            self.timer.stop(); speak("Session Complete. Analysis ends.")

class Planner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PRE-FLIGHT"); self.resize(600, 500); self.setStyleSheet("background:#111; color:#eee;")
        l = QVBoxLayout(); w = QWidget(); w.setLayout(l); self.setCentralWidget(w)
        
        l.addWidget(QLabel("MICRO-GOAL (e.g. Write Essay Paragraph 1):"))
        self.g = QLineEdit(); l.addWidget(self.g)
        l.addWidget(QLabel("DURATION (MINUTES):"))
        self.t = QLineEdit("60"); l.addWidget(self.t)
        l.addWidget(QLabel("ALLOWED APPS (Comma separated):"))
        self.a = QTextEdit("code, kitty, obsidian, zathura, libreoffice, anki"); self.a.setMaximumHeight(100); l.addWidget(self.a)
        
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
