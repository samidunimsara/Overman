#!/bin/bash

export WAYLAND_DISPLAY=wayland-0

# --- CONFIGURATION & CONSTANTS ---
DATA_DIR="$HOME/.local/share/overman" 
TEMP_IMG="/tmp/overman_audit.png"

mkdir -p "$DATA_DIR"

# HARD BANNED APPS (Immediate Kill -9)
# Add keywords here. It checks Window Title, Class, and InitialClass.
BANNED=("porn" "chatgpt" "sex" "gemini" "instagram" "tiktok" "reddit" "shorts" "reels" "twitter" "facebook" "ycombinator")

# --- MANUAL CONFIGURATION (EDIT THESE) ---
SESSION_GOAL="Deep Work Protocol"
SESSION_DURATION=60
# Whitelist apps (Regex format: app1|app2|app3). Case insensitive.
WHITELIST="kitty|anki|obsidian|mpv|zathura|sublime_text|alacritty|thorium-browser"

# --- GLOBAL VARIABLES ---
START_TIME=$(date +%s)
DRIFT_SECONDS=0

# CSS Styling (Void Minimalist - Compact)
DARK_CSS="
#yad-window { background-color: #050505; color: #00ff00; font-family: 'JetBrains Mono', 'Monospace'; }
label { color: #00ff00; font-weight: bold; font-size: 11px; }
entry { background-color: #111111; color: #00ff00; border: 1px solid #00ff00; padding: 5px; }
button { background-color: #00ff00; color: #050505; border: none; font-weight: bold; padding: 8px; }
button:hover { background-color: #333333; color: #0d1117; border: 1px solid #30363d; }
"
CSS_FILE=$(mktemp)
echo "$DARK_CSS" > "$CSS_FILE"

# --- FUNCTIONS ---

function punish_user() {
    # Voice / Audio Punishment
    if [ -f "$HOME/ff/Dow8.mp4" ]; then
        mpv --no-video --volume=60 "$HOME/ff/Dow8.mp4" &
    else
        espeak-ng "Return to your goal." &
    fi
    # Dim Screen
    if command -v brightnessctl &> /dev/null; then brightnessctl s 10%; fi
}

function restore_environment() {
    if command -v brightnessctl &> /dev/null; then brightnessctl s 100%; fi
}

function get_stats() {
    local elapsed=$(( $(date +%s) - START_TIME ))
    local total_time=$(( elapsed > 0 ? elapsed : 1 ))
    local focus_ratio=$(( 100 - (DRIFT_SECONDS * 100 / total_time) ))
    if [ $focus_ratio -lt 0 ]; then focus_ratio=0; fi
    echo "$focus_ratio"
}

function monitor_clients() {
    if ! command -v hyprctl &> /dev/null; then return; fi

    # 1. SCAN ALL CLIENTS (Background & Foreground)
    CLIENTS_JSON=$(hyprctl clients -j)
    
    VIOLATION_FOUND=0
    KILLED_APP=""

    while IFS=$'\t' read -r PID CLASS TITLE I_CLASS I_TITLE; do
        FULL_META="${CLASS} ${TITLE} ${I_CLASS} ${I_TITLE}"
        FULL_META="${FULL_META,,}"

        for bad in "${BANNED[@]}"; do
            if [[ "$FULL_META" == *"$bad"* ]]; then
                kill -9 "$PID" 2>/dev/null
                notify-send "OVERMAN" "EXECUTED: $bad (PID: $PID)"
                VIOLATION_FOUND=1
                KILLED_APP="$bad"
            fi
        done
    done < <(echo "$CLIENTS_JSON" | jq -r '.[] | "\(.pid)\t\(.class)\t\(.title)\t\(.initialClass)\t\(.initialTitle)"')

    if [ $VIOLATION_FOUND -eq 1 ]; then
        run_audit "DISTRACTION DETECTED: $KILLED_APP" "kill the worm" "INTERVENTION"
        return
    fi

    # 2. CHECK ACTIVE WINDOW (Drift)
    ACTIVE_JSON=$(hyprctl activewindow -j)
    A_CLASS=$(echo "$ACTIVE_JSON" | jq -r '.class // empty')
    A_TITLE=$(echo "$ACTIVE_JSON" | jq -r '.title // empty')
    
    if [ -n "$A_CLASS" ]; then
        A_META="${A_CLASS} ${A_TITLE}"
        if ! echo "$A_META" | grep -iEq "$WHITELIST"; then
            DRIFT_SECONDS=$((DRIFT_SECONDS + 10))
            punish_user
            run_audit "FOCUS LOST" "command the beast" "DRIFT DETECTED"
        fi
    fi
}

function run_audit() {
    local prompt_text=$1
    local mantra=$2
    local title=$3
    
    if command -v grim &> /dev/null; then 
        grim "$TEMP_IMG"
        if command -v magick &> /dev/null; then
            magick "$TEMP_IMG" -resize 400x "$TEMP_IMG"
        elif command -v convert &> /dev/null; then
            convert "$TEMP_IMG" -resize 400x "$TEMP_IMG"
        else
            rm -f "$TEMP_IMG"
        fi
    else 
        rm -f "$TEMP_IMG"
    fi

    while true; do
        CUR_TIME=$(date +"%H:%M:%S")
        SCORE=$(get_stats)
        
        INFO_BLOCK="<b>GOAL:</b> $SESSION_GOAL\n"
        INFO_BLOCK+="<b>CONSCIENTIOUSNESS:</b> <span color='$( [ $SCORE -lt 50 ] && echo "#ff0000" || echo "#00ff00" )'>$SCORE%</span>"

        USER_INPUT=$(yad --form \
            --title="$title" \
            --center --fixed \
            --width=450 --height=400 \
            --undecorated \
            --css="$CSS_FILE" \
            --image="$TEMP_IMG" --image-on-top \
            --text="<span size='xx-large' color='#00ff00'>$CUR_TIME</span>\n\n$INFO_BLOCK\n\n<b>$prompt_text</b>\n\nTYPE: <span color='#000080'>'$mantra'</span>" \
            --field="":ENTRY "" \
            --button="OVERCOME:0" \
            --button="SURRENDER:1")
        
        if [ $? -ne 0 ]; then
            punish_user
            continue
        fi

        CLEAN_INPUT=$(echo "$USER_INPUT" | cut -d'|' -f1)

        if [[ "${CLEAN_INPUT,,}" == "${mantra,,}" ]]; then
            restore_environment
            break
        else
            punish_user
            yad --text="<span size='large' color='red'>INCORRECT.</span>" \
                --timeout=1 --no-buttons --undecorated --center --css="$CSS_FILE"
        fi
    done
}

# --- MAIN EXECUTION ---

START_TIME=$(date +%s)
LAST_BIO_CHECK=$START_TIME

trap "rm -f $CSS_FILE $TEMP_IMG; exit" SIGINT SIGTERM

notify-send "OVERMAN" "Protocol Engaged: $SESSION_GOAL"

while true; do
    CURRENT_TS=$(date +%s)
    
    monitor_clients
    
    if (( CURRENT_TS - LAST_BIO_CHECK >= 600 )); then
        run_audit "Man is a rope over an abyss." "overcome yourself" "REALITY CHECK"
        LAST_BIO_CHECK=$(date +%s)
    fi

    sleep 10
done
