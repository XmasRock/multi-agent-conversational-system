# 1. Installer BlueZ (si pas déjà installé)
sudo apt install -y bluez bluez-tools pulseaudio-module-bluetooth

# 2. Activer Bluetooth
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# 3. Pairage de l'enceinte
bluetoothctl

# Dans bluetoothctl:
[bluetooth]# power on
[bluetooth]# agent on
[bluetooth]# default-agent
[bluetooth]# scan on

# Attendre détection de votre enceinte (noter l'adresse MAC)
# Exemple: Device AA:BB:CC:DD:EE:FF My Speaker

[bluetooth]# pair AA:BB:CC:DD:EE:FF
[bluetooth]# trust AA:BB:CC:DD:EE:FF
[bluetooth]# connect AA:BB:CC:DD:EE:FF
[bluetooth]# exit

# 4. Configurer PulseAudio
pactl list cards  # Noter le nom de votre enceinte
pactl set-default-sink bluez_sink.AA_BB_CC_DD_EE_FF


# copier /etc/systemd/system/bluetooth-speaker.service
sudo systemctl enable bluetooth-speaker
sudo systemctl start bluetooth-speaker