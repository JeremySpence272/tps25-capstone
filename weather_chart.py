import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def load_weather_data(city="New York", state="New York"):
    """
    Load weather data from CSV file for a specific city and state.
    
    Args:
        city (str): City name to filter for
        state (str): State name to filter for
        
    Returns:
        list: List of weather data dictionaries
    """
    file_path = "weather_export.csv"
    
    if not os.path.exists(file_path):
        return []
    
    try:
        weather_data = []
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('city', '').lower() == city.lower() and row.get('state', '').lower() == state.lower():
                    weather_data.append(row)
        return weather_data
    except Exception as e:
        print(f"Error loading weather data: {e}")
        return []

def create_temperature_chart():
    """
    Create and display a temperature chart for New York, NY showing actual vs predicted data.
    """
    # Load weather data for New York, NY
    weather_data = load_weather_data("New York", "New York")
    
    if not weather_data:
        messagebox.showerror("No Data", "No weather data found for New York, NY.\n\nPlease export some weather data first.")
        return
    
    # Parse and sort data by date
    dates = []
    temps = []
    predicted_flags = []
    
    for row in weather_data:
        try:
            date = datetime.strptime(row['weather_date'], '%Y-%m-%d')
            temp = float(row['temp']) if row['temp'] else 0
            predicted = row['predicted'].lower() == 'true'
            
            dates.append(date)
            temps.append(temp)
            predicted_flags.append(predicted)
        except (ValueError, KeyError) as e:
            print(f"Error parsing row: {e}")
            continue
    
    if not dates:
        messagebox.showerror("No Data", "No valid temperature data found for New York, NY.")
        return
    
    # Sort data by date
    sorted_data = sorted(zip(dates, temps, predicted_flags))
    dates, temps, predicted_flags = zip(*sorted_data)
    
    # Separate actual and predicted data
    actual_dates, actual_temps = [], []
    predicted_dates, predicted_temps = [], []
    
    for date, temp, is_predicted in zip(dates, temps, predicted_flags):
        if is_predicted:
            predicted_dates.append(date)
            predicted_temps.append(temp)
        else:
            actual_dates.append(date)
            actual_temps.append(temp)
    
    # Create new window for the chart
    chart_window = tk.Toplevel()
    chart_window.title("Temperature Chart - New York, NY")
    chart_window.geometry("1000x600")
    
    # Create matplotlib figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot actual data (solid line with circles)
    if actual_dates and actual_temps:
        ax.plot(actual_dates, actual_temps, 'o-', color='#2E86AB', linewidth=2, 
                markersize=6, label='Actual Temperature', markerfacecolor='#2E86AB')
    
    # Plot predicted data (dashed line with triangles)
    if predicted_dates and predicted_temps:
        ax.plot(predicted_dates, predicted_temps, '^--', color='#F24236', linewidth=2,
                markersize=6, label='Predicted Temperature', markerfacecolor='#F24236')
    
    # Add connecting line from today to tomorrow
    today = datetime.now().date()
    today_temp = None
    tomorrow_temp = None
    tomorrow_date = None
    
    # Find today's actual temperature
    for date, temp, is_predicted in zip(dates, temps, predicted_flags):
        if date.date() == today and not is_predicted:
            today_temp = temp
            break
    
    # Find tomorrow's predicted temperature
    for date, temp, is_predicted in zip(dates, temps, predicted_flags):
        if date.date() > today and is_predicted:
            tomorrow_temp = temp
            tomorrow_date = date
            break
    
    # Draw connecting line if both points exist
    if today_temp is not None and tomorrow_temp is not None and tomorrow_date is not None:
        ax.plot([today, tomorrow_date], [today_temp, tomorrow_temp], 
                '--', color='#F24236', linewidth=2, alpha=0.8)
    
    # Customize the chart
    ax.set_title('Temperature Trends - New York, NY', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Temperature (°F)', fontsize=12)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Add legend
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
    
    # Add temperature range annotation
    if temps:
        min_temp = min(temps)
        max_temp = max(temps)
        ax.text(0.02, 0.98, f'Range: {min_temp:.1f}°F - {max_temp:.1f}°F', 
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Add divider line between actual and predicted data
    today = datetime.now().date()
    ax.axvline(x=today, color='gray', linestyle=':', alpha=0.7, linewidth=2)
    ax.text(today, max(temps) if temps else 80, 'Today', rotation=90, 
            verticalalignment='bottom', horizontalalignment='right',
            color='gray', fontweight='bold')
    
    # Set y-axis limits with some padding
    if temps:
        temp_range = max_temp - min_temp
        padding = max(temp_range * 0.1, 5)  # At least 5 degrees padding
        ax.set_ylim(min_temp - padding, max_temp + padding)
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Embed the plot in the tkinter window
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Add a close button
    close_button = tk.Button(chart_window, text="Close", command=chart_window.destroy)
    close_button.pack(pady=10)
    
    # Make sure the window is brought to front
    chart_window.lift()
    chart_window.attributes('-topmost', True)
    chart_window.after_idle(lambda: chart_window.attributes('-topmost', False))

def show_temperature_chart():
    """
    Main function to show the temperature chart. This is called from the GUI.
    """
    try:
        create_temperature_chart()
    except Exception as e:
        messagebox.showerror("Chart Error", f"Error creating temperature chart: {str(e)}")

if __name__ == "__main__":
    # For testing purposes
    show_temperature_chart() 