# BlockSpot

BlockSpot is a self-hosted neighborhood hotspot that works without internet.

It is both a public service and an open source project.

For visitors — connect to a local BlockSpot and browse Wikipedia, maps, emergency info, and community tools. No internet, no account, no tracking. Just connect and explore.

For hosts — build and run your own BlockSpot, share useful content with your neighborhood, and join a growing network of independently operated nodes around the world. Learn, tinker, and make something awesome.

---

## The idea

The internet is incredible but fragile — it requires infrastructure, connectivity, and corporations to function. BlockSpot is a small rebellion against that dependency.

Each BlockSpot is independently owned and operated. There's no central server, no company behind it. Some hosts run one because it's a fun and rewarding. Others because their neighborhood needs it. Most because it's both.

---

## Node status

Every BlockSpot is described by two independent dimensions: how it's powered, and how it's connected.

**Power**

| Status | Description |
|---|---|
| ⚡ Grid | Powered from mains electricity |
| 🔋 Battery | Running on battery power |
| ☀️ Solar | Solar powered |
| 🔌 Hybrid | Combination of power sources |

**Connectivity**

| Status | Description |
|---|---|
| 🔴 Offline | No internet connection, local content only |
| 🟡 Hybrid | Local services + optional internet passthrough |
| 🟢 Online | Full internet + local content layer, browseable from anywhere |

A node can be any combination — solar powered and offline, grid powered and online, battery powered and hybrid, and so on.

Online nodes can be accessed remotely via `yourname.blockspot.dev` using a Cloudflare Tunnel — no port forwarding or static IP required.

---

## The network

BlockSpot nodes are independent but loosely connected. Each host can:

- List their node in the [BlockSpot directory](https://blockspot.dev)
- Publish a feed or blog about their setup, content, and local happenings
- Follow other hosts and their updates

Think of it like a webring for offline hotspots — each one unique, each one reflecting its neighborhood.

---

## blockspot.json

Every node can publish a `blockspot.json` file to participate in the directory:

```json
{
  "name": "Dave's BlockSpot",
  "location": "Manchester, NH",
  "power": "grid",
  "connectivity": "hybrid",
  "hardware": "mini PC + travel router",
  "stack": ["docker", "kiwix", "caddy"],
  "content": ["wikipedia", "maps", "local-wiki", "emergency-info"],
  "feed": "https://yoursite.com/blockspot",
  "endpoint": "dave.blockspot.dev"
}
```

This is an early draft of the spec — contributions welcome.

---

## Reference implementation

This repo contains one way to run a BlockSpot. There are many others.

**Hardware**
- Mini PC (any low-power x86 or ARM board works)
- Travel router (GL.iNet or similar)

**Stack**
- Docker + Docker Compose
- [Kiwix](https://www.kiwix.org) — offline Wikipedia, books, and more
- [Caddy](https://caddyserver.com) — reverse proxy and custom homepage

**What's included**
- `docker-compose.yml` — spins up all services
- Caddy config with a clean homepage routing to all apps
- Sample `blockspot.json`
- Setup guide for connecting a travel router

---

## Getting started

```bash
git clone https://github.com/blockspot-dev/blockspot
cd blockspot
cp .env.example .env
docker compose up -d
```

Then connect your travel router to the mini PC and configure it to route traffic to `192.168.x.x`. Full setup guide in [SETUP.md](./SETUP.md).

---

## Content ideas

Some things hosts run on their BlockSpot:

- Wikipedia (via Kiwix)
- OpenStreetMap tiles — offline maps
- Local neighborhood wiki
- Emergency contacts and preparedness info
- Community bulletin board
- Games
- Local media server

---

## Other implementations

BlockSpot is a concept, not a stack. You can run one on:

- A Raspberry Pi
- An old laptop
- An OpenWRT router with USB storage
- A NAS

If you've built your own implementation, open a PR to add it to the [implementations list](./IMPLEMENTATIONS.md).

---

## Remote access via blockspot.dev

Online-status nodes can be accessed from anywhere via a free subdomain.

Setup uses [Cloudflare Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) — no static IP or port forwarding needed. Registration is currently manual while the automated system is in development. Open an issue to request your subdomain.

---

## Contributing

This is a hacker project built for fun. Contributions welcome — new implementations, content packs, blockspot.json spec improvements, or just sharing what you're running.

Open an issue or PR at [github.com/blockspot-dev/blockspot](https://github.com/blockspot-dev/blockspot).

---

## License

MIT
