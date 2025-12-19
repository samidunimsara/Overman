#!/bin/bash

export WAYLAND_DISPLAY=wayland-0

# --- CONFIGURATION & CONSTANTS ---
DATA_DIR="$HOME/.local/share/overman" 
mkdir -p "$DATA_DIR"

# HARD BANNED APPS (Immediate Kill -9)
BANNED=("porn" "how to" "nano" "sh" "ai" "gemini" "chatgpt" "sex" "xhamster" "instagram" "tiktok" "reddit" "shorts" "reels" "twitter" "facebook" "gemini" "deepseek" "opsec" "x" "Teligram" "nano" "sh")

# --- MANUAL CONFIGURATION ---
SESSION_GOAL="Deep Work Protocol"
INITIAL_DURATION=60
SESSION_DURATION=$INITIAL_DURATION
WHITELIST="anki|obsidian|mpv|zathura|thorium-browser|oxfordlearnersdictionaries|english"

# --- [NEW] RANDOM AUDIT FIELDS (Pipe Separated) ---
# 1. The philosophical text displayed in the popup
AUDIT_QUOTES="You have made your way from worm to man, and much within you is still worm. Once you were apes, and even now man is more ape than any ape.|Man is a bridge and not a goal... the greatness in man is that he is a bridge and an over-going. Are you crossing the bridge right now, or are you sitting down in the dirt with the beasts?|You are a regression! You have made your way from worm to man, but much within you is still worm. Do you want to be the ebb of this great flood?|The ape is a laughing-stock to man... and even now, man is more ape than any ape. Your 'instinct' to scroll is just the chattering of a primate in a digital cage.|Your 'desire' for this site is not yours. It is the belly. It is the itch. It is the animal. Where is the Sovereign Individual?|Are you the master of your drives or a clever animal with a mouse?|What have you done today to overcome the animal within you?|Is this cheap pleasure worth the death of your potential?|You are a bridge, not a goal. Stop sitting in the dirt.|The ape is a laughing-stock to man. Are you becoming one now?|All beings so far have created something beyond themselves; and do you want to be the ebb of this great flood and even go back to the beasts rather than overcome man?|Man is a rope over an abyss.|The animal seeks comfort.|Command yourself.|The herd is calling.|Pain is weakness leaving the body.|Spirit cuts into life.|You are choosing decay.|Stop lying to yourself."

# 2. The phrase you must TYPE to unlock
AUDIT_MANTRAS="No one can build you the bridge on which you, and only you, must cross the river of life|overcome myself|kill the worm|command the beast|harness the will|stay hard|focus now|no surrender|The ape is a laughing-stock to man. Are you becoming one now?"

# Convert pipe-separated strings to arrays (Use | to allow commas in quotes)
IFS='|' read -r -a QUOTE_ARRAY <<< "$AUDIT_QUOTES"
IFS='|' read -r -a MANTRA_ARRAY <<< "$AUDIT_MANTRAS"


# --- GLOBAL VARIABLES ---
START_TIME=$(date +%s)
DRIFT_SECONDS=0
ADDED_PENALTY_MINUTES=0

# CSS Styling (Navy/Dark Minimalist - Compact)
DARK_CSS="
#yad-window { background-color: #020205; color: #aaddff; font-family: 'JetBrains Mono', 'Monospace'; }
label { color: #aaddff; font-weight: bold; font-size: 10px; }
entry { background-color: #0a0a12; color: #ffffff; border: 1px solid #334455; padding: 4px; }
button { background-color: #003366; color: #ffffff; border: none; font-weight: bold; padding: 6px; }
button:hover { background-color: #004488; }
"
CSS_FILE=$(mktemp)
echo "$DARK_CSS" > "$CSS_FILE"

# --- FUNCTIONS ---

function format_time_left() {
    local current_ts=$(date +%s)
    local elapsed=$((current_ts - START_TIME))
    local total_duration_sec=$(( (SESSION_DURATION + ADDED_PENALTY_MINUTES) * 60 ))
    local remaining=$((total_duration_sec - elapsed))
    
    if [ $remaining -le 0 ]; then
        echo "00:00:00"
    else
        printf "%02d:%02d:%02d" $((remaining/3600)) $(((remaining%3600)/60)) $((remaining%60))
    fi
}

function punish_user() {
    if [ -f "$HOME/ff/Dow8.mp4" ]; then
        mpv --no-video --volume=60 "$HOME/ff/Dow8.mp4" &
    else
        espeak-ng "Return to your goal." &
    fi
    if command -v brightnessctl &> /dev/null; then brightnessctl s 5%; fi
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

function get_random_quote() {
    echo "${QUOTE_ARRAY[$RANDOM % ${#QUOTE_ARRAY[@]}]}"
}

function get_random_mantra() {
    echo "${MANTRA_ARRAY[$RANDOM % ${#MANTRA_ARRAY[@]}]}"
}

function monitor_clients() {
    if ! command -v hyprctl &> /dev/null; then return; fi

    # 1. SCAN ALL CLIENTS
    CLIENTS_JSON=$(hyprctl clients -j)
    VIOLATION_FOUND=0
    KILLED_APP=""

    while IFS=$'\t' read -r PID CLASS TITLE I_CLASS I_TITLE; do
        FULL_META="${CLASS} ${TITLE} ${I_CLASS} ${I_TITLE}"
        FULL_META="${FULL_META,,}"

        for bad in "${BANNED[@]}"; do
            if [[ "$FULL_META" == *"$bad"* ]]; then
                kill -9 "$PID" 2>/dev/null
                notify-send "OVERMAN" "EXECUTED: $bad (+10 MIN PENALTY)"
                VIOLATION_FOUND=1
                KILLED_APP="$bad"
                ADDED_PENALTY_MINUTES=$((ADDED_PENALTY_MINUTES + 10))
            fi
        done
    done < <(echo "$CLIENTS_JSON" | jq -r '.[] | "\(.pid)\t\(.class)\t\(.title)\t\(.initialClass)\t\(.initialTitle)"')

    if [ $VIOLATION_FOUND -eq 1 ]; then
        # When caught, force a random mantra to unlock
        RAND_MANTRA=$(get_random_mantra)
        run_audit "DISTRACTION: <span color='#ff3333'>$KILLED_APP</span>" "$RAND_MANTRA" "INTERVENTION"
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
            
            # Randomize drift checks too
            RAND_QUOTE=$(get_random_quote)
            RAND_MANTRA=$(get_random_mantra)
            run_audit "$RAND_QUOTE" "$RAND_MANTRA" "DRIFT DETECTED"
        fi
    fi
}

function run_audit() {
    local prompt_text=$1
    local mantra=$2
    local title=$3
    
    while true; do
        SCORE=$(get_stats)
        TIME_LEFT=$(format_time_left)
        
        INFO_BLOCK="<span size='small' color='#888888'>GOAL:</span> <span color='#00aaff'>$SESSION_GOAL</span>\n"
        INFO_BLOCK+="<span size='small' color='#888888'>TIME LEFT:</span> <span color='#ffffff' weight='bold'>$TIME_LEFT</span>\n"
        INFO_BLOCK+="<span size='small' color='#888888'>PENALTY:</span> <span color='#ff3333'>+${ADDED_PENALTY_MINUTES}m</span>"

        USER_INPUT=$(yad --form \
            --title="$title" \
            --center --fixed \
            --width=300 \
            --undecorated \
            --no-escape \
            --css="$CSS_FILE" \
            --text="$INFO_BLOCK\n\n$prompt_text\n\nTYPE: <span color='#00aaff' weight='bold'>'$mantra'</span>" \
            --field="":ENTRY "" \
            --button="VERIFY:0")
        
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
            yad --text="<span size='large' color='red' weight='bold'>WRONG.</span>" \
                --timeout=1 --no-buttons --undecorated --center --css="$CSS_FILE" --width=200
        fi
    done
}

# --- MAIN EXECUTION ---

START_TIME=$(date +%s)
LAST_BIO_CHECK=$START_TIME

trap "rm -f $CSS_FILE; exit" SIGINT SIGTERM

notify-send "OVERMAN" "Protocol Engaged: $SESSION_GOAL"

while true; do
    CURRENT_TS=$(date +%s)
    
    monitor_clients
    
    # 10 Min Reality Check - NOW RANDOMIZED
    if (( CURRENT_TS - LAST_BIO_CHECK >= 60 )); then
        RAND_QUOTE=$(get_random_quote)
        RAND_MANTRA=$(get_random_mantra)
        run_audit "$RAND_QUOTE" "$RAND_MANTRA" "REALITY CHECK"
        LAST_BIO_CHECK=$(date +%s)
    fi

    sleep 10
done
