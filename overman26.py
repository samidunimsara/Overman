import sys, os, json, time, subprocess, base64
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, 
                             QTreeWidget, QTreeWidgetItem, QFrame)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap, QBrush

# --- CONSTANTS & PERSISTENCE ---
DATA_DIR = Path.home() / ".local/share/overman"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"
TEMP_IMG = "/tmp/overman_audit.png"
BANNED = ["porn", "sex", "facebook", "instagram", "tiktok", "reddit", "shorts", "reels"]
CHALLENGES = {
    "Venerable": "respect", "Ubiquitous": "everywhere",
    "Selbstbeherrschung": "self-control", "Der Wille zur Macht": "will to power"
}

# --- STYLING ---
STYLE = """
    QWidget { background-color: #050505; color: #00ff00; font-family: 'JetBrains Mono', 'Impact'; }
    QLineEdit { border: 1px solid #00ff00; background: #111; padding: 5px; color: #00ff00; }
    QPushButton { background: #00ff00; color: #050505; border: none; font-weight: bold; padding: 10px; }
    QTreeWidget { border: 1px solid #00ff00; background: #050505; }
    QProgressBar { border: 1px solid #00ff00; background: #050505; text-align: center; }
    QProgressBar::chunk { background-color: #00ff00; }
"""

# --- DATA ENGINE ---
class Session:
    def __init__(self):
        self.goal = ""
        self.duration = 60
        self.whitelist = []
        self.logs = {} # {app: {title: seconds}}
        self.start_time = time.time()
        self.drift_seconds = 0
        self.is_active = False

    def get_focus_ratio(self):
        total = max(1, time.time() - self.start_time)
        return max(0, int(((total - self.drift_seconds) / total) * 100))

# --- WARDEN ENGINE ---
class Warden(QThread):
    audit_sig = pyqtSignal()
    tick_sig = pyqtSignal()

    def run(self):
        last_audit = time.time()
        drift_start = None
        while True:
            time.sleep(2)
            try:
                win = json.loads(subprocess.check_output(["hyprctl", "activewindow", "-j"]))
                app = win.get("class", "").lower()
                title = win.get("title", "").lower()
                
                # Kill Switch
                if any(x in app or x in title for x in BANNED):
                    subprocess.run(["hyprctl", "dispatch", "closewindow", f"class:{app}"])
                    continue

                # Logging
                if app not in session.logs: session.logs[app] = {}
                session.logs[app][title] = session.logs[app].get(title, 0) + 2

                # Drift Logic
                if app not in session.whitelist and "python" not in app:
                    session.drift_seconds += 2
                    if drift_start is None: drift_start = time.time()
                    elapsed_drift = time.time() - drift_start
                    
                    if 60 <= elapsed_drift < 62:
                        subprocess.Popen(["espeak-ng", "Samidu, return to your goal."])
                    if elapsed_drift > 300:
                        subprocess.run(["brightnessctl", "s", "10%"])
                else:
                    if drift_start: subprocess.run(["brightnessctl", "s", "100%"])
                    drift_start = None

                if time.time() - last_audit > 600:
                    self.audit_sig.emit()
                    last_audit = time.time()
                
                self.tick_sig.emit()
            except: pass

# --- UI COMPONENTS ---
class WillpowerPie(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        ratio = session.get_focus_ratio()
        p.setBrush(QBrush(QColor("#ff0000")))
        p.drawPie(QRectF(10, 10, 80, 80), 0, 16 * 360)
        p.setBrush(QBrush(QColor("#00ff00")))
        p.drawPie(QRectF(10, 10, 80, 80), 90 * 16, int(ratio * 3.6 * 16))

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COMMAND CENTER")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setProperty("class", "overman-dashboard")
        self.setStyleSheet(STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        
        # Sidebar
        side = QVBoxLayout()
        self.shame = QLabel()
        self.pie = WillpowerPie()
        self.pie.setFixedSize(100, 100)
        
        # Comparative Analytics
        self.compare = QLabel("Loading historical data...")
        
        btn_end = QPushButton("TERMINATE & REPORT")
        btn_end.clicked.connect(self.generate_report)
        
        side.addWidget(QLabel("STATUS: ACTIVE"))
        side.addWidget(self.shame)
        side.addWidget(self.pie)
        side.addWidget(self.compare)
        side.addStretch()
        side.addWidget(QLabel("'Man is a rope over an abyss'"))
        side.addWidget(btn_end)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Target", "Time"])
        
        layout.addLayout(side, 1)
        layout.addWidget(self.tree, 2)
        self.setLayout(layout)

    def refresh(self):
        ratio = session.get_focus_ratio()
        loss = (session.drift_seconds / 3600) * 2.5
        self.shame.setText(f"INTELLECT: 97%\nCONSCIENTIOUSNESS: 43%\nWILLPOWER: {ratio}%\nPOTENTIAL LOSS: -{loss:.2f}")
        
        # Load Comparison
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                hist = json.load(f)
                avg = sum(x['ratio'] for x in hist[-10:]) / len(hist[-10:]) if hist else 0
                diff = ratio - avg
                color = "#00ff00" if diff >= 0 else "#ff0000"
                self.compare.setText(f"10-DAY AVG: {avg:.1f}%\nTREND: {diff:+.1f}%")
                self.compare.setStyleSheet(f"color: {color};")

        self.tree.clear()
        for app, titles in session.logs.items():
            node = QTreeWidgetItem([app, ""])
            for t, s in titles.items(): QTreeWidgetItem(node, [t[:40], f"{s}s"])
            self.tree.addTopLevelItem(node)
        self.tree.expandAll()
        self.pie.update()

    def generate_report(self):
        # Save History
        entry = {"date": str(datetime.now()), "ratio": session.get_focus_ratio(), "goal": session.goal}
        hist = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f: hist = json.load(f)
        hist.append(entry)
        with open(HISTORY_FILE, 'w') as f: json.dump(hist, f)

        # Generate HTML
        img_b64 = ""
        if os.path.exists(TEMP_IMG):
            with open(TEMP_IMG, "rb") as f: img_b64 = base64.b64encode(f.read()).decode()

        html_path = DATA_DIR / "report.html"
        content = f"""
        <html><body style="background:#050505; color:#00ff00; font-family:monospace; padding:50px;">
        <h1 style="border-bottom:5px solid #00ff00;">SESSION CHRONICLE: {session.goal}</h1>
        <h2>WILLPOWER RATIO: {session.get_focus_ratio()}%</h2>
        <h3>ACTIVITY TREE:</h3><pre>{json.dumps(session.logs, indent=4)}</pre>
        <h3>LAST AUDIT EVIDENCE:</h3><img src="data:image/png;base64,{img_b64}" style="width:600px; border:2px solid #ff0000;">
        <p style="margin-top:50px;">"He who cannot obey himself will be commanded."</p>
        </body></html>
        """
        html_path.write_text(content)
        subprocess.run(["xdg-open", str(html_path)])
        sys.exit()

class Lockout(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(STYLE)
        subprocess.run(["grim", TEMP_IMG])
        
        l = QVBoxLayout()
        self.q = list(CHALLENGES.keys())[int(time.time()) % len(CHALLENGES)]
        
        lbl = QLabel(f"AUDIT TRIGGERED. DEFINE: '{self.q}'")
        lbl.setFont(QFont("Impact", 20))
        
        img = QLabel()
        img.setPixmap(QPixmap(TEMP_IMG).scaled(600, 400))
        
        self.ans = QLineEdit()
        self.ans.returnPressed.connect(self.verify)
        
        l.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(img, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.ans)
        self.setLayout(l)
        self.showFullScreen()

    def verify(self):
        if CHALLENGES[self.q] in self.ans.text().lower():
            self.callback(); self.close()
        else:
            subprocess.Popen(["espeak-ng", "Incorrect. Kill the worm."])

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.bar = QProgressBar(self)
        self.bar.setFixedSize(350, 20)
        self.bar.setStyleSheet(STYLE)
        self.show()

    def update_bar(self):
        rem = max(0, int(session.duration * 60 - (time.time() - session.start_time)))
        self.bar.setValue(int((rem / (session.duration * 60)) * 100))
        self.bar.setFormat(f"{session.goal} | {rem//60}m remaining")

class Architect(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        l = QVBoxLayout()
        l.addWidget(QLabel("THE ARCHITECT: DEFINE THE CONQUEST"))
        self.g = QLineEdit(placeholderText="Micro-Goal"); l.addWidget(self.g)
        self.t = QLineEdit(placeholderText="Session Mins"); l.addWidget(self.t)
        self.w = QLineEdit(placeholderText="Whitelist (kitty, firefox)"); l.addWidget(self.w)
        btn = QPushButton("ENGAGE PROTOCOL"); btn.clicked.connect(self.start)
        l.addWidget(btn)
        self.setLayout(l)

    def start(self):
        session.goal = self.g.text()
        session.duration = int(self.t.text() or 60)
        session.whitelist = [x.strip() for x in self.w.text().split(",")]
        self.close()

# --- MAIN ---
session = Session()
if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    app = QApplication(sys.argv)
    
    arch = Architect(); arch.show(); app.exec()
    
    dash = Dashboard(); dash.show()
    ov = Overlay()
    
    warden = Warden()
    warden.tick_sig.connect(dash.refresh)
    warden.tick_sig.connect(ov.update_bar)
    warden.audit_sig.connect(lambda: Lockout(lambda: None))
    warden.start()
    
    sys.exit(app.exec())
