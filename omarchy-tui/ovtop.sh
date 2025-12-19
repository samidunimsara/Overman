#!/bin/bash

# --- PERSISTENCE SETUP ---
DATA_DIR="$HOME/.local/share/overman"
DB_FILE="$DATA_DIR/archive_db.json"
mkdir -p "$DATA_DIR"

# Initialize DB if missing
if [ ! -f "$DB_FILE" ]; then
    echo '{"goal_sec": 0, "waste_sec": 0, "apps": {}, "total_tracked": 0}' > "$DB_FILE"
fi

# CONFIGURATION
WHITELIST="anki|sublime_text|code|obsidian|kitty|alacritty|zathura"
GOAL_TARGET_SEC=108000 # 30 Hours

# COLORS
G='\033[0;32m' # Overman/Goal
R='\033[0;31m' # Animal/Waste
Y='\033[1;33m' # Quote Highlight
B='\033[0;34m' # Archive/Blue
NC='\033[0m'

# NIETZSCHEAN QUOTES
QUOTES=(
    "Are you an animal?" "Instinct noticed." "This urge is small." "The animal seeks comfort."
    "Command yourself." "The herd is calling." "You chose instinct over will." "This is animal behavior."
    "Man is something to be overcome." "You failed this moment." "Remain animal." "Discipline was offered."
    "You are obeying impulse." "The overman would not be here." "You are choosing decay."
    "Stop lying to yourself." "This is why you are still here." "Overcome or repeat forever."
    "Close it. Now." "You are choosing weakness right now." "This is how small men waste their lives."
    "The herd welcomes you. Greatness does not." "Either overcome yourself—or stay mediocre."
    "No excuse. No escape. Work." "You came here to escape. Leave." "The Overman does not scroll."
    "Burn the weak habit. Work." "Obey your goal, not your impulse." "If you can’t command yourself, you will be commanded."
    "Become who you are—one focused minute at a time." "Your work today builds the person you will become."
)

# --- ENGINE ---
draw_spectrum() {
    local val=$1; local max=$2; local color=$3; local width=40
    local perc=$(( val * 100 / (max > 0 ? max : 1) ))
    local fill=$(( perc * width / 100 ))
    [ $fill -gt $width ] && fill=$width
    
    printf " ${color}"
    for ((i=0; i<fill; i++)); do printf "█"; done
    printf "${NC}"
    for ((i=fill; i<width; i++)); do printf "░"; done
    printf " %d%%" "$perc"
}

update_db() {
    local class=$1; local title=$2
    local is_goal=0
    [[ "$class" =~ ($WHITELIST) ]] && is_goal=1

    tmp=$(mktemp)
    if [ "$is_goal" -eq 1 ]; then
        jq --arg cls "$class" --arg tit "$title" \
        '.apps[$cls].total += 2 | .apps[$cls].windows[$tit] += 2 | .goal_sec += 2 | .total_tracked += 2' "$DB_FILE" > "$tmp"
    else
        jq --arg cls "$class" --arg tit "$title" \
        '.apps[$cls].total += 2 | .apps[$cls].windows[$tit] += 2 | .waste_sec += 2 | .total_tracked += 2' "$DB_FILE" > "$tmp"
    fi
    mv "$tmp" "$DB_FILE"
}

# --- RENDER LOOP ---
LAST_QUOTE_CHANGE=$(date +%s)
CURRENT_QUOTE="${QUOTES[$RANDOM % ${#QUOTES[@]}]}"
PREV_CLASS=""

while true; do
    ACTIVE=$(hyprctl activewindow -j)
    CLASS=$(echo "$ACTIVE" | jq -r '.class // "Idle"')
    TITLE=$(echo "$ACTIVE" | jq -r '.title // "Empty"')
    
    update_db "$CLASS" "$TITLE"

    # Notification Function: Trigger when switching to a non-whitelisted app
    if [[ "$CLASS" != "$PREV_CLASS" && ! "$CLASS" =~ ($WHITELIST) && "$CLASS" != "Idle" ]]; then
        notify-send -u critical "OVERMAN ALERT" "$CURRENT_QUOTE"
    fi
    PREV_CLASS="$CLASS"

    # Rotate Quote every 30 seconds
    NOW=$(date +%s)
    if (( NOW - LAST_QUOTE_CHANGE >= 30 )); then
        CURRENT_QUOTE="${QUOTES[$RANDOM % ${#QUOTES[@]}]}"
        LAST_QUOTE_CHANGE=$NOW
    fi

    # Read Stats
    GOAL_SEC=$(jq -r '.goal_sec' "$DB_FILE")
    WASTE_SEC=$(jq -r '.waste_sec' "$DB_FILE")
    TOTAL_SEC=$(jq -r '.total_tracked' "$DB_FILE")

    clear
    echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━ Übermensch & Self-Overcoming ━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  OVERMAN ARCHIVE | STATE: $([[ "$CLASS" =~ ($WHITELIST) ]] && echo -e "${G}CONQUERING${NC}" || echo -e "${R}ANIMALISTIC${NC}")"
    echo -e "  ACTIVE: ${B}$CLASS${NC} | $TITLE"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo -e "\n  ${B}BEHAVIORAL SPECTRUM:${NC}"
    echo -ne "  TOWARD GOAL    "; draw_spectrum "$GOAL_SEC" "$GOAL_TARGET_SEC" "$G"
    echo -e " ($((${GOAL_SEC}/3600))h / 30h)"
    
    echo -ne "  WASTED LIFE    "; draw_spectrum "$WASTE_SEC" "$TOTAL_SEC" "$R"
    echo -e " ($((${WASTE_SEC}/60))m)"

    echo -e "\n  ${G}COGNITIVE HIERARCHY:${NC}"
    jq -r '.apps | to_entries | sort_by(.value.total) | reverse | .[:5] | .[] | "\(.key)|\(.value.total)"' "$DB_FILE" | while IFS='|' read -r app sec; do
        MARK="✅"; [[ ! "$app" =~ ($WHITELIST) ]] && MARK="❌"
        echo -e "  ├── $app ($((${sec}/60))m) $MARK"
        
        jq -r --arg app "$app" '.apps[$app].windows | to_entries | sort_by(.value) | reverse | .[:2] | .[] | "\(.key)|\(.value)"' "$DB_FILE" | while IFS='|' read -r win val; do
            echo -e "  │   └── ${win:0:45} ($((${val}/60))m)"
        done
    done

    echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  LOGGED ACTIVITY: $((${TOTAL_SEC}/3600))h total tracked."
    echo -e "  ${Y}“${CURRENT_QUOTE}”${NC}"
    
    sleep 2
done
