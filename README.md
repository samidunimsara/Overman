```
sudo pacman -S zenity jq grim bc
```


`overman_system.sh
Save this file in ~/.config/hypr/scripts/overman_system.sh and make it executable (chmod +x).`

cat ~/.local/share/overman_logs/activity.csv | awk -F, '{print $2}' | sort | uniq -c | sort -nr | head -n 10
