"""
API Integration Patterns
Chapter 11: Architecture & Backend Integration

Demonstrates how a chatbot backend integrates with external APIs
to fetch live data and enrich its responses.

Examples covered:
  1. Weather API integration (fetching live data for a slot)
  2. Generic REST API wrapper with retry logic and timeout handling
  3. Webhook receiver (inbound events from external systems)

Run with:
    python api_integration.py
"""

import os
import time
import json
import logging
import requests
from typing import Any, Dict, Optional
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ─────────────────────────────────────────────
# 1. Generic REST API Client
# ─────────────────────────────────────────────

class APIClient:
    """
    A reusable REST API client with:
      - Configurable base URL and headers
      - Automatic retry with exponential back-off
      - Request/response logging
      - Timeout handling
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        self.base_url    = base_url.rstrip("/")
        self.timeout     = timeout
        self.max_retries = max_retries
        self.session     = requests.Session()

        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept":        "application/json",
        })
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, payload: Optional[Dict] = None) -> Dict:
        return self._request("POST", endpoint, json=payload)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url     = f"{self.base_url}/{endpoint.lstrip('/')}"
        attempt = 0

        while attempt < self.max_retries:
            attempt += 1
            try:
                logger.info(f"{method} {url} (attempt {attempt})")
                response = self.session.request(
                    method, url, timeout=self.timeout, **kwargs
                )
                response.raise_for_status()
                logger.info(f"Response: {response.status_code}")
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timed out (attempt {attempt})")
                if attempt >= self.max_retries:
                    return {"error": "Request timed out after multiple retries."}

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e.response.status_code} — {e}")
                return {"error": f"HTTP {e.response.status_code}: {str(e)}"}

            except requests.exceptions.ConnectionError:
                logger.error("Connection error")
                if attempt >= self.max_retries:
                    return {"error": "Could not connect to the API."}

            # Exponential back-off before retry
            wait = 2 ** attempt
            logger.info(f"Retrying in {wait}s…")
            time.sleep(wait)

        return {"error": "Max retries exceeded."}


# ─────────────────────────────────────────────
# 2. Weather API Integration Example
# ─────────────────────────────────────────────

class WeatherService:
    """
    Fetches current weather data for a given city.
    Uses the Open-Meteo API (free, no key required) for demonstration.

    In a real chatbot, this would be called when the user asks
    "What's the weather in Mumbai?" and the NLU has extracted
    the city entity.
    """

    GEO_URL     = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self):
        self.geo_client     = APIClient(self.GEO_URL)
        self.weather_client = APIClient(self.WEATHER_URL)

    def get_coordinates(self, city: str) -> Optional[Dict]:
        """Look up latitude/longitude for a city name."""
        result = requests.get(
            self.GEO_URL,
            params={"name": city, "count": 1, "language": "en"},
            timeout=10
        )
        data = result.json()
        if data.get("results"):
            loc = data["results"][0]
            return {
                "name":      loc["name"],
                "country":   loc.get("country", ""),
                "latitude":  loc["latitude"],
                "longitude": loc["longitude"],
            }
        return None

    def get_weather(self, city: str) -> str:
        """Return a human-readable weather summary for the given city."""
        coords = self.get_coordinates(city)
        if not coords:
            return f"Sorry, I couldn't find the location '{city}'."

        params = {
            "latitude":   coords["latitude"],
            "longitude":  coords["longitude"],
            "current":    "temperature_2m,weathercode,windspeed_10m",
            "timezone":   "auto",
        }
        result = requests.get(self.WEATHER_URL, params=params, timeout=10)
        data   = result.json().get("current", {})

        temp      = data.get("temperature_2m", "N/A")
        wind      = data.get("windspeed_10m", "N/A")
        wcode     = data.get("weathercode", 0)
        condition = self._weather_code_to_description(wcode)

        return (
            f"Current weather in {coords['name']}, {coords['country']}:\n"
            f"  🌡️  Temperature: {temp}°C\n"
            f"  💨 Wind speed:  {wind} km/h\n"
            f"  ☁️  Conditions:  {condition}"
        )

    @staticmethod
    def _weather_code_to_description(code: int) -> str:
        descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Icy fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
            95: "Thunderstorm", 99: "Thunderstorm with hail",
        }
        return descriptions.get(code, f"Weather code {code}")


# ─────────────────────────────────────────────
# 3. Webhook Receiver (Flask route example)
# ─────────────────────────────────────────────

def create_webhook_handler():
    """
    Returns a Flask blueprint that handles inbound webhooks from
    external systems (e.g. payment confirmations, CRM updates).

    In production, mount this on your main Flask app:
        from api_integration import create_webhook_handler
        app.register_blueprint(create_webhook_handler())
    """
    from flask import Blueprint, request, jsonify
    import hmac, hashlib

    bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")

    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-in-production")

    def verify_signature(payload: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature to ensure the webhook is genuine."""
        expected = hmac.new(
            WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    @bp.route("/payment", methods=["POST"])
    def payment_webhook():
        signature = request.headers.get("X-Signature", "")
        if not verify_signature(request.data, signature):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401

        event = request.get_json()
        event_type = event.get("type", "unknown")
        logger.info(f"Webhook received: {event_type}")

        if event_type == "payment.completed":
            order_id = event.get("order_id")
            logger.info(f"Payment confirmed for order {order_id}")
            # Trigger chatbot notification to user here

        elif event_type == "payment.failed":
            order_id = event.get("order_id")
            logger.warning(f"Payment failed for order {order_id}")

        return jsonify({"status": "received"}), 200

    @bp.route("/crm-update", methods=["POST"])
    def crm_update_webhook():
        data = request.get_json()
        logger.info(f"CRM update received: {json.dumps(data, indent=2)}")
        # Update user context in session store, enrich chatbot responses, etc.
        return jsonify({"status": "processed"}), 200

    return bp


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────

def demo():
    print("=== API Integration Demo ===\n")

    # Demo 1: Weather service
    print("1. Weather API Integration")
    print("-" * 40)
    weather = WeatherService()
    for city in ["Mumbai", "London", "New York"]:
        print(f"\nFetching weather for {city}...")
        print(weather.get_weather(city))

    print("\n\n2. Generic API Client")
    print("-" * 40)
    # Fetch a public JSON API as a demo
    client = APIClient("https://jsonplaceholder.typicode.com")
    post   = client.get("/posts/1")
    print(f"Fetched post title: {post.get('title', 'N/A')}")

    print("\n\n3. Webhook handler registered — see create_webhook_handler()")
    print("   Mount it on a Flask app to receive inbound events.")


if __name__ == "__main__":
    demo()
