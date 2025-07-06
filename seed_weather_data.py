import requests
import os
import csv
import datetime
from dotenv import load_dotenv
from fetch_coordinates import get_city_coordinates

# Load environment variables
load_dotenv()

def get_historical_weather_data(lat: float, lon: float, dt: int) -> dict:
    """
    Get historical weather data using OpenWeatherMap Time Machine API.
    
    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
        dt (int): Unix timestamp for the date
    
    Returns:
        Dict containing historical weather data, or None if request fails
    """
    api_key = os.getenv('OPENWEATHERMAP_KEY1')
    
    if not api_key:
        print("Error: OPENWEATHERMAP_KEY1 not found in environment variables")
        return None
    
    # Build the API URL
    base_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
    params = {
        'lat': lat,
        'lon': lon,
        'dt': dt,
        'appid': api_key,
        'units': 'imperial'
    }
    
    try:
        # Make the API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None

def seed_weather_data():
    """
    Seed the weather_export.csv file with historical weather data for New York, NY
    for the last 7 days.
    """
    print("🌍 Seeding weather data for New York, NY - Last 7 days")
    print("=" * 60)
    
    # Get coordinates for New York, NY
    print("Getting coordinates for New York, NY...")
    coordinates = get_city_coordinates("New York", "NY", "US")
    if not coordinates:
        print("❌ Failed to get coordinates for New York, NY")
        return
    
    print(f"✅ Coordinates: {coordinates}")
    
    lat = coordinates['lat']
    lon = coordinates['lon']
    city_name = coordinates['name']
    state = coordinates.get('state', 'NY')
    
    # Get the last 7 days (excluding today)
    today = datetime.date.today()
    historical_dates = []
    
    for i in range(1, 8):  # 1 to 7 days ago
        date = today - datetime.timedelta(days=i)
        # Convert to unix timestamp (start of day)
        dt = int(datetime.datetime.combine(date, datetime.time.min).timestamp())
        historical_dates.append((date, dt))
    
    print(f"📅 Fetching data for dates: {[date.strftime('%Y-%m-%d') for date, _ in historical_dates]}")
    
    # Prepare CSV data
    csv_data = []
    export_date = today.strftime("%Y-%m-%d")
    
    for date, dt in historical_dates:
        print(f"📡 Fetching data for {date.strftime('%Y-%m-%d')}...")
        
        # Get historical weather data
        weather_data = get_historical_weather_data(lat, lon, dt)
        
        if not weather_data or 'data' not in weather_data or not weather_data['data']:
            print(f"❌ Failed to get weather data for {date.strftime('%Y-%m-%d')}")
            continue
        
        # Extract weather info from the data array (should have one element)
        day_data = weather_data['data'][0]
        
        # Extract temperature data
        temp = day_data.get('temp', 0)
        
        # Extract humidity
        humidity = day_data.get('humidity', 0)
        
        # Extract rain data (if available)
        rain = 0  # Historical data doesn't typically have rain field
        
        # Extract weather summary
        summary = ""
        if 'weather' in day_data and day_data['weather']:
            weather_info = day_data['weather'][0]
            summary = weather_info.get('description', '').title()
        
        # Create row for CSV
        row = {
            'weather_date': date.strftime("%Y-%m-%d"),
            'export_date': export_date,
            'city': city_name,
            'state': state,
            'temp': round(temp, 1) if temp else "",
            'humidity': humidity,
            'rain': rain,
            'summary': summary,
            'predicted': False  # Historical data is actual, not predicted
        }
        
        csv_data.append(row)
        print(f"✅ Data fetched for {date.strftime('%Y-%m-%d')}: {temp}°F, {summary}")
    
    if not csv_data:
        print("❌ No data to write to CSV")
        return
    
    # Write to CSV file
    file_path = "weather_export.csv"
    
    try:
        # Read existing data if file exists
        existing_data = []
        file_exists = os.path.exists(file_path)
        
        if file_exists:
            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    existing_data = list(reader)
                print(f"📖 Read {len(existing_data)} existing rows from {file_path}")
            except Exception as e:
                print(f"⚠️ Could not read existing data: {e}")
        
        # Create set of location+date combinations we're adding
        locations_dates_to_add = set()
        for row in csv_data:
            location_date_key = f"{row['city']}|{row['state']}|{row['weather_date']}"
            locations_dates_to_add.add(location_date_key)
        
        # Filter existing data to avoid duplicates
        filtered_existing_data = []
        for existing_row in existing_data:
            existing_city = existing_row.get('city', '')
            existing_state = existing_row.get('state', '')
            existing_weather_date = existing_row.get('weather_date', '')
            existing_location_date_key = f"{existing_city}|{existing_state}|{existing_weather_date}"
            
            # Keep existing row if it's not a location+date we're adding
            if existing_location_date_key not in locations_dates_to_add:
                # Ensure the existing row has the predicted field for backward compatibility
                if 'predicted' not in existing_row:
                    existing_row['predicted'] = False
                filtered_existing_data.append(existing_row)
            else:
                print(f"🔄 Replacing existing data for {existing_city}, {existing_state} on {existing_weather_date}")
        
        # Combine filtered existing data with new data
        all_data = filtered_existing_data + csv_data
        
        # Write everything back to file
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['weather_date', 'export_date', 'city', 'state', 'temp', 'humidity', 'rain', 'summary', 'predicted']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write all data rows
            for row in all_data:
                writer.writerow(row)
        
        print(f"✅ Successfully seeded {len(csv_data)} new rows to {file_path}")
        print(f"📊 Total rows in file: {len(all_data)} (kept {len(filtered_existing_data)} existing + added {len(csv_data)} new)")
        print("📊 File is ready for use with the weather GUI export feature!")
        
    except Exception as e:
        print(f"❌ Error writing to CSV: {e}")

def main():
    """Main function"""
    seed_weather_data()

if __name__ == "__main__":
    main() 