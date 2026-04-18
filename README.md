# BlockSpot

BlockSpot is a self-hosted neighborhood hotspot that works without internet.

**For visitors** — when the internet goes down, BlockSpot stays up. Connect and browse Wikipedia, maps, emergency info, and community tools. No account, no tracking, no internet required.

**For hosts** — run your own node, serve your neighborhood, and join a growing network of independently operated nodes. Learn, tinker, and build something useful.

> *Build it. Host it. Be ready.*

---

## The idea

Most of the internet requires the internet. BlockSpot doesn’t.

Plug in a small computer and a travel router, and anyone nearby can connect to a local Wi-Fi network and access useful content—Wikipedia, maps, emergency info, and more—served directly from your device.

When connectivity drops, your block doesn’t have to.

Each BlockSpot is independently owned and operated. No central server. No company behind it. Some people run one to serve their community. Others to learn. Most because it’s both.

---

## Reference implementation

This repo contains one way to run a BlockSpot—simple, self-hosted, and easy to modify.

### Hardware

* Mini PC (any low-power x86 or ARM board works)
* Travel router (GL.iNet or similar)

### Stack

* Docker + Docker Compose
* Kiwix — offline Wikipedia and more
* Caddy — reverse proxy and homepage

### Included

* `docker-compose.yml` — runs the core services
* Caddy config with a simple homepage
* Setup guide for connecting a travel router

---

## Getting started

```bash
git clone https://github.com/blockspot-dev/blockspot
cd blockspot
cp .env.example .env
docker compose up -d
```

Then connect your travel router and point it to the host machine. See `SETUP.md` for details.

---

## What you can run on it

* Wikipedia and reference books
* Offline maps (OpenStreetMap)
* Local neighborhood wiki
* Emergency contacts and preparedness info
* Community bulletin board
* Games

Even a simple setup is useful.

---

## Other implementations

BlockSpot is a concept, not a stack.

Run it on a Raspberry Pi, old laptop, OpenWRT router, or NAS. If you’ve built your own version, open a PR to add it to `IMPLEMENTATIONS.md`.

---

## Roadmap

A few things in progress:

* **blockspot.json** — a simple way for nodes to describe themselves
* **Directory** — a public listing of nodes at https://blockspot.dev

Ideas welcome—open an issue and help shape it.

---

## Contributing

Contributions welcome—implementations, content ideas, docs, or just sharing what you’re running.

Open an issue or PR at https://github.com/blockspot-dev/blockspot

---

## License

MIT
