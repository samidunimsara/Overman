#!/bin/bash

# ==========================================
# CONFIGURATION
# ==========================================
# CHANGE THIS TO YOUR ONE TRUE GOAL
MY_GOAL="COMPLETE THE PROJECT ARCHITECTURE"

# Directory to store your life data
LOG_DIR="$HOME/.local/share/overman_logs"
SCREENSHOT_DIR="$LOG_DIR/screenshots"
ACTIVITY_LOG="$LOG_DIR/activity.csv"

mkdir -p "$SCREENSHOT_DIR"

# Nietzschean Data
TRIAL_TEXTS=(
    "Man is a rope, tied between beast and overman. What is great in man is that he is a bridge."
    "I teach you the overman. Man is something that shall be overcome."
    "Your 'instinct' to scroll is just the chattering of a primate in a digital cage."
    "He who cannot obey himself will be commanded."
    "The belly is the reason why man does not so easily take himself for a god."
    "Spirit is the life that itself cuts into life."
    "Are you crossing the bridge right now, or are you sitting in the dirt?"
)
PHRASES=("overcome" "will to power" "i am a bridge" "command myself" "no last man")

# ==========================================
# 1. THE SILENT OBSERVER (Background Tracking)
# ==========================================
track_activity() {
    while true; do
        # Sleep first to allow startup
        sleep 60
        
        # Get current timestamp
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        
        # Get Active Window Class & Title from Hyprland
        WINDOW_INFO=$(hyprctl activewindow -j)
        APP_CLASS=$(echo "$WINDOW_INFO" | jq -r ".class")
        APP_TITLE=$(echo "$WINDOW_INFO" | jq -r ".title")
        
        # If no window is focused, mark as Idle
        if [ "$APP_CLASS" == "null" ] || [ -z "$APP_CLASS" ]; then
            APP_CLASS="Idle/Desktop"
            APP_TITLE="-"
        fi

        # Log to CSV: Time, App, Detailed Title
        echo "$TIMESTAMP,$APP_CLASS,$APP_TITLE" >> "$ACTIVITY_LOG"
    done
}

# ==========================================
# 2. THE ANALYST (Generate Report)
# ==========================================
generate_report() {
    # 1. Take a Screenshot of your shame/glory
    SCREEN_NAME="proof_$(date +%s).png"
    grim "$SCREENSHOT_DIR/$SCREEN_NAME"

    # 2. Analyze the last 10 entries (approx 10 mins) of the log
    # We use awk to count occurrences of App names
    SUMMARY=$(tail -n 10 "$ACTIVITY_LOG" | awk -F, '{print $2}' | sort | uniq -c | sort -nr)
    
    # Format the summary for the popup
    REPORT_TEXT="CURRENT TIME: $(date '+%H:%M')\n"
    REPORT_TEXT+="--------------------------------\n"
    REPORT_TEXT+="GOAL: $MY_GOAL\n"
    REPORT_TEXT+="--------------------------------\n"
    REPORT_TEXT+="RECENT ACTIVITY (Last 10 mins):\n"
    
    # Simple loop to format the 'uniq -c' output
    while read -r count name; do
        # Calculate approximate percentage (count * 10 since we capture every minute)
        REPORT_TEXT+="  - $name: ${count}0%\n"
    done <<< "$SUMMARY"
}

# ==========================================
# 3. THE ENFORCER (Popup Logic)
# ==========================================
run_audit() {
    local quote=$1
    local mantra=$2
    
    # Generate the fresh report
    generate_report

    while true; do
        # Combine Report + Quote for the user
        FULL_DISPLAY="$REPORT_TEXT\n\n--------------------------------\nPHILOSOPHY:\n$quote\n\nTYPE: '$mantra'"

        USER_INPUT=$(zenity --entry \
            --title="EVOLUTIONARY AUDIT" \
            --text="$FULL_DISPLAY" \
            --width=600 --height=500 \
            --ok-label="I AM FOCUSED" \
            --cancel-label="I AM DISTRACTED")

        # If user hits Cancel/Close, restart loop immediately
        if [ $? -ne 0 ]; then
            continue
        fi

        # Check mantra
        if [[ "${USER_INPUT,,}" == "${mantra,,}" ]]; then
            # Show a quick success notification
            notify-send "Overman System" "Focus Recorded. Proceed."
            break
        else
            zenity --error --text="FAILURE. THE ANIMAL IS IN CONTROL." --timeout=2
        fi
    done
}

# ==========================================
# MAIN EXECUTION LOOP
# ==========================================

# Start the tracker in the background
track_activity &
TRACKER_PID=$!

# Ensure tracker dies when this script dies
trap "kill $TRACKER_PID" EXIT

# The Main Loop
while true; do
    # Wait 10 Minutes (600 seconds)
    sleep 600
    
    # Pick random challenges
    RAND_QUOTE=${TRIAL_TEXTS[$RANDOM % ${#TRIAL_TEXTS[@]}]}
    RAND_PHRASE=${PHRASES[$RANDOM % ${#PHRASES[@]}]}
    
    run_audit "$RAND_QUOTE" "$RAND_PHRASE"
done
