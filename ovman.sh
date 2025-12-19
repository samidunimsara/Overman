#!/bin/bash

# --- CONFIGURATION & CONSTANTS ---
DATA_DIR="$HOME/.local/share/overman" 
TEMP_IMG="/tmp/overman_audit.png"

mkdir -p "$DATA_DIR"

# HARD BANNED APPS (Immediate Kill)
BANNED=("porn" "sex" "anki" "instagram" "tiktok" "reddit" "shorts" "reels" "twitter")

# CSS Styling (Void Minimalist - Compact)
DARK_CSS="
#yad-window { background-color: #050505; color: #00ff00; font-family: 'JetBrains Mono', 'Monospace'; }
label { color: #00ff00; font-weight: bold; font-size: 11px; }
entry { background-color: #111111; color: #00ff00; border: 1px solid #00ff00; padding: 5px; }
button { background-color: #00ff00; color: #050505; border: none; font-weight: bold; padding: 8px; }
button:hover { background-color: #333333; color: #ffffff; border: 1px solid #ffffff; }
"
CSS_FILE=$(mktemp)
echo "$DARK_CSS" > "$CSS_FILE"

# Nietzschean Trials
TRIAL_TEXTS=(
    "Man is a rope over an abyss."
    "Your 97th percentile intellect is useless if you cannot command your finger."
    "He who cannot obey himself will be commanded."
    "Potential is just energy doing nothing. Burn yourself."
    "Spirit is the life that itself cuts into life."
    "Are you a regression? Much within you is still worm."
)

PHRASES=(
    "overcome myself"
    "command the beast"
    "harness the will"
    "not a last man"
    "cross the abyss"
    "will to power"
)

# --- GLOBAL VARIABLES ---
SESSION_GOAL=""
SESSION_DURATION=60
WHITELIST=""
START_TIME=$(date +%s)
DRIFT_SECONDS=0

# --- FUNCTIONS ---

function the_architect() {
    INPUT=$(yad --form \
        --title="THE ARCHITECT" \
        --center --width=350 --undecorated \
        --window-icon="terminal" \
        --css="$CSS_FILE" \
        --text="<span size='large' color='#00ff00'>DEFINE THE CONQUEST</span>" \
        --field="MICRO-GOAL":ENTRY \
        --field="DURATION (Mins)":NUM \
        --field="WHITELIST (comma sep)":ENTRY \
        --button="ENGAGE:0")
    
    if [ $? -ne 0 ]; then exit 0; fi

    SESSION_GOAL=$(echo "$INPUT" | cut -d'|' -f1)
    SESSION_DURATION=$(echo "$INPUT" | cut -d'|' -f2 | cut -d',' -f1) 
    WHITELIST_RAW=$(echo "$INPUT" | cut -d'|' -f3)
    WHITELIST=$(echo "$WHITELIST_RAW" | tr ',' '|')
    
    if [ -z "$WHITELIST" ]; then WHITELIST="kitty|code|obsidian|mpv|zathura"; fi
}

function punish_user() {
    if [ -f "$AUDIO_FILE" ]; then
        mpv  --no-video  --volume=50 ~/ff/Dow8.mp4  &
    else
        espeak-ng "Return to your goal." &
    fi
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

function check_active_window() {
    if ! command -v hyprctl &> /dev/null; then return; fi

    ACTIVE_JSON=$(hyprctl activewindow -j)
    CLASS=$(echo "$ACTIVE_JSON" | jq -r '.class' | tr '[:upper:]' '[:lower:]')
    TITLE=$(echo "$ACTIVE_JSON" | jq -r '.title' | tr '[:upper:]' '[:lower:]')

    # Kill Banned
    for bad in "${BANNED[@]}"; do
        if [[ "$CLASS" == *"$bad"* ]] || [[ "$TITLE" == *"$bad"* ]]; then
            ADDRESS=$(echo "$ACTIVE_JSON" | jq -r '.address')
            hyprctl dispatch closewindow "address:$ADDRESS"
            run_audit "DISTRACTION: $bad" "kill the worm" "INTERVENTION"
        fi
    done

    # Check Drift
    if [[ ! "$CLASS" =~ $WHITELIST ]] && [ -n "$CLASS" ]; then
        DRIFT_SECONDS=$((DRIFT_SECONDS + 2))
        if (( DRIFT_SECONDS % 60 == 0 )); then
             mpv  --no-video  --volume=50 ~/ff/Dow8.mp4 &
        fi
    fi
}

function run_audit() {
    local prompt_text=$1
    local mantra=$2
    local title=$3
    
    # 1. Capture & RESIZE Screenshot (Vital for UI size)
    if command -v grim &> /dev/null; then 
        grim "$TEMP_IMG"
        # Resize to 400px width so it fits in the popup
        if command -v magick &> /dev/null; then
            magick "$TEMP_IMG" -resize 400x "$TEMP_IMG"
        elif command -v convert &> /dev/null; then
            convert "$TEMP_IMG" -resize 400x "$TEMP_IMG"
        else
            # If no ImageMagick, delete image to prevent giant window
            rm -f "$TEMP_IMG"
        fi
    else 
        rm -f "$TEMP_IMG"
    fi

    # 2. The Popup Loop
    while true; do
        CUR_TIME=$(date +"%H:%M:%S")
        SCORE=$(get_stats)
        
        INFO_BLOCK="<b>GOAL:</b> $SESSION_GOAL\n"
        INFO_BLOCK+="<b>CONSCIENTIOUSNESS:</b> <span color='$( [ $SCORE -lt 50 ] && echo "#ff0000" || echo "#00ff00" )'>$SCORE%</span>"

        # --width/--height fixed to reasonable sizes
        # --image-on-top puts image above text
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
the_architect

START_TIME=$(date +%s)
LAST_AUDIT=$START_TIME
LAST_BIO_CHECK=$START_TIME

trap "rm -f $CSS_FILE $TEMP_IMG; exit" SIGINT SIGTERM

notify-send "OVERMAN" "Protocol Engaged: $SESSION_GOAL"

while true; do
    CURRENT_TS=$(date +%s)
    
    check_active_window
    
    # 5 Mins: Bio Check
    if (( CURRENT_TS - LAST_BIO_CHECK >= 300 )); then
        run_audit "Man is a rope over an abyss." "overcome yourself" "REALITY CHECK"
        LAST_BIO_CHECK=$(date +%s)
    fi

    # 10 Mins: Trial
    if (( CURRENT_TS - LAST_AUDIT >= 60 )); then
        RANDOM_TEXT=${TRIAL_TEXTS[$RANDOM % ${#TRIAL_TEXTS[@]}]}
        RANDOM_PHRASE=${PHRASES[$RANDOM % ${#PHRASES[@]}]}
        run_audit "$RANDOM_TEXT" "$RANDOM_PHRASE" "AUDIT"
        LAST_AUDIT=$(date +%s)
    fi

    sleep 2
done
