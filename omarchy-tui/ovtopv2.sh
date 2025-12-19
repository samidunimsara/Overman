#!/bin/bash

# --- PERSISTENCE SETUP ---
DATA_DIR="$HOME/.local/share/overman"
DB_FILE="$DATA_DIR/archive_db.json"
SURRENDER_LOG="$DATA_DIR/surrender.log"
mkdir -p "$DATA_DIR"

# --- MONTHLY RESET LOGIC ---
CURRENT_MONTH=$(date +%Y-%m)
if [ -f "$DATA_DIR/last_reset" ]; then
    LAST_RESET=$(cat "$DATA_DIR/last_reset")
    if [ "$LAST_RESET" != "$CURRENT_MONTH" ]; then
        cp "$DB_FILE" "$DATA_DIR/archive_$LAST_RESET.json"
        echo '{"goal_sec": 0, "waste_sec": 0, "apps": {}, "total_tracked": 0, "streak": 0}' > "$DB_FILE"
        echo "$CURRENT_MONTH" > "$DATA_DIR/last_reset"
    fi
else
    echo "$CURRENT_MONTH" > "$DATA_DIR/last_reset"
fi

# Initialize DB if missing
if [ ! -f "$DB_FILE" ]; then
    echo '{"goal_sec": 0, "waste_sec": 0, "apps": {}, "total_tracked": 0, "streak": 2}' > "$DB_FILE"
fi

# CONFIGURATION
WHITELIST="anki|sublime_text|code|obsidian|kitty|alacritty|zathura"
GOAL_TARGET_SEC=108000 # 30 Hours

# COLORS
G='\033[0;32m' # Focus Green
R='\033[0;31m' # Animal Red
B='\033[0;34m' # Structural Blue
Y='\033[1;33m' # Alert Yellow
C='\033[0;36m' # URL/Title Cyan
NC='\033[0m'

# --- ENGINE ---
HISTORY=()
draw_decay_graph() {
    echo -ne "  "
    for val in "${HISTORY[@]}"; do
        if [ "$val" -eq 1 ]; then echo -ne "${G}▴${NC}"; else echo -ne "${R}▾${NC}"; fi
    done
    echo -e "\n  ${R}ANIMAL <───────────────────────────> OVERMAN${NC}"
}

fmt_time() {
    local sec=$1
    echo "$((sec/3600))h $(((sec%3600)/60))m"
}

draw_bar() {
    local val=$1; local max=$2; local color=$3; local width=35
    local perc=$(( val * 100 / (max > 0 ? max : 1) ))
    local fill=$(( perc * width / 100 ))
    [ $fill -gt $width ] && fill=$width
    printf "${color}"
    for ((i=0; i<fill; i++)); do printf "█"; done
    printf "${NC}"
    for ((i=fill; i<width; i++)); do printf "░"; done
    printf " %d%%" "$perc"
}

# --- RENDER LOOP ---
while true; do
    ACTIVE=$(hyprctl activewindow -j)
    CLASS=$(echo "$ACTIVE" | jq -r '.class // "Idle"')
    TITLE=$(echo "$ACTIVE" | jq -r '.title // "Empty"')
    IS_FOCUS=0
    [[ "$CLASS" =~ ($WHITELIST) ]] && IS_FOCUS=1

    # Update Graph History (Last 40 intervals)
    HISTORY+=($IS_FOCUS)
    if [ ${#HISTORY[@]} -gt 40 ]; then HISTORY=("${HISTORY[@]:1}"); fi

    # Update Database
    tmp=$(mktemp)
    if [ "$IS_FOCUS" -eq 1 ]; then
        jq --arg cls "$CLASS" --arg tit "$TITLE" '.apps[$cls].total += 2 | .apps[$cls].windows[$tit] += 2 | .goal_sec += 2 | .total_tracked += 2' "$DB_FILE" > "$tmp"
    else
        jq --arg cls "$CLASS" --arg tit "$TITLE" '.apps[$cls].total += 2 | .apps[$cls].windows[$tit] += 2 | .waste_sec += 2 | .total_tracked += 2' "$DB_FILE" > "$tmp"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SURRENDER: $CLASS | $TITLE" >> "$SURRENDER_LOG"
    fi
    mv "$tmp" "$DB_FILE"

    GOAL_SEC=$(jq -r '.goal_sec' "$DB_FILE")
    WASTE_SEC=$(jq -r '.waste_sec' "$DB_FILE")
    STREAK=$(jq -r '.streak // 0' "$DB_FILE")

    clear
    echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${Y}ÜBERMENSCH // SELF-OVERCOMING TRACKER${NC}"
    echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "  STATE        : $([ $IS_FOCUS -eq 1 ] && echo -e "${G}OVERMAN (ASCENDING)${NC}" || echo -e "${R}ANIMAL (DECAYING)${NC}")"
    echo -e "  ACTIVE       : ${C}$CLASS${NC}"
    echo -e "  WINDOW       : $TITLE"

    echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ⏱ BEHAVIORAL SPECTRUM"
    echo -e "${B}──────────────────────────────────────────────────────────────${NC}"
    echo -ne "  GOAL EXECUTION   "; draw_bar "$GOAL_SEC" "$GOAL_TARGET_SEC" "$G"; echo -e " ($(fmt_time $GOAL_SEC) / 30h)"
    echo -ne "  DECADENCE INDEX  "; draw_bar "$WASTE_SEC" "$((GOAL_SEC+WASTE_SEC))" "$R"; echo -e " ($(fmt_time $WASTE_SEC) wasted)"
    echo -e ""
    draw_decay_graph

    echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  📂 COGNITIVE HIERARCHY"
    echo -e "${B}──────────────────────────────────────────────────────────────${NC}"
    jq -r '.apps | to_entries | sort_by(.value.total) | reverse | .[:3] | .[] | "\(.key)|\(.value.total)"' "$DB_FILE" | while IFS='|' read -r app sec; do
        MARK="✓"; COLOR=$G; [[ ! "$app" =~ ($WHITELIST) ]] && { MARK="✗"; COLOR=$R; }
        echo -e "  ${COLOR}${MARK} ${app}${NC} ($(fmt_time $sec))"
        jq -r --arg app "$app" '.apps[$app].windows | to_entries | sort_by(.value) | reverse | .[:2] | .[] | "\(.key)|\(.value)"' "$DB_FILE" | while IFS='|' read -r win val; do
            echo -e "  ${B}│   └──${NC} ${C}${win:0:40}...${NC} ($(fmt_time $val))"
        done
    done

    echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ⚡ ALERTS & ENFORCEMENT"
    echo -e "${B}──────────────────────────────────────────────────────────────${NC}"
    [ $IS_FOCUS -eq 0 ] && echo -e "  [!] ${R}Recommended: CLOSE $CLASS NOW${NC}"
    echo -e "  [!] ${Y}\"Man is something to be overcome.\"${NC}"

    echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  📊 DAILY SUMMARY"
    echo -e "${B}──────────────────────────────────────────────────────────────${NC}"
    echo -e "  FOCUS TIME    : $(fmt_time $GOAL_SEC)"
    echo -e "  DISTRACTIONS  : $(fmt_time $WASTE_SEC)"
    echo -e "  STREAK        : $STREAK days"
    echo -e "  VERDICT       : $([ $GOAL_SEC -gt $WASTE_SEC ] && echo -e "${G}Rising.${NC}" || echo -e "${R}You obey impulse. Reclaim control now.${NC}")"
    echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    sleep 2
done
