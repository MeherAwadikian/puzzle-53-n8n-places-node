# Puzzle #53 — n8n community node calling the Google Places API

Task Forge puzzle series (`#automate-me-this-puzzle`), puzzle #53 (2026-03-09):
install and use a Google Places **community node** in n8n (not the built-in
HTTP Request node — a real third-party npm package registered as an n8n
node type).

## What's real here

- **`n8n-package-proof/`** — the actual published community node package,
  `@cryptodevops/n8n-nodes-google-places@1.2.1`, downloaded via `npm pack`
  (not hand-written). Its `GooglePlaces.node.js` calls
  `https://maps.googleapis.com/maps/api/place/*` directly and exposes Text
  Search / Nearby Search / Place Details operations with a documented output
  shape (`formatPlaceData`: `place_id`, `name`, `address`, `rating`,
  `price_level`, `types`, `latitude`/`longitude`, `google_maps_link`).
- **`workflow.json`** — a real n8n workflow wired against this exact
  community node type (`@cryptodevops/n8n-nodes-google-places.googlePlaces`),
  ready to import into any n8n instance with community packages enabled and
  a Google Places API credential configured.
- **`server.py` + `index.html`** — a runnable substitute backend/demo page
  that reproduces the node's exact Text Search request/response contract
  live, end to end, independent of n8n being installed.

## Why a substitute backend

No Google Places API key exists anywhere on this machine (checked all
Hermes profile `.env` files + the master key reference — same situation
puzzle #34 hit for the same API family). `server.py` swaps the upstream
call for SerpAPI's `engine=google_maps` (the documented substitute from
puzzle #34), reusing the same `SERPAPI_API_KEY`, and maps SerpAPI's
`local_results` into the identical field names the real node's
`formatPlaceData()` produces — so the mechanic being proven is the node's
actual contract, not a different one.

## Why the workflow wasn't live-imported into n8n

This session's n8n runs in Docker, whose WSL disk is symlinked to the `D:`
drive — and `D:` is physically disconnected right now (confirmed via
`Get-PSDrive`), the same recurring, intermittent hardware issue documented
for puzzles #29/#34/#42/#45/#47. Per the lesson learned there, restarting
Docker doesn't help while the drive is actually gone, so rather than loop
retrying, `workflow.json` was built against the real, current node schema
and the mechanic was proven independently via the substitute backend. The
one remaining step, once `D:`/Docker are back: enable community packages
(`N8N_COMMUNITY_PACKAGES_ENABLED=true`), install
`@cryptodevops/n8n-nodes-google-places` from the n8n UI, add a Google
Places API credential, and import `workflow.json`.

## Live verification performed

- `server.py` run locally; `GET /api/places?q=coffee+shops+in+Beirut` hit
  the real SerpAPI endpoint and returned 10 real Beirut coffee shops with
  real `place_id`s, coordinates, and ratings.
- Opened `index.html` in a real browser (claude-in-chrome) and ran two
  distinct live searches through the actual UI: "coffee shops in Beirut"
  (10 results, Lebanon addresses) and "pharmacies in Dubai" (10 distinct
  results, UAE addresses) — proves the page drives a real live query, not
  a cached/hardcoded response.

## Run it yourself

```bash
export SERPAPI_API_KEY=<your key>
python server.py        # serves http://127.0.0.1:8053/
```

No secrets are committed; the key is read from the environment only.
