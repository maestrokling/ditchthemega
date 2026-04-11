# DitchTheMega

**Practical guides to leaving Big Tech ecosystems. Free. Open source. No tracking.**

→ [ditchthemega.com](https://ditchthemega.com)

## What this is

Not a boycott manifesto. Not a moral lecture. A practical guide that assumes you've already decided to reduce your Big Tech dependency and need to know how. Service by service. With real alternatives and honest assessments of what you gain and lose.

## Phase 1: Amazon

Complete buyer and seller guides for leaving the Amazon ecosystem:

**Buyers:**
- Amazon Prime
- Amazon Shopping (alternatives by category)
- Kindle & Digital Books (including DRM reality)
- Audible
- Prime Video
- Alexa & Smart Home migration
- Ring Security Cameras
- Amazon Photos
- Amazon Pharmacy
- Subscribe & Save
- Your Amazon Data (export + deletion)
- What You Actually Lose (honest page)

**Sellers:**
- Seller Assessment (where are you dependent?)
- Building a Direct Channel
- Alternative Marketplaces
- Fulfillment Without FBA
- The Financial Reality

**Coming soon:** Google, Meta, Apple, Microsoft

## Stack

- Pure static HTML/CSS/JS
- Python build script (`build.py`) — no framework dependencies
- Deployed on Cloudflare Pages

## Run locally

```bash
python3 build.py
# Output in public/
cd public && python3 -m http.server 8080
```

## Contributing

Content is in `content/services/*.yaml`. Each file is a service with structured fields. PRs welcome for corrections, updated alternatives, or new services.

## Principles

- No data collection
- No affiliate links
- No paid recommendations  
- Honest about tradeoffs (Amazon does some things well — we say so)
- Open source

## Related

- [CancelFreely](https://cancelfreely.com) — cancel any subscription, step by step
- [DeleteFreely](https://deletefreely.com) — delete your data from major companies
