import requests
import os
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

def get_stock_price(symbol):
    try:
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            raise Exception("Finnhub API key not found in .env file")
            
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Check if we got valid data
        if data.get('c') == 0 and data.get('h') == 0 and data.get('l') == 0:
            raise Exception(f"Could not find stock data for symbol: {symbol}")

        return {
            'currentPrice': data['c'],
            'change': data['d'],
            'percentChange': data['dp'],
            'highPrice': data['h'],
            'lowPrice': data['l'],
            'openPrice': data['o'],
            'previousClose': data['pc'],
            'symbol': symbol.upper()
        }

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch stock data: {str(e)}")
    except KeyError as e:
        raise Exception(f"Invalid response format: {str(e)}")
    except ValueError as e:
        raise Exception(f"Invalid numeric value in response: {str(e)}")
    except Exception as e:
        raise Exception(f"Error getting stock price: {str(e)}") 