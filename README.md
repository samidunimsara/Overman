ubermensch.py

sudo pacman -S python-pyqt6 python-pandas python-matplotlib espeak-ng grim hyprland

~/.config/hypr/hyprland.conf
```bash
# THE TRUTH ENGINE RULES
windowrulev2 = float, class:(truth-engine)
windowrulev2 = center, class:(truth-engine)
windowrulev2 = size 1100 750, class:(truth-engine)
windowrulev2 = opacity 0.95, class:(truth-engine)

# LOCKOUT & OVERLAY RULES
windowrulev2 = fullscreen, class:(truth-lockout)
windowrulev2 = stayfocused, class:(truth-lockout)
windowrulev2 = pin, class:(truth-overlay)
windowrulev2 = nofocus, class:(truth-overlay)
windowrulev2 = float, class:(truth-overlay)
windowrulev2 = move 100%-400 20, class:(truth-overlay)
```

Run hyprctl reload after saving.

--------------------------------------------------------
```
sudo pacman -S zenity jq grim bc
```


`overman_system.sh
Save this file in ~/.config/hypr/scripts/overman_system.sh and make it executable (chmod +x).`

cat ~/.local/share/overman_logs/activity.csv | awk -F, '{print $2}' | sort | uniq -c | sort -nr | head -n 10
