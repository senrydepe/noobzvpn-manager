# NoobzVPN Manager Bot

Telegram Bot untuk manajemen NoobzVPN

## Fitur
- 🟢 Start/Stop VPN Service
- 🔴 Create/Delete VPN User
- 🔵 Block/Unblock User
- 🟣 Renew User Account
- 📊 Real-time Traffic Monitoring
- 🌐 Server Information Display
- 🔌 Port Configuration:
  - HTTP: Port 80
  - HTTPS: Port 443

## Instalasi Lengkap

### 1. Install NoobzVPN
```bash
# Update system
apt update && apt upgrade -y

# Install dependensi
apt install -y python3 git vnstat

# Clone & install NoobzVPN
git clone https://github.com/noobz-id/noobzvpns.git
cd noobzvpns
sudo ./install.sh

# Verifikasi instalasi
sudo systemctl status noobzvpns
