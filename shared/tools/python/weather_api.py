import requests
import os
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

def get_weather(city):
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            raise Exception("OpenWeather API key not found in .env file")
        
        # First get coordinates for the city
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data:
            raise Exception(f"Could not find location: {city}")

        lat, lon = geo_data[0]['lat'], geo_data[0]['lon']

        # Then get weather data
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        return {
            'temperature': round(weather_data['main']['temp']),
            'description': weather_data['weather'][0]['description'],
            'humidity': weather_data['main']['humidity'],
            'windSpeed': weather_data['wind']['speed'],
            'city': weather_data['name'],
            'country': weather_data['sys']['country']
        }

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch weather data: {str(e)}")
    except KeyError as e:
        raise Exception(f"Invalid response format: {str(e)}")
    except Exception as e:
        raise Exception(f"Error getting weather: {str(e)}") 