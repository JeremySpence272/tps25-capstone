import csv
import os
import datetime
from typing import Dict, Any
from tkinter import messagebox

def export_daily_weather_to_csv(weather_data: Dict[str, Any], coordinates: Dict[str, Any]) -> None:
    """
    Export daily weather data to CSV file. Data is appended to weather_export.csv.
    
    Args:
        weather_data: Weather data from OpenWeatherMap API
        coordinates: Location coordinates and name data
    """
    # Check if we have daily weather data
    if not weather_data or 'daily' not in weather_data:
        messagebox.showerror("Export Error", "No daily weather data available to export.")
        return
    
    # Get city and state information
    city_name = coordinates.get('name', 'Unknown')
    state = coordinates.get('state', '')
    
    # Fixed filename
    file_path = "weather_export.csv"
    
    # Get current export date
    export_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Extract daily weather data
        daily_data = weather_data['daily']
        
        # Get today's date for comparison
        today = datetime.date.today()
        
        # Read existing data if file exists
        existing_data = []
        file_exists = os.path.exists(file_path)
        
        if file_exists:
            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    existing_data = list(reader)
            except Exception:
                pass  # If we can't read existing data, start fresh
        
        # Prepare CSV data
        csv_data = []
        locations_dates_to_overwrite = set()
        
        for day_data in daily_data:
            # Extract weather date from timestamp
            weather_timestamp = day_data.get('dt', 0)
            weather_date = datetime.datetime.fromtimestamp(weather_timestamp).strftime("%Y-%m-%d") if weather_timestamp else export_date
            
            # Determine if this is predicted or actual data
            weather_date_obj = datetime.datetime.strptime(weather_date, "%Y-%m-%d").date()
            is_predicted = weather_date_obj > today
            
            # Extract temperature data
            temp_info = day_data.get('temp', {})
            temp = temp_info.get('day', 0)
            
            # Extract humidity
            humidity = day_data.get('humidity', 0)
            
            # Extract rain data (if available)
            rain = day_data.get('rain', 0)
            if isinstance(rain, dict):
                rain = rain.get('1h', 0)  # Get 1-hour rain volume
            
            # Extract weather summary
            summary = ""
            if 'weather' in day_data and day_data['weather']:
                weather_info = day_data['weather'][0]
                summary = weather_info.get('description', '').title()
            
            # Create row for CSV
            row = {
                'weather_date': weather_date,
                'export_date': export_date,
                'city': city_name,
                'state': state,
                'temp': round(temp, 1),
                'humidity': humidity,
                'rain': rain,
                'summary': summary,
                'predicted': is_predicted
            }
            
            csv_data.append(row)
            # Create a unique identifier for location + date combination
            location_date_key = f"{city_name}|{state}|{weather_date}"
            locations_dates_to_overwrite.add(location_date_key)
        
        # Filter existing data to handle overwrites
        filtered_existing_data = []
        for existing_row in existing_data:
            existing_weather_date = existing_row.get('weather_date', '')
            existing_city = existing_row.get('city', '')
            existing_state = existing_row.get('state', '')
            existing_predicted = existing_row.get('predicted', '').lower()
            
            # For backward compatibility, if 'predicted' field doesn't exist, assume it's actual data (false)
            if not existing_predicted:
                existing_predicted = 'false'
            
            # Create location+date key for existing row
            existing_location_date_key = f"{existing_city}|{existing_state}|{existing_weather_date}"
            
            # Keep existing row if:
            # 1. It's not a location+date we're updating, OR
            # 2. It's a location+date we're updating but it's already predicted=false (actual data)
            if (existing_location_date_key not in locations_dates_to_overwrite or 
                existing_predicted == 'false'):
                # If it's same location+date and already predicted=false, skip adding new data for that location+date
                if (existing_location_date_key in locations_dates_to_overwrite and 
                    existing_predicted == 'false'):
                    # Remove matching location+date from csv_data to avoid duplication
                    csv_data = [row for row in csv_data if 
                               f"{row['city']}|{row['state']}|{row['weather_date']}" != existing_location_date_key]
                else:
                    # Ensure the existing row has the predicted field
                    if 'predicted' not in existing_row:
                        existing_row['predicted'] = False
                    filtered_existing_data.append(existing_row)
            # If existing_location_date_key is in locations_dates_to_overwrite and existing_predicted is 'true',
            # we don't add it to filtered_existing_data, so it gets overwritten
        
        # Combine filtered existing data with new data
        all_data = filtered_existing_data + csv_data
        
        # Write to CSV file (overwrite mode since we're managing the data)
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['weather_date', 'export_date', 'city', 'state', 'temp', 'humidity', 'rain', 'summary', 'predicted']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Always write header
            writer.writeheader()
            
            # Write all data rows
            for row in all_data:
                writer.writerow(row)
        
        # Show success message
        new_rows_count = len(csv_data)
        existing_rows_count = len(filtered_existing_data)
        total_rows_count = len(all_data)
        
        message = f"Daily weather data exported successfully!\n\nFile: {file_path}\n"
        if existing_rows_count > 0:
            message += f"Existing rows kept: {existing_rows_count}\n"
        message += f"New rows added: {new_rows_count}\n"
        message += f"Total rows in file: {total_rows_count}"
        
        messagebox.showinfo("Export Successful", message)
        
    except Exception as e:
        messagebox.showerror("Export Error", f"Error exporting data: {str(e)}")

def validate_export_data(weather_data: Dict[str, Any], coordinates: Dict[str, Any]) -> bool:
    """
    Validate that we have the required data for export.
    
    Args:
        weather_data: Weather data from OpenWeatherMap API
        coordinates: Location coordinates and name data
        
    Returns:
        bool: True if data is valid for export, False otherwise
    """
    if not weather_data:
        return False
    
    if 'daily' not in weather_data:
        return False
    
    if not weather_data['daily']:
        return False
    
    if not coordinates or 'name' not in coordinates:
        return False
    
    return True 