"""
Test OpenWeatherMap API connection
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('../.env')

def test_openweather_api():
    """Test if OpenWeather API key is working"""
    
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    print("=" * 60)
    print("Testing OpenWeatherMap API")
    print("=" * 60)
    print()
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    print()
    
    # Test with Dhaka, Bangladesh
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Dhaka&appid={api_key}"
    
    print("📡 Testing API call for Dhaka weather...")
    print()
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API Key is ACTIVE!")
            print()
            print("Weather Data for Dhaka:")
            print(f"  Temperature: {data['main']['temp'] - 273.15:.1f}°C")
            print(f"  Weather: {data['weather'][0]['main']}")
            print(f"  Description: {data['weather'][0]['description']}")
            print(f"  Humidity: {data['main']['humidity']}%")
            print(f"  Wind Speed: {data['wind']['speed']} m/s")
            print()
            print("=" * 60)
            print("✅ OpenWeather API Test PASSED!")
            print("=" * 60)
            print()
            print("You're ready to start testing Phase 2 pipeline!")
            print("📖 Next: ../TESTING-QUICK-START.md")
            return True
            
        elif response.status_code == 401:
            print("⏰ API Key is NOT YET ACTIVE")
            print()
            print("Error: Invalid API key")
            print()
            print("This is normal for new accounts!")
            print("OpenWeather API keys need 10-15 minutes to activate.")
            print()
            print("Please wait a few more minutes and run this test again:")
            print("  python test_openweather.py")
            print()
            return False
            
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    test_openweather_api()
