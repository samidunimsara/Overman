import tkinter as tk
import random
import time
import subprocess
import os

# Nietzschean Dataset
CHALLENGES = [
    {"q": "Man is a rope tied between beast and ______.", "a": "overman"},
    {"q": "The name of the most contemptible being seeking only cheap pleasure?", "a": "last man"},
    {"q": "Type: 'I command myself'", "a": "I command myself"},
    {"q": "What must you have in you to give birth to a dancing star?", "a": "chaos"},
    {"q": "He who cannot obey himself will be ______.", "a": "commanded"}
]

QUOTES = [
    "You have made your way from worm to man, and much within you is still worm.",
    "Is this mindless action worth the death of your potential?",
    "The ape is a laughing-stock to man. Are you becoming a laughing-stock?",
    "Your 'will' is currently just a biological twitch. Reclaim it."
]

def force_hyprland_focus():
    """Forces Hyprland to focus the audit window immediately."""
    try:
        subprocess.run(["hyprctl", "dispatch", "focuswindow", "title:^(EVOLUTIONARY AUDIT)$"], check=False)
    except:
        pass

def show_popup():
    root = tk.Tk()
    root.title("EVOLUTIONARY AUDIT")
    
    # Visuals
    root.configure(bg='#000000')
    root.geometry("600x400")
    root.attributes('-topmost', True)

    challenge = random.choice(CHALLENGES)
    quote = random.choice(QUOTES)

    # UI Elements
    tk.Label(root, text="[ SYSTEM HALTED BY WILL ]", fg="#ff0000", bg="black", font=("Courier", 18, "bold")).pack(pady=20)
    tk.Label(root, text=quote, fg="#aaaaaa", bg="black", wraplength=500, font=("Courier", 11, "italic")).pack(pady=10)
    tk.Label(root, text=challenge["q"], fg="#ffffff", bg="black", font=("Courier", 12)).pack(pady=20)

    entry = tk.Entry(root, font=("Courier", 14), bg="#111111", fg="white", insertbackground="white", justify='center')
    entry.pack(pady=10, ipady=5)
    entry.focus_set()

    def check_answer(event=None):
        if entry.get().strip().lower() == challenge["a"].lower():
            root.destroy()
        else:
            entry.delete(0, tk.END)
            error_label.config(text="THE BEAST REJOICES IN YOUR FAILURE. TRY AGAIN.")

    error_label = tk.Label(root, text="", fg="red", bg="black", font=("Courier", 10))
    error_label.pack()

    # Bind Enter key to the check function
    root.bind('<Return>', check_answer)
    
    # Prevent closing via Alt+F4 or 'X' button
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Force focus every 1 second to prevent you from clicking away
    def periodic_focus():
        force_hyprland_focus()
        root.after(1000, periodic_focus)
    
    periodic_focus()
    root.mainloop()

if __name__ == "__main__":
    # Initial wait before the first check
    while True:
        time.sleep(600)  # 10 Minutes
        show_popup()
