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
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

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

    d_mbs = d_mbps / 8
    u_mbs = u_mbps / 8

    return d_mbps, u_mbps, d_mbs, u_mbs, st.results.ping

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
    notes = []
    risk = "LOW"

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

        if mbs > 5:
            quality = "4K Ready"
        elif mbs > 2:
            quality = "HD Ready"
        else:
            quality = "Low Quality"

        return f"{mbps:.2f} Mbps | {mbs:.2f} MB/s ({quality})"
    except:
        return "FAILED"

# ================= DASHBOARD TEXT =================
def dashboard_text():
    d_mbps, u_mbps, d_mbs, u_mbs, ping = retry(speed_test)
    ip, isp, country, dist = retry(ip_info)
    dnsr = dns_test()
    sec, risk = security_check()
    activity, speed_state = live_network_activity()
    video = video_test()

    text = f"""
📡 ANDROID NETWORK REPORT

⬇ Download : {d_mbps:.2f} Mbps | {d_mbs:.2f} MB/s
⬆ Upload   : {u_mbps:.2f} Mbps | {u_mbs:.2f} MB/s
📶 Ping     : {ping:.1f} ms

🌐 IP       : {ip}
🏢 ISP      : {isp}
🌍 Country  : {country}
📍 Distance : {dist:.1f} km from India

⚙ DNS Test
  {' | '.join(dnsr)}

🔐 Security Risk : {risk}
🛡 Notes         : {', '.join(sec)}

🎥 Streaming : {video}
📊 Network   : {activity} ({speed_state})

⏱ Time : {time.strftime('%d-%m-%Y %H:%M:%S')}
"""
    return text.strip()

# ================= TELEGRAM SEND =================
def send_telegram(msg):
    requests.post(TG_SEND, data={
        "chat_id": CHAT_ID,
        "text": msg[:4000]
    })

# ================= TELEGRAM LISTENER =================
def telegram_listener():
    offset = 0
    print("[+] Telegram Bot Running")

    while True:
        data = requests.get(TG_UPDATES, params={
            "timeout": 30,
            "offset": offset
        }).json()

        for update in data.get("result", []):
            offset = update["update_id"] + 1
            msg = update.get("message", {}).get("text", "")

            if msg == "/start":
                report = dashboard_text()
                send_telegram(report)

        time.sleep(2)

# ================= MAIN =================
if __name__ == "__main__":
    telegram_listener()
