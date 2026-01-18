"""
Weather Tool

Fetches weather information using OpenWeatherMap API.
"""

import logging
import os
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WeatherTool:
    """Tool for fetching weather information."""
    
    def __init__(self):
        """Initialize Weather Tool with API key."""
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        if not self.api_key or self.api_key == 'your-api-key-here':
            logger.warning("⚠️  OPENWEATHER_API_KEY not set. Weather queries will fail.")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        logger.info("Weather Tool initialized")
    
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather for a location.
        
        Args:
            location: City name or "City, Country Code"
            
        Returns:
            Dictionary with weather information or error
        """
        logger.info(f"Fetching weather for: {location}")
        
        try:
            # Make API request
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric'  # Celsius
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            weather_info = {
                'location': data['name'],
                'country': data['sys']['country'],
                'temperature': round(data['main']['temp']),
                'feels_like': round(data['main']['feels_like']),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': round(data['wind']['speed'] * 3.6, 1),  # Convert m/s to km/h
                'success': True
            }
            
            logger.info(f"✅ Weather fetched: {weather_info['temperature']}°C in {weather_info['location']}")
            return weather_info
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"❌ Location not found: {location}")
                return {
                    'success': False,
                    'error': f"I couldn't find weather information for '{location}'. Please check the city name."
                }
            else:
                logger.error(f"❌ HTTP error: {e}")
                return {
                    'success': False,
                    'error': "I encountered an error fetching the weather. Please try again."
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {e}")
            return {
                'success': False,
                'error': "I couldn't connect to the weather service. Please check your internet connection."
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                'success': False,
                'error': "An unexpected error occurred while fetching the weather."
            }
    
    def format_weather_response(self, weather_data: Dict[str, Any]) -> str:
        """
        Format weather data into a natural language response.
        
        Args:
            weather_data: Weather information dictionary
            
        Returns:
            Formatted response string
        """
        if not weather_data.get('success'):
            return weather_data.get('error', 'Unable to fetch weather information.')
        
        location = weather_data['location']
        country = weather_data['country']
        temp = weather_data['temperature']
        feels_like = weather_data['feels_like']
        description = weather_data['description']
        humidity = weather_data['humidity']
        wind = weather_data['wind_speed']
        
        response = f"The weather in {location}, {country} is currently {temp}°C with {description}. "
        response += f"It feels like {feels_like}°C. "
        response += f"Humidity is {humidity}% and wind speed is {wind} km/h."
        
        return response
