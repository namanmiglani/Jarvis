"""
Weather Tool

Fetches weather information using WeatherAPI.com.
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
        self.api_key = os.getenv('WEATHER_API_KEY')
        if not self.api_key or self.api_key == 'your-api-key-here':
            logger.warning("⚠️  WEATHER_API_KEY not set. Weather queries will fail.")
        self.base_url = "http://api.weatherapi.com/v1/current.json"
        logger.info("Weather Tool initialized")
    
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather for a location.
        
        Args:
            location: City name or "City, Country"
            
        Returns:
            Dictionary with weather information or error
        """
        logger.info(f"Fetching weather for: {location}")
        
        try:
            # Make API request
            params = {
                'key': self.api_key,
                'q': location,
                'aqi': 'no'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            weather_info = {
                'location': data['location']['name'],
                'region': data['location']['region'],
                'country': data['location']['country'],
                'temperature': round(data['current']['temp_c']),
                'feels_like': round(data['current']['feelslike_c']),
                'condition': data['current']['condition']['text'],
                'humidity': data['current']['humidity'],
                'wind_kph': round(data['current']['wind_kph'], 1),
                'wind_dir': data['current']['wind_dir'],
                'is_day': data['current']['is_day'] == 1,
                'success': True
            }
            
            logger.info(f"✅ Weather fetched: {weather_info['temperature']}°C in {weather_info['location']}")
            return weather_info
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
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
        region = weather_data['region']
        country = weather_data['country']
        temp = weather_data['temperature']
        feels_like = weather_data['feels_like']
        condition = weather_data['condition']
        humidity = weather_data['humidity']
        wind = weather_data['wind_kph']
        wind_dir = weather_data['wind_dir']
        
        # Build location string
        if region:
            location_str = f"{location}, {region}, {country}"
        else:
            location_str = f"{location}, {country}"
        
        response = f"The weather in {location_str} is currently {temp}°C with {condition}. "
        response += f"It feels like {feels_like}°C. "
        response += f"Humidity is {humidity}% and wind is {wind} km/h from the {wind_dir}."
        
        return response
