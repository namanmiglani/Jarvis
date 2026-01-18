"""
Maps Tool - Find nearest places using Google Places API
"""

import httpx
import logging
import os
import math
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class MapsTool:
    """Tool for finding places and calculating distances."""
    
    def __init__(self):
        """Initialize maps tool."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables")
            
        self.base_url = "https://places.googleapis.com/v1/places:searchText"
        self.current_location = None
        logger.info("Maps Tool initialized")
        
    async def _get_location(self) -> Dict[str, float]:
        """
        Get current location using Google Geolocation API.
        Returns: Dict with 'lat' and 'lon'
        """
        # Return cached location if available
        if self.current_location:
            return self.current_location
            
        if not self.api_key:
            logger.error("Google API Key missing")
            return None

        try:
            url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {"considerIp": True}  # Use IP and Wi-Fi to locate
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                data = response.json()
                
                if response.status_code == 200 and "location" in data:
                    loc = data["location"]
                    self.current_location = {
                        "lat": loc["lat"],
                        "lon": loc["lng"],
                        "city": "Unknown" # Geolocation API doesn't return city name
                    }
                    logger.info(f"📍 Detected location: {loc['lat']}, {loc['lng']} (via Google)")
                    return self.current_location
                else:
                    logger.error(f"Failed to get location from Google API: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching location: {e}")
            return None

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate Haversine distance between two points in km.
        """
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    async def get_nearest_place(self, query: str) -> Dict:
        """
        Find the nearest place matching the query.
        """
        if not self.api_key:
            return {"success": False, "error": "Google API Key missing"}

        # 1. Get Location
        location = await self._get_location()
        if not location:
            return {"success": False, "error": "Could not determine current location"}

        lat = location["lat"]
        lon = location["lon"]

        # 2. Query Google Places API
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            # Requesting display name, address, and location coordinates
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating"
        }

        # Using locationBias to prefer results near the user
        payload = {
            "textQuery": query,
            "maxResultCount": 3,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "radius": 2000  # Bias towards 2km radius, but will return results outside if needed
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Google API Error: {response.text}")
                    return {"success": False, "error": f"API Error: {response.status_code}"}
                
                data = response.json()
                places = data.get("places", [])
                
                if not places:
                    return {
                        "success": True, 
                        "found": False, 
                        "message": f"I couldn't find any places matching '{query}' nearby."
                    }

                # 3. Process results to find the strictly nearest one
                # AND prepare the full list for the HUD
                nearest_place = None
                min_dist = float('inf')
                
                processed_places = []

                for place in places:
                    p_lat = place["location"]["latitude"]
                    p_lon = place["location"]["longitude"]
                    dist = self._calculate_distance(lat, lon, p_lat, p_lon)
                    
                    place_data = {
                        "name": place["displayName"]["text"],
                        "address": place.get("formattedAddress", "Unknown Address"),
                        "rating": place.get("rating", "N/A"),
                        "distance_km": round(dist, 2),
                        "distance_miles": round(dist * 0.621371, 2)
                    }
                    
                    processed_places.append(place_data)
                    
                    if dist < min_dist:
                        min_dist = dist
                        nearest_place = place_data
                
                # Sort processed places by distance
                processed_places.sort(key=lambda x: x["distance_km"])

                return {
                    "success": True,
                    "found": True,
                    "place": nearest_place,
                    "places": processed_places,
                    "user_city": location.get("city")
                }

        except Exception as e:
            logger.error(f"Maps tool error: {e}")
            return {"success": False, "error": str(e)}

    def format_response(self, result: Dict) -> str:
        """Format the result into a natural language response."""
        if not result.get("success"):
            return f"I encountered an error finding that place: {result.get('error')}"
        
        if not result.get("found"):
            return result.get("message")
        
        place = result["place"]
        # e.g. "The nearest Starbucks is 1.2 kilometers away at 123 Main St."
        return (f"The nearest {place['name']} is {place['distance_km']} kilometers away "
                f"({place['distance_miles']} miles), located at {place['address']}.")
