import sys, os, json, time, subprocess, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, 
                             QTreeWidget, QTreeWidgetItem, QFrame)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap, QPen

# --- STYLING CONSTANTS (VOID MINIMALISM) ---
BG_COLOR = "#000000"
ACCENT_COLOR = "#00FF00" # Cyber Lime
ERR_COLOR = "#FF0000"
FONT_PRIMARY = "JetBrains Mono"

QSS = f"""
    QWidget {{ background-color: {BG_COLOR}; color: {ACCENT_COLOR}; font-family: '{FONT_PRIMARY}'; border: 1px solid {ACCENT_COLOR}; }}
    QLabel {{ border: none; }}
    QLineEdit {{ background: #050505; border: 1px solid {ACCENT_COLOR}; padding: 5px; color: {ACCENT_COLOR}; }}
    QPushButton {{ background: {ACCENT_COLOR}; color: {BG_COLOR}; font-weight: bold; border: none; padding: 10px; }}
    QPushButton:hover {{ background: #00CC00; }}
    QTreeWidget {{ border: 1px solid {ACCENT_COLOR}; background: {BG_COLOR}; }}
    QProgressBar {{ border: 1px solid {ACCENT_COLOR}; background: {BG_COLOR}; text-align: center; }}
    QProgressBar::chunk {{ background-color: {ACCENT_COLOR}; }}
"""

# --- DATA STRUCTURES ---
class SessionData:
    def __init__(self):
        self.goal = ""
        self.duration_mins = 0
        self.whitelist = []
        self.email_pass = ""
        self.start_time = datetime.now()
        self.logs = {} # {app: {title: sec}}
        self.history = [] # List of (timestamp, is_focused) for the graph
        self.total_drift = 0
        self.is_locked = False
        self.last_screenshot = "/tmp/audit.png"

session = SessionData()

# --- LIGHTWEIGHT CUSTOM GRAPH WIDGET ---
class WillpowerGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(150)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        painter.setPen(QPen(QColor(ACCENT_COLOR), 1))
        
        # Draw Grid lines
        painter.setOpacity(0.1)
        for i in range(0, w, 40): painter.drawLine(i, 0, i, h)
        for i in range(0, h, 20): painter.drawLine(0, i, w, i)
        painter.setOpacity(1.0)

        if not session.history: return
        
        # Draw Willpower Flux (Line Graph)
        path_pen = QPen(QColor(ACCENT_COLOR), 2)
        painter.setPen(path_pen)
        
        step = w / max(len(session.history), 1)
        points = []
        for i, (ts, status) in enumerate(session.history):
            y = 20 if status else h - 20
            points.append(QPoint(int(i * step), int(y)))
            
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])

# --- BACKGROUND WARDEN ---
class Warden(QThread):
    update_tick = pyqtSignal()
    audit_required = pyqtSignal()

    def run(self):
        last_audit = time.time()
        while True:
            time.sleep(2)
            win = self.get_win()
            if not win: continue
            
            app = win.get("class", "unknown").lower()
            title = win.get("title", "unknown").lower()
            
            # Monitoring logic
            is_focused = app in session.whitelist or "python3" in app
            session.history.append((time.time(), is_focused))
            if len(session.history) > 100: session.history.pop(0)

            if app not in session.logs: session.logs[app] = {}
            session.logs[app][title] = session.logs[app].get(title, 0) + 2

            if not is_focused:
                session.total_drift += 2
                if session.total_drift % 60 == 0:
                    subprocess.Popen(["espeak-ng", f"Focus Samidu. {app} is not allowed."])
                if session.total_drift > 300: # 5 mins total drift
                    subprocess.run(["brightnessctl", "s", "5%"])
            else:
                subprocess.run(["brightnessctl", "s", "100%"])

            if time.time() - last_audit > 600: # 10 min audit
                self.audit_required.emit()
                last_audit = time.time()
            
            self.update_tick.emit()

    def get_win(self):
        try:
            return json.loads(subprocess.check_output(["hyprctl", "activewindow", "-j"]))
        except: return None

# --- UI COMPONENTS ---

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setProperty("class", "overman-dashboard")
        self.setStyleSheet(QSS)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        
        # Left Panel: Stats & Shame
        sidebar = QVBoxLayout()
        self.title = QLabel("OVERMAN PROTOCOL v.FINAL")
        self.title.setFont(QFont(FONT_PRIMARY, 14, QFont.Weight.Bold))
        
        self.stats = QLabel("INTELLECT: 97%\nCONSCIENTIOUSNESS: 43%\nSTATUS: MONITORING")
        self.stats.setStyleSheet(f"color: {ACCENT_COLOR}; border-top: 1px solid {ACCENT_COLOR}; padding-top: 10px;")
        
        self.quote = QLabel(f"'{time.ctime()}'\nHe who cannot obey himself\nwill be commanded.")
        self.quote.setWordWrap(True)
        self.quote.setStyleSheet("font-style: italic; opacity: 0.7;")

        self.graph = WillpowerGraph()
        
        sidebar.addWidget(self.title)
        sidebar.addWidget(self.stats)
        sidebar.addStretch()
        sidebar.addWidget(QLabel("WILLPOWER FLUX"))
        sidebar.addWidget(self.graph)
        sidebar.addWidget(self.quote)
        
        # Right Panel: Tree Audit
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["PROCESS", "TIME"])
        self.tree.setColumnWidth(0, 250)
        
        btn_exit = QPushButton("TERMINATE SESSION & REPORT")
        btn_exit.clicked.connect(self.terminate)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self.tree)
        right_panel.addWidget(btn_exit)

        layout.addLayout(sidebar, 1)
        layout.addLayout(right_panel, 2)
        self.setLayout(layout)
        self.resize(900, 500)

    def update_ui(self):
        self.graph.update()
        loss = (session.total_drift / 3600) * 1.5
        self.stats.setText(f"INTELLECT: 97%\nCONSCIENTIOUSNESS: 43%\nDRIFT: {session.total_drift}s\nPOTENTIAL LOSS: -{loss:.2f} IELTS pts")
        
        self.tree.clear()
        for app, titles in session.logs.items():
            parent = QTreeWidgetItem([app, ""])
            for t, s in titles.items():
                QTreeWidgetItem(parent, [t[:40], f"{s}s"])
            self.tree.addTopLevelItem(parent)
        self.tree.expandAll()

    def terminate(self):
        # Email logic same as previous but with formatted minimalist text
        sys.exit()

class Lockout(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(QSS)
        subprocess.run(["grim", session.last_screenshot])
        
        l = QVBoxLayout()
        img = QLabel()
        img.setPixmap(QPixmap(session.last_screenshot).scaled(500, 300))
        
        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Define 'Selbstbeherrschung' to unlock...")
        self.inp.returnPressed.connect(self.validate)
        
        l.addWidget(QLabel("AUDIT IN PROGRESS: EVIDENCE ATTACHED"))
        l.addWidget(img)
        l.addWidget(self.inp)
        self.setLayout(l)
        self.showFullScreen()

    def validate(self):
        if self.inp.text().lower() == "self-control":
            self.callback()
            self.close()
        else:
            subprocess.Popen(["espeak-ng", "Failure. Try again."])

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"background: {BG_COLOR}; border: 1px solid {ACCENT_COLOR};")
        self.bar = QProgressBar(self)
        self.bar.setGeometry(0, 0, 350, 20)
        self.show()

    def tick(self):
        elapsed = (datetime.now() - session.start_time).total_seconds()
        total = session.duration_mins * 60
        rem = max(0, int(((total - elapsed) / total) * 100)) if total > 0 else 0
        self.bar.setValue(rem)
        self.bar.setFormat(f"STAY THE COURSE: {rem}%")

# --- INITIALIZER ---
class Architect(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(QSS)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        l = QVBoxLayout()
        self.g = QLineEdit(placeholderText="Micro-Goal"); l.addWidget(self.g)
        self.t = QLineEdit(placeholderText="Duration (Mins)"); l.addWidget(self.t)
        self.w = QLineEdit(placeholderText="Whitelist (comma separated)"); l.addWidget(self.w)
        self.p = QLineEdit(placeholderText="App Password"); self.p.setEchoMode(QLineEdit.EchoMode.Password); l.addWidget(self.p)
        b = QPushButton("ENGAGE"); b.clicked.connect(self.engage); l.addWidget(b)
        self.setLayout(l)
    
    def engage(self):
        session.goal = self.g.text()
        session.duration_mins = int(self.t.text() or 1)
        session.whitelist = [x.strip() for x in self.w.text().split(",")]
        session.email_pass = self.p.text()
        self.close()

if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    app = QApplication(sys.argv)
    
    init = Architect(); init.show(); app.exec()
    
    dash = Dashboard(); dash.show()
    ov = Overlay()
    
    warden = Warden()
    warden.update_tick.connect(dash.update_ui)
    warden.update_tick.connect(ov.tick)
    warden.audit_required.connect(lambda: Lockout(lambda: None))
    warden.start()
    
    sys.exit(app.exec())
