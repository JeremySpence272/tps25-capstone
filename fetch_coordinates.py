import requests
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load environment variables from .env file
load_dotenv()

def get_city_coordinates(city_name: str, state_code: str = "", country_code: str = "", limit: int = 1) -> Optional[Dict[str, Any]]:
    """
    Get latitude and longitude coordinates for a city using OpenWeatherMap Geocoding API.
    
    Args:
        city_name (str): Name of the city
        state_code (str, optional): State code (for US cities)
        country_code (str, optional): Country code (ISO 3166)
        limit (int, optional): Number of locations to return (default: 1)
    
    Returns:
        Dict containing city information including lat/lon, or None if not found
    """
    # Get API key from environment variables
    api_key = os.getenv('OPENWEATHERMAP_KEY1')
    
    if not api_key:
        print("Error: OPENWEATHERMAP_KEY1 not found in environment variables")
        return None
    
    # Build the query string
    query_parts = [city_name]
    if state_code:
        query_parts.append(state_code)
    if country_code:
        query_parts.append(country_code)
    
    query = ",".join(query_parts)
    
    # Build the API URL
    base_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        'q': query,
        'limit': limit,
        'appid': api_key
    }
    
    try:
        # Make the API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        
        if not data:
            print(f"No coordinates found for city: {city_name}")
            return None
        
        # Return the first result
        city_info = data[0]
        return {
            'name': city_info.get('name'),
            'lat': city_info.get('lat'),
            'lon': city_info.get('lon'),
            'country': city_info.get('country'),
            'state': city_info.get('state', ''),
            'local_names': city_info.get('local_names', {})
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None

def main():
    """
    Example usage of the get_city_coordinates function
    """
    # Example 1: Simple city lookup
    print("=== Example 1: Simple city lookup ===")
    result = get_city_coordinates("London")
    if result:
        print(f"City: {result['name']}")
        print(f"Country: {result['country']}")
        print(f"Latitude: {result['lat']}")
        print(f"Longitude: {result['lon']}")
    
    print("\n=== Example 2: City with state (US) ===")
    result = get_city_coordinates("Austin", "TX", "US")
    if result:
        print(f"City: {result['name']}")
        print(f"State: {result['state']}")
        print(f"Country: {result['country']}")
        print(f"Latitude: {result['lat']}")
        print(f"Longitude: {result['lon']}")

if __name__ == "__main__":
    main()
