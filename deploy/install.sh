#!/bin/bash
# Run ON THE PI:  bash ~/gmr/deploy/install.sh
# - installs the server as a systemd service (gmr.service, port 8000)
# - downloads the Fredoka font + installs emoji font
# - sets Chromium to start full-screen at boot, adapting to what the Pi runs:
#     labwc / wayfire / X11 desktop  -> session autostart entry
#     no desktop (Pi OS Lite)         -> cage + chromium as a systemd service on tty1
set -euo pipefail
ME=$(whoami); HOME_DIR=$HOME; UID_=$(id -u)
D="$HOME_DIR/gmr"; DEP="$D/deploy"
say(){ printf '\n\033[1;36m== %s\033[0m\n' "$*"; }

say "System"
. /etc/os-release; echo "$PRETTY_NAME  $(uname -m)  mem: $(free -m | awk '/Mem/{print $2}') MB"
python3 --version

say "Packages"
PK=(curl fonts-noto-color-emoji)
if command -v chromium >/dev/null || command -v chromium-browser >/dev/null; then :; else
  if apt-cache show chromium >/dev/null 2>&1; then PK+=(chromium); else PK+=(chromium-browser); fi
fi
# detect desktop stack
MODE=""
if pgrep -x labwc >/dev/null; then MODE=labwc
elif pgrep -x wayfire >/dev/null; then MODE=wayfire
elif pgrep -x Xorg >/dev/null || pgrep -x X >/dev/null; then MODE=x11
elif [ -f /etc/lightdm/lightdm.conf ]; then
  S=$(grep -E '^(user-session|autologin-session)=' /etc/lightdm/lightdm.conf | tail -1)
  case "$S" in *labwc*) MODE=labwc;; *wayfire*) MODE=wayfire;; *) MODE=x11;; esac
fi
[ -z "$MODE" ] && { MODE=cage; PK+=(cage seatd); }
echo "kiosk mode: $MODE"
sudo apt-get install -y --no-install-recommends "${PK[@]}"

say "Fredoka font"
mkdir -p "$D/app/static/fonts"
if [ ! -s "$D/app/static/fonts/Fredoka.woff2" ]; then
  CSS=$(curl -fsSL -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36" \
        "https://fonts.googleapis.com/css2?family=Fredoka:wght@400..700&display=swap" || true)
  U=$(echo "$CSS" | grep -oE 'https://[^)]+\.woff2' | head -1)
  if [ -n "$U" ]; then curl -fsSL "$U" -o "$D/app/static/fonts/Fredoka.woff2" && echo "downloaded $U"; else echo "font download skipped (offline?) - system font fallback"; fi
fi

say "Server service (gmr.service)"
sed -e "s|__USER__|$ME|g" -e "s|__HOME__|$HOME_DIR|g" -e "s|__UID__|$UID_|g" "$DEP/gmr.service" | sudo tee /etc/systemd/system/gmr.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now gmr.service
sudo systemctl restart gmr.service
sleep 1
curl -fsS http://127.0.0.1:8000/health && echo "  <- server OK"

say "Kiosk autostart ($MODE)"
chmod +x "$DEP/kiosk.sh"
LINE="$DEP/kiosk.sh"
case "$MODE" in
  labwc)
    mkdir -p ~/.config/labwc
    [ -f ~/.config/labwc/autostart ] || { [ -f /etc/xdg/labwc/autostart ] && cp /etc/xdg/labwc/autostart ~/.config/labwc/autostart || true; }
    touch ~/.config/labwc/autostart
    grep -q "gmr/deploy/kiosk.sh" ~/.config/labwc/autostart || echo "$LINE &" >> ~/.config/labwc/autostart
    echo "added to ~/.config/labwc/autostart";;
  wayfire)
    mkdir -p ~/.config; touch ~/.config/wayfire.ini
    grep -q '^\[autostart\]' ~/.config/wayfire.ini || printf '\n[autostart]\n' >> ~/.config/wayfire.ini
    grep -q "gmr/deploy/kiosk.sh" ~/.config/wayfire.ini || sed -i "/^\[autostart\]/a gmr = $LINE" ~/.config/wayfire.ini
    echo "added to ~/.config/wayfire.ini [autostart]";;
  x11)
    A=~/.config/lxsession/LXDE-pi/autostart; mkdir -p "$(dirname $A)"
    [ -f "$A" ] || { [ -f /etc/xdg/lxsession/LXDE-pi/autostart ] && cp /etc/xdg/lxsession/LXDE-pi/autostart "$A" || true; }
    touch "$A"
    grep -q "gmr/deploy/kiosk.sh" "$A" || printf '@xset s off\n@xset -dpms\n@xset s noblank\n@%s\n' "$LINE" >> "$A"
    echo "added to $A";;
  cage)
    sudo usermod -aG video,render,input,tty "$ME" || true
    sed -e "s|__USER__|$ME|g" -e "s|__HOME__|$HOME_DIR|g" -e "s|__UID__|$UID_|g" "$DEP/gmr-kiosk.service" | sudo tee /etc/systemd/system/gmr-kiosk.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl set-default graphical.target
    sudo systemctl enable gmr-kiosk.service
    echo "gmr-kiosk.service enabled (cage on tty1)";;
esac

# screen blanking off (Pi OS helper handles X11 + wayland sessions)
if command -v raspi-config >/dev/null; then sudo raspi-config nonint do_blanking 1 || true; fi

say "Done"
echo "Server:  http://$(hostname -I | awk '{print $1}'):8000"
echo "Flic:    POST http://$(hostname -I | awk '{print $1}'):8000/event  {\"task\":\"wake\"}"
case "$MODE" in
  cage) echo "Reboot to start the kiosk:  sudo reboot";;
  *)    echo "Start the kiosk now without rebooting:  $LINE &   (or reboot)";;
esac
