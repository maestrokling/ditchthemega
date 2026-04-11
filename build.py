#!/usr/bin/env python3
"""
DitchTheMega build script
Reads content/services/*.yaml → generates public/ static site
Run: python3 build.py
"""
import yaml, os, glob, html, shutil
from datetime import date

CONTENT_DIR = "content/services"
PUBLIC_DIR  = "public"
SITE_URL    = "https://ditchthemega.com"

CATEGORY_LABELS = {
    "membership":     "Membership",
    "shopping":       "Shopping",
    "digital-content":"Digital Content",
    "streaming":      "Streaming",
    "smart-home":     "Smart Home",
    "storage":        "Storage",
    "health":         "Health",
    "data-privacy":   "Data & Privacy",
    "seller":         "For Sellers",
    "meta":           "Reference",
}

DIFF_LABEL = ["", "Easy", "Moderate", "Involved", "Complex", "Very Hard"]
DIFF_CLASS = ["", "d1", "d2", "d3", "d4", "d5"]

def e(s):
    return html.escape(str(s or ""), quote=True)

def load_services():
    services = []
    for path in sorted(glob.glob(f"{CONTENT_DIR}/*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        data["_path"] = path
        services.append(data)
    return services

def render_list(items):
    if not items:
        return ""
    lis = "".join(f"<li>{e(i)}</li>" for i in items)
    return f"<ul>{lis}</ul>"

def render_alternatives(alts):
    if not alts:
        return ""
    items = []
    for a in alts:
        name = e(a.get("name",""))
        url  = a.get("url","")
        cost = a.get("cost","")
        note = e(a.get("notes",""))
        link = f'<a href="{e(url)}" target="_blank" rel="noopener">{name}</a>' if url else f"<strong>{name}</strong>"
        cost_str = f' <span class="alt-cost">{e(cost)}</span>' if cost else ""
        items.append(f"<li>{link}{cost_str} — {note}</li>")
    return "<ul>" + "".join(items) + "</ul>"

def render_steps(steps):
    if not steps:
        return ""
    lis = "".join(f"<li>{e(s)}</li>" for s in steps)
    return f"<ol>{lis}</ol>"

def nav_html(active_slug=""):
    return f'''<header>
  <nav class="site-nav">
    <a href="/" class="nav-logo">DitchTheMega</a>
    <a href="/amazon/" class="nav-link">Amazon Guide</a>
    <a href="/about/" class="nav-link">About</a>
  </nav>
</header>'''

def footer_html():
    return f'''<footer>
  <p>Free. Open source. No tracking. No affiliate links.</p>
  <p>Part of the data sovereignty toolkit: 
     <a href="https://cancelfreely.com">CancelFreely</a> &middot; 
     <a href="https://deletefreely.com">DeleteFreely</a>
  </p>
  <p><a href="https://github.com/maestrokling/ditchthemega">GitHub</a> &middot; <a href="/about/">About</a></p>
</footer>'''

def page_shell(title, description, canonical, content, extra_head=""):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <link rel="canonical" href="{e(canonical)}">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{e(canonical)}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary">
  <link rel="stylesheet" href="/style.css">
  {extra_head}
</head>
<body>
{nav_html()}
<main>
{content}
</main>
{footer_html()}
</body>
</html>'''

def build_service_page(svc):
    slug = svc["slug"]
    title = svc["title"]
    subtitle = svc.get("subtitle", "")
    difficulty = svc.get("difficulty", 0)
    diff_label = DIFF_LABEL[difficulty] if difficulty else ""
    diff_class = DIFF_CLASS[difficulty] if difficulty else ""

    sections = []

    # Hero
    sections.append(f'''<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/amazon/">Amazon</a> › {e(title)}</div>
  <h1>{e(title)}</h1>
  <p class="subtitle">{e(subtitle)}</p>
  {"" if not difficulty else f'<span class="difficulty {diff_class}">{diff_label} migration</span>'}
</div>''')

    # What it is
    if svc.get("what_it_is"):
        sections.append(f'<section class="card"><h2>What it is</h2><p>{e(svc["what_it_is"])}</p></section>')

    # Privacy case
    if svc.get("privacy_case"):
        sections.append(f'<section class="card card-privacy"><h2>⚠️ The privacy case</h2><p>{e(svc["privacy_case"])}</p></section>')

    # DRM note
    if svc.get("drm_note"):
        sections.append(f'<section class="card card-note"><h2>Legal note</h2><p>{e(svc["drm_note"])}</p></section>')

    # Honest assessment
    if svc.get("honest_assessment"):
        sections.append(f'<section class="card card-honest"><h2>Honest assessment</h2><p>{e(svc["honest_assessment"])}</p></section>')

    # What you lose
    if svc.get("what_you_lose"):
        sections.append(f'<section class="card"><h2>What you lose</h2>{render_list(svc["what_you_lose"])}</section>')

    # What Amazon has (data export page)
    if svc.get("what_amazon_has"):
        items = svc["what_amazon_has"]
        sections.append(f'<section class="card"><h2>What Amazon has on you</h2>{render_list(items)}</section>')

    # Real losses (what-you-lose page)
    if svc.get("real_losses"):
        rl_html = ""
        for loss in svc["real_losses"]:
            rl_html += f'<div class="loss-item"><h3>{e(loss["title"])}</h3><p>{e(loss["detail"])}</p></div>'
        sections.append(f'<section class="card"><h2>What Amazon genuinely does better</h2>{rl_html}</section>')

    if svc.get("the_honest_frame"):
        sections.append(f'<section class="card card-honest"><h2>The honest frame</h2><p>{e(svc["the_honest_frame"])}</p></section>')

    if svc.get("what_changes_over_time"):
        sections.append(f'<section class="card"><h2>What changes over time</h2><p>{e(svc["what_changes_over_time"])}</p></section>')

    # Data to export
    if svc.get("data_to_export"):
        sections.append(f'<section class="card"><h2>Data to export first</h2>{render_list(svc["data_to_export"])}</section>')

    # How to backup (Kindle)
    if svc.get("how_to_backup_legally"):
        sections.append(f'<section class="card"><h2>How to back up your library</h2>{render_list(svc["how_to_backup_legally"])}</section>')

    # How to request data
    if svc.get("how_to_request"):
        sections.append(f'<section class="card"><h2>How to request your data</h2>{render_list(svc["how_to_request"])}</section>')

    if svc.get("how_to_delete"):
        sections.append(f'<section class="card"><h2>How to delete your data</h2>{render_list(svc["how_to_delete"])}</section>')

    if svc.get("account_deletion_warning"):
        sections.append(f'<section class="card card-note"><h2>⚠️ Before you close your account</h2><p>{e(svc["account_deletion_warning"])}</p></section>')

    # How to cancel
    if svc.get("how_to_cancel"):
        cf = svc.get("cancelfreely_link","")
        cf_link = f' <a href="{e(cf)}" class="cf-link" target="_blank" rel="noopener">→ Step-by-step guide on CancelFreely</a>' if cf else ""
        sections.append(f'<section class="card"><h2>How to cancel{cf_link}</h2>{render_list(svc["how_to_cancel"])}</section>')

    # How to transfer (pharmacy)
    if svc.get("how_to_transfer"):
        sections.append(f'<section class="card"><h2>How to transfer prescriptions</h2>{render_list(svc["how_to_transfer"])}</section>')

    # Alternatives (simple list)
    if svc.get("alternatives"):
        sections.append(f'<section class="card"><h2>Alternatives</h2>{render_alternatives(svc["alternatives"])}</section>')

    # Alternatives by category
    if svc.get("alternatives_by_category"):
        alts_html = ""
        for cat in svc["alternatives_by_category"]:
            alts_html += f'<h3>{e(cat["category"])}</h3>{render_alternatives(cat["options"])}'
        sections.append(f'<section class="card"><h2>Alternatives by category</h2>{alts_html}</section>')

    if svc.get("alternatives_by_type"):
        alts_html = ""
        for cat in svc["alternatives_by_type"]:
            alts_html += f'<h3>{e(cat["type"])}</h3>{render_alternatives(cat["options"])}'
        sections.append(f'<section class="card"><h2>Alternatives</h2>{alts_html}</section>')

    # Device migration (Alexa)
    if svc.get("device_migration"):
        dm_html = ""
        for d in svc["device_migration"]:
            dm_html += f'<div class="device-item"><strong>{e(d["category"])}</strong><p>{e(d["notes"])}</p></div>'
        sections.append(f'<section class="card"><h2>Device-by-device migration</h2>{dm_html}</section>')

    # Migration steps
    if svc.get("migration_steps"):
        sections.append(f'<section class="card card-steps"><h2>Migration steps</h2>{render_steps(svc["migration_steps"])}</section>')

    content = "\n".join(sections)
    canonical = f"{SITE_URL}/amazon/{slug}/"
    description = subtitle or f"How to leave Amazon {title} — alternatives, data export, and migration guide."
    return page_shell(f"{title} — DitchTheMega", description, canonical, content)

def build_sellers_hub(services):
    seller_svcs = [s for s in services if s.get("category") == "seller"]
    cards = ""
    for svc in seller_svcs:
        slug = svc["slug"]
        title = svc["title"]
        subtitle = svc.get("subtitle","")
        diff = svc.get("difficulty",0)
        diff_label = DIFF_LABEL[diff] if diff else ""
        diff_class = DIFF_CLASS[diff] if diff else "d1"
        cards += f'''<a href="/amazon/{slug}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(title)}</h2>
    <p>{e(subtitle)}</p>
    {"" if not diff else f'<span class="difficulty {diff_class}">{diff_label}</span>'}
  </div>
</a>'''

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/amazon/">Amazon</a> › For Sellers</div>
  <h1>Amazon Seller Exit Guide</h1>
  <p class="subtitle">Amazon's designed its seller program to maximize your dependency.<br>
  Here's how to build your way out — without killing your revenue overnight.</p>
</div>
<div class="service-grid">
{cards}
</div>'''

    return page_shell(
        "Amazon Seller Exit Guide — DitchTheMega",
        "Free guides to reducing Amazon seller dependency. Direct channels, alternative marketplaces, fulfillment options, and financial comparisons.",
        f"{SITE_URL}/amazon/sellers/",
        content
    )

def build_amazon_hub(services):
    # Filter to non-meta, non-seller services
    cards = ""
    for svc in services:
        if svc.get("category") in ("meta", "seller"):
            continue
        slug = svc["slug"]
        title = svc["title"]
        subtitle = svc.get("subtitle","")
        diff = svc.get("difficulty",0)
        diff_label = DIFF_LABEL[diff] if diff else ""
        diff_class = DIFF_CLASS[diff] if diff else "d1"
        cards += f'''<a href="/amazon/{slug}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(title)}</h2>
    <p>{e(subtitle)}</p>
    {"" if not diff else f'<span class="difficulty {diff_class}">{diff_label}</span>'}
  </div>
</a>'''

    # Sellers card
    cards += f'''<a href="/amazon/sellers/" class="service-card">
  <div class="service-card-inner">
    <h2>For Sellers</h2>
    <p>Reduce Amazon dependency without killing revenue overnight</p>
  </div>
</a>'''

    # What you lose card
    cards += f'''<a href="/amazon/what-you-lose/" class="service-card card-honest-link">
  <div class="service-card-inner">
    <h2>What You Actually Lose</h2>
    <p>The honest page no other guide writes</p>
  </div>
</a>'''

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Amazon</div>
  <h1>Leaving the Amazon Ecosystem</h1>
  <p class="subtitle">Amazon isn't a store. It's twenty services wearing a trench coat.<br>
  Here's how to take it apart, service by service.</p>
</div>
<div class="service-grid">
{cards}
</div>'''

    return page_shell(
        "Leave Amazon — Complete Exit Guide | DitchTheMega",
        "Practical, step-by-step guides to leaving every Amazon service. Kindle, Alexa, Ring, Prime, Photos, and more. Free. No tracking.",
        f"{SITE_URL}/amazon/",
        content
    )

def build_landing():
    content = f'''<div class="landing-hero">
  <h1>Big Tech made it easy to move in.<br>We make it possible to move out.</h1>
  <p class="landing-sub">Practical, honest guides to leaving the platforms that have made themselves load-bearing in your life.<br>No lectures. No ideology. Just the map.</p>
</div>
<div class="doors-grid">
  <a href="/amazon/" class="door door-open">
    <div class="door-inner">
      <span class="door-icon">📦</span>
      <h2>Amazon</h2>
      <p>Shopping, Prime, Kindle, Alexa, Ring, Photos, and more</p>
      <span class="door-status open">Guide available →</span>
    </div>
  </a>
  <div class="door door-coming">
    <div class="door-inner">
      <span class="door-icon">🔍</span>
      <h2>Google</h2>
      <p>Search, Gmail, Maps, YouTube, Android, Drive</p>
      <span class="door-status coming">Coming soon</span>
    </div>
  </div>
  <div class="door door-coming">
    <div class="door-inner">
      <span class="door-icon">👤</span>
      <h2>Meta</h2>
      <p>Facebook, Instagram, WhatsApp, Threads</p>
      <span class="door-status coming">Coming soon</span>
    </div>
  </div>
  <div class="door door-coming">
    <div class="door-inner">
      <span class="door-icon">🍎</span>
      <h2>Apple</h2>
      <p>iCloud, App Store, Apple One, Find My</p>
      <span class="door-status coming">Coming soon</span>
    </div>
  </div>
  <div class="door door-coming">
    <div class="door-inner">
      <span class="door-icon">🪟</span>
      <h2>Microsoft</h2>
      <p>Windows, Office 365, LinkedIn, GitHub</p>
      <span class="door-status coming">Coming soon</span>
    </div>
  </div>
</div>
<div class="philosophy">
  <p>No data collected. No affiliate links. No paid recommendations. 
  <a href="/about/">Why we built this →</a></p>
</div>'''

    return page_shell(
        "DitchTheMega — Leave Big Tech Ecosystems",
        "Practical guides to leaving Amazon, Google, Meta, Apple, and Microsoft. Step-by-step. Honest about tradeoffs. Free.",
        f"{SITE_URL}/",
        content
    )

def build_about():
    content = '''<div class="page-hero">
  <h1>About DitchTheMega</h1>
</div>
<section class="card">
  <h2>What this is</h2>
  <p>A free, practical guide to extracting yourself from Big Tech ecosystems. Not a boycott manifesto. Not a moral lecture. A technical and practical guide that assumes you've already decided to reduce your dependence and need to know how.</p>
  <p>The positioning: <em>You've decided to leave. Here's the map.</em></p>
</section>
<section class="card">
  <h2>What this isn't</h2>
  <p>This site doesn't tell you <em>why</em> to leave Amazon. There are a hundred articles and a Netflix documentary for that. This site tells you <em>how</em>. Service by service. With real alternatives and honest assessments of what you gain and lose.</p>
</section>
<section class="card">
  <h2>Principles</h2>
  <ul>
    <li><strong>No data collection.</strong> We don't track you. We don't have analytics. We don't use cookies.</li>
    <li><strong>No affiliate links.</strong> Every alternative listed is listed because it's good, not because we get paid.</li>
    <li><strong>No paid recommendations.</strong> No one pays to be listed here.</li>
    <li><strong>Honest about tradeoffs.</strong> We have a page called <a href="/amazon/what-you-lose/">What You Actually Lose</a>. Amazon does some things well. We say so.</li>
    <li><strong>Open source.</strong> All content is on <a href="https://github.com/maestrokling/ditchthemega" target="_blank" rel="noopener">GitHub</a>. Corrections and additions welcome.</li>
  </ul>
</section>
<section class="card">
  <h2>Part of a portfolio</h2>
  <p>DitchTheMega is part of a small set of data sovereignty tools:</p>
  <ul>
    <li><a href="https://cancelfreely.com">CancelFreely</a> — cancel any subscription, step by step</li>
    <li><a href="https://deletefreely.com">DeleteFreely</a> — delete your data from major companies</li>
    <li>DitchTheMega — leave the most entrenched ecosystems</li>
  </ul>
</section>'''

    return page_shell(
        "About — DitchTheMega",
        "Why we built DitchTheMega. No data collection, no affiliate links, honest about tradeoffs.",
        f"{SITE_URL}/about/",
        content
    )

def build_sitemap(services):
    urls = [SITE_URL + "/", SITE_URL + "/amazon/", SITE_URL + "/amazon/sellers/", SITE_URL + "/about/"]
    for svc in services:
        urls.append(f"{SITE_URL}/amazon/{svc['slug']}/")
    today = date.today().isoformat()
    items = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>'''

def main():
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    services = load_services()
    print(f"Loaded {len(services)} services")

    # Landing page
    with open(f"{PUBLIC_DIR}/index.html", "w") as f:
        f.write(build_landing())
    print("Built: index.html")

    # Amazon hub
    os.makedirs(f"{PUBLIC_DIR}/amazon", exist_ok=True)
    with open(f"{PUBLIC_DIR}/amazon/index.html", "w") as f:
        f.write(build_amazon_hub(services))
    print("Built: amazon/index.html")

    # About
    os.makedirs(f"{PUBLIC_DIR}/about", exist_ok=True)
    with open(f"{PUBLIC_DIR}/about/index.html", "w") as f:
        f.write(build_about())
    print("Built: about/index.html")

    # Sellers hub
    os.makedirs(f"{PUBLIC_DIR}/amazon/sellers", exist_ok=True)
    with open(f"{PUBLIC_DIR}/amazon/sellers/index.html", "w") as f:
        f.write(build_sellers_hub(services))
    print("Built: amazon/sellers/index.html")

    # Service pages
    for svc in services:
        slug = svc["slug"]
        out_dir = f"{PUBLIC_DIR}/amazon/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(build_service_page(svc))
        print(f"Built: amazon/{slug}/index.html")

    # Sitemap (add sellers hub)
    with open(f"{PUBLIC_DIR}/sitemap.xml", "w") as f:
        f.write(build_sitemap(services))
    print("Built: sitemap.xml")

    # Robots.txt
    with open(f"{PUBLIC_DIR}/robots.txt", "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    print("Built: robots.txt")

    print(f"\nDone. {len(services) + 3} pages generated in {PUBLIC_DIR}/")

if __name__ == "__main__":
    main()
