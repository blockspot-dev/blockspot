# BlockSpot Community Hotspot — Setup \& Recovery Guide

*Last updated: April 2026*

**Server IP:** 192.168.8.211  
**Local URL:** http://blockspot.local  
**Router:** GL-iNet GL-A1300 (Slate Plus)  
**Router Admin:** http://192.168.8.1  
**LuCI Admin:** http://192.168.8.1/cgi-bin/luci  
**Router SSH:** `ssh root@192.168.8.1` (port 22)  
**Pi-hole Admin:** http://localhost:8053/admin (on server only)

\---

## 1\. Router Security Settings

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

|Setting|Value|
|-|-|
|Input|Accept|
|Output|Accept|
|Forward|Reject|
|Masquerading|unchecked|
|Allow forward to destination zones|none (uncheck wan)|

### Firewall — Traffic Rules

LuCI → Network → Firewall → Traffic Rules — add these rules and move them to the **top** of the list:

**Rule 1: Guest DNS (UDP)**

|Field|Value|
|-|-|
|Name|Guest DNS|
|Protocol|UDP|
|Source zone|guest|
|Destination zone|lan|
|Destination address|192.168.8.211|
|Destination port|53|
|Action|Accept|

**Rule 2: Guest to Server HTTP/S**

|Field|Value|
|-|-|
|Name|Guest to Server HTTP/S|
|Protocol|TCP|
|Source zone|guest|
|Destination zone|lan|
|Destination address|192.168.8.211|
|Destination port|80 443 53|
|Action|Accept|

**Rule 3: NoDogSplash**

|Field|Value|
|-|-|
|Name|NoDogSplash|
|Protocol|TCP|
|Source zone|guest|
|Destination zone|local/device input|
|Destination port|2050|
|Action|Accept|

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

\---

## 2\. NoDogSplash (Captive Portal)

### Installation

Requires internet on the router — connect via repeater mode temporarily.

1. LuCI → System → Software → Update lists
2. If HTTPS fails, change repo URLs from `https://` to `http://` in the Configuration tab
3. Search for `nodogsplash` and install

### Configuration via SSH

```bash
ssh root@192.168.8.1

uci set nodogsplash.@nodogsplash\[0].gatewayinterface='br-guest'
uci set nodogsplash.@nodogsplash\[0].redirectURL='http://blockspot.local'
uci commit nodogsplash
/etc/init.d/nodogsplash restart
```

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
<title>BlockSpot Community Hotspot</title>
<style>
  body { font-family: sans-serif; text-align: center; padding: 40px; background: #f5f5f5; }
  h1 { color: #333; }
  p { color: #666; }
  .note { font-size: 14px; color: #888; margin-top: 20px; }
  a { color: #007bff; }
  input\[type=submit] { background: #007bff; color: white; border: none; padding: 15px 40px; font-size: 18px; border-radius: 8px; cursor: pointer; margin-top: 20px; }
</style>
</head>
<body>
<h1>Welcome to BlockSpot Community Hotspot</h1>
<p>Free offline resources for the community — maps, encyclopedias, and more.</p>
<p>Tap Continue to get started. You will be redirected to our home page automatically.</p>
<form method="get" action="$authaction">
<input type="hidden" name="tok" value="$tok">
<input type="hidden" name="redir" value="http://blockspot.local">
<input type="submit" value="Continue">
</form>
<p class="note">If you are not redirected automatically, open your browser and visit <a href="http://blockspot.local">blockspot.local</a></p>
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

\---

## 3\. Server Docker Setup

> \*\*Pi-hole is required.\*\* Guest devices use your server (192.168.8.211) as their DNS via the DHCP option. Pi-hole must be running to resolve `blockspot.local`. Without it, guests can only reach the server by IP address.

### compose.yaml Key Points

|Service|Port Binding|
|-|-|
|Kiwix|127.0.0.1:1200:8080 (localhost only)|
|MapServer|127.0.0.1:1300:8080 (localhost only)|
|Pi-hole DNS|53:53/tcp and 53:53/udp (all interfaces)|
|Pi-hole admin|127.0.0.1:8053:80 (localhost only)|
|Caddy|80 and 443 (all interfaces)|

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

```
http://192.168.8.211, http://blockspot.local {
    # Captive portal detection - iOS
    handle /hotspot-detect.html {
        redir http://blockspot.local 302
    }
    handle /library/test/success.html {
        redir http://blockspot.local 302
    }
    # Captive portal detection - Android/Chrome
    handle /generate\_204 {
        redir http://blockspot.local 302
    }
    handle /gen\_204 {
        redir http://blockspot.local 302
    }
    # Captive portal detection - Windows
    handle /ncsi.txt {
        redir http://blockspot.local 302
    }
    handle /connecttest.txt {
        redir http://blockspot.local 302
    }
    handle /mapserver {
        root \* /srv
        rewrite \* /mapserver/index.html
        file\_server
    }
    handle /mapserver/ {
        root \* /srv
        rewrite \* /mapserver/index.html
        file\_server
    }
    handle /mapserver/\* {
        uri strip\_prefix /mapserver
        reverse\_proxy mapserver:8080
    }
    handle /kiwix/\* {
        uri strip\_prefix /kiwix
        reverse\_proxy kiwix:8080
    }
    handle {
        root \* /srv
        file\_server
    }
}
```

\---

## 4\. Windows Firewall Rules

In Windows Defender Firewall with Advanced Security → Inbound Rules:

|Rule Name|Protocol|Port(s)|Profile|Action|
|-|-|-|-|-|
|BlockSpot Guest Access|TCP|80, 443|Public|Allow|
|Block Direct Service Ports|TCP|1200, 1300|All|Block|

> \*\*Note:\*\* Port 53 (DNS) does not need a Windows Firewall rule — the LuCI traffic rules in the router handle DNS routing from the guest network to Pi-hole.

\---

## 5\. Post-Firmware-Update Recovery Checklist

After any firmware update, restore in this order:

* \[ ] Change router admin password (System → Admin Password)
* \[ ] Enable client isolation on both radio interfaces (LuCI → Network → Wireless)
* \[ ] Set guest zone firewall: Input=Accept, Forward=Reject, uncheck wan forward
* \[ ] Add traffic rules: Guest DNS, Guest to Server HTTP/S, NoDogSplash (move to top)
* \[ ] Add DNS address: `/blockspot.local/192.168.8.211` (LuCI → Network → DHCP and DNS → Addresses)
* \[ ] Set guest DHCP option: `6,192.168.8.211` (LuCI → Network → Interfaces → guest → DHCP Server → Advanced Settings)
* \[ ] Connect router to internet via repeater and reinstall NoDogSplash
* \[ ] Configure NoDogSplash via SSH (see Section 2)
* \[ ] Restore custom splash page via SSH (see Section 2)
* \[ ] Disconnect repeater
* \[ ] Start Docker containers on server: `docker compose up -d`
* \[ ] Verify Pi-hole DNS record for blockspot.local exists at http://localhost:8053/admin

