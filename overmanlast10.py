import sys
import os
import json
import time
import subprocess
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, 
                             QTreeWidget, QTreeWidgetItem, QFrame)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap

# --- CONFIGURATION & DATA ASSETS ---
NIETZSCHE_QUOTES = [
    "He who cannot obey himself will be commanded.",
    "Your intellect is a tool for a master, not a toy for an animal.",
    "Man is a rope tied between beast and Overman."
]

CHALLENGES = {
    "Venerable": "Deserving high respect",
    "Ubiquitous": "Present everywhere",
    "Selbstbeherrschung": "Self-control",
    "Der Wille zur Macht": "The will to power"
}

BANNED_KEYWORDS = ["porn", "xxx", "sex", "facebook", "instagram", "tiktok", "reddit", "shorts", "reels"]

# --- GLOBAL SESSION DATA (RAM ONLY) ---
class SessionData:
    def __init__(self):
        self.goal = ""
        self.duration_mins = 0
        self.whitelist = []
        self.email_pass = ""
        self.start_time = datetime.now()
        self.logs = {} # {app_class: {title: duration}}
        self.total_drift_seconds = 0
        self.last_screenshot_path = "/tmp/overman_audit.png"
        self.is_locked = False

session = SessionData()

# --- UTILITIES ---
def get_active_window():
    try:
        output = subprocess.check_output(["hyprctl", "activewindow", "-j"])
        return json.loads(output)
    except:
        return None

def speak(text):
    subprocess.Popen(["espeak-ng", f"'{text}'"])

# --- WARDEN THREAD (BACKGROUND ENFORCEMENT) ---
class WardenThread(QThread):
    audit_trigger = pyqtSignal()
    update_signal = pyqtSignal()

    def run(self):
        last_audit = time.time()
        drift_start = None
        
        while True:
            time.sleep(2)
            now = time.time()
            win = get_active_window()
            
            if not win or "class" not in win: continue
            
            app_class = win["class"].lower()
            title = win["title"].lower()

            # 1. Kill Switch
            if any(k in title or k in app_class for k in BANNED_KEYWORDS):
                subprocess.run(["hyprctl", "dispatch", "closewindow", f"class:{app_class}"])
                continue

            # 2. Log Tracking
            if app_class not in session.logs: session.logs[app_class] = {}
            session.logs[app_class][title] = session.logs[app_class].get(title, 0) + 2

            # 3. Drift Sentinel
            if app_class not in session.whitelist and app_class != "python3":
                if drift_start is None: drift_start = now
                drift_duration = now - drift_start
                session.total_drift_seconds += 2
                
                if 60 <= drift_duration < 62:
                    speak(f"Samidu, focus check. You are in {app_class}")
                elif drift_duration >= 300:
                    subprocess.run(["brightnessctl", "s", "10%"])
            else:
                if drift_start is not None:
                    subprocess.run(["brightnessctl", "s", "100%"])
                    drift_start = None

            # 4. Audit Trigger (10 Mins)
            if now - last_audit >= 600:
                self.audit_trigger.emit()
                last_audit = now
            
            self.update_signal.emit()

# --- GUI COMPONENTS ---

class LockoutWindow(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setProperty("class", "overman-lockout")
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #050505; color: #00ff00; font-family: 'JetBrains Mono';")
        layout = QVBoxLayout()
        
        # Evidence
        subprocess.run(["grim", session.last_screenshot_path])
        img_label = QLabel()
        pixmap = QPixmap(session.last_screenshot_path)
        img_label.setPixmap(pixmap.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio))
        
        self.q_key = list(CHALLENGES.keys())[int(time.time()) % len(CHALLENGES)]
        self.ans = CHALLENGES[self.q_key]
        
        label = QLabel(f"EVIDENCE COLLECTED. ACTIVE RECALL REQUIRED:\nDefine: '{self.q_key}'")
        label.setFont(QFont("JetBrains Mono", 18, QFont.Weight.Bold))
        
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.check_ans)
        
        layout.addWidget(img_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.input)
        self.setLayout(layout)
        self.showFullScreen()

    def check_ans(self):
        if self.input.text().lower().strip() == self.ans.lower().strip():
            self.close()
            self.callback()
        else:
            speak("Incorrect.")
            self.input.clear()

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setProperty("class", "overman-overlay")
        self.layout = QVBoxLayout()
        self.bar = QProgressBar()
        self.bar.setStyleSheet("QProgressBar { border: 1px solid #00ff00; background: #050505; } QProgressBar::chunk { background-color: #00ff00; }")
        self.bar.setTextVisible(True)
        self.layout.addWidget(self.bar)
        self.setLayout(self.layout)
        self.show()

    def update_bar(self):
        elapsed = (datetime.now() - session.start_time).total_seconds()
        total = session.duration_mins * 60
        val = int((1 - (elapsed / total)) * 100) if total > 0 else 0
        self.bar.setValue(val)
        self.bar.setFormat(f"{datetime.now().strftime('%H:%M:%S')} | {val}%")

class Architect(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THE ARCHITECT")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #050505; color: #00ff00;")
        layout = QVBoxLayout()
        
        self.goal = QLineEdit(placeholderText="Micro-Goal (e.g. Essay Body 1)")
        self.time = QLineEdit(placeholderText="Duration (Minutes)")
        self.white = QLineEdit(placeholderText="Whitelist (comma separated: kitty,code)")
        self.mail = QLineEdit(placeholderText="Gmail App Password")
        self.mail.setEchoMode(QLineEdit.EchoMode.Password)
        
        btn = QPushButton("INITIALIZE PROTOCOL")
        btn.clicked.connect(self.start)
        
        for w in [self.goal, self.time, self.white, self.mail, btn]: layout.addWidget(w)
        self.setLayout(layout)

    def start(self):
        session.goal = self.goal.text()
        session.duration_mins = int(self.time.text() or 0)
        session.whitelist = [x.strip() for x in self.white.text().split(",")]
        session.email_pass = self.mail.text()
        self.close()

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setProperty("class", "overman-dashboard")
        self.setStyleSheet("background-color: #050505; color: #00ff00; font-family: 'JetBrains Mono';")
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Sidebar
        sidebar = QVBoxLayout()
        self.shame = QLabel()
        sidebar.addWidget(self.shame)
        
        self.quote = QLabel(NIETZSCHE_QUOTES[0])
        self.quote.setWordWrap(True)
        sidebar.addWidget(self.quote)

        report_btn = QPushButton("END & REPORT")
        report_btn.clicked.connect(self.send_report)
        sidebar.addWidget(report_btn)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Activity", "Time"])
        self.tree.setStyleSheet("QTreeWidget { background: #050505; border: 1px solid #00ff00; }")

        main_layout.addLayout(sidebar, 1)
        main_layout.addWidget(self.tree, 2)
        self.setLayout(main_layout)

    def update_stats(self):
        loss = (session.total_drift_seconds / 3600) * 0.5 # Arbitrary "Potential Loss"
        self.shame.setText(f"INTELLECT: 97th %\nCONSCIENTIOUSNESS: 43% (FAILURE)\nIELTS POTENTIAL LOSS: -{loss:.2f}")
        
        self.tree.clear()
        for app, titles in session.logs.items():
            parent = QTreeWidgetItem([app, ""])
            total_app_time = 0
            for title, sec in titles.items():
                QTreeWidgetItem(parent, [title[:30], f"{sec}s"])
                total_app_time += sec
            parent.setText(1, f"{total_app_time}s")
            self.tree.addTopLevelItem(parent)

    def send_report(self):
        try:
            msg = MIMEMultipart()
            msg['From'] = "overman.protocol@arch.omarchy"
            msg['To'] = "schattenbyte0x.de@gmail.com"
            msg['Subject'] = f"SESSION REPORT: {session.goal}"
            
            body = f"Goal: {session.goal}\nFocus Ratio: {((session.duration_mins*60 - session.total_drift_seconds)/(session.duration_mins*60))*100:.2f}%\n\nLogs:\n{json.dumps(session.logs, indent=2)}"
            msg.attach(MIMEText(body, 'plain'))
            
            with open(session.last_screenshot_path, 'rb') as f:
                img = MIMEImage(f.read())
                msg.attach(img)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login("schattenbyte0x.de@gmail.com", session.email_pass)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Failed to send email: {e}")
        
        os.system("rm /tmp/overman_audit.png")
        sys.exit()

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    app = QApplication(sys.argv)
    
    # 1. Start Architect
    arch = Architect()
    arch.show()
    app.exec() # Wait for initialization
    
    # 2. Setup Components
    dash = Dashboard()
    overlay = Overlay()
    
    def trigger_audit():
        session.is_locked = True
        dash.audit_win = LockoutWindow(lambda: setattr(session, 'is_locked', False))
    
    warden = WardenThread()
    warden.audit_trigger.connect(trigger_audit)
    warden.update_signal.connect(dash.update_stats)
    warden.update_signal.connect(overlay.update_bar)
    warden.start()
    
    dash.show()
    sys.exit(app.exec())
