#!/usr/bin/env python3
"""
DitchTheMega build script
Reads content/services/*.yaml → generates public/ static site
Run: python3 build.py
"""
import yaml, os, glob, html, shutil, json
from datetime import date

# ── Affiliate Links ───────────────────────────────────────────────────────────
# Replace PLACEHOLDER values with your real affiliate URLs once approved.
# Keys are matched against alternative 'url' fields (partial match on domain).
# Build script will use the affiliate URL when a match is found.
# Format: "domain-fragment": "full-affiliate-url"
AFFILIATE_LINKS = {
    # ShareASale programs (get IDs from shareasale.com after approval)
    "kobo.com":          "PLACEHOLDER_kobo_shareasale",
    "libro.fm":          "PLACEHOLDER_librofm_shareasale",
    "bookshop.org":      "PLACEHOLDER_bookshop_shareasale",
    "chewy.com":         "PLACEHOLDER_chewy_shareasale",
    "grove.co":          "PLACEHOLDER_grove_shareasale",
    "thrivemarket.com":  "PLACEHOLDER_thrive_shareasale",
    "chirpbooks.com":    "PLACEHOLDER_chirp_shareasale",
    "iherb.com":         "PLACEHOLDER_iherb_shareasale",
    "thredup.com":       "PLACEHOLDER_thredup_shareasale",
    # Impact.com / direct programs
    "shopify.com":       "PLACEHOLDER_shopify_impact",       # $150/merchant
    "shipbob.com":       "PLACEHOLDER_shipbob_impact",
    "scribd.com":        "PLACEHOLDER_scribd_direct",
    "proton.me":         "PLACEHOLDER_proton_direct",
    # Add more as you join programs
}

def affiliate_url(url):
    """Return affiliate URL if one exists for this domain, else original URL."""
    if not url:
        return url
    for domain, aff_url in AFFILIATE_LINKS.items():
        if domain in url and not aff_url.startswith("PLACEHOLDER"):
            return aff_url
    return url

def is_affiliate(url):
    """Return True if this URL has a live (non-placeholder) affiliate link."""
    if not url:
        return False
    for domain, aff_url in AFFILIATE_LINKS.items():
        if domain in url and not aff_url.startswith("PLACEHOLDER"):
            return True
    return False

CONTENT_DIR = "content/services"
PUBLIC_DIR  = "public"
SITE_URL    = "https://ditchthemega.com"

# Related guides map: slug → list of (slug, title) to show as related
RELATED = {
    "prime":          [("shopping", "Amazon Shopping"), ("prime-video", "Prime Video"), ("subscribe-save", "Subscribe & Save"), ("data-export", "Your Amazon Data")],
    "shopping":       [("prime", "Amazon Prime"), ("subscribe-save", "Subscribe & Save"), ("what-you-lose", "What You Actually Lose")],
    "kindle":         [("kindle-unlimited", "Kindle Unlimited"), ("audible", "Audible"), ("prime-video", "Prime Video"), ("data-export", "Your Amazon Data")],
    "audible":        [("kindle", "Kindle & Digital Books"), ("prime-video", "Prime Video")],
    "prime-video":    [("prime", "Amazon Prime"), ("audible", "Audible"), ("kindle", "Kindle & Digital Books")],
    "alexa":          [("alexa-deep-dive", "Home Assistant Setup Guide"), ("ring", "Ring Security"), ("photos", "Amazon Photos"), ("data-export", "Your Amazon Data")],
    "ring":           [("alexa", "Alexa & Smart Home"), ("photos", "Amazon Photos"), ("data-export", "Your Amazon Data")],
    "photos":         [("alexa", "Alexa & Smart Home"), ("data-export", "Your Amazon Data")],
    "pharmacy":       [("data-export", "Your Amazon Data"), ("subscribe-save", "Subscribe & Save")],
    "subscribe-save": [("prime", "Amazon Prime"), ("shopping", "Amazon Shopping")],
    "data-export":    [("ring", "Ring Security"), ("alexa", "Alexa & Smart Home"), ("kindle", "Kindle & Digital Books")],
    "what-you-lose":  [("prime", "Amazon Prime"), ("shopping", "Amazon Shopping"), ("alexa", "Alexa & Smart Home")],
    "kindle-unlimited":       [("kindle", "Kindle & Digital Books"), ("audible", "Audible"), ("prime", "Amazon Prime")],
    "alexa-deep-dive":        [("alexa", "Alexa & Smart Home"), ("ring", "Ring Security"), ("data-export", "Your Amazon Data")],
    "seller-migration-timeline": [("seller-assessment", "Seller Assessment"), ("seller-direct-channel", "Building a Direct Channel"), ("seller-financials", "The Financial Reality")],
    "seller-assessment":      [("seller-direct-channel", "Building a Direct Channel"), ("seller-marketplaces", "Alternative Marketplaces"), ("seller-financials", "The Financial Reality"), ("seller-migration-timeline", "90-Day Migration Plan")],
    "seller-direct-channel":  [("seller-assessment", "Seller Assessment"), ("seller-migration-timeline", "90-Day Migration Plan"), ("seller-marketplaces", "Alternative Marketplaces"), ("seller-advertising", "Advertising Without Amazon")],
    "seller-marketplaces":    [("seller-assessment", "Seller Assessment"), ("seller-fulfillment", "Fulfillment Without FBA"), ("seller-financials", "The Financial Reality")],
    "seller-fulfillment":     [("seller-assessment", "Seller Assessment"), ("seller-financials", "The Financial Reality"), ("seller-direct-channel", "Building a Direct Channel")],
    "seller-financials":      [("seller-assessment", "Seller Assessment"), ("seller-fulfillment", "Fulfillment Without FBA"), ("seller-advertising", "Advertising Without Amazon")],
    "seller-advertising":     [("seller-direct-channel", "Building a Direct Channel"), ("seller-marketplaces", "Alternative Marketplaces"), ("seller-financials", "The Financial Reality")],
}

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
    "google":         "Google",
    "apple":          "Apple",
    "meta":           "Meta",
    "microsoft":      "Microsoft",
    "alternatives":   "Alternatives",
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
        dest = affiliate_url(url)
        aff_badge = ' <span class="aff-badge" title="Affiliate link — we may earn a commission">aff</span>' if is_affiliate(url) else ""
        rel = 'noopener sponsored' if is_affiliate(url) else 'noopener'
        link = f'<a href="{e(dest)}" target="_blank" rel="{rel}">{name}</a>{aff_badge}' if url else f"<strong>{name}</strong>"
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
    <a href="/amazon/" class="nav-link">Amazon</a>
    <a href="/google/" class="nav-link">Google</a>
    <a href="/apple/" class="nav-link">Apple</a>
    <a href="/meta/" class="nav-link">Meta</a>
    <a href="/microsoft/" class="nav-link">Microsoft</a>
    <a href="/alternatives/" class="nav-link">Alternatives</a>
    <a href="/about/" class="nav-link">About</a>
  </nav>
</header>'''

def footer_html():
    return f'''<footer>
  <p>Free. Open source. No tracking. <a href="/about/#affiliate">Some links are affiliate links.</a> We only recommend services we'd list anyway.</p>
  <p>Part of the data sovereignty toolkit: 
     <a href="https://cancelfreely.com">CancelFreely</a> &middot; 
     <a href="https://deletefreely.com">DeleteFreely</a>
  </p>
  <p><a href="/about/">About</a> &middot; <a href="https://ko-fi.com/cancelfreely" target="_blank" rel="noopener">☕ Buy us a coffee</a></p>
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

def howto_jsonld(svc):
    steps = svc.get("migration_steps", [])
    if not steps:
        return ""
    step_items = ",\n".join(
        f'{{"@type":"HowToStep","text":{json.dumps(str(s))}}}' for s in steps
    )
    title = svc["title"]
    subtitle = svc.get("subtitle", "")
    schema = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"HowTo",
"name":{json.dumps(f'How to leave {title}')},
"description":{json.dumps(subtitle)},
"step":[{step_items}]}}
</script>'''
    return schema

def breadcrumb_jsonld(title, slug):
    schema = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {{"@type":"ListItem","position":1,"name":"Home","item":"{SITE_URL}/"}},
  {{"@type":"ListItem","position":2,"name":"Amazon","item":"{SITE_URL}/amazon/"}},
  {{"@type":"ListItem","position":3,"name":{json.dumps(title)},"item":"{SITE_URL}/amazon/{slug}/"}}
]}}
</script>'''
    return schema

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

    # Hardware options (alexa-deep-dive)
    if svc.get("hardware_options"):
        hw_html = ""
        for h in svc["hardware_options"]:
            name = e(h.get("name",""))
            cost = e(h.get("cost",""))
            note = e(h.get("notes",""))
            url  = h.get("url","")
            link = f'<a href="{e(url)}" target="_blank" rel="noopener">{name}</a>' if url else f"<strong>{name}</strong>"
            hw_html += f'<div class="device-item"><h3>{link} <span class="alt-cost">{cost}</span></h3><p>{note}</p></div>'
        sections.append(f'<section class="card"><h2>Hardware options</h2>{hw_html}</section>')

    if svc.get("installation_steps"):
        sections.append(f'<section class="card card-steps"><h2>Installation steps</h2>{render_steps(svc["installation_steps"])}</section>')

    if svc.get("migrating_alexa_devices"):
        mad = svc["migrating_alexa_devices"]
        intro = e(mad.get("intro",""))
        devs_html = f"<p>{intro}</p>" if intro else ""
        for d in mad.get("devices",[]):
            devs_html += f'<div class="device-item"><h3>{e(d["type"])}</h3><p>{e(d["notes"])}</p></div>'
        sections.append(f'<section class="card"><h2>Migrating your devices</h2>{devs_html}</section>')

    if svc.get("voice_control_alternatives"):
        sections.append(f'<section class="card"><h2>Voice control alternatives</h2>{render_alternatives(svc["voice_control_alternatives"])}</section>')

    if svc.get("advanced_features"):
        af_html = ""
        for f_ in svc["advanced_features"]:
            af_html += f'<div class="loss-item"><h3>{e(f_["title"])}</h3><p>{e(f_["detail"])}</p></div>'
        sections.append(f'<section class="card"><h2>What Home Assistant can do that Alexa can\'t</h2>{af_html}</section>')

    if svc.get("resources"):
        res_html = ""
        for r in svc["resources"]:
            name = e(r.get("name",""))
            url  = r.get("url","")
            note = e(r.get("notes",""))
            link = f'<a href="{e(url)}" target="_blank" rel="noopener">{name}</a>' if url else f"<strong>{name}</strong>"
            res_html += f"<li>{link}" + (f" — {note}" if note else "") + "</li>"
        sections.append(f'<section class="card"><h2>Resources</h2><ul>{res_html}</ul></section>')

    # Seller migration timeline phases
    if svc.get("guiding_principles"):
        sections.append(f'<section class="card card-honest"><h2>Guiding principles</h2>{render_list(svc["guiding_principles"])}</section>')

    for phase_key, phase_label in [("phase_1","Phase 1"), ("phase_2","Phase 2"), ("phase_3","Phase 3")]:
        if svc.get(phase_key):
            ph = svc[phase_key]
            title_ph = e(ph.get("title", phase_label))
            sub_ph   = e(ph.get("subtitle",""))
            tasks    = ph.get("tasks",[])
            milestone = e(ph.get("milestone",""))
            tasks_html = render_steps(tasks)
            ms_html = f'<p class="alt-cost" style="margin-top:.75rem;"><strong>Milestone:</strong> {milestone}</p>' if milestone else ""
            sections.append(f'<section class="card card-steps"><h2>{title_ph}</h2><p style="color:#94a3b8;margin-bottom:.75rem;">{sub_ph}</p>{tasks_html}{ms_html}</section>')

    if svc.get("what_success_looks_like"):
        sections.append(f'<section class="card card-honest"><h2>What success looks like at day 90</h2>{render_list(svc["what_success_looks_like"])}</section>')

    if svc.get("what_not_to_do"):
        sections.append(f'<section class="card card-privacy"><h2>What not to do</h2>{render_list(svc["what_not_to_do"])}</section>')

    if svc.get("kindle_device_note"):
        sections.append(f'<section class="card card-note"><h2>Note: Kindle device vs. Kindle Unlimited</h2><p>{e(svc["kindle_device_note"])}</p></section>')

    # Related guides
    related = RELATED.get(slug, [])
    if related:
        links = "".join(f'<li><a href="/amazon/{r_slug}/">{e(r_title)}</a></li>' for r_slug, r_title in related)
        sections.append(f'<section class="card"><h2>Related guides</h2><ul>{links}</ul></section>')

    content = "\n".join(sections)
    canonical = f"{SITE_URL}/amazon/{slug}/"
    description = subtitle or f"How to leave Amazon {title} — alternatives, data export, and migration guide."
    extra_head = howto_jsonld(svc) + "\n" + breadcrumb_jsonld(title, slug)
    return page_shell(f"{title} — DitchTheMega", description, canonical, content, extra_head=extra_head)

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

    # Your Content card
    cards += f'''<a href="/amazon/your-content/" class="service-card card-honest-link">
  <div class="service-card-inner">
    <h2>Your Digital Content</h2>
    <p>What you can take, what you lose, and the DRM reality</p>
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
  <a href="/google/" class="door door-open">
    <div class="door-inner">
      <span class="door-icon">🔍</span>
      <h2>Google</h2>
      <p>Search, Gmail, Maps, YouTube, Android, Photos</p>
      <span class="door-status open">Guide available →</span>
    </div>
  </a>
  <a href="/apple/" class="door door-open">
    <div class="door-inner">
      <span class="door-icon">🍎</span>
      <h2>Apple</h2>
      <p>iCloud, iTunes purchases, App Store, Apple Music, Find My</p>
      <span class="door-status open">Guide available →</span>
    </div>
  </a>
  <a href="/meta/" class="door door-open">
    <div class="door-inner">
      <span class="door-icon">👤</span>
      <h2>Meta</h2>
      <p>Facebook, Instagram, WhatsApp, Threads</p>
      <span class="door-status open">Guide available →</span>
    </div>
  </a>

  <a href="/microsoft/" class="door door-open">
    <div class="door-inner">
      <span class="door-icon">🪟</span>
      <h2>Microsoft</h2>
      <p>Windows, Microsoft 365, LinkedIn, OneDrive</p>
      <span class="door-status open">Guide available →</span>
    </div>
  </a>
</div>
<div class="philosophy">
  <p>No data collected. No affiliate links. No paid recommendations. 
  <a href="/about/">Why we built this →</a></p>
</div>'''

    website_schema = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebSite",
"name":"DitchTheMega","url":"{SITE_URL}/",
"description":"Practical guides to leaving Big Tech ecosystems. Free. No tracking."}}
</script>'''
    return page_shell(
        "DitchTheMega — Leave Big Tech Ecosystems",
        "Practical guides to leaving Amazon, Google, Meta, Apple, and Microsoft. Step-by-step. Honest about tradeoffs. Free.",
        f"{SITE_URL}/",
        content,
        extra_head=website_schema
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
    <li><strong>No paid recommendations.</strong> No company pays to be listed. Recommendations exist because they're good.</li>
    <li><strong>Honest about tradeoffs.</strong> We have a page called <a href="/amazon/what-you-lose/">What You Actually Lose</a>. Amazon does some things well. We say so.</li>
    <li><strong>Honest about tradeoffs.</strong> Corrections and improvements are welcome — <a href="/about/#affiliate">see our principles</a>.</li>
  </ul>
</section>
<section class="card" id="affiliate">
  <h2>On affiliate links</h2>
  <p>Some links on this site are affiliate links, marked with a small <span class="aff-badge">aff</span> badge. If you click one and make a purchase, we may earn a commission at no extra cost to you.</p>
  <p>Our policy: <strong>we only link to services we would recommend regardless of whether an affiliate program exists.</strong> The alternative was listed first; the affiliate link was added after. If a better option exists that doesn't have an affiliate program, we list it anyway — you can see this throughout the site.</p>
  <p>Affiliate commissions keep this resource free and fund continued development. CancelFreely and DeleteFreely remain completely affiliate-free. DitchTheMega is different — it's a deeper guide that takes more to maintain, and affiliate revenue is how we sustain it honestly.</p>
</section>
<section class="card">
  <h2>Part of a portfolio</h2>
  <p>DitchTheMega is part of a small set of data sovereignty tools:</p>
  <ul>
    <li><a href="https://cancelfreely.com">CancelFreely</a> — cancel any subscription, step by step. No affiliate links.</li>
    <li><a href="https://deletefreely.com">DeleteFreely</a> — delete your data from major companies. No affiliate links.</li>
    <li>DitchTheMega — leave the most entrenched ecosystems. Affiliate links disclosed.</li>
  </ul>
</section>
<section class="card">
  <h2>Report an error</h2>
  <p>Something wrong or out of date? <a href="mailto:hello@ditchthemega.com">Let us know</a>.</p>
</section>'''

    return page_shell(
        "About — DitchTheMega",
        "Why we built DitchTheMega. No data collection, no affiliate links, honest about tradeoffs.",
        f"{SITE_URL}/about/",
        content
    )

def build_sitemap(services):
    urls = [SITE_URL + "/", SITE_URL + "/amazon/", SITE_URL + "/amazon/sellers/",
            SITE_URL + "/google/", SITE_URL + "/apple/", SITE_URL + "/meta/",
            SITE_URL + "/microsoft/", SITE_URL + "/alternatives/", SITE_URL + "/about/"]
    for svc in services:
        cat = svc.get("category","")
        if cat == "google":
            urls.append(f"{SITE_URL}/google/{svc['slug']}/")
        elif cat == "apple":
            urls.append(f"{SITE_URL}/apple/{svc['slug']}/")
            # also add the custom your-content page
            if svc['slug'] == 'icloud':  # anchor to add once
                urls.append(f"{SITE_URL}/apple/apple-your-content/")
        elif cat == "meta":
            urls.append(f"{SITE_URL}/meta/{svc['slug']}/")
        elif cat == "microsoft":
            urls.append(f"{SITE_URL}/microsoft/{svc['slug']}/")
        elif cat == "alternatives":
            urls.append(f"{SITE_URL}/alternatives/{svc['slug']}/")
        else:
            urls.append(f"{SITE_URL}/amazon/{svc['slug']}/")
    today = date.today().isoformat()
    items = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>'''

def build_google_hub(services):
    google_svcs = [s for s in services if s.get("category") == "google"]
    cards = ""
    for svc in google_svcs:
        slug = svc["slug"]
        title = svc["title"]
        subtitle = svc.get("subtitle","")
        diff = svc.get("difficulty",0)
        diff_label = DIFF_LABEL[diff] if diff else ""
        diff_class = DIFF_CLASS[diff] if diff else "d1"
        cards += f'''<a href="/google/{slug}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(title)}</h2>
    <p>{e(subtitle)}</p>
    {"" if not diff else f'<span class="difficulty {diff_class}">{diff_label}</span>'}
  </div>
</a>'''

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Google</div>
  <h1>Leaving the Google Ecosystem</h1>
  <p class="subtitle">Google isn\'t a search engine. It\'s a surveillance network that also does search, email, maps, video, and your phone.<br>
  Here\'s how to reduce your dependency, service by service.</p>
</div>
<div class="service-grid">
{cards}
</div>'''

    return page_shell(
        "Leave Google — Complete Exit Guide | DitchTheMega",
        "Practical guides to leaving Google services — Gmail, Google Search, Maps, YouTube, Photos, and Android. Free. No tracking.",
        f"{SITE_URL}/google/",
        content
    )

def build_alternatives_hub(services):
    alt_svcs = [s for s in services if s.get("category") == "alternatives"]
    cards = ""
    for svc in alt_svcs:
        slug = svc["slug"]
        title = svc["title"]
        subtitle = svc.get("meta_description","")
        cards += f'''<a href="/alternatives/{slug}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(title)}</h2>
    <p style="font-size:0.8rem;color:#64748b;">{e(subtitle[:100])}</p>
  </div>
</a>'''

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Alternatives</div>
  <h1>Amazon Alternatives by Category</h1>
  <p class="subtitle">The best replacements for Amazon, category by category. Honest comparisons, real prices, genuine tradeoffs.</p>
</div>
<div class="service-grid">
{cards}
</div>'''

    return page_shell(
        "Amazon Alternatives — DitchTheMega",
        "The best Amazon alternatives by category — books, electronics, pet supplies, Prime, and more. Honest comparisons.",
        f"{SITE_URL}/alternatives/",
        content
    )

def build_alternatives_page(svc):
    slug = svc["slug"]
    title = svc["title"]
    description = svc.get("meta_description","")
    intro = svc.get("intro","")
    the_math = svc.get("the_math",{})
    options = svc.get("options",[])
    honest = svc.get("honest_assessment","")
    bottom_line = svc.get("bottom_line","")

    sections = []
    sections.append(f'<div class="page-hero"><div class="breadcrumb"><a href="/">Home</a> › <a href="/alternatives/">Alternatives</a> › {e(title)}</div><h1>{e(title)}</h1></div>')

    if intro:
        sections.append(f'<section class="card"><p>{e(intro)}</p></section>')

    if the_math:
        sections.append(f'<section class="card card-honest"><h2>{e(the_math.get("title",""))}</h2><p>{e(the_math.get("content",""))}</p></section>')

    for opt in options:
        name = e(opt.get("name",""))
        url  = opt.get("url","")
        cost = e(opt.get("cost",""))
        best = e(opt.get("best_for",""))
        price_note = e(opt.get("price_vs_amazon",""))
        shipping = e(opt.get("shipping",""))
        pros = opt.get("pros",[])
        cons = opt.get("cons",[])
        verdict = e(opt.get("verdict",""))
        dest = affiliate_url(url)
        aff = ' <span class="aff-badge" title="Affiliate link">aff</span>' if is_affiliate(url) else ""
        rel = 'noopener sponsored' if is_affiliate(url) else 'noopener'
        link = f'<a href="{e(dest)}" target="_blank" rel="{rel}">{name}</a>{aff}' if url else f'<strong>{name}</strong>'
        cost_str = f' <span class="alt-cost">{cost}</span>' if cost else ""
        pros_html = "".join(f"<li>{e(p)}</li>" for p in pros)
        cons_html = "".join(f"<li>{e(c)}</li>" for c in cons)
        detail = f'<p><strong>Best for:</strong> {best}</p>' if best else ""
        detail += f'<p><strong>Price vs Amazon:</strong> {price_note}</p>' if price_note else ""
        detail += f'<p><strong>Shipping:</strong> {shipping}</p>' if shipping else ""
        detail += f'<ul>{pros_html}</ul>' if pros else ""
        if cons:
            detail += f'<p style="color:#94a3b8;font-size:0.85rem;"><strong>Tradeoffs:</strong></p><ul style="color:#94a3b8;font-size:0.85rem;">{cons_html}</ul>'
        verdict_html = f'<div class="can-wait" style="margin-top:.75rem;"><strong>Verdict:</strong> {verdict}</div>' if verdict else ""
        sections.append(f'<section class="card"><h2>{link}{cost_str}</h2>{detail}{verdict_html}</section>')

    if honest:
        sections.append(f'<section class="card card-honest"><h2>Honest assessment</h2><p>{e(honest)}</p></section>')
    if bottom_line:
        sections.append(f'<section class="card card-steps"><h2>Bottom line</h2><p>{e(bottom_line)}</p></section>')

    return page_shell(
        f"{title} | DitchTheMega",
        description,
        f"{SITE_URL}/alternatives/{slug}/",
        "\n".join(sections)
    )

def build_google_service_page(svc):
    """Google service pages route to /google/slug/ instead of /amazon/slug/"""
    slug = svc["slug"]
    title = svc["title"]
    subtitle = svc.get("subtitle","")
    # Temporarily patch slug for breadcrumb and canonical
    svc["_google"] = True
    sections = []
    sections.append(f'<div class="page-hero"><div class="breadcrumb"><a href="/">Home</a> › <a href="/google/">Google</a> › {e(title)}</div><h1>{e(title)}</h1><p class="subtitle">{e(subtitle)}</p></div>')
    # Reuse the build_service_page logic by temporarily masking category
    orig_cat = svc.get("category")
    svc["category"] = "_skip_"
    # call the inner render logic inline
    if svc.get("privacy_case"):
        sections.append(f'<section class="card card-privacy"><h2>⚠️ The privacy case</h2><p>{e(svc["privacy_case"])}</p></section>')
    if svc.get("what_it_is"):
        sections.append(f'<section class="card"><h2>What it is</h2><p>{e(svc["what_it_is"])}</p></section>')
    if svc.get("what_you_lose"):
        sections.append(f'<section class="card"><h2>What you lose</h2>{render_list(svc["what_you_lose"])}</section>')
    if svc.get("honest_assessment"):
        sections.append(f'<section class="card card-honest"><h2>Honest assessment</h2><p>{e(svc["honest_assessment"])}</p></section>')
    if svc.get("the_privacy_minimum"):
        sections.append(f'<section class="card card-note"><h2>The privacy minimum</h2><p>{e(svc["the_privacy_minimum"])}</p></section>')
    if svc.get("data_to_export"):
        sections.append(f'<section class="card"><h2>Data to export first</h2>{render_list(svc["data_to_export"])}</section>')
    if svc.get("alternatives"):
        sections.append(f'<section class="card"><h2>Alternatives</h2>{render_alternatives(svc["alternatives"])}</section>')
    if svc.get("migration_steps"):
        sections.append(f'<section class="card card-steps"><h2>Migration steps</h2>{render_steps(svc["migration_steps"])}</section>')
    related = RELATED.get(slug, [])
    if related:
        links = "".join(f'<li><a href="/google/{r_slug}/">{e(r_title)}</a></li>' for r_slug, r_title in related)
        sections.append(f'<section class="card"><h2>Related guides</h2><ul>{links}</ul></section>')
    svc["category"] = orig_cat
    description = subtitle or f"How to leave {title} — alternatives, data export, and migration guide."
    return page_shell(
        f"{title} — DitchTheMega",
        description,
        f"{SITE_URL}/google/{slug}/",
        "\n".join(sections)
    )

def build_apple_hub(services):
    apple_svcs = [s for s in services if s.get("category") == "apple"]
    cards = ""
    for svc in apple_svcs:
        slug = svc["slug"]
        title = svc["title"]
        subtitle = svc.get("subtitle","")
        diff = svc.get("difficulty",0)
        diff_label = DIFF_LABEL[diff] if diff else ""
        diff_class = DIFF_CLASS[diff] if diff else "d1"
        cards += f'''<a href="/apple/{slug}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(title)}</h2>
    <p>{e(subtitle)}</p>
    {"" if not diff else f'<span class="difficulty {diff_class}">{diff_label}</span>'}
  </div>
</a>'''

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Apple</div>
  <h1>Leaving the Apple Ecosystem</h1>
  <p class="subtitle">Apple\'s lock-in is different from Amazon\'s or Google\'s. It\'s not about surveillance — it\'s about DRM.<br>
  Content you purchased through Apple cannot legally be transferred to other platforms. Understand what you\'re leaving before you go.</p>
</div>
<div class="card card-caution" style="margin-bottom:1.5rem;">
  <h2>⚠️ Read this before anything else</h2>
  <p>Movies, TV shows, and books purchased through iTunes and Apple Books are DRM-locked to Apple\'s ecosystem.
  There is no legal way to export them to another platform. Audit your purchases before leaving.
  See the <a href="/apple/apple-your-content/">Your Digital Content guide</a> for the full picture.</p>
</div>
<div class="service-grid">
{cards}
</div>'''

    return page_shell(
        "Leave Apple — Complete Exit Guide | DitchTheMega",
        "Practical guides to leaving Apple\'s ecosystem — iCloud, iTunes purchases, App Store, Apple Music, and Apple ID. Honest about DRM tradeoffs.",
        f"{SITE_URL}/apple/",
        content
    )

def build_apple_service_page(svc):
    """Apple service pages route to /apple/slug/"""
    slug = svc["slug"]
    title = svc["title"]
    subtitle = svc.get("subtitle","")
    sections = []
    sections.append(f'<div class="page-hero"><div class="breadcrumb"><a href="/">Home</a> › <a href="/apple/">Apple</a> › {e(title)}</div><h1>{e(title)}</h1><p class="subtitle">{e(subtitle)}</p></div>')

    for field, label, card_class in [
        ("drm_note", "⚠️ DRM — what you can\'t take with you", "card-note"),
        ("the_drm_warning", "⚠️ Before you leave Apple", "card-note"),
        ("the_hard_truth", "⚠️ The hard truth", "card-caution"),
        ("important_distinction", "Important distinction", "card-honest"),
        ("the_purchase_problem", "The purchase problem", "card-caution"),
        ("privacy_case", "Privacy case", "card-privacy"),
    ]:
        if svc.get(field):
            sections.append(f'<section class="card {card_class}"><h2>{label}</h2><p>{e(svc[field])}</p></section>')

    if svc.get("what_it_is"):
        sections.append(f'<section class="card"><h2>What it is</h2><p>{e(svc["what_it_is"])}</p></section>')
    if svc.get("what_icloud_holds"):
        sections.append(f'<section class="card"><h2>What iCloud holds</h2>{render_list(svc["what_icloud_holds"])}</section>')
    if svc.get("what_you_lose"):
        sections.append(f'<section class="card"><h2>What you lose</h2>{render_list(svc["what_you_lose"])}</section>')
    if svc.get("honest_assessment"):
        sections.append(f'<section class="card card-honest"><h2>Honest assessment</h2><p>{e(svc["honest_assessment"])}</p></section>')
    if svc.get("itunes_music_note"):
        sections.append(f'<section class="card card-honest"><h2>iTunes music note</h2><p>{e(svc["itunes_music_note"])}</p></section>')
    if svc.get("itunes_movie_options"):
        sections.append(f'<section class="card"><h2>Your options for iTunes movies</h2>{render_list(svc["itunes_movie_options"])}</section>')
    if svc.get("movies_anywhere"):
        ma = svc["movies_anywhere"]
        sections.append(f'<section class="card card-honest"><h2>Movies Anywhere</h2><p>{e(ma.get("description",""))}</p><p style="color:#94a3b8;font-size:0.85rem;margin-top:.5rem;">{e(ma.get("caveat",""))}</p></section>')
    if svc.get("audit_first"):
        sections.append(f'<section class="card card-steps"><h2>Audit your purchases first</h2><p>{e(svc["audit_first"])}</p></section>')
    if svc.get("cross_platform_apps"):
        sections.append(f'<section class="card"><h2>Cross-platform alternatives exist for most apps</h2><p>{e(svc["cross_platform_apps"])}</p></section>')
    if svc.get("apple_subscriptions_warning"):
        sections.append(f'<section class="card card-caution"><h2>⚠️ Cancel subscriptions before leaving</h2><p>{e(svc["apple_subscriptions_warning"])}</p></section>')
    if svc.get("before_you_close"):
        sections.append(f'<section class="card card-steps"><h2>Before you close your Apple ID</h2>{render_list(svc["before_you_close"])}</section>')
    if svc.get("find_my_privacy"):
        sections.append(f'<section class="card card-honest"><h2>Find My privacy — the good news</h2><p>{e(svc["find_my_privacy"])}</p></section>')
    if svc.get("find_my_alternatives"):
        sections.append(f'<section class="card"><h2>Find My alternatives</h2>{render_list(svc["find_my_alternatives"])}</section>')
    if svc.get("data_to_export"):
        sections.append(f'<section class="card"><h2>Data to export first</h2>{render_list(svc["data_to_export"])}</section>')
    if svc.get("purchased_content_options"):
        sections.append(f'<section class="card"><h2>Purchased content options</h2>{render_list(svc["purchased_content_options"])}</section>')
    if svc.get("migration_strategy"):
        sections.append(f'<section class="card card-steps"><h2>Migration strategy</h2>{render_list(svc["migration_strategy"])}</section>')
    if svc.get("alternatives"):
        sections.append(f'<section class="card"><h2>Alternatives</h2>{render_alternatives(svc["alternatives"])}</section>')
    if svc.get("reducing_google_on_stock_android") or svc.get("note_on_iphone"):
        if svc.get("note_on_iphone"):
            sections.append(f'<section class="card card-note"><h2>Why iPhone isn\'t listed here</h2><p>{e(svc["note_on_iphone"])}</p></section>')
    if svc.get("migration_steps"):
        sections.append(f'<section class="card card-steps"><h2>Migration steps</h2>{render_steps(svc["migration_steps"])}</section>')
    related = RELATED.get(slug, [])
    if related:
        links = "".join(f'<li><a href="/apple/{r_slug}/">{e(r_title)}</a></li>' for r_slug, r_title in related)
        sections.append(f'<section class="card"><h2>Related guides</h2><ul>{links}</ul></section>')
    description = subtitle or f"How to leave {title} — DRM considerations, alternatives, and migration guide."
    return page_shell(
        f"{title} — DitchTheMega",
        description,
        f"{SITE_URL}/apple/{slug}/",
        "\n".join(sections)
    )

def build_generic_hub(services, category, slug_prefix, title, subtitle, description, canonical):
    svcs = [s for s in services if s.get("category") == category]
    cards = ""
    for svc in svcs:
        s_slug = svc["slug"]
        s_title = svc["title"]
        s_subtitle = svc.get("subtitle","")
        diff = svc.get("difficulty",0)
        diff_label = DIFF_LABEL[diff] if diff else ""
        diff_class = DIFF_CLASS[diff] if diff else "d1"
        cards += f'''<a href="/{slug_prefix}/{s_slug}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(s_title)}</h2>
    <p>{e(s_subtitle)}</p>
    {"" if not diff else f'<span class="difficulty {diff_class}">{diff_label}</span>'}
  </div>
</a>'''
    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › {e(title)}</div>
  <h1>{e(title)}</h1>
  <p class="subtitle">{e(subtitle)}</p>
</div>
<div class="service-grid">
{cards}
</div>'''
    return page_shell(f"{title} — DitchTheMega", description, canonical, content)

def build_generic_service_page(svc, slug_prefix):
    slug = svc["slug"]
    title = svc["title"]
    subtitle = svc.get("subtitle","")
    sections = []
    sections.append(f'<div class="page-hero"><div class="breadcrumb"><a href="/">Home</a> › <a href="/{slug_prefix}/">{slug_prefix.capitalize()}</a> › {e(title)}</div><h1>{e(title)}</h1><p class="subtitle">{e(subtitle)}</p></div>')
    if svc.get("privacy_case"):
        sections.append(f'<section class="card card-privacy"><h2>⚠️ Privacy case</h2><p>{e(svc["privacy_case"])}</p></section>')
    if svc.get("what_it_is"):
        sections.append(f'<section class="card"><h2>What it is</h2><p>{e(svc["what_it_is"])}</p></section>')
    if svc.get("what_you_lose"):
        sections.append(f'<section class="card"><h2>What you lose</h2>{render_list(svc["what_you_lose"])}</section>')
    if svc.get("honest_assessment"):
        sections.append(f'<section class="card card-honest"><h2>Honest assessment</h2><p>{e(svc["honest_assessment"])}</p></section>')
    if svc.get("reducing_linkedin_exposure"):
        sections.append(f'<section class="card card-note"><h2>If you\'re not ready to leave entirely</h2>{render_list(svc["reducing_linkedin_exposure"])}</section>')
    if svc.get("reducing_privacy_on_windows"):
        sections.append(f'<section class="card card-note"><h2>Reduce data collection without switching OS</h2>{render_list(svc["reducing_privacy_on_windows"])}</section>')
    if svc.get("data_to_export"):
        sections.append(f'<section class="card"><h2>Data to export first</h2>{render_list(svc["data_to_export"])}</section>')
    if svc.get("account_deletion"):
        sections.append(f'<section class="card"><h2>Deleting your account</h2>{render_list(svc["account_deletion"])}</section>')
    if svc.get("alternatives"):
        sections.append(f'<section class="card"><h2>Alternatives</h2>{render_alternatives(svc["alternatives"])}</section>')
    if svc.get("migration_steps"):
        sections.append(f'<section class="card card-steps"><h2>Migration steps</h2>{render_steps(svc["migration_steps"])}</section>')
    related = RELATED.get(slug, [])
    if related:
        prefix = slug_prefix
        links = "".join(f'<li><a href="/{prefix}/{r_slug}/">{e(r_title)}</a></li>' for r_slug, r_title in related)
        sections.append(f'<section class="card"><h2>Related guides</h2><ul>{links}</ul></section>')
    description = subtitle or f"How to leave {title} — privacy case, alternatives, and migration guide."
    return page_shell(f"{title} — DitchTheMega", description, f"{SITE_URL}/{slug_prefix}/{slug}/", "\n".join(sections))

def build_your_content_page(ecosystem, slug_prefix, title_subtitle, intro, sections_html):
    content = f'''
<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/{slug_prefix}/">{ecosystem}</a> › Your Digital Content</div>
  <h1>Your Digital Content</h1>
  <p class="subtitle">{title_subtitle}</p>
</div>
{intro}
{sections_html}
'''
    return page_shell(
        f"Your {ecosystem} Digital Content | DitchTheMega",
        f"What you can take from {ecosystem}\'s ecosystem, what you can replace, and what you effectively lose.",
        f"{SITE_URL}/{slug_prefix}/your-content/",
        content
    )

def build_google_your_content():
    intro = '''<div class="card card-honest">
  <p>Google Takeout is one of the most comprehensive data export tools any tech company offers. Your content is mostly exportable. The problem isn\'t that Google traps your content. <strong>The problem is that Google keeps a shadow profile of everything you\'ve ever done — and that profile is not in the export.</strong></p>
  <p>Leaving Google is less about taking your content and more about cutting the data pipeline.</p>
</div>'''

    sections = '''<h2>Section 1 — Content you own and can export</h2>
<p style="margin-bottom:1rem;color:#94a3b8;font-size:0.9rem;">Start with <strong>takeout.google.com</strong> — one of the best data export tools in the industry.</p>

<section class="card">
  <h2>Gmail</h2>
  <ul>
    <li><strong>Google Takeout:</strong> select Gmail → exports as MBOX file (standard format, imports anywhere)</li>
    <li><strong>IMAP:</strong> connect any email client (Thunderbird, Proton Bridge) → drag mail to new provider</li>
    <li><strong>Direct migration:</strong> Proton Mail, Fastmail, and Tuta offer built-in Gmail import tools</li>
  </ul>
  <p class="card" style="background:#1a1205;border-color:#78350f;padding:.75rem 1rem;margin-top:.75rem;"><strong>Critical step people forget:</strong> Your Gmail address is probably the login for dozens of other services. Update every service that uses your Gmail before you stop using it. This takes weeks. Start early.</p>
</section>

<section class="card">
  <h2>Google Photos</h2>
  <p>Google Takeout exports your library as ZIP files with original JPEG, PNG, HEIC, MP4 files.</p>
  <p><strong>Known issue:</strong> Takeout stores photo metadata (dates, locations, album info) in separate JSON sidecar files rather than embedded in the image EXIF. Without merging these, your exported photos lose date and location data. Use ExifTool or Google Photos Takeout Helper to merge them before importing elsewhere. Worth knowing before you export.</p>
</section>

<section class="card">
  <h2>Google Drive, Calendar, Contacts</h2>
  <ul>
    <li><strong>Drive:</strong> Takeout exports everything. Google-native formats convert automatically: Docs → .docx, Sheets → .xlsx, Slides → .pptx. Verify complex documents after conversion.</li>
    <li><strong>Calendar:</strong> Exports as .ics files — universal standard. Imports into any calendar app.</li>
    <li><strong>Contacts:</strong> contacts.google.com → Export → vCard. Imports anywhere.</li>
  </ul>
</section>

<section class="card">
  <h2>Location History</h2>
  <p>Takeout exports your complete location history — everywhere you\'ve been, when, and how long. Download it if you want a personal record. Then <strong>delete it from Google\'s servers</strong> at myactivity.google.com.</p>
  <p>This is one of the most sensitive datasets any company holds about you. Make a deliberate decision about whether you want Google to keep it.</p>
</section>

<h2>Section 2 — Content you can replace but not transfer</h2>

<section class="card">
  <h2>Google Play Books</h2>
  <p><strong>Good news:</strong> Google uses Adobe DRM on most titles, not proprietary Google DRM. Some titles are DRM-free (publisher dependent). This makes Google\'s ebook store more portable than Amazon\'s or Apple\'s.</p>
  <ul>
    <li><strong>DRM-free titles:</strong> Download the EPUB. Works everywhere. Move to Calibre, Kobo, or any reading app.</li>
    <li><strong>Adobe DRM titles:</strong> Readable in any Adobe Digital Editions-compatible app — Kobo, Nook, various third-party readers. Not locked to Google.</li>
  </ul>
  <p style="color:#94a3b8;font-size:0.875rem;">Overall: Google Play Books is the least locked-in ebook ecosystem among major platforms. If you buy ebooks from a major retailer, Google is the most portable choice.</p>
</section>

<section class="card">
  <h2>Google Play Movies</h2>
  <p>Google participates in Movies Anywhere. Link your Google account at moviesanywhere.com — eligible purchases become accessible on Apple TV, Amazon, Vudu, and other linked platforms.</p>
  <p>Google\'s movie ecosystem is the most portable of the three major platforms thanks to Movies Anywhere. If you buy digital movies, Google is the best starting point for cross-platform access.</p>
</section>

<h2>Section 3 — Google\'s real lock-in isn\'t content</h2>

<section class="card card-privacy">
  <h2>The data shadow you can\'t export</h2>
  <p>Google knows what you search for, watch, where you go, who you email, what you buy, what ads you click, what questions you ask at 3 AM, what symptoms you look up, what routes you drive, what restaurants you visit. Your content is exportable. <strong>Your data shadow is not.</strong></p>
  <p>You can download your location history, but Google\'s model of your behavior — the advertising profile, the prediction engine, the inferences drawn from fifteen years of search queries — is not in the export.</p>
  <p>You can export your files in an afternoon. Disentangling your life from Google\'s surveillance infrastructure takes months. Both are worth doing.</p>
  <p>The main <a href="/google/">Google exit guide</a> covers the data pipeline: replacing Chrome, search, Gmail, Maps, and Android\'s default Google integration.</p>
</section>

<section class="card">
  <h2>Related guides</h2>
  <ul>
    <li><a href="/google/gmail/">Gmail — migration guide</a></li>
    <li><a href="/google/google-photos/">Google Photos — export and alternatives</a></li>
    <li><a href="/google/google-search/">Google Search — breaking the habit</a></li>
    <li><a href="/amazon/your-content/">Compare: Amazon content lock-in</a></li>
    <li><a href="/apple/apple-your-content/">Compare: Apple content lock-in</a></li>
  </ul>
</section>'''

    return build_your_content_page("Google", "google",
        "What you can take, what you can replace, and why Google\'s real lock-in isn\'t your content.",
        intro, sections)

def build_meta_your_content():
    intro = '''<div class="card card-honest">
  <p>Meta doesn\'t sell you ebooks, movies, or music. Meta\'s product is you.</p>
  <p>Your \"content\" on Meta is your posts, photos, messages, friendships, group memberships, memories, and — if you\'ve been on Facebook since college — sixteen years of your life. <strong>Almost all of it is exportable. The technical lock-in is minimal. The emotional and social lock-in is enormous.</strong></p>
</div>'''

    sections = '''<h2>Section 1 — Content you own and can export</h2>

<section class="card">
  <h2>Facebook data</h2>
  <p>facebook.com/dyi (Download Your Information). Choose all time, JSON format, high quality media.</p>
  <p>What\'s included: every post, photo, video, comment, every Messenger message including group chats, your friends list, every event, marketplace activity, pages liked, groups, check-ins, every ad you\'ve clicked, and — often startlingly — every advertiser who uploaded your contact information to target you.</p>
  <p><strong>Allow days for large archives.</strong> Request before you\'re ready to delete, not the same day.</p>
</section>

<section class="card">
  <h2>Instagram data</h2>
  <p>Instagram app → Settings → Your Activity → Download Your Information. Includes every photo/video you posted, Reels, DMs, followers/following list, comments, and likes.</p>
</section>

<section class="card">
  <h2>WhatsApp data</h2>
  <p>Settings → Chats → Export Chat. One conversation at a time — there is no bulk export. This is a deliberate design choice. You get text files with attached media (photos, videos, voice messages) in standard formats.</p>
</section>

<section class="card card-caution">
  <h2>Messenger conversations with people who have died</h2>
  <p>If you have Messenger conversations with someone who is no longer alive, export them before deleting your account. Once your account is deleted, these conversations are gone. This content may have deep personal value and exists nowhere else.</p>
</section>

<h2>Section 2 — What you can\'t take with you</h2>

<section class="card">
  <h2>Your social graph</h2>
  <p>You can export your friends list as names and profile URLs. You cannot import a social graph into another platform. Your connections exist on Facebook because your connections are on Facebook.</p>
  <p><strong>Before deactivating:</strong> collect phone numbers and email addresses of the 30–50 people you actually want to stay in touch with. Not your 847 Facebook friends. The real ones. Get their numbers. Text them.</p>
</section>

<section class="card">
  <h2>Facebook Groups</h2>
  <p>When you leave Facebook, you lose access to groups. For important communities (neighborhood, hobby, support groups), check whether they exist elsewhere — Discord, Reddit, a mailing list. Some people deactivate their profile but keep Messenger and group access. Facebook allows this.</p>
</section>

<section class="card">
  <h2>Meta Quest VR purchases</h2>
  <p>Games purchased through the Meta Quest Store are tied to your Meta account. Delete your account and they\'re gone, no refund.</p>
  <ul>
    <li><strong>Keep your Meta account solely for VR.</strong> You can delete Facebook, Instagram, and WhatsApp while maintaining a Meta account for Quest. VR purchases persist.</li>
    <li><strong>Move to SteamVR</strong> for future PC VR purchases — more stable platform, longer track record.</li>
  </ul>
</section>

<h2>Section 3 — The bigger picture</h2>

<section class="card card-privacy">
  <h2>Meta\'s lock-in is social, not technical</h2>
  <p>Apple locks you in with hardware. Amazon with content. Google with data. <strong>Meta locks you in with people.</strong></p>
  <p>Your family is on Facebook. Your friends are on Instagram. Your group chat is on WhatsApp. The cost of leaving Meta is not lost content or lost purchases. It\'s social friction: the conversations you miss, the events you don\'t hear about, the slow drift from people you used to be connected to effortlessly.</p>
  <p>The 30-day grace period on account deletion means you can find out what you\'d actually lose before the decision is permanent. That\'s worth using.</p>
</section>

<section class="card">
  <h2>Deleting your account correctly</h2>
  <p>Removing all your content and changing your name is not deletion. Your advertising profile still exists. Your data remains. Use the real deletion: <strong>facebook.com/help/delete_account</strong>. 30-day grace period. Deletion completes in up to 90 days. Some data (messages you sent to others) may persist in the other person\'s account.</p>
</section>

<section class="card">
  <h2>Related guides</h2>
  <ul>
    <li><a href="/meta/facebook/">Facebook — migration guide</a></li>
    <li><a href="/meta/instagram/">Instagram — alternatives</a></li>
    <li><a href="/meta/whatsapp/">WhatsApp — Signal migration</a></li>
    <li><a href="/amazon/your-content/">Compare: Amazon content lock-in</a></li>
  </ul>
</section>'''

    return build_your_content_page("Meta", "meta",
        "Your posts and photos are exportable. Your social graph is Meta\'s.",
        intro, sections)

def build_microsoft_your_content():
    intro = '''<div class="card card-honest">
  <p>Microsoft\'s consumer content lock-in is the lightest of any major tech company. Your Office documents are standard formats. Your email is IMAP. Your OneDrive files are just files. <strong>If you\'re going to leave a mega, this is the easy one on the content side.</strong></p>
  <p>Where Microsoft locks you in is workflow, not content — especially in enterprise contexts. This page covers the consumer side.</p>
</div>'''

    sections = '''<h2>Section 1 — Content you own and can export</h2>

<section class="card">
  <h2>OneDrive files</h2>
  <p>Your files sync to a local folder on your computer. Copy them. Or download from onedrive.live.com. Or use account.microsoft.com/privacy for a full data export.</p>
  <p>Standard files. No DRM. No conversion needed.</p>
</section>

<section class="card">
  <h2>Outlook email, contacts, and calendar</h2>
  <ul>
    <li><strong>Email:</strong> IMAP access from any email client. Same as Gmail — connect, sync, move.</li>
    <li><strong>Contacts:</strong> outlook.live.com → People → Manage → Export contacts (CSV)</li>
    <li><strong>Calendar:</strong> outlook.live.com → Calendar → Settings → publish calendar (ICS)</li>
  </ul>
  <p>Same warning as Gmail: if your @outlook.com, @hotmail.com, or @live.com address is used to log into other services, update those logins before you stop using it.</p>
</section>

<section class="card">
  <h2>OneNote</h2>
  <p>OneNote desktop (Windows): File → Export. Choose notebook/section/page. Export as PDF, Word, or .onepkg. The notebook structure (sections, pages, sub-pages) doesn\'t map cleanly to other note apps. Plan for manual migration. This is one of Microsoft\'s genuinely weak export paths.</p>
  <p style="color:#94a3b8;font-size:0.875rem;">Third-party tools exist to convert OneNote to Markdown for import into Obsidian, Joplin, or Notion. Worth researching if you have extensive notebooks.</p>
</section>

<h2>Section 2 — Microsoft 365 cancellation</h2>

<section class="card">
  <h2>What happens when you cancel Microsoft 365</h2>
  <ul>
    <li>Office apps revert to read-only mode — you can view but not edit</li>
    <li>OneDrive storage drops from 1TB to 5GB (files over 5GB become read-only; not immediately deleted)</li>
    <li>Outlook continues working as a free email client with ads</li>
  </ul>
  <p>Replacements: <a href="https://libreoffice.org" target="_blank" rel="noopener">LibreOffice</a> (free, handles 90%+ of Office documents), <a href="https://onlyoffice.com" target="_blank" rel="noopener">OnlyOffice</a> (higher format fidelity), Google Docs (cloud-based), <a href="https://cryptpad.fr" target="_blank" rel="noopener">CryptPad</a> (encrypted, open source).</p>
</section>

<h2>Section 3 — Xbox and game purchases</h2>

<section class="card">
  <h2>Xbox digital games</h2>
  <p>Game purchases are tied to your Microsoft account. Keep your account (free) and your library persists. Delete your account and your library is permanently inaccessible.</p>
  <ul>
    <li><strong>For PC gaming going forward:</strong> <a href="https://gog.com" target="_blank" rel="noopener">GOG.com</a> sells DRM-free games. You download the installer. It runs without any account or online check. You own it like a file on your hard drive.</li>
    <li><strong>Microsoft Store movies:</strong> Microsoft participates in Movies Anywhere. Link your account at moviesanywhere.com — eligible purchases become accessible on Apple TV, Amazon, Google, and Vudu.</li>
    <li><strong>Minecraft Java Edition:</strong> Worlds are local save files. Fully portable. Copy the saves folder.</li>
  </ul>
</section>

<section class="card">
  <h2>The real Microsoft lock-in</h2>
  <p>Consumer Microsoft lock-in is the gentlest of the five. The real lock-in is enterprise: Active Directory, Exchange, Teams, SharePoint, Azure. These create structural organizational dependency that\'s nearly impossible to replace without a company-wide commitment.</p>
  <p>If you\'re leaving Microsoft as a consumer, this page gives you everything you need. It\'s the easiest exit of the five.</p>
</section>

<section class="card">
  <h2>Related guides</h2>
  <ul>
    <li><a href="/microsoft/office365/">Microsoft 365 — alternatives</a></li>
    <li><a href="/microsoft/onedrive/">OneDrive — replacements</a></li>
    <li><a href="/microsoft/windows/">Windows — alternatives</a></li>
    <li><a href="/amazon/your-content/">Compare: Amazon content lock-in</a></li>
  </ul>
</section>'''

    return build_your_content_page("Microsoft", "microsoft",
        "Your documents and email are portable. Your game library is the only real DRM concern — and it\'s the lightest of the five.",
        intro, sections)

def build_amazon_your_content():
    content = '''
<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/amazon/">Amazon</a> › Your Digital Content</div>
  <h1>Your Digital Content</h1>
  <p class="subtitle">What you can take, what you can replace, and what you effectively lose.</p>
</div>
<div class="card card-caution">
  <p>Amazon\'s content Terms of Use are explicit: <em>"Kindle Content is licensed, not sold, to you by the Content Provider."</em> That sentence has cost millions of people thousands of dollars in content they believed they owned. This page is honest about what that means for you.</p>
</div>

<h2>Section 1 — Content you own and can export</h2>

<section class="card">
  <h2>Amazon Photos</h2>
  <p>Your photos are standard JPEG, HEIC, PNG, and video files. No DRM. These are yours.</p>
  <p><strong>Important:</strong> If you cancel Prime, unlimited photo storage drops to 5GB. Export <em>before</em> you cancel.</p>
  <h3>How to export</h3>
  <ul>
    <li><strong>Desktop app:</strong> Install Amazon Photos for desktop → select all → Download originals. Most reliable for large libraries.</li>
    <li><strong>Web:</strong> amazon.com/photos → select → download</li>
    <li><strong>Data export:</strong> amazon.com/privacycentral → Request your data → select Amazon Photos. Takes days for large libraries.</li>
  </ul>
</section>

<section class="card">
  <h2>Order history and account data</h2>
  <p>amazon.com/privacycentral lets you download everything Amazon has on you: every order ever, search history, browsing history, Alexa voice recordings, Kindle reading data (highlights, notes, bookmarks, reading pace), your advertising profile, wish lists, and reviews.</p>
  <p>Download this at least once even if you\'re not leaving. The scope of what Amazon holds is often startlingly comprehensive.</p>
</section>

<section class="card">
  <h2>Kindle notes and highlights</h2>
  <p>Your annotations are yours even when the underlying book is DRM-locked. Go to read.amazon.com/notebook — every highlight and note you\'ve made is there. Export manually or use a browser extension. Your thoughts, in your words, are always exportable.</p>
  <p style="color:#94a3b8;font-size:0.875rem;">Note: Amazon limits how much of a book you can highlight (typically 10–15%). Your notes (your own words) have no restriction.</p>
</section>

<h2>Section 2 — Content you can replace but not transfer</h2>

<section class="card">
  <h2>Amazon Music (streaming)</h2>
  <p>Playlists and favorites can be migrated via Soundiiz, TuneMyMusic, or FreeYourMusic to Spotify, Apple Music, Tidal, or YouTube Music.</p>
  <p><strong>Exception — MP3 purchases:</strong> If you bought MP3s from Amazon\'s digital music store (before they pivoted to streaming), those are DRM-free files you own. Download them from your Amazon Music library. They\'re yours and they play everywhere. Check your purchase history — you may own more than you think.</p>
</section>

<section class="card">
  <h2>Alexa routines, skills, and smart home configuration</h2>
  <p>None of this is portable. Alexa routines cannot be exported to Google Home or Apple HomeKit. Your smart home configuration, automations, and voice history are tied to your Amazon account.</p>
  <ul>
    <li>Screenshot your routines and automations before leaving — you\'ll rebuild manually in the new ecosystem</li>
    <li>Export your Alexa shopping lists (alexa.amazon.com)</li>
    <li>Download your voice recordings before deleting them (amazon.com/privacycentral)</li>
    <li>Delete all voice recordings: Alexa app → More → Alexa Privacy → Review Voice History → Delete all</li>
  </ul>
  <p style="color:#94a3b8;font-size:0.875rem;">If you have a complex Alexa smart home, this is the most painful migration in the Amazon exit. There is no automated path. Plan for a full weekend to rebuild from scratch in Home Assistant, Google Home, or Apple HomeKit.</p>
</section>

<h2>Section 3 — Content you effectively lose</h2>
<div class="card card-caution">
  <p>Amazon\'s three major DRM platforms — Kindle, Audible, and Prime Video — represent what may be thousands of dollars in purchases you cannot take with you through any legal means.</p>
</div>

<section class="card card-caution">
  <h2>Kindle books</h2>
  <p>Kindle controls approximately 80% of the US ebook market. Many books are Kindle-exclusive or significantly cheaper on Kindle. Amazon built this dominance deliberately. Your entire ebook library may be locked in Amazon\'s proprietary formats (AZW, AZW3, KFX), unreadable outside Kindle apps and hardware.</p>
  <h3>If you keep your Amazon account (free, no Prime needed)</h3>
  <p>Your Kindle library remains accessible through Kindle hardware, the Kindle app (iOS, Android, Mac, Windows), and read.amazon.com in any browser.</p>
  <h3>If you delete your Amazon account</h3>
  <p>Your library is permanently inaccessible. No refund. No export. Gone.</p>
  <h3>Your real options</h3>
  <ul>
    <li><strong>Keep your account but stop buying Kindle books.</strong> Existing library stays. Future purchases go to Kobo or DRM-free sources. Your Kindle library becomes an archive; your active reading moves to platforms you control.</li>
    <li><strong>Move to Kobo or DRM-free sources.</strong> Kobo sells EPUB (some DRM-free, some Adobe DRM). Many publishers sell DRM-free direct. Smashwords and similar platforms are entirely DRM-free. Calibre (free, open-source) manages a cross-platform ebook library.</li>
    <li><strong>Use your library.</strong> Libby/OverDrive covers the majority of what most readers buy. Free with your library card.</li>
    <li><strong>Accept the sunk cost.</strong> If you\'ve spent $500 on Kindle over a decade, that\'s $50/year. You read most of those books once. The question is whether inaccessible books are worth maintaining an Amazon account for. Only you can do that math.</li>
  </ul>
</section>

<section class="card card-caution">
  <h2>Audible audiobooks</h2>
  <p>You paid $15–30 each for audiobooks in Amazon\'s proprietary AAX/AAXC format. You cannot play them outside of Audible\'s app. You cannot convert them. You bought them, and you cannot use them freely.</p>
  <h3>The key distinction</h3>
  <p>The Audible <em>subscription</em> and your Audible <em>purchases</em> are separate. Canceling your Audible subscription does not delete your purchased audiobook library. Cancel the subscription; keep the account; keep your books.</p>
  <h3>Your real options</h3>
  <ul>
    <li><strong>Cancel subscription, keep account.</strong> Your purchased audiobooks remain. This is the pragmatic first step.</li>
    <li><strong>Move future purchases to Libro.fm.</strong> DRM-free MP3 downloads. Supports independent bookstores. Direct ethical and practical alternative to Audible.</li>
    <li><strong>Use Libby for audiobooks.</strong> Free. Legal. Extensive catalog via your library card.</li>
    <li><strong>Use Chirp for discount audiobooks.</strong> Pay-per-book at reduced prices. No subscription. (Note: Chirp uses its own DRM — addresses the Amazon-specific problem, not DRM generally.)</li>
  </ul>
</section>

<section class="card card-caution">
  <h2>Prime Video purchases</h2>
  <p>Same license-not-ownership model as Apple. Purchases remain accessible as long as you have an Amazon account (no Prime required). Delete your account and they\'re gone.</p>
  <p><strong>One important difference from Apple:</strong> Amazon has participated in Movies Anywhere from the start. If you linked your Amazon account to Movies Anywhere, your eligible purchases are already accessible on Apple TV, Google Play, Vudu, and other platforms. Check your Movies Anywhere account — you may have more portability than you realize.</p>
</section>

<h2>Section 4 — The approach we don\'t recommend</h2>

<section class="card card-note">
  <h2>DRM removal tools — the legal landscape</h2>
  <p>Tools exist for each of Amazon\'s DRM systems. We are not recommending them. We are documenting the landscape.</p>
  <p><strong>Kindle:</strong> Tools that decrypt Kindle books and convert them to standard EPUB, often as plugins for Calibre. The DMCA (US) and equivalent laws in most countries make DRM circumvention illegal even on content you purchased. Enforcement has historically focused on tool developers, not end users. The legal risk exists.</p>
  <p><strong>Audible:</strong> Tools that decrypt AAX/AAXC files to standard MP3 or M4A using your account\'s activation bytes. Several open-source projects exist and have been openly maintained for years. Same legal landscape as Kindle.</p>
  <p><strong>Prime Video:</strong> Screen recording tools (capture output during playback) and download/decrypt tools. Lower quality than the source, more clearly in violation of the DMCA than personal ebook backup.</p>
  <p>Our position: We believe when you pay for content, you should own it. Amazon\'s "Buy" button means "license" in their legal documents. This is a bait and switch conducted at scale. We are documenting the law as it exists. Adults can evaluate the risks. That is all.</p>
</section>

<section class="card card-honest">
  <h2>The structural solution: stop buying DRM content from Amazon</h2>
  <ul>
    <li><strong>Books:</strong> Buy DRM-free EPUB from publishers direct, Kobo, or Smashwords. Use Calibre. Borrow from Libby.</li>
    <li><strong>Audiobooks:</strong> Libro.fm (DRM-free, indie bookstore support). Libby for free borrowing.</li>
    <li><strong>Music:</strong> Amazon MP3 purchases are already DRM-free. Keep them.</li>
    <li><strong>Movies:</strong> Physical media for content you actually own. Movies Anywhere for cross-platform digital purchases.</li>
    <li><strong>Games:</strong> GOG.com for DRM-free PC games.</li>
  </ul>
</section>

<section class="card">
  <h2>The bigger picture</h2>
  <p>Amazon\'s content ecosystem is the most comprehensive lock-in strategy ever built. It is not one product. It is an interlocking set of products, each reinforcing the others: you buy a Kindle because books are cheap; you buy Kindle books because you have a Kindle; you join Prime because shipping is fast; you get Prime Video because it\'s included; you get an Echo because it works with Prime Music and your Ring doorbell.</p>
  <p>Each purchase makes the next purchase easier and makes leaving harder. This is not accidental. <strong>Amazon sells convenience. The price is dependency.</strong></p>
  <p>Your photos are yours. Your MP3 purchases are yours. Your Kindle books are Amazon\'s, and they have been since the moment you clicked "Buy now with 1-Click." The button lied. Now you know.</p>
</section>

<section class="card">
  <h2>Related guides</h2>
  <ul>
    <li><a href="/amazon/kindle/">Kindle — migration guide</a></li>
    <li><a href="/amazon/audible/">Audible — alternatives and cancellation</a></li>
    <li><a href="/amazon/prime-video/">Prime Video — what you purchased vs. what\'s streaming</a></li>
    <li><a href="/amazon/photos/">Amazon Photos — export guide</a></li>
    <li><a href="/amazon/data-export/">Your Amazon data — everything they hold</a></li>
    <li><a href="/apple/apple-your-content/">Compare: Apple content lock-in</a></li>
  </ul>
</section>
'''
    return page_shell(
        "Your Amazon Digital Content | DitchTheMega",
        "What you can take from Amazon's ecosystem, what you can replace, and what you effectively lose. Honest about Kindle DRM, Audible lock-in, and your real options.",
        f"{SITE_URL}/amazon/your-content/",
        content
    )

def build_apple_your_content():
    content = '''
<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/apple/">Apple</a> › Your Digital Content</div>
  <h1>Your Digital Content</h1>
  <p class="subtitle">What you can take, what you can replace, and what you effectively lose.</p>
</div>
<div class="card card-honest">
  <p>Some of the content you\'ve accumulated in Apple\'s ecosystem is genuinely yours.
  Some of it was never really yours to begin with. This page will be honest about the difference.</p>
</div>

<h2>Section 1 — Content you own and can export</h2>
<p class="card" style="padding:1rem 1.5rem;">This is your data. You created it, or it belongs to you by any reasonable definition. Apple provides export tools for all of it. Take it with you.</p>

<section class="card">
  <h2>Photos and videos</h2>
  <p>Your iCloud Photos library contains standard JPEG, HEIC, PNG, and MOV/MP4 files. These work everywhere. No DRM. No lock-in. These are your photos.</p>
  <h3>How to export</h3>
  <ul>
    <li><strong>Mac:</strong> Open Photos → select all → File → Export → "Export Unmodified Originals" (preserves full resolution and metadata)</li>
    <li><strong>Windows:</strong> Use iCloud for Windows to download your entire photo library</li>
    <li><strong>Web:</strong> icloud.com/photos → select → download (tedious for large libraries)</li>
    <li><strong>privacy.apple.com:</strong> Request a full data export — Apple prepares ZIP files (can take several days for large libraries)</li>
  </ul>
</section>

<section class="card">
  <h2>Documents (iCloud Drive)</h2>
  <p>Standard files in their original formats. No DRM. No conversion needed. A PDF is a PDF.</p>
  <p>Download from icloud.com/iclouddrive, use iCloud for Windows, or copy from the iCloud Drive folder on Mac. Move to any cloud storage: Proton Drive, a local drive, Nextcloud.</p>
</section>

<section class="card">
  <h2>Contacts, Calendars, Notes, Email</h2>
  <ul>
    <li><strong>Contacts:</strong> Contacts app → select all → File → Export vCard (.vcf). Universal standard. Import into any contacts app.</li>
    <li><strong>Calendars:</strong> Calendar app → File → Export per calendar (.ics). Import into Google Calendar, Proton Calendar, Outlook, or any calendar app.</li>
    <li><strong>Notes:</strong> Apple Notes has no built-in bulk export. Options: share each note as PDF manually, use privacy.apple.com full data export, or use the Exporter Mac app (exports to Markdown). This is one of Apple\'s weakest export paths.</li>
    <li><strong>Email:</strong> iCloud Mail supports IMAP. Connect via any email client (Thunderbird, Proton Bridge) and export your archive. If your primary address is @icloud.com, @me.com, or @mac.com — update every account that uses it before leaving. This is the most time-consuming part of leaving Apple.</li>
  </ul>
</section>

<section class="card">
  <h2>Health data and Passwords</h2>
  <ul>
    <li><strong>Health data:</strong> iPhone Health app → profile icon → Export All Health Data (XML format, importable into some health apps)</li>
    <li><strong>Passwords:</strong> Mac: System Settings → Passwords → Export to CSV. iOS: Settings → Passwords → Export. Import into Bitwarden, Proton Pass, or 1Password. <strong>Delete the CSV immediately after importing — it contains all your passwords in plain text.</strong></li>
  </ul>
</section>

<h2>Section 2 — Content you can replace but not transfer</h2>

<section class="card">
  <h2>Apple Music (streaming library)</h2>
  <p>Your playlists, favorites, and listening history are tied to your Apple Music subscription. When you cancel, downloaded music disappears.</p>
  <ul>
    <li><strong>Save playlists:</strong> Use Soundiiz, TuneMyMusic, or FreeYourMusic to copy playlists to Spotify, Tidal, YouTube Music. Most songs transfer successfully.</li>
    <li><strong>Uploaded music (your own files):</strong> iTunes/Music app → right-click → Download before canceling. These are your files.</li>
    <li><strong>What you lose:</strong> Listening history, recommendations, radio stations. These don\'t transfer.</li>
  </ul>
  <p style="color:#94a3b8;font-size:0.875rem;">Streaming music is inherently non-portable. This is the same on every platform. You never owned the music; you rented access. The playlists are the only thing worth saving.</p>
</section>

<section class="card">
  <h2>App data and preferences</h2>
  <p>Apps that sync through their own cloud service (Notion, Todoist, Strava) are portable — your data survives regardless of device. Apps that sync only through iCloud are not. Before leaving, check each app: does it have its own login and cloud sync? If yes, portable. If iCloud-only, export what you can from within the app first.</p>
</section>

<h2>Section 3 — Content you effectively lose</h2>
<div class="card card-caution">
  <p>This is the hard section. It reveals the fundamental difference between buying a physical object and buying a digital license. The situation is worth being angry about.</p>
</div>

<section class="card card-caution">
  <h2>Movies and TV shows (iTunes purchases)</h2>
  <p>You may have spent hundreds of dollars on iTunes movies. <strong>What you actually have is a license to stream or download those titles within Apple\'s ecosystem.</strong> You did not buy a movie. You bought permission to watch a movie on Apple\'s terms.</p>
  <h3>If you keep your Apple ID (free, no hardware required)</h3>
  <p>You can still watch purchases via: Apple TV app on Roku, Fire TV, Samsung/LG/Sony Smart TVs; iTunes on Windows; apple.com/tv in a browser. Keeping your Apple ID costs nothing.</p>
  <h3>If you delete your Apple ID</h3>
  <p>Your purchases are gone. Permanently. Apple does not offer refunds.</p>
  <h3>Your options</h3>
  <ul>
    <li><strong>Keep your Apple ID.</strong> It\'s free. This is the pragmatic choice for most people.</li>
    <li><strong>Accept the loss.</strong> Most iTunes purchases were watched once and never again. Calculate the honest value of maintaining access.</li>
    <li><strong>Movies Anywhere:</strong> Connect your Apple account. If a movie is Movies Anywhere eligible (Disney, Universal, Warner, Sony), it becomes accessible on Google Play, Amazon, Vudu. This doesn\'t fix past purchases but check what transfers.</li>
    <li><strong>Buy physical media going forward.</strong> A Blu-ray you own doesn\'t require a license. It doesn\'t disappear when a company changes its terms. This sounds archaic. It\'s also the only format that provides actual ownership.</li>
  </ul>
</section>

<section class="card card-caution">
  <h2>Books (Apple Books purchases)</h2>
  <p>Apple Books purchases are DRM-protected EPUBs tied to your Apple ID. Same situation as movies — licensed, not owned. Apple Books is not available on Windows or Android. Your options:</p>
  <ul>
    <li>Keep your Apple ID and read on Mac, iPad, or iPhone</li>
    <li>Re-purchase DRM-free ebooks from Kobo, direct publishers, or Smashwords going forward</li>
    <li>Use Libby/OverDrive for free library ebooks (you don\'t own them, but you didn\'t pay for them either)</li>
  </ul>
</section>

<section class="card">
  <h2>Apps (App Store purchases)</h2>
  <p>iOS and macOS apps run only on Apple hardware. Paid apps you\'ve purchased — including expensive professional tools like Procreate ($12.99), Final Cut Pro ($299), Logic Pro ($199) — are non-transferable. No refunds, no equivalents on other platforms.</p>
  <p>A $4.99 app from 2016 is a sunk cost. A $299 professional app you use daily is a different calculation. Factor this into your timeline for leaving Apple hardware.</p>
</section>

<h2>Section 4 — The approach we don\'t recommend</h2>

<section class="card card-note">
  <h2>DRM removal tools — the legal landscape</h2>
  <p>Tools exist that strip DRM from purchased digital content: movies, ebooks, and audiobooks. They work by intercepting the decryption process during playback. They produce standard files (MP4, EPUB, MP3) that play on any device.</p>
  <p><strong>We are not recommending these tools. We are explaining the legal situation.</strong></p>
  <p>In the United States, the Digital Millennium Copyright Act (DMCA) makes it illegal to circumvent DRM — even on content you purchased. The law does not distinguish between personal backup and piracy distribution. Similar laws apply in the EU, UK, Canada, and most other jurisdictions. Enforcement has historically targeted distributors and tool makers rather than individual consumers, but individual risk is not zero. If resulting files are shared, risk increases substantially.</p>
  <p>DRM removal tools are also frequently distributed through unofficial channels. Some contain malware. Some are legitimate. The user bears all risk of determining which is which.</p>
  <p>Our position: We believe when you pay for content, you should own it. We believe DRM treats paying customers worse than pirates, who receive DRM-free files by default. We believe the legal framework is hostile to consumers. We also believe in describing the law as it is, not as it should be. Adults can make their own decisions with full information. That\'s what this page provides.</p>
</section>

<section class="card card-honest">
  <h2>The structural solution: stop buying DRM content</h2>
  <p>The best way to avoid DRM lock-in is to stop accumulating it going forward:</p>
  <ul>
    <li><strong>Music:</strong> Buy from Bandcamp (DRM-free downloads, artists paid directly). Rip CDs you own. iTunes music purchases have been DRM-free since 2009 — the problem is streaming, not purchases.</li>
    <li><strong>Movies:</strong> Buy physical media (Blu-ray). Use Movies Anywhere to link accounts across platforms for future digital purchases. Treat digital movie "purchases" as rentals with no expiration date and price accordingly.</li>
    <li><strong>Books:</strong> Buy DRM-free EPUB from publishers, Kobo, Smashwords, or direct from authors. Use Calibre to manage your library across devices.</li>
    <li><strong>Audiobooks:</strong> Buy from Libro.fm (DRM-free, supports local bookstores).</li>
    <li><strong>Apps:</strong> Prefer cross-platform apps (web apps, apps on multiple platforms). This reduces switching costs when you eventually change platforms again.</li>
  </ul>
</section>

<section class="card">
  <h2>The bigger picture</h2>
  <p>When you bought a VHS tape, you owned it. You could watch it on any VCR. You could lend it, sell it, or watch it twenty years later on a different device that hadn\'t been manufactured when you bought the tape.</p>
  <p>When you "buy" a movie on Apple TV, you own a license to stream it within Apple\'s ecosystem for as long as Apple maintains the service and the licensing agreements with the content owners remain in effect. You cannot lend it. You cannot sell it. You cannot play it on a device Apple doesn\'t support. If Apple\'s agreement with the studio ends, the movie can disappear from your library. <strong>This has happened.</strong></p>
  <p>This is not unique to Apple. Amazon, Google, and every digital storefront work the same way. The difference is that Apple\'s ecosystem is designed so thoroughly that many people accumulate thousands of dollars in purchases before they realize what "purchase" actually means in this context.</p>
  <p>Your photos are yours. Your documents are yours. Your purchased movies are Apple\'s, and they always were. Now you know. Now you can decide.</p>
</section>

<section class="card">
  <h2>Related guides</h2>
  <ul>
    <li><a href="/apple/icloud/">iCloud — everything the account holds</a></li>
    <li><a href="/apple/apple-tv-itunes/">iTunes purchases — your options</a></li>
    <li><a href="/apple/apple-music/">Apple Music migration</a></li>
    <li><a href="/apple/app-store/">App Store — what you lose</a></li>
    <li><a href="/apple/find-my-apple-id/">Closing your Apple ID</a></li>
  </ul>
</section>
'''
    return page_shell(
        "Your Digital Content — Apple | DitchTheMega",
        "What you can take from Apple's ecosystem, what you can replace, and what you effectively lose. Honest about DRM, digital licenses, and your real options.",
        f"{SITE_URL}/apple/apple-your-content/",
        content
    )

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

    # Google hub
    os.makedirs(f"{PUBLIC_DIR}/google", exist_ok=True)
    with open(f"{PUBLIC_DIR}/google/index.html", "w") as f:
        f.write(build_google_hub(services))
    print("Built: google/index.html")

    # Alternatives hub
    os.makedirs(f"{PUBLIC_DIR}/alternatives", exist_ok=True)
    with open(f"{PUBLIC_DIR}/alternatives/index.html", "w") as f:
        f.write(build_alternatives_hub(services))
    print("Built: alternatives/index.html")

    # Service pages
    for svc in services:
        slug = svc["slug"]
        cat  = svc.get("category","")
        if cat in ("meta", "seller", "google", "alternatives", "apple", "microsoft", "amazon-meta"):
            continue  # handled separately below
        out_dir = f"{PUBLIC_DIR}/amazon/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(build_service_page(svc))
        print(f"Built: amazon/{slug}/index.html")

    # Google service pages
    for svc in [s for s in services if s.get("category") == "google"]:
        slug = svc["slug"]
        out_dir = f"{PUBLIC_DIR}/google/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(build_google_service_page(svc))
        print(f"Built: google/{slug}/index.html")

    # Alternatives pages
    for svc in [s for s in services if s.get("category") == "alternatives"]:
        slug = svc["slug"]
        out_dir = f"{PUBLIC_DIR}/alternatives/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(build_alternatives_page(svc))
        print(f"Built: alternatives/{slug}/index.html")

    # Apple hub
    os.makedirs(f"{PUBLIC_DIR}/apple", exist_ok=True)
    with open(f"{PUBLIC_DIR}/apple/index.html", "w") as f:
        f.write(build_apple_hub(services))
    print("Built: apple/index.html")

    # Apple service pages
    for svc in [s for s in services if s.get("category") == "apple"]:
        slug = svc["slug"]
        out_dir = f"{PUBLIC_DIR}/apple/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(build_apple_service_page(svc))
        print(f"Built: apple/{slug}/index.html")

    # Amazon Your Content page (custom, not YAML-driven)
    out_dir = f"{PUBLIC_DIR}/amazon/your-content"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_amazon_your_content())
    print("Built: amazon/your-content/index.html")

    # Apple Your Content page (custom, not YAML-driven)
    out_dir = f"{PUBLIC_DIR}/apple/apple-your-content"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_apple_your_content())
    print("Built: apple/apple-your-content/index.html")

    # Google Your Content
    out_dir = f"{PUBLIC_DIR}/google/your-content"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_google_your_content())
    print("Built: google/your-content/index.html")

    # Meta hub and service pages
    os.makedirs(f"{PUBLIC_DIR}/meta", exist_ok=True)
    with open(f"{PUBLIC_DIR}/meta/index.html", "w") as f:
        f.write(build_generic_hub(services, "meta", "meta",
            "Leaving the Meta Ecosystem",
            "Facebook, Instagram, WhatsApp, and Threads. Here's how to reduce your exposure to Meta's surveillance infrastructure.",
            "Practical guides to leaving Facebook, Instagram, WhatsApp, and Threads. No lectures. Just the steps.",
            f"{SITE_URL}/meta/"))
    print("Built: meta/index.html")
    for svc in [s for s in services if s.get("category") == "meta"]:
        slug = svc["slug"]
        out_dir = f"{PUBLIC_DIR}/meta/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(build_generic_service_page(svc, "meta"))
        print(f"Built: meta/{slug}/index.html")

    # Meta Your Content
    out_dir = f"{PUBLIC_DIR}/meta/your-content"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_meta_your_content())
    print("Built: meta/your-content/index.html")

    # Microsoft hub and service pages
    os.makedirs(f"{PUBLIC_DIR}/microsoft", exist_ok=True)
    with open(f"{PUBLIC_DIR}/microsoft/index.html", "w") as f:
        f.write(build_generic_hub(services, "microsoft", "microsoft",
            "Leaving the Microsoft Ecosystem",
            "Windows, Microsoft 365, LinkedIn, and OneDrive. Here's how to reduce your dependency on Microsoft's stack.",
            "Practical guides to leaving Windows, Microsoft 365, LinkedIn, and OneDrive. Honest about what stays Windows-only.",
            f"{SITE_URL}/microsoft/"))
    print("Built: microsoft/index.html")
    for svc in [s for s in services if s.get("category") == "microsoft"]:
        slug = svc["slug"]
        out_dir = f"{PUBLIC_DIR}/microsoft/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(build_generic_service_page(svc, "microsoft"))
        print(f"Built: microsoft/{slug}/index.html")

    # Microsoft Your Content
    out_dir = f"{PUBLIC_DIR}/microsoft/your-content"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_microsoft_your_content())
    print("Built: microsoft/your-content/index.html")

    # Sitemap (add sellers hub)
    with open(f"{PUBLIC_DIR}/sitemap.xml", "w") as f:
        f.write(build_sitemap(services))
    print("Built: sitemap.xml")

    # Robots.txt
    with open(f"{PUBLIC_DIR}/robots.txt", "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    print("Built: robots.txt")

    page_count = len([s for s in services if s.get('category') not in ('meta',)]) + 5  # hubs + about
    print(f"\nDone. {page_count}+ pages generated in {PUBLIC_DIR}/")

if __name__ == "__main__":
    main()
