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
    <a href="/what-is-lock-in/" class="nav-link">What Is Lock-In?</a>
    <a href="/alternatives/" class="nav-link">Alternatives</a>
    <a href="/guides/secure-home-automation/" class="nav-link">Home Automation</a>
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
  <p><a href="/about/">About</a> &middot; <a href="/what-is-lock-in/">What Is Lock-In?</a> &middot; <a href="/privacy/">Privacy</a> &middot; <a href="/terms/">Terms</a> &middot; <a href="https://ko-fi.com/cancelfreely" target="_blank" rel="noopener">☕ Buy us a coffee</a></p>
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

    # ClosingAccounts cross-link
    if svc.get("closing_accounts_note"):
        sections.append(f'<section class="card"><h2>Closing this account after a death?</h2><p>{e(svc["closing_accounts_note"])}</p><p style="margin-top:.5rem;"><a href="https://closingaccounts.com" target="_blank" rel="noopener">Visit closingaccounts.com →</a></p></section>')

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
    # Filter to Amazon services only (exclude other mega-corp categories)
    NON_AMAZON = {"meta", "seller", "google", "apple", "microsoft", "alternatives"}
    cards = ""
    for svc in services:
        if svc.get("category") in NON_AMAZON:
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
  <p style="margin-top:.5rem;font-size:.85rem;"><a href="/what-is-lock-in/" style="color:#94a3b8;">Why is this harder than canceling a subscription? →</a></p>
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
<div class="card" style="margin-bottom:1.5rem;background:#161b27;border-color:#1e2433;">
  <p style="font-size:.9rem;color:#94a3b8;">Leaving Big Tech is harder than canceling a subscription. Content you bought is locked to their ecosystem. Data you shared lives on their servers. Relationships you built exist only on their platforms. <a href="/what-is-lock-in/" style="color:#f59e0b;">Understand the three types of lock-in →</a></p>
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
  <p style="margin-top:.75rem;"><strong>Deep dive:</strong> <a href="/guides/secure-home-automation/">Secure home automation without Big Tech</a> — the complete Home Assistant guide.</p>
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

def build_what_is_lock_in():
    content = '''
<div class="page-hero">
  <h1>What Is Ecosystem Lock-In?</h1>
  <p class="subtitle">Why leaving Big Tech is harder than canceling a subscription — and how to think about it.</p>
</div>

<section class="card">
  <h2>Not all lock-in is the same</h2>
  <p>"Lock-in" gets used loosely to mean "hard to leave." But the reasons it\'s hard to leave are very different across companies, and understanding which type of lock-in you\'re facing tells you what kind of migration work is ahead of you.</p>
  <p>There are three types:</p>
</section>

<section class="card card-caution">
  <h2>Type 1: Content lock-in (DRM)</h2>
  <p>You paid for something, but you don\'t own it. Your Kindle books, your iTunes movies, your Audible audiobooks, your Apple Books purchases — these are licenses, not property. They are encrypted with DRM (Digital Rights Management) and can only be accessed through the company\'s software on the company\'s approved devices.</p>
  <p>If you leave the ecosystem and close your account, the content is gone. There is no legal way to export it in a format that works elsewhere. The button that said \"Buy\" meant \"License under our terms.\"</p>
  <p><strong>Who does this:</strong> Amazon (Kindle, Audible, Prime Video), Apple (iTunes movies, Apple Books, App Store), Google (some Play Books, Play Movies), Microsoft (Xbox games, Microsoft Store movies).</p>
  <p><strong>The structural solution:</strong> Stop buying DRM-locked content. Buy DRM-free ebooks from Kobo, Smashwords, or publishers directly. Buy audiobooks from Libro.fm. Buy movies on physical media or through Movies Anywhere-linked storefronts. Buy PC games from GOG.com. Going forward, you own what you buy.</p>
</section>

<section class="card card-privacy">
  <h2>Type 2: Data lock-in (surveillance)</h2>
  <p>You didn\'t buy anything — the product was you. Google has fifteen years of your search history, location history, email content, YouTube watch history, and voice commands. Meta has your social graph, your messages, your behavioral profile. These companies don\'t lock up your content — they lock up their knowledge of you.</p>
  <p>You can export your files in an afternoon. Your data shadow is not in the export. Google\'s model of your behavior — the advertising profile, the predictions, the inferences drawn from a decade of queries — is not a file you can download and take with you. It remains on Google\'s servers whether or not you\'ve exported your photos.</p>
  <p><strong>Who does this:</strong> Google (the most extensive), Meta (social and behavioral data), Amazon (purchase and voice data), Microsoft (enterprise and telemetry data).</p>
  <p><strong>The structural solution:</strong> Stop the flow, then drain the reservoir. Replace the services that collect the most data per day first (browser, search engine, maps, Android). Then delete the historical data that\'s already been collected. The Google guide covers this in the <a href="/google/cutting-the-pipeline/">Cutting the Pipeline</a> five-phase plan.</p>
</section>

<section class="card card-honest">
  <h2>Type 3: Social lock-in (network effects)</h2>
  <p>Your family is on Facebook. Your friends are on Instagram. Your group chat is on WhatsApp. The restaurant you like posts specials on Instagram stories. This isn\'t technical lock-in at all — it\'s social infrastructure that happens to run on private platforms.</p>
  <p>You can export all your photos and posts from Meta\'s platforms in an afternoon. What you can\'t export is your social graph. The connections, the groups, the communities. These exist on Facebook because your people are on Facebook. No technical solution changes that.</p>
  <p><strong>Who does this:</strong> Meta (the purest example), Apple (iMessage creates a social pressure dynamic unique to the US), to a lesser extent Google (Gmail is where people expect to reach you).</p>
  <p><strong>The structural solution:</strong> Collect contact information (phone numbers, email addresses) before leaving. Move to platforms where relationships can exist independent of any single company\'s servers — direct text, email, Signal. Accept that some connections will fade. This is the cost of leaving, and it\'s worth being honest about.</p>
</section>

<section class="card">
  <h2>Why this matters</h2>
  <p>Knowing which type of lock-in you\'re facing tells you where to focus your energy:</p>
  <ul>
    <li>If your biggest concern is <strong>content lock-in</strong>, the work is exporting what you can, accepting the sunk cost of what you can\'t, and changing your purchasing habits going forward.</li>
    <li>If your biggest concern is <strong>data surveillance</strong>, the work is replacing the high-leakage services first and systematically deleting the historical record.</li>
    <li>If your biggest concern is <strong>social lock-in</strong>, the work is slower and more personal: migrating relationships rather than files, and accepting that some friction is unavoidable.</li>
  </ul>
  <p>Most people face all three, with different weights for different companies. That\'s why this site is organized by company rather than by type of content — because leaving Amazon is mostly a content-lock-in problem, leaving Google is mostly a data-surveillance problem, and leaving Meta is mostly a social-lock-in problem.</p>
</section>

<section class="card">
  <h2>Where to start</h2>
  <div class="timeline-nav" style="margin-top:.5rem;">
    <a href="/amazon/" class="timeline-card"><div class="when">Content lock-in</div><div class="what">Amazon — Kindle, Audible, Prime Video</div></a>
    <a href="/google/cutting-the-pipeline/" class="timeline-card"><div class="when">Data surveillance</div><div class="what">Google — The 3-month pipeline plan</div></a>
    <a href="/meta/" class="timeline-card"><div class="when">Social lock-in</div><div class="what">Meta — Facebook, Instagram, WhatsApp</div></a>
    <a href="/apple/" class="timeline-card"><div class="when">All three types</div><div class="what">Apple — DRM + hardware + social</div></a>
    <a href="/microsoft/" class="timeline-card"><div class="when">Lightest lock-in</div><div class="what">Microsoft — easiest consumer exit</div></a>
  </div>
</section>
'''
    return page_shell(
        "What Is Ecosystem Lock-In? | DitchTheMega",
        "Why leaving Big Tech is harder than canceling a subscription. Three types of lock-in: DRM content, data surveillance, and social networks. Understanding which you face tells you what work is ahead.",
        f"{SITE_URL}/what-is-lock-in/",
        content
    )

def build_dtm_privacy():
    content = '''
<div class="page-hero">
  <h1>Privacy Policy</h1>
</div>
<section class="card">
  <p>DitchTheMega collects no personal data. We use no analytics. We set no cookies. We don\'t track your browsing. We don\'t know who you are. We don\'t want to know who you are.</p>
  <p>The site is static HTML served through Cloudflare Pages. No server-side code processes your requests. No database stores your visits.</p>
  <p>Some links on this site are affiliate links, clearly marked with an <span class="aff-badge">aff</span> badge. If you click one and make a purchase, we may earn a commission. We do not track which users click which links beyond what the affiliate program provider tracks at their end.</p>
  <p>If you email us, we receive your email. We don\'t add you to a list. We don\'t sell your address. We reply if a reply is needed and that\'s the end of it.</p>
  <p>This site exists to help you take control of your data. We start by not taking any of it.</p>
  <p style="color:var(--text-light);font-size:0.8rem;">Last updated: April 2026</p>
</section>
'''
    return page_shell(
        "Privacy Policy | DitchTheMega",
        "DitchTheMega collects no personal data. No analytics, no cookies, no tracking.",
        f"{SITE_URL}/privacy/",
        content
    )

def build_guide_home_automation():
    content = '''
<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Guides › Secure Home Automation</div>
  <h1>Secure Home Automation Without Big Tech</h1>
  <p class="subtitle">The complete guide to running a smart home that keeps all your data on hardware you own, in your house, on your network. No cloud. No subscription. No surveillance.</p>
</div>

<section class="card card-privacy">
  <h2>The problem with Alexa, Google Home, and HomeKit</h2>
  <p>Every major smart home ecosystem sends your data to the cloud. Your voice commands. Your daily routines. When you leave and when you come home. When you turn on the lights and when you go to sleep. Which rooms you use and when. Amazon and Google use this data for advertising and product development. Apple is more privacy-respecting but still cloud-dependent for most functions.</p>
  <p>A fully functional, locally controlled smart home exists. It keeps all your data on hardware you own, in your house, on your network. The answer is Home Assistant.</p>
</section>

<h2>What is Home Assistant?</h2>
<section class="card">
  <p>Home Assistant is a free, open-source home automation platform that runs on a small computer in your home. It communicates with your smart devices locally over your home network. Your data never leaves your house. There is no monthly fee. There is no cloud dependency. The project is managed by the Open Home Foundation, a nonprofit that cannot be sold or acquired.</p>
  <ul>
    <li>600,000+ active installations worldwide</li>
    <li>3,500+ integrations with smart home devices and services</li>
    <li>Support for Zigbee, Z-Wave, Matter, Thread, WiFi, and Bluetooth devices</li>
    <li>Built-in local voice assistant (Assist) that processes voice commands on your hardware without sending audio anywhere</li>
    <li>&ldquo;Works with Home Assistant&rdquo; certification program that verifies local operation without cloud subscriptions</li>
  </ul>
</section>

<h2>What you need to get started</h2>

<section class="card">
  <h2>Hardware options</h2>
  <ul>
    <li><strong>Home Assistant Green (~$99)</strong> — The official plug-and-play device. No assembly. Plug in, connect to network, open a browser. Best starting point for non-technical users.</li>
    <li><strong>Home Assistant Yellow (~$150)</strong> — More powerful, with built-in Zigbee/Thread radio. One device handles both hub and device communication.</li>
    <li><strong>Raspberry Pi 4 or 5 ($35–$80 + accessories)</strong> — The DIY option. Flash Home Assistant OS to an SD card. 15 minutes of setup if comfortable with this.</li>
    <li><strong>Any old PC or mini-PC</strong> — Home Assistant runs on any x86 machine. An old laptop, a NUC, a mini-PC. Install Home Assistant OS or run it in Docker.</li>
  </ul>
</section>

<section class="card">
  <h2>Communication radios (you may need one or more)</h2>
  <ul>
    <li><strong>Zigbee radio (Home Assistant SkyConnect, ~$30)</strong> — For Zigbee devices (IKEA, Aqara, Hue, Sonoff). Plugs into USB.</li>
    <li><strong>Z-Wave radio (Zooz ZST39, ~$30)</strong> — For Z-Wave devices (many locks, sensors, thermostats). Plugs into USB.</li>
    <li><strong>Matter/Thread</strong> — Supported natively in newer Home Assistant hardware. The emerging cross-platform standard.</li>
    <li><strong>WiFi devices</strong> — No additional radio needed. Many smart plugs, lights, and switches use WiFi with local APIs.</li>
  </ul>
  <p><strong>Total cost to start:</strong> $99 (Home Assistant Green) to $150 (Yellow with radio). Comparable to buying an Echo, but with no subscription and no surveillance.</p>
</section>

<h2>What devices work</h2>

<section class="card">
  <h2>Lighting</h2>
  <ul>
    <li>Philips Hue — works locally via Zigbee, bypassing the Hue cloud</li>
    <li>IKEA Tradfri — Zigbee, fully local, ~$8 per bulb</li>
    <li>Nanoleaf — Matter-compatible</li>
    <li>Any Zigbee-compatible bulb or switch</li>
  </ul>
  <h2>Thermostats</h2>
  <ul>
    <li>Ecobee — cloud integration, functional</li>
    <li>Generic Zigbee/Z-Wave thermostats — fully local, best for full local control</li>
    <li>Honeywell T6 Pro Z-Wave — controlled entirely through Home Assistant with no cloud involvement</li>
  </ul>
  <h2>Locks</h2>
  <ul>
    <li>Yale (Z-Wave models) — fully local</li>
    <li>Schlage (Z-Wave models) — fully local</li>
    <li>Any Z-Wave lock communicates over a local mesh network. The company could disappear and your lock still works.</li>
  </ul>
  <h2>Cameras</h2>
  <ul>
    <li><strong>UniFi Protect</strong> — local NVR, no cloud required; the gold standard for privacy-respecting cameras</li>
    <li><strong>Reolink</strong> — RTSP streams, local recording, Works with Home Assistant certified</li>
    <li><strong>Frigate</strong> — open-source NVR that runs alongside Home Assistant; AI object detection running locally</li>
    <li><strong>Avoid:</strong> Ring (Amazon, cloud-dependent, law enforcement partnerships), Wyze (cloud-dependent, security incidents), Nest cameras (Google)</li>
  </ul>
  <h2>Sensors &amp; plugs</h2>
  <ul>
    <li>Aqara — Zigbee; motion, temperature, door/window, water leak sensors; inexpensive</li>
    <li>Shelly — WiFi, local API, very popular in the Home Assistant community</li>
    <li>TP-Link Kasa — WiFi, local API</li>
    <li>Any Zigbee or Z-Wave plug/switch</li>
  </ul>
</section>

<h2>How automations work</h2>
<section class="card">
  <p>Home Assistant automations run locally on your hub. They don\'t phone home. They don\'t check with a server. Examples:</p>
  <ul>
    <li>Motion detected in the hallway after sunset → turn on light at 30% brightness. Turn off after 5 minutes of no motion.</li>
    <li>Front door unlocked → disarm security system, turn on entryway light, send notification to phone.</li>
    <li>Nobody home (based on phone GPS via HA companion app, sent directly to your hub) → set thermostat to away mode, lock doors, arm security.</li>
    <li>Washing machine power drops below 5 watts (smart plug) → notification: &ldquo;Laundry is done.&rdquo;</li>
  </ul>
  <p>All of these run <strong>without the internet</strong>. If your internet goes down, your automations keep working.</p>
</section>

<h2>Honest tradeoffs</h2>
<section class="card card-honest">
  <ul>
    <li><strong>Setup is harder than Alexa.</strong> The initial setup takes 1–4 hours depending on how many devices you have. It\'s not difficult, but it requires more attention than a consumer product.</li>
    <li><strong>The learning curve is real but manageable.</strong> Home Assistant has gotten dramatically easier. The visual automation editor and device auto-discovery mean you rarely need to touch YAML anymore.</li>
    <li><strong>Some devices still need the cloud.</strong> Ecobee, Ring, Nest, and many WiFi devices phone home to their manufacturer. Home Assistant can integrate with these, but the device itself still sends data to the manufacturer. For full local control, choose Zigbee, Z-Wave, or Matter devices.</li>
    <li><strong>Remote access requires one extra step.</strong> By default, Home Assistant is only accessible on your home network. Nabu Casa ($6.50/month) adds encrypted remote access and funds development. Or set up a VPN yourself for free.</li>
    <li><strong>Assist is not a general-purpose AI assistant.</strong> It handles device control commands extremely well. It doesn\'t handle trivia, news briefings, shopping orders, or skills.</li>
  </ul>
</section>

<h2>Starter shopping list</h2>
<section class="card card-steps">
  <h2>Under $200 — lighting and basic automation</h2>
  <ul>
    <li>Home Assistant Green: $99</li>
    <li>Home Assistant SkyConnect (Zigbee/Thread radio): $30</li>
    <li>4x IKEA Tradfri Zigbee smart bulbs: ~$32 ($8 each)</li>
    <li>1x Aqara Zigbee motion sensor: ~$16</li>
    <li>1x Aqara Zigbee door/window sensor: ~$14</li>
    <li><strong>Total: ~$191</strong></li>
  </ul>
  <p>You get: Smart lighting in 4 rooms, motion-activated hallway light, door detection, all local, all private.</p>

  <h2>Under $500 — adds thermostat and lock</h2>
  <ul>
    <li>Everything above: $191</li>
    <li>Honeywell T6 Pro Z-Wave thermostat: ~$130</li>
    <li>Zooz ZST39 Z-Wave USB stick: ~$30</li>
    <li>Yale Assure Z-Wave deadbolt: ~$140</li>
    <li><strong>Total: ~$491</strong></li>
  </ul>
</section>

<h2>Questions people actually ask</h2>

<section class="card">
  <h2>Can I lock/unlock doors and control my thermostat by voice without Alexa or Google?</h2>
  <p>Yes. Home Assistant\'s built-in voice assistant (Assist) handles this entirely locally. The entire chain: you speak → Whisper (open-source speech recognition on your hardware) converts speech to text → Home Assistant interprets the command → Z-Wave signal goes to your lock or thermostat. No internet required. No cloud. No audio stored anywhere.</p>
  <p>Specific commands work well: &ldquo;Lock the front door,&rdquo; &ldquo;Set the thermostat to 72,&rdquo; &ldquo;Turn off all lights,&rdquo; &ldquo;Is the garage door open?&rdquo;</p>
</section>

<section class="card">
  <h2>How good is voice recognition compared to Alexa?</h2>
  <p>Honest answer: Assist is good at direct commands and not good at conversational or ambiguous requests.</p>
  <p><strong>Works well:</strong> &ldquo;Turn on kitchen lights,&rdquo; &ldquo;Set thermostat to 72,&rdquo; &ldquo;Lock front door,&rdquo; &ldquo;Turn off all lights,&rdquo; sensor state queries.</p>
  <p><strong>May require specific phrasing:</strong> &ldquo;Make it warmer&rdquo; (say &ldquo;Set thermostat to 74&rdquo; instead). Custom scenes work if named clearly.</p>
  <p><strong>Doesn\'t work:</strong> General knowledge, conversational follow-ups, Alexa skills, ordering pizza, playing trivia.</p>
  <p><strong>Improving:</strong> The Home Assistant community is integrating local LLMs into Assist for better natural language understanding. This is an active development area in 2026 and improving with every release.</p>
</section>

<section class="card">
  <h2>Do automations still work if the internet goes down?</h2>
  <p>Yes. All automations run on your local hub. Motion-triggered lights, thermostat schedules, door automations, security arming — all continue without internet. Devices that depend on their manufacturer\'s cloud (Ecobee, Ring, Nest) stop working during an outage, but that\'s not a Home Assistant limitation. Zigbee, Z-Wave, Thread, and Matter devices with local control continue to function regardless.</p>
</section>

<section class="card">
  <h2>Can I check cameras from my phone when away from home?</h2>
  <p>Yes, with one extra step:</p>
  <ul>
    <li><strong>Nabu Casa ($6.50/month)</strong> — Official encrypted relay. Your camera feeds and controls are accessible from anywhere via the HA app. Nabu Casa doesn\'t store your data; it relays the encrypted connection. The fee funds Home Assistant development.</li>
    <li><strong>VPN (free, technical)</strong> — WireGuard on your router makes your phone virtually on your home network. No third party involved.</li>
    <li><strong>Reverse proxy (free, most technical)</strong> — Expose Home Assistant via HTTPS with a domain name. Requires DNS and SSL knowledge.</li>
  </ul>
</section>

<section class="card">
  <h2>Can my family, partner, and guests use it?</h2>
  <p>Yes. Multiple approaches: individual user accounts with permission levels in the HA companion app; wall-mounted tablets running the HA dashboard (no app needed for guests); physical Z-Wave switches that work like normal switches for anyone; Assist voice satellites in rooms.</p>
</section>

<section class="card">
  <h2>I\'m not technical. Can I actually do this?</h2>
  <p>With Home Assistant Green: close to consumer-grade. Plug in, open browser, follow wizard. Auto-discovery finds many devices. Zigbee pairing is click → pair mode → done. Visual automation editor for common setups.</p>
  <p>The honest comparison:</p>
  <ul>
    <li>Setting up an Echo: 5 minutes</li>
    <li>Setting up Home Assistant Green with 5 devices: 1–2 hours</li>
    <li>Setting up Home Assistant with 30 devices and 15 automations: a weekend project</li>
    <li>Maintenance after initial setup: about the same as any smart home system</li>
  </ul>
  <p>The learning curve is front-loaded. The first weekend is the hardest. After that, adding devices and automations gets faster.</p>
</section>

<section class="card">
  <h2>What\'s the easiest first step?</h2>
  <p>Start with smart lighting. Buy the Home Assistant Green ($99), a Zigbee USB stick ($30), and 3–5 IKEA Tradfri Zigbee bulbs ($8 each). Set up one automation: motion sensor turns on the hallway light after sunset. Total cost under $180. Total setup time about an hour. You now have a locally controlled, private smart lighting system that nobody is surveilling.</p>
</section>

<section class="card">
  <h2>Can I keep using Alexa or Google alongside Home Assistant?</h2>
  <p>Yes. Home Assistant integrates with both. In this configuration: your voice command goes through Amazon (Alexa processes speech) → Alexa sends the command to Home Assistant → Home Assistant sends it to your device locally. Amazon hears &ldquo;turn on the kitchen lights.&rdquo; Amazon does not know the state of your lights, your automation schedule, your sensor data, or anything else. This is a reasonable transition strategy: keep Alexa\'s polished voice interface while moving device control to Home Assistant.</p>
</section>

<section class="card">
  <h2>How does Home Assistant compare to Apple HomeKit?</h2>
  <p>HomeKit is the closest mainstream ecosystem to Home Assistant\'s privacy model. Apple doesn\'t use your home automation data for advertising and processes many commands locally. For Apple users who want privacy and simplicity, HomeKit is a reasonable choice.</p>
  <p><strong>Home Assistant advantages:</strong> 3,500+ device integrations vs HomeKit\'s ~1,000; much more powerful automations; runs on any hardware; fully customizable dashboards; Assist voice processing is fully local (Siri sends some data to Apple).</p>
  <p><strong>HomeKit advantages:</strong> Simpler setup (scan a code); seamless Apple ecosystem integration; family sharing is easier; iPhone Control Center and lock screen integration.</p>
  <p>They can coexist. Home Assistant has a HomeKit Bridge integration that exposes HA devices to HomeKit. Many people run Home Assistant for heavy lifting and use HomeKit as a secondary iPhone control interface.</p>
</section>

<section class="card">
  <h2>What happens if Home Assistant as a project shuts down?</h2>
  <p>Home Assistant is managed by the Open Home Foundation, a nonprofit that cannot be sold or acquired. The software is open source (Apache 2.0). Even if the organization ceased to exist, the code is public and the community would continue it. Compare this to commercial platforms: when Google killed Works with Nest, when Samsung stopped supporting SmartThings Hub V1, when Wink started charging monthly fees to avoid shutdown — customers were stranded. Home Assistant can\'t strand you because your automations run on your hardware.</p>
</section>

<section class="card">
  <h2>Is Home Assistant secure?</h2>
  <p>Generally more secure than cloud-based smart homes because your devices are not exposed to the internet by default. In cloud-based systems, your devices communicate with internet servers; a breach of those servers can expose your home. In Home Assistant, devices talk to a hub on your local network, not reachable from outside unless you configure it.</p>
  <p>Best practices: keep Home Assistant updated (automatic by default); use strong passwords + 2FA; use Nabu Casa or VPN for remote access rather than directly exposing to internet; consider putting IoT devices on a separate VLAN; prefer Zigbee/Z-Wave/Thread over WiFi where possible.</p>
</section>

<section class="card">
  <h2>Resources</h2>
  <ul>
    <li><a href="https://home-assistant.io" target="_blank" rel="noopener">home-assistant.io</a> — official site, documentation, hardware</li>
    <li><a href="https://community.home-assistant.io" target="_blank" rel="noopener">community.home-assistant.io</a> — forum, 700,000+ members</li>
    <li><a href="https://www.reddit.com/r/homeassistant" target="_blank" rel="noopener">r/homeassistant</a> — 450,000+ members; questions always answered</li>
    <li><a href="https://www.youtube.com/@HomeAssistant" target="_blank" rel="noopener">Home Assistant YouTube</a> — official tutorials</li>
  </ul>
</section>

<section class="card">
  <h2>Related guides</h2>
  <ul>
    <li><a href="/amazon/alexa/">Alexa & Smart Home — migration guide</a></li>
    <li><a href="/amazon/alexa-deep-dive/">Home Assistant setup — device-by-device migration from Alexa</a></li>
    <li><a href="/alternatives/smart-home/">Smart Home alternatives overview</a></li>
    <li><a href="/amazon/ring/">Ring replacement — UniFi, Eufy, Reolink</a></li>
  </ul>
</section>
'''
    return page_shell(
        "Secure Home Automation Without Big Tech | DitchTheMega",
        "The complete guide to Home Assistant: local smart home control with no cloud, no subscription, and no surveillance. Hardware options, device compatibility, Q&A.",
        f"{SITE_URL}/guides/secure-home-automation/",
        content
    )

def build_dtm_terms():
    content = '''
<div class="page-hero">
  <h1>Terms of Use</h1>
</div>
<section class="card">
  <p>DitchTheMega provides general information about leaving Big Tech ecosystems. It is not legal advice. We make reasonable efforts to keep information accurate and current but cannot guarantee accuracy. Use at your own risk.</p>
  <p>Information about DRM circumvention tools is provided for informational purposes only. We do not recommend, endorse, or provide instructions for circumventing DRM. Laws governing DRM circumvention vary by jurisdiction. Nothing on this site should be construed as legal guidance about DRM removal.</p>
  <p>Links to third-party sites are not endorsements. Some links are affiliate links, disclosed on every page where they appear. We are not responsible for the practices of the services we document or link to.</p>
  <p>Affiliate links are clearly marked. We only link to services we would recommend regardless of whether an affiliate program exists.</p>
  <p style="color:var(--text-light);font-size:0.8rem;">Last updated: April 2026</p>
</section>
'''
    return page_shell(
        "Terms of Use | DitchTheMega",
        "DitchTheMega provides general information, not legal advice. DRM information is informational only.",
        f"{SITE_URL}/terms/",
        content
    )

def build_about():
    content = '''<div class="page-hero">
  <h1>About DitchTheMega</h1>
</div>
<section class="card">
  <h2>What this is</h2>
  <p>A free, practical guide to extracting yourself from Big Tech ecosystems: Amazon, Google, Apple, Meta, and Microsoft. Not a boycott manifesto. Not a moral lecture. A practical guide that assumes you\'ve already decided to reduce your dependence and need to know how.</p>
  <p>You\'ve decided to leave. Here\'s the map.</p>
</section>
<section class="card">
  <h2>What this isn\'t</h2>
  <p>This site doesn\'t tell you <em>why</em> to leave. There are a hundred articles and documentaries for that. This site tells you <em>how</em> — service by service, company by company, with real alternatives and honest assessments of what you gain and what you lose. Including the things Big Tech does genuinely well that no single alternative matches.</p>
</section>
<section class="card">
  <h2>What we cover</h2>
  <ul>
    <li><a href="/amazon/">Amazon</a> — Prime, Kindle, Audible, Alexa, Ring, Photos, Pharmacy, and more</li>
    <li><a href="/google/">Google</a> — Gmail, Search, Maps, YouTube, Photos, Android</li>
    <li><a href="/apple/">Apple</a> — iCloud, iTunes purchases, App Store, iMessage, hardware migration</li>
    <li><a href="/meta/">Meta</a> — Facebook, Instagram, WhatsApp, Threads</li>
    <li><a href="/microsoft/">Microsoft</a> — Windows, Microsoft 365, LinkedIn, OneDrive, Xbox</li>
    <li><a href="/alternatives/">Alternatives</a> — email, cloud storage, browsers, messaging, password managers, VPN, and more</li>
    <li><a href="/guides/secure-home-automation/">Secure Home Automation</a> — leaving Alexa and Google Home for a local-first setup</li>
  </ul>
</section>
<section class="card">
  <h2>Principles</h2>
  <ul>
    <li><strong>No data collection.</strong> We don't track you. We don't have analytics. We don't use cookies.</li>
    <li><strong>No paid recommendations.</strong> No company pays to be listed. Recommendations exist because they're good.</li>
    <li><strong>Honest about tradeoffs.</strong> Every company guide has a "what you genuinely lose" section. Big Tech does some things well. We say so.</li>
    <li><strong>Open to corrections.</strong> Something wrong or out of date? Corrections and improvements are welcome — <a href="/about/#affiliate">see our principles</a>.</li>
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
  <p>Something wrong or out of date? <a href="mailto:info@ditchthemega.com">Let us know</a>.</p>
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
            SITE_URL + "/microsoft/", SITE_URL + "/alternatives/", SITE_URL + "/about/",
            SITE_URL + "/what-is-lock-in/", SITE_URL + "/privacy/", SITE_URL + "/terms/"]
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

    # Add featured cards for the custom pages
    cards += '''<a href="/google/cutting-the-pipeline/" class="service-card" style="border-color:#f59e0b;">
  <div class="service-card-inner">
    <h2>Cutting the Pipeline</h2>
    <p>The phased 3-month plan. Stop the flow, drain the reservoir.</p>
    <span class="difficulty d1">Start here</span>
  </div>
</a>'''
    cards += '''<a href="/google/your-content/" class="service-card card-honest-link">
  <div class="service-card-inner">
    <h2>Your Digital Content</h2>
    <p>What to export, what transfers, what Google keeps</p>
  </div>
</a>'''
    cards += '''<a href="/google/google-data-cleanup/" class="service-card">
  <div class="service-card-inner">
    <h2>Data Cleanup Walkthrough</h2>
    <p>Step-by-step: delete what Google has collected about you</p>
  </div>
</a>'''

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Google</div>
  <h1>Leaving the Google Ecosystem</h1>
  <p class="subtitle">Google isn\'t a search engine. It\'s a surveillance network that also does search, email, maps, video, and your phone.<br>
  Here\'s how to reduce your dependency, service by service.</p>
  <p style="margin-top:.5rem;font-size:.85rem;"><a href="/what-is-lock-in/" style="color:#94a3b8;">Why is this harder than canceling a subscription? →</a></p>
</div>
<div class="card card-honest" style="margin-bottom:1.5rem;">
  <h2>What Google genuinely does better than any alternative</h2>
  <ul>
    <li><strong>Google Maps business data</strong> — hours, reviews, real-time traffic. No alternative matches the density. Use it in a browser when you need it; don\'t make it the default app.</li>
    <li><strong>YouTube\'s content library</strong> — no alternative platform has the same breadth. Watch without tracking (Invidious, Brave) rather than pretending alternatives don\'t exist.</li>
    <li><strong>Google Search quality</strong> — for very recent news, local results, and specific technical queries, Google is still ahead. DuckDuckGo covers 95% of daily use.</li>
    <li><strong>Google Scholar</strong> — for academic research, no real equivalent yet.</li>
    <li><strong>Gmail deliverability</strong> — Proton and Tuta occasionally land in spam at servers that implicitly trust Gmail. Real consideration for professional email.</li>
  </ul>
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

def alt_entry(name, url, replaces, privacy, free_tier, cost, platform, tradeoff):
    free_badge = '<span class="alt-badge alt-free">Free tier</span>' if free_tier else ''
    cost_str = f'<span class="alt-badge alt-cost">{e(cost)}</span>' if cost else ''
    return f'''<div class="alt-entry">
  <div class="alt-header">
    <a href="{e(url)}" target="_blank" rel="noopener" class="alt-name">{e(name)}</a>
    {free_badge}{cost_str}
  </div>
  <div class="alt-meta">
    <span><strong>Replaces:</strong> {e(replaces)}</span>
    <span><strong>Privacy:</strong> {e(privacy)}</span>
    <span><strong>Platforms:</strong> {e(platform)}</span>
  </div>
  <p class="alt-tradeoff"><strong>Honest tradeoff:</strong> {e(tradeoff)}</p>
</div>'''

ALT_STYLE = '''<style>
  .alt-entry{background:var(--paper);border:1px solid var(--border);border-radius:8px;padding:1.25rem;margin-bottom:1rem}
  .alt-header{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap;margin-bottom:.6rem}
  .alt-name{font-size:1rem;font-weight:700;color:#f59e0b;text-decoration:none}
  .alt-name:hover{text-decoration:underline}
  .alt-badge{font-size:.7rem;font-weight:700;padding:2px 8px;border-radius:20px}
  .alt-free{background:#052e16;color:#86efac}
  .alt-cost{background:#1e2433;color:#94a3b8}
  .alt-meta{display:grid;gap:.3rem;margin-bottom:.5rem;font-size:.85rem;color:#94a3b8}
  .alt-tradeoff{font-size:.875rem;color:#64748b}
  .alt-section{margin-bottom:2.5rem}
  .alt-section h2{font-size:1.1rem;font-weight:700;color:#f1f5f9;border-bottom:1px solid var(--border);padding-bottom:.5rem;margin-bottom:1rem}
  .aff-note{background:#1a1205;border:1px solid #78350f;border-radius:8px;padding:.75rem 1rem;margin-bottom:1.5rem;font-size:.8rem;color:#d1d5db}
</style>'''

def build_alternatives_category_page(slug, title, description, sections_html):
    content = f'''{ALT_STYLE}
<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/alternatives/">Alternatives</a> › {e(title)}</div>
  <h1>{e(title)}</h1>
  <p class="subtitle">{e(description)}</p>
</div>
<div class="aff-note">ℹ️ This page is affiliate-free. Recommendations exist because they\'re good, not because we earn a commission. The rest of DitchTheMega has <a href="/about/#affiliate" style="color:#fcd34d;">disclosed affiliate links</a> where they exist. Not here.</div>
{sections_html}
<section class="card"><h2>Related guides</h2><ul>
<li><a href="/alternatives/">All alternatives categories</a></li>
<li><a href="/what-is-lock-in/">What is ecosystem lock-in?</a></li>
</ul></section>'''
    return page_shell(
        f"{title} | DitchTheMega",
        description,
        f"{SITE_URL}/alternatives/{slug}/",
        content
    )

def build_alternatives_pages():
    pages = {}

    # Email
    pages["email"] = build_alternatives_category_page("email",
        "Email Alternatives",
        "Privacy-respecting alternatives to Gmail, Outlook, and Yahoo Mail.",
        '<div class="alt-section"><h2>Email providers</h2>\n' +
        alt_entry("Proton Mail", "https://proton.me/mail", "Gmail, Outlook, Yahoo Mail",
            "End-to-end encrypted; Swiss jurisdiction; Proton cannot read your email",
            True, "From $3.99/month", "Web, iOS, Android, desktop",
            "Occasional deliverability issues to servers that implicitly trust Gmail; small storage on free tier") +
        alt_entry("Tuta", "https://tuta.com", "Gmail, Outlook",
            "End-to-end encrypted including subject lines; German jurisdiction; post-quantum encryption",
            True, "From €1/month", "Web, iOS, Android, desktop",
            "Smaller ecosystem than Proton; contacts can\'t decrypt your emails unless they also use Tuta") +
        alt_entry("Fastmail", "https://fastmail.com", "Gmail, Outlook",
            "Not end-to-end encrypted, but privacy-respecting; no advertising; Australian company",
            False, "From $3/month", "Web, iOS, Android",
            "Not encrypted at rest like Proton/Tuta; better UX than both") +
        "</div>")

    # Cloud Storage
    pages["cloud-storage"] = build_alternatives_category_page("cloud-storage",
        "Cloud Storage Alternatives",
        "Privacy-respecting alternatives to Google Drive, OneDrive, iCloud, and Dropbox.",
        '<div class="alt-section"><h2>Cloud storage</h2>\n' +
        alt_entry("Proton Drive", "https://proton.me/drive", "Google Drive, OneDrive, iCloud Drive",
            "End-to-end encrypted; files private even from Proton",
            True, "From $3.99/month", "Web, iOS, Android, desktop",
            "Smaller storage on free tier than Google; newer and still building features") +
        alt_entry("Cryptomator", "https://cryptomator.org", "Google Drive, Dropbox, any cloud provider",
            "Client-side encryption layer for any cloud; you control the encryption key",
            True, "$14.99 one-time (mobile)", "Windows, Mac, Linux, iOS, Android",
            "Adds a layer of setup complexity; the vault must be unlocked before accessing files") +
        alt_entry("Nextcloud", "https://nextcloud.com", "Google Drive, OneDrive",
            "Self-hosted; you control the server; zero third-party involvement",
            True, "Free (self-hosted)", "Web, iOS, Android, desktop",
            "Requires your own server hardware or a hosting provider; more setup than commercial cloud") +
        alt_entry("Synology NAS", "https://synology.com", "Google Photos, iCloud, Google Drive",
            "Local storage on your hardware; nothing leaves your home",
            False, "$200–500 hardware (one-time)", "Web, iOS, Android, desktop",
            "One-time hardware cost; electricity; no off-site backup unless configured") +
        "</div>")

    # Browsers & Search
    pages["browsers-and-search"] = build_alternatives_category_page("browsers-and-search",
        "Browser & Search Alternatives",
        "Privacy-respecting alternatives to Chrome, Edge, and Google Search.",
        '<div class="alt-section"><h2>Browsers</h2>\n' +
        alt_entry("Brave", "https://brave.com", "Chrome, Edge",
            "Chromium-based; built-in ad and tracker blocking; no telemetry to Google",
            True, "Free", "Windows, Mac, Linux, iOS, Android",
            "Some sites have issues with Brave\'s ad blocking; Brave has its own ad network (opt-in)") +
        alt_entry("Firefox", "https://firefox.com", "Chrome, Edge",
            "Independent engine; Mozilla nonprofit; customizable privacy settings",
            True, "Free", "Windows, Mac, Linux, iOS, Android",
            "Slightly slower on some sites than Chromium-based browsers; requires configuration for maximum privacy") +
        "</div>\n<div class=\"alt-section\"><h2>Search engines</h2>\n" +
        alt_entry("Brave Search", "https://search.brave.com", "Google Search, Bing",
            "Independent search index; not a Google or Bing wrapper; no tracking",
            True, "Free", "Web, browser integration",
            "Smaller index than Google; occasional gaps on very specific or very recent queries") +
        alt_entry("DuckDuckGo", "https://duckduckgo.com", "Google Search",
            "No search history; no profiling; !bang syntax for quick searches",
            True, "Free", "Web, browser, iOS, Android",
            "Partially powered by Bing; less strong on local search than Google") +
        alt_entry("Startpage", "https://startpage.com", "Google Search",
            "Returns Google results without Google tracking you; privacy proxy for Google\'s index",
            True, "Free", "Web",
            "Still effectively using Google\'s index; best transition option if Google result quality matters") +
        alt_entry("Kagi", "https://kagi.com", "Google Search",
            "Paid search; no advertising; you\'re the customer not the product; highly customizable",
            False, "From $5/month", "Web, browser integration",
            "Costs money; worth evaluating for a month to see if quality justifies the price") +
        "</div>")

    # Messaging
    pages["messaging"] = build_alternatives_category_page("messaging",
        "Messaging Alternatives",
        "Privacy-respecting alternatives to WhatsApp, iMessage, Facebook Messenger, and SMS.",
        '<div class="alt-section"><h2>Messaging apps</h2>\n' +
        alt_entry("Signal", "https://signal.org", "WhatsApp, iMessage, Facebook Messenger",
            "End-to-end encrypted by default; open source; nonprofit; no metadata collection",
            True, "Free", "iOS, Android, Windows, Mac, Linux",
            "Your contacts also need Signal; green bubble equivalent when messaging non-Signal users") +
        alt_entry("Element (Matrix)", "https://element.io", "WhatsApp, Slack, Discord",
            "Decentralized, federated, open source; can self-host your own server",
            True, "Free", "iOS, Android, Web, desktop",
            "More technical setup; smaller user base than Signal; powerful for teams and communities") +
        "</div>")

    # Password Managers
    pages["password-managers"] = build_alternatives_category_page("password-managers",
        "Password Manager Alternatives",
        "Privacy-respecting alternatives to Google Password Manager, iCloud Keychain, and LastPass.",
        '<div class="alt-section"><h2>Password managers</h2>\n' +
        alt_entry("Bitwarden", "https://bitwarden.com", "Google Password Manager, iCloud Keychain, LastPass",
            "Open source; audited; can be self-hosted; excellent free tier",
            True, "Free / $10/year premium", "iOS, Android, Web, all browsers, desktop",
            "Cloud-synced by default (though you can self-host); no offline access without the app") +
        alt_entry("Proton Pass", "https://proton.me/pass", "Google Password Manager, iCloud Keychain",
            "End-to-end encrypted; integrated with Proton ecosystem; email aliases included",
            True, "Free / included in Proton plans", "iOS, Android, Web, all browsers",
            "Newer than Bitwarden; smaller feature set but catching up") +
        alt_entry("KeePassXC", "https://keepassxc.org", "Any cloud password manager",
            "Fully local; vault is a file on your device; never touches a server",
            True, "Free", "Windows, Mac, Linux",
            "No automatic sync between devices; you manage your vault file manually") +
        "</div>")

    # VPN
    pages["vpn"] = build_alternatives_category_page("vpn",
        "VPN Alternatives",
        "VPNs that don\'t log your activity. (Most commercial VPNs do.)",
        '<div class="alt-section"><h2>Privacy-respecting VPNs</h2>\n' +
        alt_entry("Mullvad", "https://mullvad.net", "ISP tracking; commercial VPNs that log",
            "No account required; no email; pay with cash; the most anonymous VPN",
            False, "€5/month", "Windows, Mac, Linux, iOS, Android",
            "Account number instead of email means harder to recover if lost; no free tier") +
        alt_entry("Proton VPN", "https://protonvpn.com", "ISP tracking; commercial logging VPNs",
            "Audited no-logs; open source; free tier has no data limit",
            True, "Free / from $4.99/month", "Windows, Mac, Linux, iOS, Android",
            "Free tier is slower and limited to three countries") +
        "</div>")

    # Maps
    pages["maps-and-navigation"] = build_alternatives_category_page("maps-and-navigation",
        "Maps & Navigation Alternatives",
        "Privacy-respecting alternatives to Google Maps and Waze.",
        '<div class="alt-section"><h2>Navigation apps</h2>\n' +
        alt_entry("Apple Maps", "https://apple.com/maps", "Google Maps",
            "On-device processing where possible; no persistent location history sent to Apple",
            True, "Free", "iOS, macOS, iPadOS",
            "Apple-ecosystem only; business data density still catching up to Google") +
        alt_entry("OsmAnd", "https://osmand.net", "Google Maps, Waze",
            "Open source; offline maps; OpenStreetMap data; no tracking",
            True, "Free / $9.99 OsmAnd+", "iOS, Android",
            "Weaker on business hours and real-time traffic; more features than most people need") +
        alt_entry("Organic Maps", "https://organicmaps.app", "Google Maps",
            "Open source; offline-first; no tracking; no ads",
            True, "Free", "iOS, Android",
            "Focused on navigation and hiking; thinner on business listings and transit") +
        "</div>")

    # Productivity
    pages["productivity"] = build_alternatives_category_page("productivity",
        "Productivity Alternatives",
        "Alternatives to Google Docs, Microsoft 365, Notion, Evernote, and OneNote.",
        '<div class="alt-section"><h2>Office suites</h2>\n' +
        alt_entry("LibreOffice", "https://libreoffice.org", "Microsoft 365, Google Docs/Sheets/Slides",
            "Free; open source; local; handles most Office formats",
            True, "Free", "Windows, Mac, Linux",
            "The 10% of complex Office documents (advanced macros, pivot tables) may not convert perfectly") +
        alt_entry("CryptPad", "https://cryptpad.fr", "Google Docs, Microsoft 365",
            "End-to-end encrypted; open source; nonprofit; collaborative",
            True, "Free / from €5/month", "Web",
            "Smaller feature set than Google Docs; occasional performance issues on large documents") +
        alt_entry("OnlyOffice", "https://onlyoffice.com", "Microsoft 365, Google Docs",
            "Open source; high Office format compatibility",
            True, "Free desktop / paid server", "Windows, Mac, Linux, Web",
            "Closer to Microsoft\'s UI than LibreOffice; better format fidelity on complex documents") +
        "</div>\n<div class=\"alt-section\"><h2>Notes</h2>\n" +
        alt_entry("Obsidian", "https://obsidian.md", "Notion, Evernote, OneNote, Google Keep",
            "Local-first; Markdown; no cloud unless you choose sync",
            True, "Free / $8/month sync", "Windows, Mac, Linux, iOS, Android",
            "No web app; notes are plain text Markdown files; less structured than Notion") +
        alt_entry("Standard Notes", "https://standardnotes.com", "Evernote, Google Keep, Apple Notes",
            "End-to-end encrypted; open source; notes are yours forever",
            True, "Free / from $3.33/month", "Web, iOS, Android, desktop",
            "Simpler than Obsidian; fewer features but cleaner interface") +
        "</div>")

    # Streaming
    pages["streaming"] = build_alternatives_category_page("streaming",
        "Streaming Alternatives",
        "Important note: streaming alternatives are lateral moves, not privacy upgrades.",
        '<div class="alt-section"><h2>The honest truth about streaming</h2>\n' +
        '<div class="card card-note"><p>All streaming services track your viewing habits. There is no privacy-respecting streaming alternative. Switching from Prime Video to Netflix trades Amazon\'s surveillance for Netflix\'s. The recommendation is to use streaming services in a privacy-focused browser (Brave, Firefox) without being signed into a Google/Amazon/Apple account where possible.</p>' +
        '<p>For music: buy DRM-free from Bandcamp. For movies and TV shows: physical media (Blu-ray) is the only DRM-free option. Your library\'s DVD loan program is free.</p></div>\n' +
        '<h2>If you want to move between streaming services</h2>\n' +
        alt_entry("Tidal", "https://tidal.com", "Spotify, Apple Music, Amazon Music",
            "Independent (not a Big Five company); higher audio quality (HiFi/Atmos)",
            False, "From $10.99/month", "Web, iOS, Android, desktop",
            "Smaller catalog in some regions; Jay-Z ownership means less neutral than Mullvad or Signal") +
        alt_entry("Bandcamp", "https://bandcamp.com", "Spotify, Apple Music (for purchases)",
            "Artists receive majority of revenue; DRM-free MP3/FLAC downloads",
            True, "Pay-per-album", "Web, iOS, Android",
            "Not a full streaming library replacement; best for artists you actively want to support") +
        "</div>")

    # Gaming
    pages["gaming"] = build_alternatives_category_page("gaming",
        "Gaming Alternatives",
        "DRM-free and more portable alternatives to the Xbox Store, Amazon Games, and Google Play Games.",
        '<div class="alt-section"><h2>PC gaming platforms</h2>\n' +
        alt_entry("GOG.com", "https://gog.com", "Xbox Store, Amazon Games, Epic Games Store",
            "DRM-free; you own the installer; runs without any account or internet check",
            False, "Pay-per-game", "Windows, Mac, Linux",
            "Smaller library than Steam; focuses on quality over quantity; older games especially well-represented") +
        alt_entry("itch.io", "https://itch.io", "Xbox Store, Steam (indie games)",
            "Many games are DRM-free; indie-first; creator-friendly revenue split",
            True, "Pay-per-game", "Windows, Mac, Linux",
            "Indie-focused; not a source for AAA games") +
        alt_entry("Steam", "https://store.steampowered.com", "Xbox Store, Amazon Games",
            "Most portable DRM of the major PC stores; long track record; generous refunds",
            False, "Pay-per-game", "Windows, Mac, Linux (via Proton)",
            "Not DRM-free; requires the Steam client; but more portable than Xbox/PlayStation/Epic stores") +
        "</div>")

    # Smart Home
    pages["smart-home"] = build_alternatives_category_page("smart-home",
        "Smart Home Alternatives",
        "Privacy-respecting alternatives to Alexa, Google Home, and Ring.",
        '<div class="alt-section"><h2>Smart home platform</h2>\n' +
        alt_entry("Home Assistant", "https://home-assistant.io", "Amazon Alexa/Echo, Google Home/Nest, Apple HomeKit",
            "Open source; runs locally; your data never leaves your house; no subscription",
            True, "Free (hardware: $99 Green, $150 Yellow)", "Any device with a browser; native iOS/Android app",
            "Setup takes 1–2 hours; learning curve is real but front-loaded; much more powerful than Alexa once running") +
        "</div>\n<div class=\"alt-section\"><h2>Cameras (Ring alternatives)</h2>\n" +
        alt_entry("UniFi Protect", "https://ui.com/camera-security", "Ring, Nest cameras",
            "Local storage only; footage never sent to a cloud server; no subscription required",
            False, "Hardware: $100–400 NVR + cameras", "Web, iOS, Android",
            "Requires a UniFi NVR or Dream Machine; higher upfront cost; best-in-class for privacy") +
        alt_entry("Reolink", "https://reolink.com", "Ring, Wyze",
            "Local storage via SD card or NAS; optional cloud (not required)",
            False, "$30–$100 per camera", "Web, iOS, Android",
            "Good value; cloud optional not required; less polished app than Ring") +
        "</div>\n<p style=\"margin-top:1rem;\"><a href=\"/guides/secure-home-automation/\">See the complete Home Assistant guide →</a></p>")

    # Shopping
    pages["shopping"] = build_alternatives_category_page("shopping",
        "Shopping Alternatives",
        "Where to buy things online that isn\'t Amazon, by category.",
        '<div class="alt-section"><h2>General merchandise</h2>\n' +
        alt_entry("Walmart.com", "https://walmart.com", "Amazon general shopping",
            "No Amazon relationship; Walmart+ for shipping",
            False, "$98/year Walmart+", "Web, iOS, Android",
            "Narrower selection than Amazon for niche items; no third-party marketplace concerns") +
        alt_entry("Target.com", "https://target.com", "Amazon general shopping",
            "No Amazon relationship; same-day via Shipt in many areas",
            False, "$99/year Target Circle 360", "Web, iOS, Android",
            "Stronger for household, grocery, clothing; weaker for electronics and niche items") +
        "</div>\n<div class=\"alt-section\"><h2>Books</h2>\n" +
        alt_entry("Bookshop.org", "https://bookshop.org", "Amazon books",
            "10% of every purchase supports independent bookstores",
            False, "Same prices as Amazon", "Web",
            "No used books; no Kindle format; print and DRM-free ebook for some publishers") +
        alt_entry("ThriftBooks", "https://thriftbooks.com", "Amazon used books",
            "No Amazon relationship",
            False, "Pay-per-book", "Web, iOS, Android",
            "Used only; slightly slower shipping than Amazon") +
        alt_entry("Libby (your library)", "https://libbyapp.com", "Kindle Unlimited, Audible",
            "Free; library card is a subscription you\'ve already paid for",
            True, "Free", "iOS, Android, Kindle",
            "Wait times on popular titles; can\'t keep books forever") +
        "</div>\n<div class=\"alt-section\"><h2>Pet supplies</h2>\n" +
        alt_entry("Chewy", "https://chewy.com", "Amazon pet supplies",
            "No Amazon relationship; often cheaper than Amazon on pet food",
            False, "Free shipping on $49+", "Web, iOS, Android",
            "Pet-specific only; $49 minimum for free shipping") +
        "</div>\n<div class=\"alt-section\"><h2>Household & cleaning</h2>\n" +
        alt_entry("Grove Collaborative", "https://grove.co", "Amazon Subscribe & Save (household)",
            "B Corp; no Amazon relationship",
            False, "Free shipping with membership", "Web, iOS, Android",
            "Natural/eco-focused; subscription model; smaller selection than Amazon") +
        "</div>")

    return pages

def build_alternatives_hub(services):
    # Category pages (new expanded alternatives)
    cat_pages = [
        ("email", "Email", "Gmail, Outlook, Yahoo Mail"),
        ("cloud-storage", "Cloud Storage", "Google Drive, OneDrive, iCloud"),
        ("browsers-and-search", "Browsers & Search", "Chrome, Google Search, Edge"),
        ("messaging", "Messaging", "WhatsApp, iMessage, Messenger"),
        ("password-managers", "Password Managers", "Google Passwords, iCloud Keychain"),
        ("vpn", "VPN", "Commercial logging VPNs; ISP tracking"),
        ("maps-and-navigation", "Maps & Navigation", "Google Maps, Waze"),
        ("productivity", "Productivity", "Google Docs, Microsoft 365, Notion"),
        ("streaming", "Streaming", "Prime Video, Apple TV+, YouTube Premium"),
        ("gaming", "Gaming", "Xbox Store, Amazon Games"),
        ("smart-home", "Smart Home", "Alexa, Google Home, Ring"),
        ("shopping", "Shopping", "Amazon general shopping"),
    ]
    cat_cards = "".join(f'''<a href="/alternatives/{slug}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(title)}</h2>
    <p style="font-size:.8rem;color:#64748b;">Replaces: {e(replaces)}</p>
  </div>
</a>''' for slug, title, replaces in cat_pages)

    # Legacy YAML-driven pages (Amazon-specific comparisons)
    alt_svcs = [s for s in services if s.get("category") == "alternatives"]
    legacy_cards = "".join(f'''<a href="/alternatives/{svc["slug"]}/" class="service-card">
  <div class="service-card-inner">
    <h2>{e(svc["title"])}</h2>
    <p style="font-size:.8rem;color:#64748b;">{e(svc.get("meta_description","")[:80])}</p>
  </div>
</a>''' for svc in alt_svcs)

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Alternatives</div>
  <h1>Privacy-Respecting Alternatives</h1>
  <p class="subtitle">For every Big Tech service you use, there is a privacy-respecting option that works. Some are better. Some are harder. All of them let you leave.</p>
</div>
<div style="background:#1a1205;border:1px solid #78350f;border-radius:8px;padding:.75rem 1rem;margin-bottom:1.5rem;font-size:.8rem;color:#d1d5db;">ℹ️ These pages are affiliate-free. Every recommendation exists because it\'s good, not because we earn a commission.</div>
<div class="service-grid">
{cat_cards}
</div>
<h2 style="margin-top:2rem;margin-bottom:1rem;color:#f1f5f9;">Amazon shopping comparisons</h2>
<div class="service-grid">
{legacy_cards}
</div>'''

    return page_shell(
        "Privacy-Respecting Alternatives — DitchTheMega",
        "Alternatives to Gmail, Google Drive, Chrome, WhatsApp, iCloud, Alexa, and more. Honest comparisons. No affiliate links.",
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

    # Add Privacy Comparison as a custom card (not YAML-driven)
    cards += '''<a href="/apple/privacy-comparison/" class="service-card">
  <div class="service-card-inner">
    <h2>Privacy vs Lock-In</h2>
    <p>Why Apple&#39;s privacy is different than its lock-in — and what switching really means</p>
    <span class="difficulty d2">Moderate</span>
  </div>
</a>'''

    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › Apple</div>
  <h1>Leaving the Apple Ecosystem</h1>
  <p class="subtitle">Apple\'s lock-in is different from Amazon\'s or Google\'s. It\'s not about surveillance — it\'s about DRM.<br>
  Content you purchased through Apple cannot legally be transferred to other platforms. Understand what you\'re leaving before you go.</p>
  <p style="margin-top:.5rem;font-size:.85rem;"><a href="/what-is-lock-in/" style="color:#94a3b8;">Why is this harder than canceling a subscription? →</a></p>
</div>
<div class="card card-caution" style="margin-bottom:1.5rem;">
  <h2>⚠️ Read this before anything else</h2>
  <p>Movies, TV shows, and books purchased through iTunes and Apple Books are DRM-locked to Apple\'s ecosystem.
  There is no legal way to export them to another platform. Audit your purchases before leaving.
  See the <a href="/apple/apple-your-content/">Your Digital Content guide</a> for the full picture.</p>
</div>
<div class="card card-honest" style="margin-bottom:1.5rem;">
  <h2>What you genuinely lose when you leave Apple</h2>
  <ul>
    <li><strong>iTunes/Apple Books purchases</strong> — DRM-locked, not transferable to other platforms</li>
    <li><strong>iMessage</strong> — end-to-end encryption with your Apple contacts; green bubble fallback is unencrypted SMS</li>
    <li><strong>AirDrop, Handoff, Universal Clipboard</strong> — seamless cross-device workflows with no Android/Windows equivalent</li>
    <li><strong>Apple Watch full functionality</strong> — requires iPhone; leaving iPhone severely limits Watch capabilities</li>
    <li><strong>Apple\'s privacy advantage</strong> — Apple\'s data practices are genuinely better than most alternatives; leaving for Google trades lock-in for surveillance</li>
    <li><strong>Build quality and ecosystem coherence</strong> — Apple hardware and software are designed together in ways Android/Windows aren\'t</li>
  </ul>
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
    if svc.get("digital_legacy"):
        dl = svc["digital_legacy"]
        dl_html = render_list(dl) if isinstance(dl, list) else f'<p>{e(dl)}</p>'
        sections.append(f'<section class="card"><h2>Digital Legacy & Closing Accounts</h2>{dl_html}<p style="margin-top:.5rem;">If someone in your life has passed away and you need to access their Apple account, see <a href="https://closingaccounts.com" target="_blank" rel="noopener">closingaccounts.com</a> for guidance specific to bereavement.</p></section>')
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

def build_generic_hub(services, category, slug_prefix, title, subtitle, description, canonical, **kwargs):
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
    # Extra content: what you genuinely lose (passed via lose_html)
    lose_html = kwargs.get('lose_html', '')
    content = f'''<div class="page-hero amazon-hero">
  <div class="breadcrumb"><a href="/">Home</a> › {e(title)}</div>
  <h1>{e(title)}</h1>
  <p class="subtitle">{e(subtitle)}</p>
</div>
{lose_html}
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

def build_google_cutting_pipeline():
    content = '''
<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/google/">Google</a> › Cutting the Pipeline</div>
  <h1>Cutting the Pipeline</h1>
  <p class="subtitle">A phased, realistic guide to disentangling your life from Google\'s surveillance infrastructure. Not a product swap list. A migration plan organized by what actually matters most.</p>
</div>

<div class="card card-privacy">
  <h2>Two separate projects</h2>
  <p><strong>Project 1: Stop the flow.</strong> Replace Google services so new data stops being collected. This is what every other guide covers.</p>
  <p style="margin-top:.5rem;"><strong>Project 2: Drain the reservoir.</strong> Delete, export, or restrict the data Google already has about you. Almost nobody covers this.</p>
  <p style="margin-top:.5rem;">Both projects take time. Both matter. This guide covers both, in the order that actually works.</p>
</div>

<section class="card">
  <h2>The order of operations</h2>
  <p>Most guides say \"start with the easy things.\" That\'s wrong. <strong>Start with the services that leak the most data per day, regardless of difficulty.</strong></p>
  <p style="margin-top:.75rem;margin-bottom:.5rem;color:#94a3b8;font-size:0.85rem;">Ranked by daily data leakage:</p>
  <ol style="font-size:0.875rem;">
    <li><strong>Chrome</strong> — every page you visit, every search, every form you fill, every password you save</li>
    <li><strong>Google Search</strong> — every question you ask, every curiosity, every fear, every symptom</li>
    <li><strong>Android / Google Play Services</strong> — your location, app usage, contacts, call log, WiFi connections</li>
    <li><strong>Google Maps</strong> — everywhere you go, how long you stay, how you get there</li>
    <li><strong>Gmail</strong> — every email sent and received, every receipt, every password reset</li>
    <li><strong>YouTube</strong> — everything you watch, how long, what you search for, what you click away from</li>
    <li>Google Drive, Photos, Calendar, Contacts, Assistant/Nest (significant but lower volume)</li>
  </ol>
  <p style="margin-top:.75rem;">The top four account for the vast majority of data Google collects. Replace those four first.</p>
</section>

<h2>Phase 1 — The Big Four (Week 1–2)</h2>

<section class="card card-steps">
  <h2>1A: Replace Chrome</h2>
  <p><em>Why first:</em> Chrome gives Google visibility into every URL you visit, every search, every form you fill, every password. Replacing it reduces Google\'s visibility more than any other single change.</p>
  <ul>
    <li><strong>Brave</strong> — Chromium-based; your extensions still work; built-in ad/tracker blocking; no telemetry to Google</li>
    <li><strong>Firefox</strong> — independent engine; more customizable; strong privacy with the right settings</li>
  </ul>
  <p>How: Install Brave or Firefox → import bookmarks/passwords from Chrome (one-click) → set as system default → sign out of Chrome → after two weeks without issues, uninstall Chrome.</p>
  <p style="color:#94a3b8;font-size:0.85rem;">Time: 15 minutes.</p>
</section>

<section class="card card-steps">
  <h2>1B: Replace Google Search</h2>
  <p><em>Why second:</em> Every search query is a direct transmission of your questions, fears, and interests. Search is the most intimate data pipeline.</p>
  <ul>
    <li><strong>Brave Search</strong> — independent index, not a Google/Bing wrapper, private</li>
    <li><strong>DuckDuckGo</strong> — established, reliable, does not track</li>
    <li><strong>Startpage</strong> — Google results without Google tracking; best transition option</li>
  </ul>
  <p>How: Browser Settings → Search Engine → change default. On your phone: change search engine in browser app. Delete the Google Search app.</p>
  <p style="color:#94a3b8;font-size:0.85rem;">Time: 2 minutes. Honest note: results are equivalent for most searches. For the rare query where you need Google specifically, add \"!g\" to search it directly via DuckDuckGo\'s bang syntax.</p>
</section>

<section class="card card-steps">
  <h2>1C: Contain Android</h2>
  <p><em>Why third:</em> Android collects your location, app usage, contacts, call history, and WiFi connections continuously. Three options by disruption level:</p>
  <h3>Option A — Restrict on existing phone (30 min)</h3>
  <ul>
    <li>Turn off Location History: Settings → Location → Google Location History. <em>Also</em> turn it off at myactivity.google.com/activitycontrols (phone setting and account setting are separate; both must be off)</li>
    <li>Turn off Web & App Activity: myactivity.google.com/activitycontrols</li>
    <li>Turn off YouTube History: same page</li>
    <li>Disable Ad Personalization: Settings → Google → Ads → opt out</li>
    <li>Revoke unnecessary permissions from all Google apps (especially Location, Microphone, Camera, Contacts)</li>
    <li>Disable Google Assistant: Settings → Google → Google Assistant → turn off</li>
    <li>Replace Gboard (sends typing data to Google) with OpenBoard or FlorisBoard (F-Droid)</li>
  </ul>
  <h3>Option B — Replace Google apps while keeping Play Services</h3>
  <p>Swap Gmail for Proton Mail, Maps for OsmAnd, Photos for a local gallery, Drive for Proton Drive, Calendar for Proton Calendar. Install F-Droid for open-source apps without Google Play Services.</p>
  <h3>Option C — De-Googled OS (advanced)</h3>
  <p>GrapheneOS (Pixel hardware, best security, sandboxed Google Play option), CalyxOS (Pixel + some Motorola, microG compatibility), LineageOS (wide device support, more technical). Option A + B provides 80% of the privacy benefit with 20% of the disruption.</p>
</section>

<section class="card card-steps">
  <h2>1D: Delete your Google Maps location history</h2>
  <p>Go to <strong>timeline.google.com</strong> and look at what Google has recorded. This is often shocking.</p>
  <ul>
    <li>Delete all: timeline.google.com → Settings → Delete all Location History</li>
    <li>Set auto-delete: myactivity.google.com/activitycontrols → Location History → auto-delete → 3 months</li>
    <li>Replace the app: OsmAnd or Organic Maps for navigation; browser (not the app, not signed in) for the occasional business lookup</li>
  </ul>
  <p style="color:#94a3b8;font-size:0.85rem;">Honest note: Google Maps\' business data (hours, reviews, real-time info) has no equivalent. Use it in a browser when you genuinely need it. Just don\'t make it the default.</p>
</section>

<h2>Phase 2 — Email and identity (Week 2–6)</h2>

<section class="card">
  <h2>2A: Migrate from Gmail</h2>
  <p>Gmail is the hardest Google service to leave, not because the migration is technically difficult, but because your Gmail address is your identity across the internet. It\'s the login for dozens or hundreds of other services.</p>
  <ol>
    <li><strong>Choose your new email provider</strong> — Proton Mail (E2E encrypted, Easy Switch Gmail import), Tuta (encrypted including subject lines), Fastmail (fast, excellent UX, Australian)</li>
    <li><strong>Import your Gmail archive</strong> — Proton\'s Easy Switch imports messages, labels, contacts, and calendar automatically via IMAP</li>
    <li><strong>Set up Gmail forwarding</strong> — Gmail settings → forward all incoming mail to your new address. Keep this active for 6–12 months</li>
    <li><strong>Update other services</strong> — prioritize: financial accounts, government accounts, healthcare, insurance, then everything else. This takes weeks. The forwarding catches what you miss.</li>
    <li><strong>Do NOT delete your Gmail yet</strong> — keep it active with forwarding for at least 6–12 months</li>
  </ol>
  <p style="color:#94a3b8;font-size:0.85rem;">Time: 1 hour setup; weeks to months for address migration. This is the hard one.</p>
</section>

<h2>Phase 3 — Media and storage (Week 4–8)</h2>

<section class="card">
  <h2>3A: YouTube</h2>
  <p>You cannot fully replace YouTube. The content you watch is there because creators publish there. <strong>The realistic goal is to watch YouTube without being tracked.</strong></p>
  <ul>
    <li><strong>Use YouTube without signing in</strong> — your history isn\'t tied to your identity. Use Brave (blocks YouTube ads natively) or Firefox + uBlock Origin.</li>
    <li><strong>Use Invidious or FreeTube (desktop app)</strong> — privacy frontends that strip tracking entirely</li>
    <li><strong>Nebula</strong> ($30/year) — many top educational creators publish here first or exclusively</li>
  </ul>
</section>

<section class="card">
  <h2>3B–3E: Photos, Drive, Calendar, Contacts</h2>
  <ul>
    <li><strong>Photos:</strong> Export via Takeout, move to iCloud, Proton Drive, or a local NAS. See <a href="/google/your-content/">your content guide</a> for the metadata sidecar issue.</li>
    <li><strong>Drive:</strong> Move to Proton Drive, Nextcloud, or local storage. Export → Google formats auto-convert to .docx/.xlsx on export.</li>
    <li><strong>Calendar:</strong> Export as .ics → import into Proton Calendar, Apple Calendar, or Fastmail.</li>
    <li><strong>Contacts:</strong> Export as vCard → import into your new email provider\'s contacts system.</li>
  </ul>
</section>

<h2>Phase 4 — Drain the reservoir (Week 6–10)</h2>

<div class="card card-caution">
  <p>This is the phase nobody else covers. You\'ve stopped the flow of new data. Now deal with the data Google already has.</p>
</div>

<section class="card">
  <h2>4A: Audit what Google has</h2>
  <p>Go to <strong>myaccount.google.com/data-and-privacy</strong>. Spend 30 minutes looking at it. Not because you need to — because understanding the scope is the most effective motivation for completing this guide. Most people are disturbed by what they find.</p>
  <ul>
    <li>Web & App Activity: every search, every app interaction, every Chrome page visit</li>
    <li>Location History: everywhere you\'ve been. timeline.google.com.</li>
    <li>YouTube History: everything you\'ve watched and searched</li>
    <li>Voice & Audio Activity: every Google Assistant interaction, recorded as actual audio files</li>
    <li>Ad Personalization: the advertising profile built from all of the above</li>
  </ul>
</section>

<section class="card card-steps">
  <h2>4B: Delete historical data</h2>
  <ul>
    <li><strong>Location:</strong> timeline.google.com → Settings → Delete all. Set auto-delete to 3 months.</li>
    <li><strong>Web & App Activity:</strong> myactivity.google.com → Delete activity by → All time → All products. Set auto-delete to 3 months.</li>
    <li><strong>YouTube History:</strong> myactivity.google.com → filter by YouTube → Delete all. Set auto-delete to 3 months.</li>
    <li><strong>Voice & Audio:</strong> myactivity.google.com → filter by Voice & Audio → Delete all. Turn off Voice & Audio Activity.</li>
    <li><strong>Ad Personalization:</strong> adssettings.google.com → turn off.</li>
  </ul>
  <p><strong>Before deleting:</strong> download everything first via <a href="https://takeout.google.com" target="_blank" rel="noopener">takeout.google.com</a>. This is your personal archive of everything Google has collected about you. Store it securely.</p>
</section>

<section class="card">
  <h2>4C: Close or contain the account</h2>
  <p><strong>If keeping (for YouTube fallback or other services):</strong> Remove all personal info from your Google Profile, turn off all Activity Controls, remove payment methods, enable Inactive Account Manager to auto-delete if abandoned.</p>
  <p style="margin-top:.5rem;"><strong>If deleting entirely:</strong> myaccount.google.com → Data and Privacy → Delete your Google Account. 30-day grace period. Do not do this until Phase 2 (Gmail migration) is complete and verified. The most common mistake: deleting before updating a financial institution\'s email, then being locked out of the financial account.</p>
</section>

<h2>Phase 5 — Ongoing containment (permanent)</h2>

<section class="card card-note">
  <h2>What you can\'t fully escape</h2>
  <ul>
    <li><strong>Google Analytics</strong> — on most websites. Brave and Firefox + uBlock Origin block it.</li>
    <li><strong>Google Fonts</strong> — loaded from Google servers on many sites. Privacy browsers handle this.</li>
    <li><strong>reCAPTCHA</strong> — on millions of sites. There is no avoiding this without breaking many websites. One area where Google\'s surveillance is inescapable.</li>
    <li><strong>AMP</strong> — Brave and Firefox redirect AMP links to original sources automatically.</li>
    <li><strong>Gmail contacts</strong> — people who email you from Gmail are tracked by Google. Encrypted email (Proton-to-Proton) solves this for contacts who are also leaving Google.</li>
  </ul>
</section>

<section class="card card-honest">
  <h2>What you genuinely can\'t replace</h2>
  <ul>
    <li><strong>Google Maps\' business data</strong> — hours, reviews, real-time info. Use OsmAnd for navigation. Use a browser (not the app, not signed in) for business lookups.</li>
    <li><strong>YouTube\'s content library</strong> — no alternative matches the breadth. Watch without tracking instead.</li>
    <li><strong>Google Scholar</strong> — academic research. No real equivalent yet. Use through Brave.</li>
    <li><strong>Gmail\'s deliverability</strong> — Proton and Tuta emails occasionally land in spam at servers that trust Google implicitly. Real consideration for professional email.</li>
    <li><strong>Android app compatibility</strong> — some banking and messaging apps require Google Play Services. GrapheneOS\'s sandboxed Play approach resolves most, not all.</li>
  </ul>
  <p style="margin-top:.75rem;">Being honest about these gaps doesn\'t undermine the guide. It strengthens it. Knowing where the limits are helps you work with them instead of being surprised by them.</p>
</section>

<section class="card">
  <h2>The realistic timeline</h2>
  <ul>
    <li><strong>Week 1–2:</strong> Replace Chrome (15 min), Search (2 min), contain Android (30 min–2 hrs), delete Maps history (15 min)</li>
    <li><strong>Week 2–6:</strong> Gmail migration setup (1 hr); update other services (ongoing for weeks)</li>
    <li><strong>Week 4–8:</strong> Photos, Drive, Calendar, Contacts migration (a few hours each)</li>
    <li><strong>Week 6–10:</strong> Drain the reservoir (2–4 hours, emotionally intense, technically simple)</li>
    <li><strong>Ongoing:</strong> New habits, occasional Google use via browser only, maintaining the new defaults</li>
  </ul>
  <p style="margin-top:.75rem;color:#94a3b8;font-size:0.875rem;">Total: about 3 months for a thorough de-Googling. The browser and search changes are instant. The email migration takes weeks. The data cleanup takes a focused afternoon. The habit changes take a month before they feel natural.</p>
</section>

<section class="card">
  <h2>Related guides</h2>
  <ul>
    <li><a href="/google/your-content/">Export your Google data</a></li>
    <li><a href="/google/gmail/">Gmail migration guide</a></li>
    <li><a href="/google/google-search/">Google Search alternatives</a></li>
    <li><a href="/google/android/">Android de-Googling</a></li>
    <li><a href="/google/google-maps/">Google Maps alternatives</a></li>
    <li><a href="/google/youtube/">YouTube without tracking</a></li>
  </ul>
</section>
'''
    return page_shell(
        "Cutting the Pipeline — Google | DitchTheMega",
        "A phased, realistic guide to leaving Google. Stop the flow of new data and drain the reservoir of what Google already holds. Takes about 3 months. Start with the browser.",
        f"{SITE_URL}/google/cutting-the-pipeline/",
        content
    )

def build_google_data_cleanup_page(svc):
    slug = svc["slug"]
    sections = []
    sections.append(f'<div class="page-hero"><div class="breadcrumb"><a href="/">Home</a> › <a href="/google/">Google</a> › Data Cleanup</div><h1>{e(svc["title"])}</h1><p class="subtitle">{e(svc.get("subtitle",""))}</p></div>')
    if svc.get("why_this_matters"):
        sections.append(f'<section class="card card-privacy"><h2>Why this matters</h2><p>{e(svc["why_this_matters"])}</p></section>')
    # Each step
    step_keys = [("step_1_web_activity","Step 1"),("step_2_location","Step 2"),("step_3_youtube","Step 3"),("step_4_voice","Step 4"),("step_5_ads","Step 5"),("step_6_dashboard","Step 6"),("step_7_export","Step 7")]
    for key, label in step_keys:
        step = svc.get(key)
        if not step: continue
        title = e(step.get("title",""))
        url = step.get("url","")
        steps_list = step.get("steps",[])
        what = e(step.get("what_you_delete") or step.get("what_you_see") or step.get("why",""))
        url_link = f' → <a href="{e(url)}" target="_blank" rel="noopener">{e(url)}</a>' if url else ""
        steps_html = "".join(f"<li>{e(s)}</li>" for s in steps_list)
        what_html = f'<p class="alt-cost" style="margin-top:.5rem;"><strong>What you delete/see:</strong> {what}</p>' if what else ""
        sections.append(f'<section class="card card-steps"><h2>{label}: {title}{url_link}</h2><ol>{steps_html}</ol>{what_html}</section>')
    if svc.get("account_deletion"):
        ad = svc["account_deletion"]
        url = ad.get("url","")
        url_link = f' → <a href="{e(url)}" target="_blank" rel="noopener">{e(url)}</a>' if url else ""
        steps_html = "".join(f"<li>{e(s)}</li>" for s in ad.get("steps",[]))
        sections.append(f'<section class="card"><h2>Deleting your account{url_link}</h2><ol>{steps_html}</ol></section>')
    if svc.get("migration_steps"):
        sections.append(f'<section class="card card-steps"><h2>How to approach this</h2>{render_steps(svc["migration_steps"])}</section>')
    sections.append('<section class="card"><h2>Related guides</h2><ul><li><a href="/google/cutting-the-pipeline/">Cutting the Pipeline — the full 3-month de-Google plan</a></li><li><a href="/google/your-content/">Your Google content — what to export</a></li></ul></section>')
    return page_shell(
        f"{svc['title']} | DitchTheMega",
        svc.get("subtitle",""),
        f"{SITE_URL}/google/{slug}/",
        "\n".join(sections)
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

<h2>Section 4 — The approach we don\'t recommend</h2>

<section class="card card-note">
  <h2>Google DRM tools — a shorter section</h2>
  <p>Google\'s content ecosystem has significantly less DRM lock-in than Apple\'s or Amazon\'s. Most Google Play Books titles use Adobe DRM (interoperable across many readers) or are DRM-free. Google participates in Movies Anywhere, making movie purchases accessible across platforms. The urgency of DRM removal is lower here than with Kindle or Audible.</p>
  <p>For titles with Adobe DRM: the same Calibre plugin ecosystem discussed in the Amazon guide handles Adobe DRM. The same legal landscape applies — DMCA Section 1201, circumvention illegal regardless of purchase, enforcement focused on tool makers not end users. The same risks are real.</p>
  <p>Our position: We believe purchased content should be owned. The law says otherwise. Tools exist. Risks are real. Adults can make their own decisions with full information. That is all.</p>
  <p>The structural solution: check whether your Google Play Books titles are DRM-free before assuming they\'re locked. Many are. For future ebook purchases, prefer DRM-free sources.</p>
</section>

<h2>What Google genuinely does better than any alternative</h2>

<section class="card card-honest">
  <ul>
    <li><strong>Google Maps business data</strong> — hours, reviews, real-time info. No alternative matches the density. Use OsmAnd or Apple Maps for navigation; use a browser (not the app, not signed in) for business lookups.</li>
    <li><strong>YouTube\'s content library</strong> — no alternative platform has the same breadth. Watch without tracking (Invidious, Brave browser) rather than pretending alternatives exist.</li>
    <li><strong>Google Scholar</strong> — academic research. No real equivalent yet.</li>
    <li><strong>Gmail\'s deliverability</strong> — Proton and Tuta emails occasionally land in spam at servers that implicitly trust Gmail. Real consideration for professional email.</li>
    <li><strong>Google Translate</strong> — DeepL is better for many language pairs, but Google covers more languages and has camera translation and conversation mode.</li>
  </ul>
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

<h2>The approach we don\'t recommend</h2>

<section class="card card-note">
  <h2>Data scraping tools and fake deletion</h2>
  <p>Tools exist that can bulk-download your Instagram posts, your Facebook data, and in some cases the posts of others through browser automation or API scraping. Meta\'s Terms of Service prohibit automated scraping. Using these tools can result in account suspension or permanent ban. In some cases, Meta has pursued legal action against scraping tool operators.</p>
  <p>For your own data, the Download Your Information tool is the legal path and provides the same or better output. We recommend using it.</p>
  <p><strong>Fake account deletion warning:</strong> Removing all your content and changing your name is not deletion. Your advertising profile remains. Your data stays on Meta\'s servers. Use the real deletion process: facebook.com/help/delete_account. The 30-day grace period exists — use it. After 30 days, deletion begins and is permanent.</p>
  <p>Our position: The official export tools are comprehensive. The reason to use the tools over scrapers is that they\'re more complete, less risky, and you don\'t leave a trace of your own data behind on an unauthorized tool\'s servers.</p>
</section>

<h2>What Meta genuinely does that nothing else does</h2>

<section class="card card-honest">
  <ul>
    <li><strong>Your social graph</strong> — the specific network of people you\'re connected to, the shared history, the groups you\'ve been part of for years. This doesn\'t exist elsewhere and can\'t be transferred.</li>
    <li><strong>Memories / On This Day</strong> — the curated history of what you posted and who you were with, surfaced unexpectedly. This is by design. It keeps you on the platform. It\'s also, sometimes, genuinely meaningful.</li>
    <li><strong>Community groups</strong> — neighborhood groups, parent groups, hobby communities, support communities. Many have no equivalent elsewhere. Some do (Discord, Reddit, Nextdoor). Many don\'t.</li>
    <li><strong>Event discovery</strong> — for local events, Facebook Events has no real equivalent for the "what\'s happening near me this weekend" use case.</li>
    <li><strong>Messenger with the deceased</strong> — if you have message threads with people who are no longer alive, those conversations may exist nowhere else. Export them before leaving. This is one of Meta\'s genuinely irreplaceable things.</li>
  </ul>
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

<h2>The approach we don\'t recommend</h2>

<section class="card card-note">
  <h2>Xbox game DRM and Microsoft Store movies</h2>
  <p>Xbox digital games use Microsoft\'s DRM — they require an account check to run. Game cracking and DRM removal for Xbox games is primarily associated with piracy rather than personal backup. We mention it only for completeness.</p>
  <p>Microsoft Store movie purchases: Microsoft participates in Movies Anywhere, making most purchases accessible across platforms already. The DRM removal question is largely resolved by that portability.</p>
  <p>Our position: Same as the other guides. GOG.com is the structural solution for PC gaming — buy DRM-free and own the installer outright. Movies Anywhere addresses the movie side.</p>
</section>

<h2>What Microsoft genuinely does better</h2>

<section class="card card-honest">
  <ul>
    <li><strong>Excel for complex models</strong> — nothing fully matches Excel for advanced pivot tables, financial models, and complex macros. LibreOffice handles 90% of use cases. The 10% is real.</li>
    <li><strong>Office format compatibility</strong> — .docx and .xlsx are the universal standard for business document exchange. LibreOffice conversion is good but not perfect on complex documents.</li>
    <li><strong>Enterprise integration</strong> — Active Directory, Exchange, Teams, SharePoint, and Azure create dependencies in organizational contexts that are genuinely hard to replace without a company-wide commitment.</li>
    <li><strong>Xbox Game Pass value</strong> — $15/month for hundreds of games is genuinely good value if you\'re a gamer. No equivalent exists in the same price bracket.</li>
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

def build_apple_privacy_comparison():
    content = '''
<div class="page-hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/apple/">Apple</a> › Privacy vs Lock-In</div>
  <h1>The Privacy Question</h1>
  <p class="subtitle">We need to have an honest conversation before you leave Apple.</p>
</div>
<div class="card card-honest" style="margin-bottom:1.5rem;">
  <p>This entire site exists to help you leave Big Tech ecosystems. Every guide we publish documents the lock-in, the data you can take with you, and the alternatives that exist. We believe you should be able to leave any ecosystem freely, and we build the tools to make that possible.</p>
  <p>But leaving Apple is not the same as leaving Google, Amazon, or Meta. And the reason it&#39;s different is privacy.</p>
  <p>Apple is not perfect. Apple&#39;s ecosystem is expensive, proprietary, and deliberately designed to make leaving difficult. The hardware lock-in is real. The DRM on purchased content is real. The iMessage social pressure is real. These are legitimate reasons to leave, and the rest of this guide covers all of them.</p>
  <p>But on the specific question of how your data is handled, Apple is meaningfully better than the alternatives most people would switch to. If you leave Apple for Google&#39;s ecosystem without understanding this, you may solve a lock-in problem by creating a surveillance problem. That is a trade you should make knowingly, not accidentally.</p>
</div>

<h2>What Apple Actually Does Well</h2>
<p>Apple&#39;s business model is selling hardware at a premium. Google&#39;s business model is selling your attention to advertisers. This difference shapes every product decision both companies make.</p>
<ul>
  <li><strong>On-device processing.</strong> Apple processes a remarkable amount of data on your device rather than sending it to their servers. Siri requests, photo recognition, text predictions, health data analysis, and many machine learning features run locally on your iPhone or Mac. When Apple does send data to their servers, they use techniques like differential privacy to add statistical noise that prevents individual identification. Google processes most of this on their servers, because processing it on their servers is how they build the advertising profile that funds the company.</li>
  <li><strong>App Tracking Transparency.</strong> In 2021, Apple introduced a requirement that apps ask your permission before tracking you across other apps and websites. This single feature cost Meta an estimated $10 billion in advertising revenue in its first year. It is the most consequential consumer privacy feature any major tech company has shipped. Google has not implemented anything equivalent on Android; doing so would undermine their own advertising business.</li>
  <li><strong>Minimal advertising profile.</strong> Apple runs an advertising business, but it is small relative to their revenue and does not depend on a detailed behavioral profile. Apple&#39;s ad targeting is based on broad demographics and the content you&#39;re currently viewing, not on a comprehensive history of your searches, locations, emails, and browsing.</li>
  <li><strong>End-to-end encryption by default.</strong> iMessage and FaceTime are end-to-end encrypted. Apple cannot read your messages or listen to your calls even if compelled by law enforcement (assuming you have Advanced Data Protection enabled). Google Messages has added end-to-end encryption for RCS, but it is not enabled by default in all configurations.</li>
  <li><strong>Advanced Data Protection.</strong> Apple offers an option to end-to-end encrypt nearly all iCloud data, including backups, photos, notes, and more. When enabled, Apple cannot access this data. This is a genuine zero-knowledge architecture for your cloud storage. Google does not offer an equivalent for Google Drive, Gmail, or Google Photos.</li>
  <li><strong>Health data.</strong> Apple Health data is encrypted on-device and in iCloud (with Advanced Data Protection). Apple has consistently refused to monetize health data or share it with third parties.</li>
</ul>

<h2>What Apple Does Not Do Well</h2>
<p>Acknowledging Apple&#39;s privacy strengths does not mean ignoring Apple&#39;s privacy weaknesses.</p>
<ul>
  <li><strong>Siri data collection.</strong> Apple was caught in 2019 having human contractors listen to Siri recordings for quality assurance without adequate disclosure. They reformed the program, but the incident revealed that &#34;privacy-focused&#34; does not mean &#34;perfect.&#34;</li>
  <li><strong>CSAM scanning controversy.</strong> In 2021, Apple announced plans to scan photos on users&#39; devices for child sexual abuse material before upload to iCloud. The backlash was severe; privacy advocates argued that on-device scanning created a surveillance infrastructure that could be expanded to other content. Apple shelved the plan, but the fact that they designed it at all raised questions about their commitment to the principle that your device is yours.</li>
  <li><strong>China and government compliance.</strong> Apple stores Chinese users&#39; iCloud data on servers operated by a Chinese state-owned company. This means the Chinese government has potential access to Chinese Apple users&#39; data. Apple&#39;s privacy protections are strong in countries with strong privacy laws. They are weaker where governments demand access.</li>
  <li><strong>Closed source.</strong> Apple&#39;s software is largely closed source. When Apple says they process data on-device, you are trusting their claim. You cannot verify it the way you can verify an open-source application.</li>
  <li><strong>App Store monopoly and data access.</strong> Apple&#39;s own apps have privileged access to device data that third-party apps do not. Apple is both the platform operator and a competitor to apps on that platform.</li>
</ul>

<h2>The Comparison That Matters</h2>
<p>If you leave Apple, where are you going? That determines whether the move is a privacy upgrade, a lateral move, or a downgrade.</p>
<ul>
  <li><strong>Apple → Google (Android with Google Services):</strong> This is a privacy downgrade for most people. You gain openness and lose the privacy architecture Apple has built over fifteen years. Google will know your location, searches, emails, app usage, contacts, and browsing history.</li>
  <li><strong>Apple → De-Googled Android (GrapheneOS on a Pixel):</strong> This is a privacy upgrade. GrapheneOS strips Google&#39;s surveillance infrastructure from Android while maintaining app compatibility. You get an open-source operating system and no data flowing to Google or Apple. The tradeoff is real — setup requires flashing a phone and some apps may not work correctly.</li>
  <li><strong>Apple → Linux (desktop/laptop):</strong> A privacy upgrade on the desktop side. Linux distributions collect no telemetry by default. The tradeoff is software compatibility — some professional applications are not available on Linux.</li>
  <li><strong>Apple → Microsoft (Windows):</strong> A lateral move at best. Windows collects telemetry by default and integrates with Microsoft&#39;s cloud services in ways that mirror Google&#39;s data collection. You gain hardware choice and lose Apple&#39;s privacy architecture.</li>
</ul>

<h2>The Honest Assessment</h2>
<div class="card card-caution">
  <p>If you are leaving Apple because of lock-in, DRM, hardware cost, repairability, or because you disagree with Apple&#39;s control over what you can install on your own device — these are all legitimate reasons. This guide exists to help you do it.</p>
  <p>If you are leaving Apple because of privacy — pause. Apple&#39;s privacy is not perfect, and we have documented the weaknesses above. But Apple&#39;s privacy architecture is, on balance, the strongest of any major consumer technology ecosystem. Leaving Apple for Google without additional steps will almost certainly result in more of your personal data being collected, analyzed, and monetized.</p>
  <p>The best outcome is not &#34;leave Apple for Google.&#34; The best outcome is &#34;leave Apple for an open, privacy-respecting stack.&#34; That means GrapheneOS on your phone, Linux on your computer, Proton for email, Signal for messaging, and DRM-free content purchases going forward. This is achievable — it is also more work than switching to a Samsung Galaxy with Google&#39;s defaults.</p>
  <p>We are not telling you to stay with Apple. We are telling you to know what you are choosing.</p>
</div>

<h2>One More Thing</h2>
<p>There is an irony in a site called &#34;Ditch the Mega&#34; telling you that one of the megas is better than the others on a specific dimension. We are comfortable with that irony because this site is built on honesty, not ideology. We are not anti-Big Tech for the sake of being anti-Big Tech. We are pro-choice in the literal sense: you should be able to choose your tools, your ecosystem, your level of privacy, and your level of convenience — with full information, not a sales pitch from any direction, including ours.</p>
<p>Apple makes it hard to leave. That is a problem, and we document it. Apple also makes it hard for other companies to surveil you. That is a feature, and we document that too. Both things are true.</p>

<div class="card" style="margin-top:2rem;">
  <h3>Related guides</h3>
  <ul>
    <li><a href="/apple/">Full Apple exit guide</a></li>
    <li><a href="/apple/apple-your-content/">Your Digital Content — DRM, what you keep, what you lose</a></li>
    <li><a href="/google/cutting-the-pipeline/">Cutting the Google Pipeline — if you&#39;re considering Android, read this first</a></li>
    <li><a href="/guides/secure-home-automation/">Replacing HomeKit with Home Assistant</a></li>
    <li><a href="/alternatives/">Privacy-respecting alternatives across all categories</a></li>
  </ul>
</div>
'''
    return page_shell(
        "Apple Privacy vs Google: Honest Comparison Before You Switch | DitchTheMega",
        "Comparing Apple and Google on privacy \u2014 where Apple wins, where it doesn&#39;t, and what switching actually means for your data.",
        f"{SITE_URL}/apple/privacy-comparison/",
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
            if slug == "google-data-cleanup":
                f.write(build_google_data_cleanup_page(svc))
            else:
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

    # Apple Privacy Comparison page (custom, not YAML-driven)
    out_dir = f"{PUBLIC_DIR}/apple/privacy-comparison"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_apple_privacy_comparison())
    print("Built: apple/privacy-comparison/index.html")

    # What Is Lock-In framework page
    out_dir = f"{PUBLIC_DIR}/what-is-lock-in"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_what_is_lock_in())
    print("Built: what-is-lock-in/index.html")

    # Privacy and Terms pages
    out_dir = f"{PUBLIC_DIR}/privacy"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_dtm_privacy())
    print("Built: privacy/index.html")

    out_dir = f"{PUBLIC_DIR}/terms"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_dtm_terms())
    print("Built: terms/index.html")

    # Google Cutting the Pipeline
    out_dir = f"{PUBLIC_DIR}/google/cutting-the-pipeline"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_google_cutting_pipeline())
    print("Built: google/cutting-the-pipeline/index.html")

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
            "Facebook, Instagram, WhatsApp, and Threads. Here's how to reduce your exposure to Meta's surveillance infrastructure. <a href='/what-is-lock-in/' style='color:#94a3b8;font-size:.85rem;'>Why is this harder than canceling? &rarr;</a>",
            "Practical guides to leaving Facebook, Instagram, WhatsApp, and Threads. No lectures. Just the steps.",
            f"{SITE_URL}/meta/",
            lose_html='''<div class="card card-honest" style="margin-bottom:1.5rem;">
  <h2>What you genuinely lose when you leave Meta</h2>
  <ul>
    <li><strong>Your social graph</strong> \u2014 the specific network of people you\u2019re connected to, the shared history, the groups. It doesn\u2019t transfer anywhere.</li>
    <li><strong>Community groups</strong> \u2014 neighborhood groups, parent groups, hobby communities. Many have no equivalent elsewhere.</li>
    <li><strong>Event discovery</strong> \u2014 for local events, Facebook Events has no real equivalent for casual \u201cwhat\u2019s happening near me\u201d discovery.</li>
    <li><strong>Memories and On This Day</strong> \u2014 the curated history surfaced unexpectedly. It\u2019s by design. It\u2019s also sometimes genuinely meaningful.</li>
    <li><strong>Messenger threads with the deceased</strong> \u2014 conversations with people who are no longer alive may exist nowhere else. Export before leaving.</li>
  </ul>
</div>'''))
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
            "Windows, Microsoft 365, LinkedIn, and OneDrive. Here's how to reduce your dependency on Microsoft's stack. <a href='/what-is-lock-in/' style='color:#94a3b8;font-size:.85rem;'>Why is this harder than canceling? &rarr;</a>",
            "Practical guides to leaving Windows, Microsoft 365, LinkedIn, and OneDrive. Honest about what stays Windows-only.",
            f"{SITE_URL}/microsoft/",
            lose_html='''<div class="card card-honest" style="margin-bottom:1.5rem;">
  <h2>What you genuinely lose when you leave Microsoft</h2>
  <ul>
    <li><strong>Excel for complex models</strong> \u2014 nothing fully matches Excel for advanced pivot tables, financial models, and macros. LibreOffice handles 90%. The 10% is real.</li>
    <li><strong>Office format compatibility</strong> \u2014 .docx and .xlsx are the universal business document standard. Conversion is good but not perfect on complex documents.</li>
    <li><strong>Xbox game library</strong> \u2014 digital game purchases are tied to your Microsoft account. GOG.com is the DRM-free alternative for future purchases.</li>
    <li><strong>LinkedIn professional presence</strong> \u2014 for job seekers and B2B professionals, LinkedIn remains where opportunities happen. Leaving has real career implications.</li>
    <li><strong>Enterprise integration</strong> \u2014 Active Directory, Teams, SharePoint. In organizational contexts, these dependencies are structural and hard to replace.</li>
  </ul>
</div>'''))
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

    # Secure Home Automation guide
    out_dir = f"{PUBLIC_DIR}/guides/secure-home-automation"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w") as f:
        f.write(build_guide_home_automation())
    print("Built: guides/secure-home-automation/index.html")

    # Expanded alternatives category pages
    alt_pages = build_alternatives_pages()
    for slug, content in alt_pages.items():
        out_dir = f"{PUBLIC_DIR}/alternatives/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/index.html", "w") as f:
            f.write(content)
        print(f"Built: alternatives/{slug}/index.html")

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
