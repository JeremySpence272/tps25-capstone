import requests
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
from fetch_coordinates import get_city_coordinates

# Load environment variables from .env file
load_dotenv()

def get_weather_data(lat: float, lon: float, exclude: str = "") -> Optional[Dict[str, Any]]:
    """
    Get comprehensive weather data using OpenWeatherMap One Call API.
    
    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
        exclude (str, optional): Parts of the weather data to exclude.
                                Options: current, minutely, hourly, daily, alerts
                                Multiple parts can be excluded using comma separation
    
    Returns:
        Dict containing weather data, or None if request fails
    """
    # Get API key from environment variables
    api_key = os.getenv('OPENWEATHERMAP_KEY1')
    
    if not api_key:
        print("Error: OPENWEATHERMAP_KEY1 not found in environment variables")
        return None
    
    # Build the API URL
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'exclude': 'minutely,hourly,alerts',
        'units': 'imperial'  # Use metric units (Celsius, m/s, etc.)
    }
    
    # Add exclude parameter if provided
    if exclude:
        params['exclude'] = exclude
    
    try:
        # Make the API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None

def get_city_weather(city_name: str, state_code: str = "", country_code: str = "", exclude: str = "") -> Optional[Dict[str, Any]]:
    """
    Get weather data for a city by first getting coordinates, then fetching weather.
    
    Args:
        city_name (str): Name of the city
        state_code (str, optional): State code (for US cities)
        country_code (str, optional): Country code (ISO 3166)
        exclude (str, optional): Parts of the weather data to exclude
    
    Returns:
        Dict containing both location and weather data, or None if request fails
    """
    print(f"Fetching weather data for city: {city_name}, state: {state_code}, country: {country_code}, exclude: {exclude}")
    
    # First, get the coordinates for the city
    coordinates = get_city_coordinates(city_name, state_code, country_code)
    if not coordinates:
        print(f"Failed to get coordinates for city: {city_name}")
        return None
    print(f"Coordinates for {city_name}: {coordinates}")
    
    # Then, get the weather data using those coordinates
    weather_data = get_weather_data(coordinates['lat'], coordinates['lon'], exclude)
    if not weather_data:
        print(f"Failed to get weather data for city: {city_name} with coordinates: {coordinates}")
        return None
    print(f"Weather data for {city_name}: {weather_data}")
    
    # Combine location and weather data
    combined_data = {
        'location': coordinates,
        'weather': weather_data
    }
    print(f"Successfully fetched and combined data for city: {city_name}")
    return combined_data

def format_current_weather(weather_data: Dict[str, Any]) -> None:
    """
    Format and display current weather information.
    
    Args:
        weather_data (Dict): Combined weather data from get_city_weather
    """
    # Check if we have the weather data in the expected structure
    if 'weather' not in weather_data or 'current' not in weather_data['weather']:
        print("Current weather data not available")
        return
    
    current = weather_data['weather']['current']
    location = weather_data.get('location', {})
    
    print(f"\n🌤️  Current Weather for {location.get('name', 'Unknown')}")
    print(f"📍 Location: {location.get('name', 'Unknown')}, {location.get('country', 'Unknown')}")
    print(f"🌡️  Temperature: {current.get('temp', 'N/A')}°C")
    print(f"🌡️  Feels like: {current.get('feels_like', 'N/A')}°C")
    print(f"💧 Humidity: {current.get('humidity', 'N/A')}%")
    print(f"🌬️  Wind Speed: {current.get('wind_speed', 'N/A')} m/s")
    print(f"👁️  Visibility: {current.get('visibility', 'N/A')} meters")
    print(f"☁️  Cloudiness: {current.get('clouds', 'N/A')}%")
    
    if 'weather' in current and current['weather']:
        weather_desc = current['weather'][0]
        print(f"🌦️  Conditions: {weather_desc.get('main', 'N/A')} - {weather_desc.get('description', 'N/A')}")

def format_daily_forecast(weather_data: Dict[str, Any], days: int = 5) -> None:
    """
    Format and display daily weather forecast.
    
    Args:
        weather_data (Dict): Combined weather data from get_city_weather
        days (int): Number of days to show in forecast
    """
    # Check if we have the weather data in the expected structure
    if 'weather' not in weather_data or 'daily' not in weather_data['weather']:
        print("Daily forecast data not available")
        return
    
    daily = weather_data['weather']['daily'][:days]
    location = weather_data.get('location', {})
    
    print(f"\n📅 {days}-Day Forecast for {location.get('name', 'Unknown')}")
    print("=" * 50)
    
    for i, day in enumerate(daily):
        day_name = "Today" if i == 0 else f"Day {i+1}"
        temp_day = day.get('temp', {}).get('day', 'N/A')
        temp_night = day.get('temp', {}).get('night', 'N/A')
        
        conditions = "N/A"
        if 'weather' in day and day['weather']:
            conditions = day['weather'][0].get('description', 'N/A')
        
        print(f"{day_name}: {temp_day}°C/{temp_night}°C - {conditions}")

def main():
    """
    Example usage of the weather API functions
    """
    print("🌍 OpenWeatherMap One Call API - Weather Data Fetcher")
    print("=" * 55)
    
    # Example: Get weather for Austin, TX with daily forecast
    print("\n=== Example: Austin, TX Weather with Forecast ===")
    result = get_city_weather("Austin", "TX", "US")
    if result:
        format_current_weather(result)
        format_daily_forecast(result)

if __name__ == "__main__":
    main() 