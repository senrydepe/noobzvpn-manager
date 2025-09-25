import os
import subprocess
import json
import asyncio
from telethon import TelegramClient, events, Button
import requests

# Konfigurasi Bot
BOT_TOKEN = "8141018167:AAGDipkWkQl7oxqMn4Sk_Mp-qCj8F-pdqHg" # BOT TELEGRAM
ADMIN_ID = 7519839885  # ID TELEGRAM
VPN_PATH = "/etc/noobzvpns/"
CONFIG_FILE = "/etc/noobzvpns/config.json"
USERS_FILE = "/etc/noobzvpns/users.json"

# Emojis
g = "🟢"
r = "🔴"
b = "🔵"
p = "🟣"
check = "✅"
nocheck = "❌"

# Inisialisasi Bot
bot = TelegramClient("noobz-manager", 6, "eb06d4abfb49dc3eeb1aeb98ae0f581e").start(bot_token=BOT_TOKEN)

# Fungsi NoobzVPN
def run_vpn_command(command):
    try:
        result = subprocess.run(
            ["noobzvpns"] + command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def get_vpn_status():
    try:
        from pystemd.systemd1 import Unit
        unit = Unit(b"noobzvpns.service")
        unit.load()
        return unit.Unit.SubState == b"running"
    except:
        return False

def get_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def get_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def get_vnstat_data():
    try:
        v = subprocess.check_output(["vnstat", "--oneline"])
        today_total = str(v).split(";")[5]
        month_total = str(v).split(";")[14].replace("\\n", "")
        return today_total, month_total
    except:
        return "N/A", "N/A"

def get_isp():
    try:
        return requests.get("http://ip-api.com/json/").json()["isp"]
    except:
        return "Unknown"

# Handler /start
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("❌ Access Denied!")
        return

    vpn_status = get_vpn_status()
    config = get_config()
    today_total, month_total = get_vnstat_data()
    isp = get_isp()

    msg = f"""
🌟 Welcome to NoobzVPN Manager 🌟

📋 ====[ INFO ]====

{'🟢' if vpn_status else '🔴'} Noobz-VPN Status: {'[ON] 🟢' if vpn_status else '[OFF] 🔴'}
🌐 Server Domain: `{config.get('host', 'N/A')}`
📡 Server ISP: `{isp}`

🔌 ====[ PORTS ]====

📡 TCP Plain: `{config.get('tcp_plain', 'N/A')}` (HTTP)
🔒 TCP SSL: `{config.get('tcp_ssl', 'N/A')}` (HTTPS)
📡 UDP STD: `{config.get('udp_std', 'N/A')}`
🔓 UDP SSL: `{config.get('udp_ssl', 'N/A')}`

📊 ====[ USAGE ]====

📈 Today RX/TX Total: `{today_total}`
📊 This Month RX/TX Total: `{month_total}`

🎯 ====[ NOOBZ-MANAGER ]===
"""

    if vpn_status:
        buttons = [
            [Button.inline(f"{nocheck} Stop VPN Service", "stop")],
            [Button.inline(f"{g} Create User", "create"),
             Button.inline(f"{r} Delete User", "delete")],
            [Button.inline(f"{r} Block User", "block"),
             Button.inline(f"{g} Unblock User", "unblock")],
            [Button.inline(f"{b} Renew User", "renew"),
             Button.inline(f"{p} Show All Users", "show")]
        ]
    else:
        buttons = [
            [Button.inline(f"{check} Start VPN Service", "start")],
            [Button.inline(f"{g} Create User", "create"),
             Button.inline(f"{r} Delete User", "delete")],
            [Button.inline(f"{r} Block User", "block"),
             Button.inline(f"{g} Unblock User", "unblock")],
            [Button.inline(f"{b} Renew User", "renew"),
             Button.inline(f"{p} Show All Users", "show")]
        ]

    await event.reply(msg, buttons=buttons)

# Handler Service Control
@bot.on(events.CallbackQuery(data=b"start"))
async def start_vpn(event):
    if event.sender_id != ADMIN_ID:
        await event.edit("❌ Access Denied!")
        return
    
    try:
        from pystemd.systemd1 import Unit
        unit = Unit(b"noobzvpns.service")
        unit.load()
        unit.Unit.Start("fail")
        await event.edit("✅ NoobzVPN Service Started!")
    except Exception as e:
        await event.edit(f"❌ Error: {str(e)}")

@bot.on(events.CallbackQuery(data=b"stop"))
async def stop_vpn(event):
    if event.sender_id != ADMIN_ID:
        await event.edit("❌ Access Denied!")
        return
    
    try:
        from pystemd.systemd1 import Unit
        unit = Unit(b"noobzvpns.service")
        unit.load()
        unit.Unit.Stop("fail")
        await event.edit("✅ NoobzVPN Service Stopped!")
    except Exception as e:
        await event.edit(f"❌ Error: {str(e)}")

# Handler User Management
@bot.on(events.CallbackQuery(data=b"create"))
async def create_user(event):
    if event.sender_id != ADMIN_ID:
        await event.edit("❌ Access Denied!")
        return
    
    await event.edit("📝 **Username:** (max 10 chars)")
    async with bot.conversation(event.chat_id) as conv:
        username = await conv.wait_event(events.NewMessage(incoming=True, from_users=ADMIN_ID))
        username = username.message.message
        
        if len(username) > 10:
            await event.respond("❌ Max username length is 10 characters!")
            return
        
        await conv.send_message("🔐 **Password:**")
        password = await conv.wait_event(events.NewMessage(incoming=True, from_users=ADMIN_ID))
        password = password.message.message
        
        await conv.send_message("⏰ **Expiry (Days):**")
        expiry = await conv.wait_event(events.NewMessage(incoming=True, from_users=ADMIN_ID))
        expiry = expiry.message.message
        
        try:
            out = run_vpn_command(f"--add-user {username} {password}")
            if "success" in str(out):
                out = run_vpn_command(f"--expired-user {username} {expiry}")
                if "success" in str(out):
                    config = get_config()
                    await event.respond(f"""
✅ **Account Created Successfully!**

🔹 **Hostname:** `{config.get('host', 'N/A')}`
🔹 **Username:** `{username}`
🔹 **Password:** `{password}`
🔹 **Expired On:** `{expiry} days`
🔹 **Access Port:** 
   - HTTP: `{config.get('tcp_plain', 'N/A')}`
   - HTTPS: `{config.get('tcp_ssl', 'N/A')}`

ENJOY! 🎉
""")
                else:
                    await event.respond("❌ Failed to set expiry!")
            else:
                await event.respond("❌ Failed to create user!")
        except Exception as e:
            await event.respond(f"❌ Error: {str(e)}")

@bot.on(events.CallbackQuery(data=b"delete"))
async def delete_user(event):
    if event.sender_id != ADMIN_ID:
        await event.edit("❌ Access Denied!")
        return
    
    await event.edit("🗑️ **Username to Delete:**")
    async with bot.conversation(event.chat_id) as conv:
        username = await conv.wait_event(events.NewMessage(incoming=True, from_users=ADMIN_ID))
        username = username.message.message
        
        try:
            out = run_vpn_command(f"--remove-user {username}")
            if "success" in str(out):
                await event.respond(f"✅ User `{username}` successfully deleted!")
            else:
                await event.respond("❌ User not found or error occurred!")
        except Exception as e:
            await event.respond(f"❌ Error: {str(e)}")

@bot.on(events.CallbackQuery(data=b"show"))
async def show_users(event):
    if event.sender_id != ADMIN_ID:
        await event.edit("❌ Access Denied!")
        return
    
    users = get_users()
    
    if not users:
        await event.edit("📋 No users found!")
        return
    
    for username, data in users.items():
        msg = f"""
📋 **User Details:**

🔹 **Username:** `{username}`
🔹 **Hash Key:** `{data.get('hash_key', 'N/A')}`
🔹 **Created On:** `{data.get('issued', 'N/A')}`
🔹 **Expired (Days):** `{data.get('expired', 'N/A')}`
🔹 **Blocked:** {'🟢 Yes' if data.get('blocked', False) else '🔴 No'}

🎯 **Actions:**
"""
        buttons = [
            [Button.inline(f"🔴 Delete", f"delete-{username}"),
             Button.inline(f"🔴 Block", f"block-{username}")],
            [Button.inline(f"🟢 Unblock", f"unblock-{username}"),
             Button.inline(f"🔵 Renew", f"renew-{username}")]
        ]
        await event.edit(msg, buttons=buttons)
        await asyncio.sleep(2)

@bot.on(events.CallbackQuery(data=lambda x: x.startswith(("block-", "unblock-", "renew-"))))
async def user_actions(event):
    if event.sender_id != ADMIN_ID:
        await event.edit("❌ Access Denied!")
        return
    
    action = event.data.decode()
    username = action.split("-", 1)[1]
    
    try:
        if action.startswith("block-"):
            out = run_vpn_command(f"--block-user {username}")
            if "success" in str(out):
                await event.edit(f"✅ User `{username}` successfully blocked!")
            else:
                await event.edit("❌ Failed to block user!")
        
        elif action.startswith("unblock-"):
            out = run_vpn_command(f"--unblock-user {username}")
            if "success" in str(out):
                await event.edit(f"✅ User `{username}` successfully unblocked!")
            else:
                await event.edit("❌ Failed to unblock user!")
        
        elif action.startswith("renew-"):
            out = run_vpn_command(f"--renew-user {username}")
            if "success" in str(out):
                await event.edit(f"✅ User `{username}` successfully renewed!")
            else:
                await event.edit("❌ Failed to renew user!")
    
    except Exception as e:
        await event.edit(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting NoobzVPN Manager Bot...")
    bot.run_until_disconnected()