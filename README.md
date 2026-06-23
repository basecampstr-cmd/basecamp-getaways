# Basecamp Getaways — website

A self-owned, static vacation-rental site (replaces Crafted Stays). Browsing happens here; booking hands off to Hospitable's Direct widget. Hosted free on Netlify, version-controlled on GitHub, so any future edit auto-deploys.

## Repo layout

```
site/                 ← THIS is what's published (Netlify publish dir)
  index.html          ← homepage: hero slideshow, scrolling collections, reviews
  property/*.html     ← one page per property (17)
  assets/
    style.css
    main.js
    site-config.js    ← ★ paste your Hospitable booking-widget URLs here
_source/              ← build tooling + data snapshots (NOT published)
  build_site.py       ← regenerates the site from the data files
  src_style.css, src_main.js
  *.json              ← property data + Airbnb photo sets pulled from your accounts
netlify.toml          ← tells Netlify to publish the /site folder, no build step
```

## How updates work (GitHub → Netlify)

Once connected (see HOST-AND-UPDATE guide), every push to the `main` branch redeploys automatically — usually live within ~30 seconds. To change wording, prices copy, or add a property, edit the files under `site/` and commit. For a full content refresh from Hospitable/Airbnb, re-run the generator in `_source/` (or ask Claude to) and copy the output into `site/`.

## Connect booking (one-time)

The site hands booking to Hospitable exactly like Crafted Stays did. In Hospitable → **Direct Bookings → Website**, create a self-hosted site, **Copy widget code** for each property, and paste each widget `src` URL into `site/assets/site-config.js` keyed by the page slug. Then register each property's live page URL back in Hospitable so the widgets activate. Until filled, each page shows a tidy "Check availability" button — nothing breaks.

## Photos

Property photos are pulled directly from your Airbnb listings (exact set and order) and load from Airbnb's image CDN. To refresh after you change photos on Airbnb, re-run the photo step in `_source/` (or ask Claude).
