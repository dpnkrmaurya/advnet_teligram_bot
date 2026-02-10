# ================= AUTO DEPENDENCY INSTALL =================
import sys, subprocess, importlib.util, warnings, time, socket

dependencies = {
    "speedtest-cli": "speedtest",
    "requests": "requests",
    "dnspython": "dns",
    "psutil": "psutil",
    "geopy": "geopy"
}

def module_exists(m):
    return importlib.util.find_spec(m) is not None

def pip_install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

for pkg, mod in dependencies.items():
    if not module_exists(mod):
        pip_install(pkg)

warnings.filterwarnings("ignore")

# ================= IMPORTS =================
import speedtest, requests, dns.resolver, psutil
from geopy.distance import geodesic

# ================= TELEGRAM CONFIG =================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

TG_SEND = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TG_UPDATES = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

INDIA_COORDS = (28.6139, 77.2090)

# ================= SAFE RETRY =================
def retry(func, tries=3):
    for _ in range(tries):
        try:
            return func()
        except:
            time.sleep(2)
    return None

# ================= SPEED TEST =================
def speed_test():
    st = speedtest.Speedtest()
    st.get_best_server()
    d_mbps = st.download() / 1_000_000
    u_mbps = st.upload() / 1_000_000
    return d_mbps, u_mbps, d_mbps / 8, u_mbps / 8, st.results.ping

# ================= IP INFO =================
def ip_info():
    data = requests.get("https://ipinfo.io/json", timeout=10).json()
    lat, lon = map(float, data["loc"].split(","))
    dist = geodesic(INDIA_COORDS, (lat, lon)).km
    return data.get("ip"), data.get("org"), data.get("country"), dist

# ================= DNS TEST =================
def dns_test():
    servers = {
        "Google": "8.8.8.8",
        "Cloudflare": "1.1.1.1",
        "Quad9": "9.9.9.9"
    }
    out = []
    for name, ip in servers.items():
        r = dns.resolver.Resolver(configure=False)
        r.nameservers = [ip]
        start = time.time()
        try:
            r.resolve("google.com", "A")
            out.append(f"{name}:{(time.time()-start)*1000:.1f}ms")
        except:
            out.append(f"{name}:FAIL")
    return out

# ================= SECURITY CHECK =================
def security_check():
    notes, risk = [], "LOW"
    try:
        if any(x in i.lower() for i in psutil.net_if_addrs()
               for x in ("tun", "vpn", "ppp", "wireguard")):
            notes.append("VPN/Tunnel Detected")
            risk = "MEDIUM"
    except:
        notes.append("Interface Restricted")
    return notes, risk

# ================= LIVE NETWORK =================
def live_network_activity():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        start = time.time()
        s.connect(("8.8.8.8", 53))
        latency = (time.time() - start) * 1000
        s.close()
        if latency < 50:
            return "HIGH", "FAST"
        elif latency < 120:
            return "MEDIUM", "STABLE"
        else:
            return "LOW", "SLOW"
    except:
        return "NONE", "OFFLINE"

# ================= VIDEO TEST =================
def video_test():
    url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"
    try:
        start = time.time()
        r = requests.get(url, timeout=10)
        mbs = len(r.content) / (time.time() - start) / 1_000_000
        mbps = mbs * 8
        quality = "4K Ready" if mbs > 5 else "HD Ready" if mbs > 2 else "Low Quality"
        return f"{mbps:.2f} Mbps | {mbs:.2f} MB/s ({quality})"
    except:
        return "FAILED"

# ================= DASHBOARD =================
def dashboard_text():
    d_mbps, u_mbps, d_mbs, u_mbs, ping = retry(speed_test)
    ip, isp, country, dist = retry(ip_info)
    dnsr = dns_test()
    sec, risk = security_check()
    activity, speed_state = live_network_activity()
    video = video_test()

    return (
        "📡 ANDROID NETWORK REPORT\n\n"
        f"⬇ Download : {d_mbps:.2f} Mbps | {d_mbs:.2f} MB/s\n"
        f"⬆ Upload   : {u_mbps:.2f} Mbps | {u_mbs:.2f} MB/s\n"
        f"📶 Ping     : {ping:.1f} ms\n\n"
        f"🌐 IP       : {ip}\n"
        f"🏢 ISP      : {isp}\n"
        f"🌍 Country  : {country}\n"
        f"📍 Distance : {dist:.1f} km from India\n\n"
        "⚙ DNS Test\n"
        f"  {' | '.join(dnsr)}\n\n"
        f"🔐 Security Risk : {risk}\n"
        f"🛡 Notes         : {', '.join(sec)}\n\n"
        f"🎥 Streaming : {video}\n"
        f"📊 Network   : {activity} ({speed_state})\n\n"
        f"⏱ Time : {time.strftime('%d-%m-%Y %H:%M:%S')}"
    )

# ================= USER LOG SAVE =================
def save_user_log(user_id, chat_id, name, username, message):
    try:
        with open("users.log", "a", encoding="utf-8") as f:
            f.write(f"Time      : {time.strftime('%d-%m-%Y %H:%M:%S')}\n")
            f.write(f"User ID   : {user_id}\n")
            f.write(f"Chat ID   : {chat_id}\n")
            f.write(f"Name      : {name}\n")
            f.write(f"Username  : @{username}\n" if username else "Username  : N/A\n")
            f.write(f"Message   : {message}\n")
            f.write("-" * 40 + "\n")
    except Exception as e:
        print("[LOG ERROR]", e)

# ================= TELEGRAM SEND =================
def send_telegram(chat_id, msg):
    requests.post(TG_SEND, data={
        "chat_id": chat_id,
        "text": msg[:4000]
    })

# ================= TELEGRAM LISTENER =================
def telegram_listener():
    offset = 0
    print("[+] Telegram Multi-User Bot Running\n")

    while True:
        try:
            data = requests.get(
                TG_UPDATES,
                params={"timeout": 30, "offset": offset},
                timeout=60
            ).json()
        except:
            time.sleep(3)
            continue

        for update in data.get("result", []):
            offset = update["update_id"] + 1

            message = update.get("message", {})
            text = message.get("text", "")
            chat = message.get("chat", {})
            user = message.get("from", {})

            chat_id = chat.get("id")
            user_id = user.get("id")
            first = user.get("first_name", "")
            last = user.get("last_name", "")
            username = user.get("username", "")
            full_name = f"{first} {last}".strip()

            # ===== SAVE USER DATA =====
            save_user_log(user_id, chat_id, full_name, username, text)

            # ===== SHOW IN TERMUX =====
            print("\n[TELEGRAM USER LOGGED]")
            print(f"User ID   : {user_id}")
            print(f"Chat ID   : {chat_id}")
            print(f"Name      : {full_name}")
            print(f"Username  : @{username}" if username else "Username  : N/A")
            print(f"Message   : {text}")
            print("-" * 34)

            # ===== COMMAND =====
            if text == "/start" and chat_id:
                send_telegram(chat_id, dashboard_text())

        time.sleep(2)

# ================= MAIN =================
if __name__ == "__main__":
    telegram_listener()
