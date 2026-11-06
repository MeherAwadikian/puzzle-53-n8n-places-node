"""
Puzzle 53 substitute backend.

Reproduces the exact request/response contract of the real
@cryptodevops/n8n-nodes-google-places community node (see
n8n-package-proof/ for the unpacked real package, GooglePlaces.node.js
formatPlaceData()), but swaps the upstream call from
maps.googleapis.com/maps/api/place/* (no Google Places API key exists
anywhere on this machine) to SerpAPI's engine=google_maps, the same
documented substitute used for puzzle #34. Same output shape:
place_id, name, address, rating, price_level, types, latitude,
longitude, google_maps_link.
"""
import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SERPAPI_KEY = os.environ.get("SERPAPI_API_KEY", "")
SERPAPI_URL = "https://serpapi.com/search.json"


def format_place_data(place: dict) -> dict:
    out = {
        "place_id": place.get("place_id") or place.get("data_id"),
        "name": place.get("title"),
        "address": place.get("address"),
        "rating": place.get("rating"),
        "price_level": place.get("price"),
        "types": place.get("type") and [place["type"]] or place.get("types"),
    }
    gps = place.get("gps_coordinates") or {}
    if gps:
        out["latitude"] = gps.get("latitude")
        out["longitude"] = gps.get("longitude")
    if place.get("link"):
        out["google_maps_link"] = place["link"]
    return out


def text_search(query: str, max_results: int = 10) -> dict:
    params = {"engine": "google_maps", "q": query, "type": "search", "api_key": SERPAPI_KEY}
    url = f"{SERPAPI_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read())
    results = data.get("local_results") or []
    places = [format_place_data(p) for p in results[:max_results]]
    summary = f"Found {len(places)} place(s):\n\n" + "\n".join(
        f"{i+1}. {p.get('name')} - {p.get('address') or 'no address'} "
        f"(rating {p.get('rating')})"
        for i, p in enumerate(places)
    )
    return {
        "ai_summary": summary,
        "total_results": len(places),
        "places": places,
        "operation": "textSearch",
        "query": query,
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/":
            with open(os.path.join(os.path.dirname(__file__), "index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/places":
            qs = urllib.parse.parse_qs(parsed.query)
            query = (qs.get("q") or [""])[0].strip()
            if not query:
                self._send_json(400, {"error": "missing q param"})
                return
            try:
                result = text_search(query)
                self._send_json(200, result)
            except Exception as exc:  # noqa: BLE001 - surface upstream failure to the demo UI
                self._send_json(502, {"error": str(exc)})
            return
        self._send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8053"))
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
