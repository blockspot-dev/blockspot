# BlockSpot Community Hotspot — Setup & Recovery Guide

_Last updated: April 2026_

**Server IP:** 192.168.8.211  
**Local URL:** http://blockspot.local  
**Router:** GL-iNet GL-A1300 (Slate Plus)  
**Router Admin:** http://192.168.8.1  
**LuCI Admin:** http://192.168.8.1/cgi-bin/luci  
**Router SSH:** `ssh root@192.168.8.1` (port 22)  
**Pi-hole Admin:** http://localhost:8053/admin (on server only)  

---

## Expected User Experience

1. User connects to **BlockSpot Community Hotspot** WiFi
2. Android shows **"Sign in to network"** notification automatically
3. User taps notification → splash page appears
4. User taps **Continue** → redirected to `blockspot.local`
5. Browser closes automatically (Android behavior, cannot be avoided)
6. User opens browser and navigates to `blockspot.local` to access content

> If the Sign in notification doesn't appear, users can open a browser and go to `blockspot.local` directly, which will show the splash page.

---

### Admin Password
Change immediately after any firmware update:
> GL.iNet panel → System → Admin Password

### Wireless — Client Isolation
Must be enabled on both radio interfaces.
1. LuCI → Network → Wireless → Edit each active BlockSpot interface
2. Advanced Settings tab → check **Isolate Clients**
3. Apply to both radio0 and radio1

### Guest Network
All public users connect to the guest network only. The host computer stays on the main network.

### Firewall — Guest Zone Settings
LuCI → Network → Firewall → Zones → guest zone:

| Setting | Value |
|---|---|
| Input | Accept |
| Output | Accept |
| Forward | Reject |
| Masquerading | unchecked |
| Allow forward to destination zones | none (uncheck wan) |

### Firewall — Traffic Rules
LuCI → Network → Firewall → Traffic Rules — add these rules and move them to the **top** of the list:

**Rule 1: Guest DNS (UDP)**
| Field | Value |
|---|---|
| Name | Guest DNS |
| Protocol | UDP |
| Source zone | guest |
| Destination zone | lan |
| Destination address | 192.168.8.211 |
| Destination port | 53 |
| Action | Accept |

**Rule 2: Guest to Server HTTP/S**
| Field | Value |
|---|---|
| Name | Guest to Server HTTP/S |
| Protocol | TCP |
| Source zone | guest |
| Destination zone | lan |
| Destination address | 192.168.8.211 |
| Destination port | 80 443 53 |
| Action | Accept |

**Rule 3: NoDogSplash**
| Field | Value |
|---|---|
| Name | NoDogSplash |
| Protocol | TCP |
| Source zone | guest |
| Destination zone | local/device input |
| Destination port | 2050 |
| Action | Accept |

### DNS — DHCP and DNS Settings
LuCI → Network → DHCP and DNS → Addresses:
```
/blockspot.local/192.168.8.211
```

### Guest Interface DHCP Options
LuCI → Network → Interfaces → Edit guest → DHCP Server → Advanced Settings → DHCP-Options:
```
6,192.168.8.211
```

---

## 2. NoDogSplash (Captive Portal)

### Installation
Requires internet on the router — connect via repeater mode temporarily.
1. LuCI → System → Software → Update lists
2. If HTTPS fails, change repo URLs from `https://` to `http://` in the Configuration tab
3. Search for `nodogsplash` and install

### Configuration via SSH
```bash
ssh root@192.168.8.1

uci set nodogsplash.@nodogsplash[0].gatewayinterface='br-guest'
uci set nodogsplash.@nodogsplash[0].redirectURL='http://blockspot.local'
uci add_list nodogsplash.@nodogsplash[0].preauthenticated_users='allow tcp port 53'
uci add_list nodogsplash.@nodogsplash[0].preauthenticated_users='allow udp port 53'
uci commit nodogsplash
/etc/init.d/nodogsplash restart
```

> **Important:** The preauthenticated DNS rules allow guests to resolve `blockspot.local` before accepting the splash page. Without these, DNS is blocked until after authentication.

### Custom Splash Page
File location: `/etc/nodogsplash/htdocs/splash.html`

```bash
cat > /etc/nodogsplash/htdocs/splash.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BlockSpot WiFi</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; background: #f0f4f8; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
  .card { background: white; border-radius: 16px; padding: 40px 32px; max-width: 420px; width: 100%; box-shadow: 0 4px 24px rgba(0,0,0,0.08); text-align: center; }
  h1 { font-size: 28px; color: #1a1a2e; margin-bottom: 8px; }
  .tagline { color: #666; font-size: 15px; margin-bottom: 28px; line-height: 1.5; }
  input[type=submit] { background: #2563eb; color: white; border: none; padding: 14px 40px; font-size: 17px; border-radius: 10px; cursor: pointer; width: 100%; margin-bottom: 24px; }
  input[type=submit]:active { background: #1d4ed8; }
  .notice { background: #fff8e1; border: 1px solid #f59e0b; border-radius: 10px; padding: 16px; text-align: left; margin: 30px 0px; }
  .notice-title { font-weight: bold; color: #b45309; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
  .notice p { color: #444; font-size: 15px; line-height: 1.5; }
  .notice a { color: #2563eb; font-weight: bold; text-decoration: none; }
</style>
</head>
<body>
<div class="card">
  <h1>BlockSpot WiFi</h1>
  <p class="tagline">A self-hosted neighborhood hotspot</p>
	<div class="notice">
    <div class="notice-title">⚠ Important</div>
    <p>After connecting, open your browser and go to <a href="http://blockspot.local">blockspot.local</a> to access all resources.</p>
  </div>
  <form method="get" action="$authaction">
    <input type="hidden" name="tok" value="$tok">
    <input type="hidden" name="redir" value="http://blockspot.local">
    <input type="submit" value="Connect">
  </form>
</div>
</body>
</html>
EOF

/etc/init.d/nodogsplash restart
```

### Useful NoDogSplash Commands
```bash
ndsctl status          # show status and connected clients
ndsctl deauth <IP>     # force client to see splash page again
ndsctl auth <IP>       # manually authenticate a client
```

---

## 3. Server Docker Setup

> **Pi-hole is required.** Guest devices use your server (192.168.8.211) as their DNS via the DHCP option. Pi-hole must be running to resolve `blockspot.local`. Without it, guests can only reach the server by IP address.

### compose.yaml Key Points
| Service | Port Binding |
|---|---|
| Kiwix | 127.0.0.1:1200:8080 (localhost only) |
| MapServer | 127.0.0.1:1300:8080 (localhost only) |
| Pi-hole DNS | 53:53/tcp and 53:53/udp (all interfaces) |
| Pi-hole admin | 127.0.0.1:8053:80 (localhost only) |
| Caddy | 80 and 443 (all interfaces) |

```bash
docker compose up -d    # start all services
docker restart caddy    # restart caddy after Caddyfile changes
```

### Pi-hole DNS Records
1. Open http://localhost:8053/admin on the server
2. Go to Local DNS → DNS Records
3. Add: `blockspot.local` → `192.168.8.211`

### Caddyfile
Caddy listens on both the IP and local hostname:

(File is already included)

---

## 4. Windows Firewall Rules

In Windows Defender Firewall with Advanced Security → Inbound Rules:

| Rule Name | Protocol | Port(s) | Profile | Action |
|---|---|---|---|---|
| BlockSpot Guest Access | TCP | 80, 443 | Public | Allow |
| Block Direct Service Ports | TCP | 1200, 1300 | All | Block |

> **Note:** Port 53 (DNS) does not need a Windows Firewall rule — the LuCI traffic rules in the router handle DNS routing from the guest network to Pi-hole.

---

## 5. Post-Firmware-Update Recovery Checklist

After any firmware update, restore in this order:

- [ ] Change router admin password (System → Admin Password)
- [ ] Enable client isolation on both radio interfaces (LuCI → Network → Wireless)
- [ ] Set guest zone firewall: Input=Accept, Forward=Reject, uncheck wan forward
- [ ] Add traffic rules: Guest DNS, Guest to Server HTTP/S, NoDogSplash (move to top)
- [ ] Add DNS address: `/blockspot.local/192.168.8.211` (LuCI → Network → DHCP and DNS → Addresses)
- [ ] Set guest DHCP option: `6,192.168.8.211` (LuCI → Network → Interfaces → guest → DHCP Server → Advanced Settings)
- [ ] Connect router to internet via repeater and reinstall NoDogSplash
- [ ] Configure NoDogSplash via SSH including preauthenticated DNS rules (see Section 2)
- [ ] Restore custom splash page via SSH (see Section 2)
- [ ] Disconnect repeater
- [ ] Start Docker containers on server: `docker compose up -d`
- [ ] Verify Pi-hole DNS record for blockspot.local exists at http://localhost:8053/admin
