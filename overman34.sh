#!/bin/bash

# --- CONFIGURATION & CONSTANTS ---
DATA_DIR="$HOME/.local/share/overman"
HISTORY_FILE="$DATA_DIR/history.log"
TEMP_IMG="/tmp/overman_audit.png"

# *** SET YOUR AUDIO FILE PATH HERE ***
#AUDIO_FILE="~/ff/Dow8.mp4" 

mkdir -p "$DATA_DIR"

# Banned Apps (Hyprland window classes/titles)
BANNED=("porn" "sex" "facebook" "anki" "tiktok" "reddit" "shorts" "reels" "twitter")

# CSS Styling (Dark Minimalist / Hacker Green)
DARK_CSS="
#yad-window { background-color: #050505; color: #00ff00; font-family: 'JetBrains Mono', 'Monospace'; }
label { color: #00ff00; font-weight: bold; font-size: 14px; }
entry { background-color: #111111; color: #00ff00; border: 1px solid #00ff00; padding: 10px; }
button { background-color: #00ff00; color: #050505; border: none; font-weight: bold; padding: 10px; }
button:hover { background-color: #333333; color: #ffffff; border: 1px solid #ffffff; }
image { border: 2px solid #ff0000; }
"
CSS_FILE=$(mktemp)
echo "$DARK_CSS" > "$CSS_FILE"

# Nietzschean Trials
TRIAL_TEXTS=(
    "Man is a rope, tied between beast and overman—a rope over an abyss."
    "Your instinct to scroll is just the chattering of a primate."
    "He who cannot obey himself will be commanded."
    "The belly is the reason why man does not so easily take himself for a god."
    "Spirit is the life that itself cuts into life."
    "Are you a regression? Much within you is still worm."
    "Stop trembling! Cross the bridge or fall!"
)

PHRASES=(
    "overcome myself"
    "command the beast"
    "harness the will"
    "not a last man"
    "cross the abyss"
    "will to power"
)

# --- FUNCTIONS ---

function punish_user() {
    # 1. Play Audio (MPV)
    # --no-terminal: keeps it clean
    # & : runs in background so script doesn't freeze
    if [ -f "$AUDIO_FILE" ]; then
        mpv --no-terminal --no-audio  --volume=50 ~/ff/Dow8.mp4 &
    else
        # Fallback if you forgot to put the file there
        espeak-ng "File not found." &
    fi

    # 2. Dim Screen
    if command -v brightnessctl &> /dev/null; then
        brightnessctl s 10%
    fi
}

function restore_environment() {
    if command -v brightnessctl &> /dev/null; then
        brightnessctl s 50%
    fi
}

function check_active_window() {
    # Uses hyprctl (Wayland) to check active window
    if ! command -v hyprctl &> /dev/null; then return; fi

    ACTIVE_JSON=$(hyprctl activewindow -j)
    # Parse class and title, convert to lowercase
    CLASS=$(echo "$ACTIVE_JSON" | jq -r '.class' | tr '[:upper:]' '[:lower:]')
    TITLE=$(echo "$ACTIVE_JSON" | jq -r '.title' | tr '[:upper:]' '[:lower:]')

    for bad in "${BANNED[@]}"; do
        if [[ "$CLASS" == *"$bad"* ]] || [[ "$TITLE" == *"$bad"* ]]; then
            # Kill the window
            ADDRESS=$(echo "$ACTIVE_JSON" | jq -r '.address')
            hyprctl dispatch closewindow "address:$ADDRESS"
            
            # Log it
            echo "$(date): KILLED $CLASS - $TITLE" >> "$HISTORY_FILE"
            
            # Immediate Audit Trigger
            run_audit "DISTRACTION DETECTED: $bad" "kill the worm" "IMMEDIATE INTERVENTION"
        fi
    done
}

function run_audit() {
    local prompt_text=$1
    local mantra=$2
    local title=$3
    
    # 1. Take Screenshot of current state (Evidence)
    if command -v grim &> /dev/null; then
        grim "$TEMP_IMG"
    else
        touch "$TEMP_IMG" # Fallback to avoid error
    fi

    # 2. Loop until correct input
    while true; do
        CUR_TIME=$(date +"%H:%M:%S")
        
        # YAD Dialog
        USER_INPUT=$(yad --form \
            --title="$title" \
            --center --fixed --width=600 --height=500 \
            --undecorated \
            --window-icon="dialog-warning" \
            --css="$CSS_FILE" \
            --image="$TEMP_IMG" \
            --text="<span size='xx-large' color='#00ff00'>$CUR_TIME</span>\n\n<b>$prompt_text</b>\n\nTYPE: <span color='#888'>'$mantra'</span>" \
            --field="":ENTRY "" \
            --button="OVERCOME:0" \
            --button="SURRENDER:1")
        
        EXIT_STATUS=$?
        CLEAN_INPUT=$(echo "$USER_INPUT" | cut -d'|' -f1)

        # Handle Exit/Surrender
        if [ $EXIT_STATUS -ne 0 ]; then
            punish_user
            continue
        fi

        # Verify Input
        if [[ "${CLEAN_INPUT,,}" == "${mantra,,}" ]]; then
            restore_environment
            break
        else
            punish_user
            # Quick error popup
            yad --text="<span size='large' color='red'>INCORRECT. THE BEAST LAUGHS.</span>" \
                --timeout=2 --no-buttons --undecorated --center --css="$CSS_FILE"
        fi
    done
}

# --- MAIN LOOPS ---
START_TIME=$(date +%s)
LAST_AUDIT=$START_TIME
LAST_BIO_CHECK=$START_TIME

# Cleanup on exit
trap "rm -f $CSS_FILE $TEMP_IMG; exit" SIGINT SIGTERM

notify-send "OVERMAN" "Protocol Engaged. You are being watched."

while true; do
    CURRENT_TS=$(date +%s)

    # 1. CONSTANT MONITORING (Every 2 seconds)
    # Checks active window and kills banned apps immediately
    check_active_window
    
    # 2. BIOLOGICAL CHECK (Every 5 mins / 300s)
    if (( CURRENT_TS - LAST_BIO_CHECK >= 300 )); then
        BIO_CHECK="Are you the master of your biological drives?\nTo proceed is to admit the 'Worm' is stronger than the 'Man'."
        run_audit "$BIO_CHECK" "overcome yourself" "BIOLOGICAL REALITY CHECK"
        LAST_BIO_CHECK=$(date +%s)
    fi

    # 3. PHILOSOPHICAL TRIAL (Randomly, roughly every 10 mins)
    if (( CURRENT_TS - LAST_AUDIT >= 60 )); then
        RANDOM_TEXT=${TRIAL_TEXTS[$RANDOM % ${#TRIAL_TEXTS[@]}]}
        RANDOM_PHRASE=${PHRASES[$RANDOM % ${#PHRASES[@]}]}
        
        run_audit "$RANDOM_TEXT" "$RANDOM_PHRASE" "EVOLUTIONARY AUDIT"
        LAST_AUDIT=$(date +%s)
    fi

    sleep 2
done
