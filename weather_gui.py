import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Tuple
import csv
import os
import threading
import requests
from PIL import Image, ImageTk
from io import BytesIO
import datetime
from fetch_coordinates import get_city_coordinates
from fetch_weather import get_weather_data
from weather_export import export_daily_weather_to_csv, validate_export_data
from weather_chart import show_temperature_chart

class WeatherGUI:
    def __init__(self, root):
        self.root = root
        self.city_data = self.load_city_data()
        self.city_options = self.prepare_city_options()
        self.selected_city_data = None  # Track the selected city and state
        self.current_weather_data = None  # Store current weather data for export
        self.current_coordinates = None  # Store current coordinates for export
        self.current_theme = "default"  # Track current theme
        self.setup_window()
        self.setup_widgets()
    
    def load_city_data(self) -> List[Tuple[str, str]]:
        """Load city and state data from CSV file"""
        city_data = []
        csv_file = "cities_dict.csv"
        
        if not os.path.exists(csv_file):
            print(f"Warning: {csv_file} not found. Autocomplete will not be available.")
            return city_data
        
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                seen_cities = set()  # To avoid duplicates
                
                for row in reader:
                    city = row.get('City', '').strip()
                    state = row.get('State', '').strip()
                    
                    # Create a unique identifier to avoid duplicates
                    city_state_combo = (city, state)
                    
                    if city and state and city_state_combo not in seen_cities:
                        city_data.append((city, state))
                        seen_cities.add(city_state_combo)
                        
        except Exception as e:
            print(f"Error loading city data: {e}")
        
        return city_data
    
    def prepare_city_options(self) -> List[str]:
        """Prepare formatted city options for autocomplete"""
        options = []
        for city, state in self.city_data:
            options.append(f"{city}, {state}")
        return sorted(options)
    
    def setup_window(self):
        """Configure the main window"""
        self.root.title("Weather App")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Center the window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configure grid weight for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def setup_widgets(self):
        """Create and arrange all GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="🌤️ Weather App", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # City input section
        input_frame = ttk.LabelFrame(main_frame, text="Search for City", padding="10")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)
        
        # City input field
        self.city_var = tk.StringVar()
        self.city_entry = ttk.Entry(
            input_frame, 
            textvariable=self.city_var,
            font=("Arial", 12),
            width=30
        )
        self.city_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Bind typing to filter city list
        self.city_entry.bind('<KeyRelease>', self.on_city_input_change)
        
        # Submit button
        self.submit_button = ttk.Button(
            input_frame,
            text="Get Weather",
            command=self.on_submit_click,
            style="Accent.TButton"
        )
        self.submit_button.grid(row=0, column=1)
        
        # City selection list
        city_list_frame = ttk.LabelFrame(main_frame, text="Select City (Required)", padding="10")
        city_list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        city_list_frame.grid_columnconfigure(0, weight=1)
        city_list_frame.grid_rowconfigure(0, weight=1)
        
        # Listbox with scrollbar for city selection
        list_frame = tk.Frame(city_list_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.city_listbox = tk.Listbox(
            list_frame,
            height=8,
            font=("Arial", 10),
            selectmode=tk.SINGLE
        )
        self.city_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for city list
        city_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.city_listbox.yview)
        city_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.city_listbox.configure(yscrollcommand=city_scrollbar.set)
        
        # Bind selection event
        self.city_listbox.bind('<<ListboxSelect>>', self.on_city_list_select)
        
        # Populate the initial city list
        self.populate_city_list()
        
        # Weather tabs
        self.create_weather_tabs(main_frame)
        main_frame.grid_rowconfigure(2, weight=1)  # City list frame
        main_frame.grid_rowconfigure(3, weight=1)  # Weather tabs
        
        # Export button section
        export_frame = ttk.Frame(main_frame, padding="5")
        export_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        export_frame.grid_columnconfigure(0, weight=1)
        export_frame.grid_columnconfigure(1, weight=1)
        
        # Button container for horizontal layout
        button_container = ttk.Frame(export_frame)
        button_container.grid(row=0, column=0, columnspan=2)
        
        # Export button
        self.export_button = ttk.Button(
            button_container,
            text="Export Daily Weather",
            command=self.on_export_click,
            state='disabled'  # Initially disabled until weather data is loaded
        )
        self.export_button.grid(row=0, column=0, padx=(0, 10))
        
        # Chart button
        self.chart_button = ttk.Button(
            button_container,
            text="Show Temp Chart",
            command=self.on_chart_click
        )
        self.chart_button.grid(row=0, column=1, padx=(10, 0))
        
        # Bind Enter key to submit
        self.root.bind('<Return>', lambda event: self.on_submit_click())
        
        # Set focus to city entry
        self.city_entry.focus()
    
    def create_weather_tabs(self, parent):
        """Create the tabbed interface for weather information"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Tab 1: Current Weather
        self.current_weather_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.current_weather_frame, text="  Current Weather  ")
        self.setup_current_weather_tab()
        
        # Tab 2: 5 Day Forecast
        self.forecast_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.forecast_frame, text="  5 Day Forecast  ")
        self.setup_forecast_tab()
        

    
    def setup_current_weather_tab(self):
        """Setup the current weather tab with visual elements"""
        # Main container
        main_container = ttk.Frame(self.current_weather_frame, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Weather icon and main info section
        top_section = ttk.Frame(main_container)
        top_section.pack(fill=tk.X, pady=(0, 20))
        
        # Weather icon (left side)
        self.weather_icon_label = ttk.Label(top_section)
        self.weather_icon_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Main weather info (right side)
        info_frame = ttk.Frame(top_section)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # City name
        self.city_name_label = ttk.Label(info_frame, text="Select a city to see weather", 
                                        font=("Arial", 16, "bold"))
        self.city_name_label.pack(anchor=tk.W)
        
        # Temperature
        self.temperature_label = ttk.Label(info_frame, text="", font=("Arial", 32, "bold"))
        self.temperature_label.pack(anchor=tk.W)
        
        # Weather description
        self.description_label = ttk.Label(info_frame, text="", font=("Arial", 12))
        self.description_label.pack(anchor=tk.W)
        
        # Weather details grid
        details_frame = ttk.LabelFrame(main_container, text="Weather Details", padding="15")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create grid for weather details
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns
        for i in range(3):
            details_grid.columnconfigure(i, weight=1)
        
        # Weather detail labels (simplified to only 4 items)
        self.feels_like_label = ttk.Label(details_grid, text="Feels like: --", font=("Arial", 10))
        self.feels_like_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.humidity_label = ttk.Label(details_grid, text="Humidity: --", font=("Arial", 10))
        self.humidity_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.sunrise_sunset_label = ttk.Label(details_grid, text="Sunrise/Sunset: --", font=("Arial", 10))
        self.sunrise_sunset_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
    
    def setup_forecast_tab(self):
        """Setup the 5-day forecast tab"""
        # Main container
        main_container = ttk.Frame(self.forecast_frame, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_container, text="5-Day Forecast", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Create horizontal frame for forecast cards
        self.forecast_cards_frame = ttk.Frame(main_container)
        self.forecast_cards_frame.pack(fill=tk.X, expand=True)
        
        # Initialize forecast day widgets (will be populated later)
        self.forecast_day_widgets = []
        
        # Create 5 forecast cards
        for i in range(5):
            # Create card frame
            card_frame = ttk.Frame(self.forecast_cards_frame)
            card_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Day name
            day_label = ttk.Label(card_frame, text="", font=("Arial", 12, "bold"))
            day_label.pack(pady=5)
            
            # Weather icon
            icon_label = ttk.Label(card_frame, text="", font=("Arial", 32))
            icon_label.pack(pady=5)
            
            # Temperature
            temp_label = ttk.Label(card_frame, text="", font=("Arial", 14, "bold"))
            temp_label.pack(pady=2)
            
            # Conditions
            conditions_label = ttk.Label(card_frame, text="", font=("Arial", 10), wraplength=100)
            conditions_label.pack(pady=2)
            
            # Store widgets for later updates
            self.forecast_day_widgets.append({
                'day': day_label,
                'icon': icon_label,
                'temp': temp_label,
                'conditions': conditions_label
            })
    

    def populate_city_list(self, filter_text: str = ""):
        """Populate the city listbox with filtered results"""
        # Clear current list
        self.city_listbox.delete(0, tk.END)
        
        # Filter cities based on input
        if filter_text:
            filtered_cities = [
                city for city in self.city_options 
                if filter_text.lower() in city.lower()
            ]
        else:
            filtered_cities = self.city_options
        
        # Limit results for performance
        filtered_cities = filtered_cities[:100]
        
        # Add filtered cities to listbox
        for city in filtered_cities:
            self.city_listbox.insert(tk.END, city)
    
    def on_city_input_change(self, event):
        """Handle typing in the city input field"""
        current_value = self.city_var.get()
        
        # Clear selected city data when user types manually
        if self.selected_city_data and current_value != self.selected_city_data.get('full_name', ''):
            self.selected_city_data = None
        
        # Update the city list based on input
        self.populate_city_list(current_value)
    
    def on_city_list_select(self, event):
        """Handle selection from the city list"""
        selection = self.city_listbox.curselection()
        if not selection:
            self.selected_city_data = None
            return
        
        # Get selected city
        selected_city = self.city_listbox.get(selection[0])
        
        # Update input field
        self.city_var.set(selected_city)
        
        # Store selected city data
        if ", " in selected_city:
            city, state = selected_city.rsplit(", ", 1)
            self.selected_city_data = {
                'city': city,
                'state': state,
                'country': 'US',
                'full_name': selected_city
            }
        else:
            self.selected_city_data = None
    
    def on_submit_click(self):
        """Handle submit button click"""
        # Validate that a city has been selected from the list
        if not self.selected_city_data:
            messagebox.showwarning(
                "Selection Required", 
                "Please select a city from the list below.\n\nType to search, then click on a city to select it."
            )
            self.city_entry.focus()
            return
        
        # Get the selected city data
        city = self.selected_city_data['city']
        state = self.selected_city_data['state']
        country = self.selected_city_data['country']
        full_name = self.selected_city_data['full_name']
        

        
        # Disable the button to prevent multiple requests
        self.submit_button.config(state='disabled')
        
        # Disable export button during new search
        self.export_button.config(state='disabled')
        
        # Run API call in separate thread to prevent GUI freezing
        def fetch_coordinates():
            try:
                # Call the fetch coordinates API
                coordinates = get_city_coordinates(city, state, country)
                
                # Use after() to update GUI from main thread
                self.root.after(0, self.display_coordinates_result, coordinates, full_name)
                
            except Exception as e:
                # Handle errors
                self.root.after(0, self.display_error, str(e))
            finally:
                # Re-enable button
                self.root.after(0, lambda: self.submit_button.config(state='normal'))
        
        # Start the thread
        thread = threading.Thread(target=fetch_coordinates)
        thread.daemon = True
        thread.start()
        

    def clear_selection(self):
        """Clear the current city selection"""
        self.selected_city_data = None
        self.city_var.set("")
        self.city_listbox.selection_clear(0, tk.END)
        self.populate_city_list()
    
    def on_export_click(self):
        """Handle export button click"""
        if not validate_export_data(self.current_weather_data, self.current_coordinates):
            messagebox.showwarning(
                "Export Not Available",
                "No weather data available to export.\n\nPlease search for a city first to load weather data."
            )
            return
        
        # Call the export function
        export_daily_weather_to_csv(self.current_weather_data, self.current_coordinates)
    
    def on_chart_click(self):
        """Handle chart button click"""
        # Call the chart function
        show_temperature_chart()
    
    def get_weather_theme(self, weather_data):
        """
        Determine the UI theme based on current weather conditions.
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            str: Theme name
        """
        if not weather_data or 'current' not in weather_data:
            return "default"
        
        current = weather_data['current']
        if 'weather' not in current or not current['weather']:
            return "default"
        
        weather_main = current['weather'][0].get('main', '').lower()
        weather_desc = current['weather'][0].get('description', '').lower()
        
        # Determine theme based on weather conditions
        if weather_main in ['clear']:
            return "sunny"
        elif weather_main in ['clouds']:
            if 'few' in weather_desc or 'scattered' in weather_desc:
                return "partly_cloudy"
            else:
                return "cloudy"
        elif weather_main in ['rain', 'drizzle']:
            return "rainy"
        elif weather_main in ['snow']:
            return "snowy"
        elif weather_main in ['thunderstorm']:
            return "stormy"
        elif weather_main in ['mist', 'fog', 'haze']:
            return "foggy"
        else:
            return "default"
    
    def apply_weather_theme(self, theme_name):
        """
        Apply visual theme to the GUI based on weather conditions.
        
        Args:
            theme_name: Name of the theme to apply
        """
        if theme_name == self.current_theme:
            return  # No change needed
        
        self.current_theme = theme_name
        
        # Define theme colors
        themes = {
            "default": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "accent": "#0078d4"
            },
            "sunny": {
                "bg": "#fff8dc",  # Light yellow
                "fg": "#8b4513",  # Brown text
                "accent": "#ff8c00"  # Orange accent
            },
            "partly_cloudy": {
                "bg": "#f0f8ff",  # Light blue
                "fg": "#2f4f4f",  # Dark gray text
                "accent": "#4682b4"  # Steel blue accent
            },
            "cloudy": {
                "bg": "#e6e6fa",  # Light gray
                "fg": "#2f2f2f",  # Dark text
                "accent": "#696969"  # Gray accent
            },
            "rainy": {
                "bg": "#e0f6ff",  # Light blue-gray
                "fg": "#191970",  # Dark blue text
                "accent": "#4169e1"  # Royal blue accent
            },
            "snowy": {
                "bg": "#f8f8ff",  # Ghost white
                "fg": "#2f4f4f",  # Dark slate gray
                "accent": "#87ceeb"  # Sky blue accent
            },
            "stormy": {
                "bg": "#2f2f2f",  # Dark gray
                "fg": "#ffffff",  # White text
                "accent": "#9370db"  # Purple accent
            },
            "foggy": {
                "bg": "#f5f5f5",  # White smoke
                "fg": "#708090",  # Slate gray text
                "accent": "#a9a9a9"  # Dark gray accent
            }
        }
        
        colors = themes.get(theme_name, themes["default"])
        
        try:
            # Apply theme to main window
            self.root.configure(bg=colors["bg"])
            
            # Create custom styles for themed elements
            style = ttk.Style()
            
            # Configure ttk styles with the theme
            style.theme_use('clam')  # Use a base theme that supports customization
            
            # Configure button style
            style.configure(
                "Weather.TButton",
                background=colors["accent"],
                foreground="white" if theme_name == "stormy" else "black",
                borderwidth=1,
                focuscolor='none'
            )
            
            # Configure frame style  
            style.configure(
                "Weather.TFrame",
                background=colors["bg"],
                relief="flat"
            )
            
            # Configure label frame style
            style.configure(
                "Weather.TLabelframe",
                background=colors["bg"],
                foreground=colors["fg"]
            )
            
            # Configure label style
            style.configure(
                "Weather.TLabel",
                background=colors["bg"],
                foreground=colors["fg"]
            )
            
            # Configure notebook style
            style.configure(
                "Weather.TNotebook",
                background=colors["bg"]
            )
            
            style.configure(
                "Weather.TNotebook.Tab",
                background=colors["accent"],
                foreground="white" if theme_name == "stormy" else "black"
            )
            
            # Apply styles to all the themed widgets
            self.apply_theme_to_widgets(colors)
            
            # Update window title with weather emoji
            weather_emojis = {
                "sunny": "☀️",
                "partly_cloudy": "⛅",
                "cloudy": "☁️",
                "rainy": "🌧️",
                "snowy": "❄️",
                "stormy": "⛈️",
                "foggy": "🌫️",
                "default": "🌤️"
            }
            
            emoji = weather_emojis.get(theme_name, "🌤️")
            self.root.title(f"{emoji} Weather App - {theme_name.replace('_', ' ').title()}")
            
        except Exception as e:
            print(f"Error applying theme: {e}")
            # Fallback to default if theme application fails
            self.root.configure(bg="#f0f0f0")
            self.root.title("Weather App")
    
    def apply_theme_to_widgets(self, colors):
        """Apply theme colors to specific widgets"""
        try:
            # Find and update all widgets recursively
            def update_widget(widget):
                widget_class = widget.winfo_class()
                
                # Apply styles based on widget type
                if widget_class == 'Button':
                    widget.configure(bg=colors["accent"], 
                                   fg="white" if self.current_theme == "stormy" else "black")
                elif widget_class == 'Frame':
                    widget.configure(bg=colors["bg"])
                elif widget_class == 'Label':
                    widget.configure(bg=colors["bg"], fg=colors["fg"])
                elif widget_class == 'TButton':
                    widget.configure(style="Weather.TButton")
                elif widget_class == 'TFrame':
                    widget.configure(style="Weather.TFrame")
                elif widget_class == 'TLabelframe':
                    widget.configure(style="Weather.TLabelframe")
                elif widget_class == 'TLabel':
                    widget.configure(style="Weather.TLabel")
                elif widget_class == 'TNotebook':
                    widget.configure(style="Weather.TNotebook")
                
                # Recursively update children
                for child in widget.winfo_children():
                    update_widget(child)
            
            # Start from root
            update_widget(self.root)
            
        except Exception as e:
            print(f"Error updating widgets: {e}")
    
    def display_coordinates_result(self, coordinates, city_name):
        """Display the coordinates result in the GUI and fetch weather data"""
        if coordinates:
            # Now fetch current weather data
            def fetch_weather():
                try:
                    lat = coordinates.get('lat')
                    lon = coordinates.get('lon')
                    
                    # Fetch weather data including daily forecast
                    weather_data = get_weather_data(lat, lon, exclude="minutely,hourly,alerts")
                    
                    # Update GUI from main thread
                    self.root.after(0, self.display_weather_result, weather_data, coordinates)
                    
                except Exception as e:
                    self.root.after(0, self.display_error, f"Weather fetch error: {str(e)}")
            
            # Start weather fetch thread
            weather_thread = threading.Thread(target=fetch_weather)
            weather_thread.daemon = True
            weather_thread.start()
            
        else:
            # Show error message for no coordinates found
            messagebox.showerror("Error", f"No coordinates found for {city_name}. Please try a different city or check your spelling.")
    
    def display_error(self, error_message):
        """Display error message in the GUI"""
        # Clear stored data and disable export button
        self.current_weather_data = None
        self.current_coordinates = None
        self.export_button.config(state='disabled')
        
        # Reset theme to default
        self.apply_weather_theme("default")
        
        messagebox.showerror("Error", f"Error occurred: {error_message}\n\nPlease check your internet connection and try again.")
    
    def display_weather_result(self, weather_data, coordinates):
        """Display weather data in current weather tab and forecast tab"""
        if weather_data and 'current' in weather_data:
            # Store weather data and coordinates for export
            self.current_weather_data = weather_data
            self.current_coordinates = coordinates
            
            # Apply weather-based theme
            theme_name = self.get_weather_theme(weather_data)
            self.apply_weather_theme(theme_name)
            
            # Update current weather tab
            self.update_current_weather_tab(weather_data, coordinates)
            
            # Update forecast tab
            self.update_forecast_tab(weather_data, coordinates)
            
            # Enable export button if we have daily data
            if 'daily' in weather_data and weather_data['daily']:
                self.export_button.config(state='normal')
            else:
                self.export_button.config(state='disabled')
            
            # Switch to current weather tab
            self.notebook.select(0)
            
        else:
            messagebox.showerror("Error", "No weather data available")
    
    def update_current_weather_tab(self, weather_data, coordinates):
        """Update the current weather tab with weather data"""
        if not weather_data or 'current' not in weather_data:
            return
            
        current = weather_data['current']
        
        # Update city name
        city_name = coordinates.get('name', 'Unknown')
        country = coordinates.get('country', '')
        state = coordinates.get('state', '')
        location_text = f"{city_name}"
        if state:
            location_text += f", {state}"
        if country:
            location_text += f", {country}"
        self.city_name_label.config(text=location_text)
        
        # Update temperature
        temp = current.get('temp', 0)
        self.temperature_label.config(text=f"{temp:.1f}°F")
        
        # Update weather description
        if 'weather' in current and current['weather']:
            weather_info = current['weather'][0]
            description = weather_info.get('description', '').title()
            self.description_label.config(text=description)
            
            # Load weather icon
            icon_code = weather_info.get('icon', '')
            if icon_code:
                self.load_weather_icon(icon_code)
        
        # Update weather details (simplified)
        feels_like = current.get('feels_like', None)
        humidity = current.get('humidity', None)
        
        self.feels_like_label.config(text=f"Feels like: {feels_like:.1f}°F" if feels_like is not None else "Feels like: --")
        self.humidity_label.config(text=f"Humidity: {humidity}%" if humidity is not None else "Humidity: --")
        
        # Update sunrise/sunset
        sunrise = current.get('sunrise', 0)
        sunset = current.get('sunset', 0)
        if sunrise and sunset:
            import datetime
            sunrise_time = datetime.datetime.fromtimestamp(sunrise).strftime("%H:%M")
            sunset_time = datetime.datetime.fromtimestamp(sunset).strftime("%H:%M")
            self.sunrise_sunset_label.config(text=f"☀️ {sunrise_time} / 🌅 {sunset_time}")
        
    def update_forecast_tab(self, weather_data, coordinates):
        """Update the 5-day forecast tab with weather data"""
        if not weather_data or 'daily' not in weather_data:
            return
            
        daily_data = weather_data['daily'][:5]  # Get first 5 days
        
        # Get today's date to calculate day names
        today = datetime.date.today()
        
        for i, day_data in enumerate(daily_data):
            if i >= len(self.forecast_day_widgets):
                break
                
            widgets = self.forecast_day_widgets[i]
            
            # Calculate day name
            forecast_date = today + datetime.timedelta(days=i)
            if i == 0:
                day_name = "Today"
            elif i == 1:
                day_name = "Tomorrow"
            else:
                day_name = forecast_date.strftime("%A")
            
            # Update day name
            widgets['day'].config(text=day_name)
            
            # Update temperature (day temp)
            temp_day = day_data.get('temp', {}).get('day', 0)
            widgets['temp'].config(text=f"{temp_day:.0f}°F")
            
            # Update conditions and icon
            if 'weather' in day_data and day_data['weather']:
                weather_info = day_data['weather'][0]
                description = weather_info.get('description', '').title()
                widgets['conditions'].config(text=description)
                
                # Load weather icon
                icon_code = weather_info.get('icon', '')
                if icon_code:
                    self.load_forecast_icon(icon_code, i)
            else:
                widgets['conditions'].config(text="")
                widgets['icon'].config(text="🌤️")
                
    def load_forecast_icon(self, icon_code, day_index):
        """Load weather icon for forecast day"""
        def fetch_icon():
            try:
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
                response = requests.get(icon_url, timeout=10)
                
                if response.status_code == 200:
                    # Load image using PIL
                    image = Image.open(BytesIO(response.content))
                    # Resize to fit nicely in the forecast cards
                    image = image.resize((50, 50), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update icon in main thread
                    self.root.after(0, self.set_forecast_icon, photo, day_index)
                else:
                    self.root.after(0, self.set_default_forecast_icon, day_index)
                    
            except Exception as e:
                print(f"Error loading forecast icon: {e}")
                self.root.after(0, self.set_default_forecast_icon, day_index)
        
        # Fetch icon in background thread
        icon_thread = threading.Thread(target=fetch_icon)
        icon_thread.daemon = True
        icon_thread.start()
    
    def set_forecast_icon(self, photo, day_index):
        """Set the weather icon for a specific forecast day"""
        if day_index < len(self.forecast_day_widgets):
            icon_widget = self.forecast_day_widgets[day_index]['icon']
            icon_widget.config(image=photo, text="")
            # Store reference to prevent garbage collection
            if not hasattr(self, 'forecast_icons'):
                self.forecast_icons = {}
            self.forecast_icons[day_index] = photo
    
    def set_default_forecast_icon(self, day_index):
        """Set a default icon for forecast day when weather icon fails to load"""
        if day_index < len(self.forecast_day_widgets):
            icon_widget = self.forecast_day_widgets[day_index]['icon']
            icon_widget.config(text="🌤️", image="")
        
    def load_weather_icon(self, icon_code):
        """Load weather icon from OpenWeatherMap"""
        def fetch_icon():
            try:
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
                response = requests.get(icon_url, timeout=10)
                
                if response.status_code == 200:
                    # Load image using PIL
                    image = Image.open(BytesIO(response.content))
                    # Resize to fit nicely in the UI
                    image = image.resize((80, 80), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update icon in main thread
                    self.root.after(0, self.set_weather_icon, photo)
                else:
                    self.root.after(0, self.set_default_icon)
                    
            except Exception as e:
                print(f"Error loading weather icon: {e}")
                self.root.after(0, self.set_default_icon)
        
        # Fetch icon in background thread
        icon_thread = threading.Thread(target=fetch_icon)
        icon_thread.daemon = True
        icon_thread.start()
    
    def set_weather_icon(self, photo):
        """Set the weather icon in the GUI"""
        self.weather_icon_label.config(image=photo)
        self.weather_icon_label.image = photo  # Keep a reference
    
    def set_default_icon(self):
        """Set a default icon when weather icon fails to load"""
        self.weather_icon_label.config(text="🌤️", font=("Arial", 48))

def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = WeatherGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 