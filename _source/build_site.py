#!/usr/bin/env python3
"""Static-site generator for the Basecamp Getaways rebuild.
Reads property_catalog.json + property_images.json, renders index.html and
one page per property into ./site, plus shared CSS/JS and a booking-widget config.
"""
import json, os, re, html, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "basecamp-site3")
ASSETS = os.path.join(SITE, "assets")
PROP_DIR = os.path.join(SITE, "property")
HERO_SRC = os.path.join(BASE, "hero_assets")
LOGO_SRC = os.path.join(BASE, "logo.png")   # drop the badge here to enable the image logo
HAS_LOGO = os.path.exists(LOGO_SRC)
HERO_FILES = sorted([f for f in os.listdir(HERO_SRC) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]) if os.path.isdir(HERO_SRC) else []

catalog = json.load(open(os.path.join(BASE, "property_catalog.json")))["properties"]
images = {p["name"]: p["images"] for p in json.load(open(os.path.join(BASE, "property_images.json")))["properties"]}
# Airbnb photo sets (ordered, list of URL strings) — primary source of truth
airbnb = {p["name"]: p.get("images", []) for p in json.load(open(os.path.join(BASE, "airbnb_images.json")))["properties"]}

# ---- The 17 publicly-listed properties, grouped into collections ----
SLUGS = {
    "Watersedge-Anderson": "watersedge",
    "Hooked on Hartwell": "hookedonhartwell",
    "Quittin Time Cottage-Lake Hartwell": "quittintimecottagelakehartwell",
    "The Keowee Getaway": "thekeoweegetaway",
    "Lake Hartwell Oasis-Anderson": "bradydrlakeharwelloasis",
    "Hartwell Haven": "hartwellhaven",
    "Walker Cove": "walkercove",
    "Lake Place": "lakeplace",
    "Foothills Cottage": "foothillscottage",
    "Endless Views-Mineral Bluff": "endlessviews",
    "River Run Retreat-Hiawassee": "riverrunretreat",
    "Star Mountain-Blue Ridge": "starmountain",
    "River Run Retreat Studio-Hiawassee": "riverrunretreatstudio",
    "Cozy Bear Cabin-Blue Ridge": "cozybearcabin",
    "Blue Chalet-Mineral Bluff": "bluechalet",
    "Blue Wall Farm Basecamp-Travelers Rest": "bluewallfarmbasecamp",
    "Saluda River Basecamp-Greenville": "riverfrontescapebasecampgreenville",
}
COLLECTIONS = [
    {"id": "lake-hartwell", "title": "Lake Hartwell Collection",
     "tagline": "Escape to the lake",
     "blurb": "Waterfront homes on South Carolina's Lake Hartwell — docks, game rooms, and sunset views, loaded with amenities and designed with care for the vacation of your dreams.",
     "names": ["Watersedge-Anderson","Hooked on Hartwell","Quittin Time Cottage-Lake Hartwell","The Keowee Getaway","Lake Hartwell Oasis-Anderson","Hartwell Haven","Walker Cove","Lake Place","Foothills Cottage"]},
    {"id": "blue-ridge", "title": "Blue Ridge Georgia Collection",
     "tagline": "Escape to the mountains",
     "blurb": "Luxury cabins tucked into the North Georgia mountains near Blue Ridge — hot tubs, fireplaces, game rooms, and breathtaking scenery just minutes from downtown.",
     "names": ["Endless Views-Mineral Bluff","River Run Retreat-Hiawassee","Star Mountain-Blue Ridge","River Run Retreat Studio-Hiawassee","Cozy Bear Cabin-Blue Ridge","Blue Chalet-Mineral Bluff"]},
    {"id": "greenville", "title": "Greenville & Travelers Rest",
     "tagline": "Upstate South Carolina",
     "blurb": "One of the most desirable getaways in the Southeast — from a riverfront luxury home minutes from downtown Greenville to a charming farm stay in Travelers Rest.",
     "names": ["Blue Wall Farm Basecamp-Travelers Rest","Saluda River Basecamp-Greenville"]},
]

# ---- Amenity humanization ----
AMENITY_LABELS = {
    "ac":"Air conditioning","wifi":"Fast Wi‑Fi","tv":"Smart TV","kitchen":"Full kitchen",
    "washer":"Washer","dryer":"Dryer","free_parking":"Free parking","free_on_premise_parking":"Free parking on premises",
    "pool":"Pool","hot_tub":"Hot tub","jacuzzi":"Hot tub","bbq":"BBQ grill","barbeque_utensils":"BBQ utensils",
    "fire_pit":"Fire pit","fireplace":"Indoor fireplace","indoor_fireplace":"Indoor fireplace",
    "pool_table":"Pool table","game_room":"Game room","boat_slip":"Boat slip / dock","dock":"Dock",
    "kayak":"Kayaks","beach_essentials":"Beach essentials","bbq_grill":"BBQ grill","coffee_maker":"Coffee maker",
    "coffee":"Coffee","dishwasher":"Dishwasher","microwave":"Microwave","oven":"Oven","stove":"Stove",
    "refrigerator":"Refrigerator","freezer":"Freezer","dining_table":"Dining table","cooking_basics":"Cooking basics",
    "dishes_and_silverware":"Dishes & silverware","wine_glasses":"Wine glasses","blender":"Blender",
    "heating":"Heating","ceiling_fan":"Ceiling fans","hot_water":"Hot water","bathtub":"Bathtub",
    "shampoo":"Shampoo","conditioner":"Conditioner","body_soap":"Body soap","hair_dryer":"Hair dryer",
    "bed_linens":"Premium linens","extra_pillows_and_blankets":"Extra pillows & blankets","essentials":"Essentials",
    "iron":"Iron","crib":"Crib","high_chair":"High chair","childrens_books_and_toys":"Kids' books & toys",
    "childrens_dinnerware":"Kids' dinnerware","board_games":"Board games","books":"Books",
    "patio":"Patio","garden":"Garden","outdoor_seating":"Outdoor seating","outdoor_dining_area":"Outdoor dining",
    "alfresco_dining":"Alfresco dining","balcony":"Balcony","bbq_area":"BBQ area",
    "smoke_detector":"Smoke detector","carbon_monoxide_detector":"Carbon monoxide detector",
    "fire_extinguisher":"Fire extinguisher","first_aid_kit":"First aid kit",
    "ev_charger":"EV charger","gym":"Gym","workspace":"Dedicated workspace","laptop_friendly_workspace":"Workspace",
    "self_check_in":"Self check‑in","smart_lock":"Smart lock","keypad":"Keypad entry",
    "pets_allowed":"Pet friendly","long_term_stays":"Long‑term stays","single_level_home":"Single‑level home",
    "waterfront":"Waterfront","lake_access":"Lake access","mountain_view":"Mountain view","lake_view":"Lake view",
    "cleaning_products":"Cleaning products","clothes_drying_rack":"Drying rack","baking_sheet":"Baking sheet",
    "bowling_alley":"Indoor games","cleaning_available_during_stay":"Cleaning available",
}
# Amenities worth surfacing as headline icons (in priority order)
HEADLINE = ["hot_tub","jacuzzi","pool","pool_table","game_room","boat_slip","dock","fire_pit","fireplace",
            "wifi","ac","kitchen","washer","dryer","bbq","free_on_premise_parking","free_parking",
            "pets_allowed","tv","waterfront","mountain_view"]

def amen_label(slug):
    return AMENITY_LABELS.get(slug, slug.replace("_"," ").title())

CHECK = '<svg viewBox="0 0 24 24" class="ic" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>'
PIN = '<svg viewBox="0 0 24 24" class="pin" aria-hidden="true"><path d="M12 21s-7-6.6-7-11a7 7 0 0114 0c0 4.4-7 11-7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>'

def esc(s):
    return html.escape(s or "", quote=True)

def title_of(name):
    # strip trailing location suffix after a hyphen
    return re.sub(r"\s*-\s*[^-]+$", "", name).strip() if "-" in name else name.strip()

def prop_by_name(name):
    for p in catalog:
        if p["name"] == name:
            return p
    return None

def location_str(p):
    parts = [p.get("city"), p.get("state")]
    return ", ".join([x for x in parts if x])

def specs(p):
    return p.get("max_guests"), p.get("bedrooms"), p.get("bathrooms")

# These 4 listings' Airbnb photos are served under a migrated namespace that 404s
# in static HTML, so use the reliable Hospitable photo set for them.
HOSP_FALLBACK = {
    "River Run Retreat-Hiawassee", "River Run Retreat Studio-Hiawassee",
    "Star Mountain-Blue Ridge", "Blue Wall Farm Basecamp-Travelers Rest",
}

def imgs_for(name):
    if name not in HOSP_FALLBACK:
        ab = airbnb.get(name) or []
        if ab:
            return ab  # Airbnb ordered URLs (exact parity with listing)
    arr = images.get(name, [])
    return [i["url"] for i in arr if i.get("url")]

def hero_img(name, p):
    arr = imgs_for(name)
    if arr:
        return arr[0]
    return p.get("picture") or ""

def format_description(text):
    if not text:
        return ""
    text = text.replace("\r\n","\n")
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        lines = [esc(l.strip()) for l in b.split("\n") if l.strip()]
        out.append("<p>" + "<br>".join(lines) + "</p>")
    return "\n".join(out)

# Build property records
records = {}
for name, slug in SLUGS.items():
    p = prop_by_name(name)
    if not p:
        print("MISSING", name); continue
    g, bd, ba = specs(p)
    gallery = imgs_for(name)
    am = p.get("amenities", []) or []
    headline = [a for a in HEADLINE if a in am][:6]
    records[name] = {
        "name": name, "slug": slug, "title": title_of(name),
        "public_name": p.get("public_name") or title_of(name),
        "city": p.get("city"), "state": p.get("state"), "street": p.get("street"),
        "location": location_str(p),
        "coords": p.get("coordinates") or {},
        "guests": g, "bedrooms": bd, "bathrooms": ba, "beds": p.get("beds"),
        "ptype": (p.get("property_type") or "home").replace("_"," ").title(),
        "summary": p.get("summary") or "",
        "description": p.get("description") or p.get("summary") or "",
        "amenities": am, "headline": headline,
        "pets": (p.get("house_rules") or {}).get("pets_allowed"),
        "gallery": gallery,
        "hero": hero_img(name, p),
    }

# ---------- HTML helpers ----------
def brand_inner(pre):
    if HAS_LOGO:
        return f'<img class="brand-logo" src="{pre}assets/logo.png" alt="Basecamp Getaways">'
    return ('<span class="brand-mark">▲</span>'
            '<span class="brand-text">Basecamp<span class="brand-sub">GETAWAYS</span></span>')

def nav(depth=0):
    pre = "../" if depth else ""
    return f'''<header class="nav" id="nav">
  <div class="wrap nav-inner">
    <a class="brand{' has-logo' if HAS_LOGO else ''}" href="{pre}index.html">
      {brand_inner(pre)}
    </a>
    <nav class="nav-links" id="navlinks">
      <a href="{pre}index.html#lake-hartwell">Lake Hartwell</a>
      <a href="{pre}index.html#blue-ridge">Blue Ridge</a>
      <a href="{pre}index.html#greenville">Greenville</a>
      <a href="{pre}index.html#properties">All Homes</a>
      <a href="{pre}index.html#owners">Own a Home</a>
      <a class="nav-cta" href="{pre}index.html#properties">Book Now</a>
    </nav>
    <button class="burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
  </div>
</header>'''

def footer(depth=0):
    pre = "../" if depth else ""
    return f'''<footer class="foot">
  <div class="wrap foot-grid">
    <div>
      <a class="brand brand-foot{' has-logo' if HAS_LOGO else ''}" href="{pre}index.html">{brand_inner(pre)}</a>
      <p class="foot-tag">Where luxury meets adventure. Hand‑selected lake and mountain homes across the Southeast.</p>
    </div>
    <div>
      <h4>Explore</h4>
      <a href="{pre}index.html#lake-hartwell">Lake Hartwell</a>
      <a href="{pre}index.html#blue-ridge">Blue Ridge Georgia</a>
      <a href="{pre}index.html#greenville">Greenville &amp; Travelers Rest</a>
      <a href="{pre}index.html#properties">All Homes</a>
    </div>
    <div>
      <h4>Contact</h4>
      <a href="tel:+18645813164">+1 864‑581‑3164</a>
      <a href="mailto:hello@basecampgetaways.com">hello@basecampgetaways.com</a>
      <a href="https://www.facebook.com/profile.php?id=100087908191610" target="_blank" rel="noopener">Facebook</a>
      <a href="https://www.instagram.com/basecampgetaways" target="_blank" rel="noopener">Instagram</a>
    </div>
  </div>
  <div class="wrap foot-base"><span>© 2026 Basecamp Getaways. All rights reserved.</span><span>Book direct — best rate, no booking fees.</span></div>
</footer>'''

NAME2REGION = {n: c["id"] for c in COLLECTIONS for n in c["names"]}

def card(rec, depth=0):
    pre = "../" if depth else ""
    g, bd, ba = rec["guests"], rec["bedrooms"], rec["bathrooms"]
    bits = []
    if g: bits.append(f"{g} guests")
    if bd: bits.append(f"{bd} bd")
    if ba: bits.append(f"{ba} ba")
    spec = " · ".join(bits)
    img = rec["hero"]
    region = NAME2REGION.get(rec["name"], "")
    return f'''<a class="card" href="{pre}property/{rec['slug']}.html" data-region="{region}" data-guests="{g or 0}" data-name="{esc(rec['title'].lower())}">
  <div class="card-img"><img loading="lazy" src="{esc(img)}" alt="{esc(rec['title'])}"></div>
  <div class="card-body">
    <h3>{esc(rec['title'])}</h3>
    <div class="card-loc">{PIN}{esc(rec['location'])}</div>
    <div class="card-spec">{esc(spec)}</div>
    <span class="card-link">View home →</span>
  </div>
</a>'''

REVIEWS = [
    ("Kelsee W.","Quittin Time Cottage","The house was perfect for our family. The game room and kids room was a big hit. The dock was awesome and you can tell a lot of thought was put into the house. This was our first time at Lake Hartwell, and we loved it!"),
    ("Wilfred G.","Endless Views","Erin was an amazing host! Very responsive and proactive before and during our stay. The property was beautiful and matched the photos exactly. We can't wait to come out again."),
    ("Taylor H.","Lake Hartwell Oasis","We had a great stay! The house was very clean and looked exactly like the pictures. The walk down to the dock was easy and convenient. We would definitely stay here again and highly recommend it."),
    ("Lyudmila D.","Hooked on Hartwell","Convenient location right by the water. Clean, comfortable, easy check‑in. Loved the game room — kids had a blast. Highly recommended."),
    ("Shannen P.","Walker Cove","Very cute place! Very well worth the money! Host is super nice!"),
    ("Ellen K.","The Keowee Getaway","Cozy spot with room for families!"),
]

def review_card(r):
    return f'''<figure class="rev">
  <div class="stars">★★★★★</div>
  <blockquote>{esc(r[2])}</blockquote>
  <figcaption><strong>{esc(r[0])}</strong><span>{esc(r[1])}</span></figcaption>
</figure>'''

def own_home_html(compact=False):
    if compact:
        return '''<section class="owners-band" id="owners">
  <div class="wrap owners-band-inner">
    <div>
      <span class="eyebrow light">Own a Home?</span>
      <h2>List with Basecamp Getaways</h2>
      <p>Full-service management for lake & mountain homes — more revenue, none of the work.</p>
    </div>
    <a class="btn" href="mailto:hello@basecampgetaways.com?subject=Property%20Management%20Inquiry">Talk to our team</a>
  </div>
</section>'''
    return '''<section class="owners" id="owners">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Own a Home?</span>
      <h2>Earn more with full-service management</h2>
      <p>You own the home — we handle everything else. Basecamp Getaways manages short-term rentals across South Carolina and North Georgia, turning your property into a polished, high-performing getaway.</p>
    </div>
    <div class="owners-grid">
      <div class="owner-card"><span class="owner-ic">$</span><h3>Maximized revenue</h3><p>Dynamic, data-driven pricing and pro listing optimization keep your calendar full at the best nightly rate.</p></div>
      <div class="owner-card"><span class="owner-ic">★</span><h3>Five-star hospitality</h3><p>24/7 guest communication, seamless check-in, and the kind of care that earns repeat bookings and great reviews.</p></div>
      <div class="owner-card"><span class="owner-ic">✦</span><h3>Truly hands-off</h3><p>Cleaning, restocking, maintenance, and turnovers — all coordinated by our local team so you never lift a finger.</p></div>
    </div>
    <div class="owners-cta">
      <a class="btn" href="mailto:hello@basecampgetaways.com?subject=Property%20Management%20Inquiry">Talk to our team</a>
      <a class="btn outline" href="tel:+18645813164">Call +1 864‑581‑3164</a>
    </div>
  </div>
</section>'''

LH_CALLOUT = '''<div class="lh-callout">
  <div>
    <strong>Exploring just Lake Hartwell?</strong>
    <span>See all our lake homes plus a complete Lake Hartwell area & fishing guide.</span>
  </div>
  <a class="btn ghost-dark" href="https://lakehartwellstays.com" target="_blank" rel="noopener">Visit Lake Hartwell Stays →</a>
</div>'''

# ---------- Pages ----------
def page_shell(title, desc, body, depth=0, extra_head=""):
    pre = "../" if depth else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/style.css">
{extra_head}
</head>
<body>
{body}
<script src="{pre}assets/site-config.js"></script>
<script src="{pre}assets/main.js"></script>
</body>
</html>'''

def build_index():
    # hero slideshow uses local optimized photos in assets/hero/
    hero_srcs = [f"assets/hero/{f}" for f in HERO_FILES] or [records["Endless Views-Mineral Bluff"]["hero"]]
    slides_html = "".join(
        f'<div class="hero-slide{" active" if i==0 else ""}" style="background-image:url(\'{esc(u)}\')"></div>'
        for i, u in enumerate(hero_srcs))
    # search bar (client-side filter of the All Homes grid)
    region_opts = "".join(f'<option value="{c["id"]}">{esc(c["title"].replace(" Collection",""))}</option>' for c in COLLECTIONS)
    guest_opts = "".join(f'<option value="{n}">{n}+ guests</option>' for n in (2,4,6,8,10,12,14,16))
    search_html = f'''<form class="search" id="searchBar" onsubmit="return false">
      <div class="search-field"><label>Destination</label>
        <select id="s-region"><option value="">Anywhere</option>{region_opts}</select></div>
      <div class="search-field"><label>Check‑in</label><input type="date" id="s-in"></div>
      <div class="search-field"><label>Check‑out</label><input type="date" id="s-out"></div>
      <div class="search-field"><label>Guests</label>
        <select id="s-guests"><option value="">Any</option>{guest_opts}</select></div>
      <button class="search-btn" id="s-go">Search stays</button>
    </form>'''
    collections_html = []
    for c in COLLECTIONS:
        cards = "\n".join(card(records[n]) for n in c["names"] if n in records)
        extra = LH_CALLOUT if c["id"] == "lake-hartwell" else ""
        collections_html.append(f'''<section class="collection" id="{c['id']}">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">{esc(c['tagline'])}</span>
      <h2>{esc(c['title'])}</h2>
      <p>{esc(c['blurb'])}</p>
    </div>
    <div class="scroller">
      <button class="scroll-btn prev" aria-label="Scroll left">‹</button>
      <div class="scroll-track">{cards}</div>
      <button class="scroll-btn next" aria-label="Scroll right">›</button>
    </div>
    {extra}
  </div>
</section>''')
    all_cards = "\n".join(card(records[n]) for c in COLLECTIONS for n in c["names"] if n in records)
    revs = "\n".join(review_card(r) for r in REVIEWS)
    body = f'''{nav(0)}
<section class="hero">
  <div class="hero-slides">{slides_html}</div>
  <div class="hero-overlay"></div>
  <div class="wrap hero-inner">
    <span class="eyebrow light">Basecamp Getaways</span>
    <h1>Where luxury<br>meets adventure</h1>
    <p>Hand‑selected waterfront and mountain homes across the Southeast — designed with care, loaded with amenities, and booked direct for the best rate.</p>
    <div class="hero-cta">
      <a class="btn" href="#properties">Explore all homes</a>
      <a class="btn ghost" href="#lake-hartwell">Lake Hartwell</a>
      <a class="btn ghost" href="#blue-ridge">Blue Ridge</a>
      <a class="btn ghost" href="#greenville">Greenville / Travelers Rest</a>
    </div>
    {search_html}
  </div>
</section>

<section class="values">
  <div class="wrap values-grid">
    <div class="val"><span class="val-ic">✦</span><h3>Curated for quality</h3><p>Every home is chosen for its location, design, and amenities — only the best make the collection.</p></div>
    <div class="val"><span class="val-ic">✦</span><h3>Book direct, save more</h3><p>Reserve straight through us with no added booking fees — the same trusted checkout, better value.</p></div>
    <div class="val"><span class="val-ic">✦</span><h3>24/7 concierge</h3><p>Local, responsive hosts ready around the clock to make your stay effortless from arrival to checkout.</p></div>
  </div>
</section>

{''.join(collections_html)}

<section class="collection alt" id="properties">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">The full collection</span><h2>Explore our properties</h2>
    <p>Browse every home across Lake Hartwell, Blue Ridge, and the Greenville area.</p></div>
    <div class="grid" id="allGrid">{all_cards}</div>
    <p class="no-results" id="noResults" hidden>No homes match those filters — <button type="button" id="clearSearch">show all homes</button>.</p>
  </div>
</section>

<section class="reviews">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Guest stories</span><h2>What our guests are saying</h2></div>
    <div class="rev-grid">{revs}</div>
  </div>
</section>

{own_home_html(compact=False)}

<section class="cta-band">
  <div class="wrap">
    <h2>Your next escape is waiting</h2>
    <p>Lake sunsets, mountain mornings, and homes that feel like your own. Find your stay and book direct today.</p>
    <a class="btn" href="#properties">Find your stay</a>
  </div>
</section>

{own_home_html(compact=True)}
{footer(0)}'''
    return page_shell("Basecamp Getaways | Luxury Lake & Mountain Vacation Rentals",
                      "Hand-selected luxury vacation rentals on Lake Hartwell, in Blue Ridge Georgia, and around Greenville SC. Book direct for the best rate.",
                      body, 0)

def build_property(rec):
    g, bd, ba, beds = rec["guests"], rec["bedrooms"], rec["bathrooms"], rec["beds"]
    gallery = rec["gallery"] or [rec["hero"]]
    main_img = gallery[0]
    thumbs = gallery[1:5]
    while len(thumbs) < 4:
        thumbs.append(main_img)
    thumbs_html = "".join(f'<div class="g-thumb"><img loading="lazy" src="{esc(u)}" alt="{esc(rec["title"])}"></div>' for u in thumbs)
    gallery_json = json.dumps(gallery)

    spec_items = []
    if g: spec_items.append(("Guests", g))
    if bd: spec_items.append(("Bedrooms", bd))
    if beds: spec_items.append(("Beds", beds))
    if ba: spec_items.append(("Bathrooms", ba))
    specs_html = "".join(f'<div class="spec"><span class="spec-n">{v}</span><span class="spec-l">{esc(l)}</span></div>' for l,v in spec_items)

    headline_html = "".join(f'<div class="hl">{CHECK}<span>{esc(amen_label(a))}</span></div>' for a in rec["headline"])

    am = rec["amenities"]
    am_html = "".join(f'<li>{CHECK}<span>{esc(amen_label(a))}</span></li>' for a in am)

    desc_html = format_description(rec["description"])

    coords = rec["coords"]
    lat, lng = coords.get("latitude"), coords.get("longitude")
    map_html = ""
    if lat and lng:
        map_html = f'''<section class="p-block">
  <h2>Where you'll be</h2>
  <p class="muted">{esc(rec['location'])}</p>
  <div class="map"><iframe loading="lazy" referrerpolicy="no-referrer-when-downgrade"
    src="https://www.google.com/maps?q={lat},{lng}&z=12&output=embed"></iframe></div>
</section>'''

    pets = '<div class="hl">'+CHECK+'<span>Pet friendly</span></div>' if rec["pets"] else ""

    body = f'''{nav(1)}
<div class="p-wrap wrap">
  <nav class="crumb"><a href="../index.html">Home</a> / <span>{esc(rec['title'])}</span></nav>

  <section class="gallery" data-gallery='{gallery_json}'>
    <div class="g-main"><img src="{esc(main_img)}" alt="{esc(rec['title'])}">
      <button class="g-all" id="showAll">▦ View all {len(gallery)} photos</button></div>
    <div class="g-side">{thumbs_html}</div>
  </section>

  <div class="p-head">
    <div>
      <h1>{esc(rec['title'])}</h1>
      <div class="p-loc">{PIN}{esc(rec['location'])} · {esc(rec['ptype'])}</div>
    </div>
  </div>

  <div class="p-layout">
    <div class="p-main">
      <div class="p-specs">{specs_html}</div>

      <section class="p-block">
        <h2>The highlights</h2>
        <div class="hl-grid">{headline_html}{pets}</div>
      </section>

      <section class="p-block">
        <h2>About this home</h2>
        <div class="prose clamp" id="prose">{desc_html}</div>
        <button class="readmore" id="readmore">Read more ↓</button>
      </section>

      <section class="p-block">
        <h2>What this place offers</h2>
        <ul class="amen">{am_html}</ul>
      </section>

      {map_html}
    </div>

    <aside class="p-aside">
      <div class="book-card" id="bookCard" data-slug="{rec['slug']}">
        <div class="book-head">
          <span class="book-eyebrow">Book direct</span>
          <h3>Reserve your stay</h3>
          <p class="book-sub">Best rate guaranteed — no added booking fees.</p>
        </div>
        <div id="booking-widget-mount" class="widget-mount"></div>
      </div>
    </aside>
  </div>
</div>

<div class="lightbox" id="lightbox" hidden>
  <button class="lb-close" id="lbClose" aria-label="Close">×</button>
  <button class="lb-prev" id="lbPrev" aria-label="Previous">‹</button>
  <img id="lbImg" src="" alt="">
  <button class="lb-next" id="lbNext" aria-label="Next">›</button>
  <div class="lb-count" id="lbCount"></div>
</div>
{footer(1)}'''
    return page_shell(f"{rec['title']} | {rec['location']} | Basecamp Getaways",
                      (rec["summary"][:150] or rec["title"]),
                      body, 1)

# ---------- Write files ----------
if os.path.exists(SITE):
    shutil.rmtree(SITE)
os.makedirs(ASSETS); os.makedirs(PROP_DIR)

open(os.path.join(SITE,"index.html"),"w").write(build_index())
for name, rec in records.items():
    open(os.path.join(PROP_DIR, rec["slug"]+".html"),"w").write(build_property(rec))

# copy authored assets
for fn in ("style.css","main.js"):
    src = os.path.join(BASE, "src_"+fn)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(ASSETS, fn))

# copy hero images
if HERO_FILES:
    hero_dst = os.path.join(ASSETS, "hero")
    os.makedirs(hero_dst, exist_ok=True)
    for f in HERO_FILES:
        shutil.copy(os.path.join(HERO_SRC, f), os.path.join(hero_dst, f))

# copy logo if provided
if HAS_LOGO:
    shutil.copy(LOGO_SRC, os.path.join(ASSETS, "logo.png"))

# site-config.js : Hospitable booking widget per property (widgetId + numeric propertyId)
WIDGET_ID = "9d085b4c-7e14-4a04-a56f-cc7c4867753a"
SLUG_PID = {
    "watersedge":"2161510","hookedonhartwell":"1273108","quittintimecottagelakehartwell":"2080462",
    "thekeoweegetaway":"1273122","bradydrlakeharwelloasis":"1806592","hartwellhaven":"2279617",
    "walkercove":"2300688","lakeplace":"2301310","foothillscottage":"2305981","endlessviews":"1880794",
    "riverrunretreat":"1273126","starmountain":"1327820","riverrunretreatstudio":"1273128",
    "cozybearcabin":"1283884","bluechalet":"1283886","bluewallfarmbasecamp":"1273112",
    "riverfrontescapebasecampgreenville":"1715332",
}
cfg = {rec["slug"]: f"https://booking.hospitable.com/widget/{WIDGET_ID}/{SLUG_PID[rec['slug']]}"
       for rec in records.values() if rec["slug"] in SLUG_PID}
config_js = "/* Booking widget configuration — Hospitable Direct.\n" \
"   Each value is the SRC of that property's Hospitable booking widget.\n" \
"   Format: https://booking.hospitable.com/widget/<widgetId>/<propertyId>\n*/\n" \
"window.SITE_CONFIG = {\n  widgets: " + json.dumps(cfg, indent=4) + ",\n" \
"  fallbackBookingUrl: \"\"\n};\n"
open(os.path.join(ASSETS,"site-config.js"),"w").write(config_js)

print("Built", 1+len(records), "pages,", len(records), "properties")
print("Slugs:", ", ".join(r["slug"] for r in records.values()))
