"""
AI Price Finder API - Backend for Flutter App
Works with Jupyter notebook SmartSearchEngine class
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import json
from typing import Dict, List, Optional

app = Flask(__name__)
CORS(app)  # Allows Flutter to connect

# ============================================
# SMART SEARCH ENGINE CLASS
# Copy this from your working Jupyter notebook
# ============================================

class SmartSearchEngine:
    """
    AI-powered search engine with FULL location support
    """
    
    def __init__(self, serpapi_key=None):
        self.serpapi_key = "f10ca0c748ac6ed6600b0c1fc8971f344fe0ed7d319c8f7a0be80e170de68d7a"
        self.use_demo_mode = False
    
    def _price_to_number(self, price_str: str) -> float:
        if not price_str:
            return 999999
        numbers = re.findall(r'\d+\.?\d*', price_str)
        if numbers:
            return float(numbers[0])
        return 999999
    
    def understand_intent(self, user_query: str) -> Dict:
        query_lower = user_query.lower()
        
        location = None
        location_type = None
        
        if 'near me' in query_lower or 'around me' in query_lower or query_lower in ['near me', 'around me', 'my location', 'near']:
            location_type = 'near_me'
            location = 'current_location'
        
        # European Cities
        europe_cities = [
            'paris', 'lyon', 'marseille', 'nice', 'bordeaux',
            'berlin', 'munich', 'hamburg', 'cologne', 'frankfurt',
            'madrid', 'barcelona', 'valencia', 'seville',
            'rome', 'milan', 'naples', 'florence', 'venice',
            'amsterdam', 'rotterdam', 'the hague',
            'brussels', 'antwerp',
            'vienna', 'salzburg',
            'zurich', 'geneva', 'bern',
            'lisbon', 'porto',
            'copenhagen', 'aarhus',
            'stockholm', 'gothenburg', 'malmo',
            'oslo', 'bergen',
            'helsinki',
            'reykjavik',
            'warsaw', 'krakow', 'gdansk',
            'prague', 'brno',
            'budapest',
            'bucharest', 'cluj-napoca',
            'sofia',
            'belgrade',
            'zagreb',
            'athens', 'thessaloniki',
            'larnaca', 'nicosia', 'limassol', 'paphos', 'ayia napa',
            'valletta',
            'vilnius', 'kaunas', 'riga', 'tallinn',
        ]
        
        uk_cities = [
            'london', 'manchester', 'birmingham', 'liverpool', 'leeds', 'newcastle',
            'bristol', 'sheffield', 'glasgow', 'edinburgh', 'aberdeen', 'dundee',
            'belfast', 'cardiff', 'swansea', 'cambridge', 'oxford', 'brighton',
            'southampton', 'portsmouth', 'nottingham', 'leicester', 'coventry'
        ]
        
        us_cities = [
            'new york', 'boston', 'philadelphia', 'washington dc', 'baltimore',
            'los angeles', 'san francisco', 'seattle', 'portland', 'san diego', 'las vegas',
            'chicago', 'detroit', 'cleveland', 'indianapolis', 'st louis', 'minneapolis', 'milwaukee',
            'miami', 'orlando', 'tampa', 'atlanta', 'charlotte', 'nashville', 'austin', 'dallas', 'houston', 'new orleans',
            'denver', 'salt lake city', 'phoenix', 'albuquerque',
            'san antonio', 'fort worth', 'el paso',
        ]
        
        asia_cities = [
            'tokyo', 'osaka', 'kyoto', 'yokohama',
            'seoul', 'busan',
            'beijing', 'shanghai', 'guangzhou', 'shenzhen',
            'singapore',
            'bangkok', 'phuket',
            'kuala lumpur',
            'mumbai', 'delhi', 'bangalore', 'chennai',
            'dubai', 'abu dhabi',
            'tel aviv', 'jerusalem',
            'istanbul', 'ankara',
        ]
        
        all_cities = europe_cities + uk_cities + us_cities + asia_cities
        
        for city in all_cities:
            if f'near {city}' in query_lower or f'in {city}' in query_lower:
                location_type = 'specific_city'
                location = city.title()
                break
        
        # Price preference
        if any(word in query_lower for word in ['cheap', 'budget', 'low cost', 'affordable', 'lowest']):
            price_preference = 'budget'
        elif any(word in query_lower for word in ['premium', 'expensive', 'luxury', 'high end']):
            price_preference = 'premium'
        else:
            price_preference = 'any'
        
        # Brand detection
        brands = ['nike', 'adidas', 'apple', 'samsung', 'sony', 'puma', 'gucci', 'zara',
                  'hm', 'levis', 'bmw', 'mercedes', 'toyota', 'honda', 'dell', 'hp']
        detected_brand = None
        for brand in brands:
            if brand in query_lower:
                detected_brand = brand
                break
        
        # Extract product
        stop_words = ['show', 'me', 'find', 'get', 'near', 'in', 'cheap', 'budget', 'low cost',
                     'premium', 'expensive', 'best', 'top', 'affordable', 'inexpensive',
                     'discount', 'sale', 'price', 'prices', 'lowest', 'around', 'please']
        
        product = query_lower
        for word in stop_words:
            product = product.replace(word, '')
        
        if detected_brand:
            product = product.replace(detected_brand, '')
        
        if location and location != 'current_location':
            product = product.replace(f'near {location.lower()}', '')
            product = product.replace(f'in {location.lower()}', '')
        
        product = ' '.join(product.split()).strip()
        if not product or product == 'near me':
            product = 'shops' if location_type == 'near_me' else 'products'
        
        # Determine search type
        if location_type == 'near_me':
            search_type = 'local_shops'
        elif location_type in ['specific_city', 'specific_country']:
            search_type = 'location_specific'
        else:
            search_type = 'online_worldwide'
        
        return {
            'original_query': user_query,
            'product': product,
            'brand': detected_brand,
            'price_preference': price_preference,
            'location': location,
            'location_type': location_type,
            'search_type': search_type,
            'search_term': f"{detected_brand + ' ' if detected_brand else ''}{product}".strip()
        }
    
    def search_online_worldwide(self, intent: Dict) -> List[Dict]:
        search_term = intent['search_term']
        
        params = {
            'engine': 'google_shopping',
            'q': search_term,
            'api_key': self.serpapi_key,
            'num': 5
        }
        
        try:
            print(f"   🌐 Searching online for: {search_term}")
            response = requests.get('https://serpapi.com/search', params=params, timeout=10)
            data = response.json()
            
            results = []
            if 'shopping_results' in data:
                for item in data['shopping_results'][:5]:
                    price_str = item.get('price', 'N/A')
                    results.append({
                        'name': item.get('title', 'Unknown'),
                        'price': price_str,
                        'currency': self._get_currency_from_price(price_str),
                        'store': item.get('source', 'Unknown'),
                        'link': item.get('link', '#'),
                        'image': item.get('thumbnail', ''),
                        'rating': item.get('rating', None),
                        'in_stock': True
                    })
                results.sort(key=lambda x: self._price_to_number(x['price']))
                print(f"   ✅ Found {len(results)} products")
                return results
            else:
                return self._get_demo_results(intent)
        except Exception as e:
            print(f"   ❌ SerpAPI Error: {e}")
            return self._get_demo_results(intent)
    
    def _get_currency_from_price(self, price_str: str) -> str:
        if '$' in price_str:
            return 'USD'
        elif '€' in price_str:
            return 'EUR'
        elif '£' in price_str:
            return 'GBP'
        return 'USD'
    
    def _get_demo_results(self, intent: Dict) -> List[Dict]:
        search_term = intent['search_term']
        return [
            {'name': f'{search_term} - Standard', 'price': '$49.99', 'currency': 'USD', 'store': 'Demo Store', 'link': '#', 'image': '', 'in_stock': True},
            {'name': f'{search_term} - Premium', 'price': '$89.99', 'currency': 'USD', 'store': 'Demo Store 2', 'link': '#', 'image': '', 'in_stock': True},
        ]
    
    def search_location_specific(self, intent: Dict) -> Dict:
        location = intent['location']
        search_term = intent['product'] if intent['product'] != 'products' else 'shopping'
        
        if location == 'current_location':
            return {
                'shops': [{
                    'name': f'{search_term.capitalize()} Stores Near You',
                    'address': '📍 Type "shops in [city name]" for specific locations',
                    'latitude': None,
                    'longitude': None,
                    'note': 'Examples: "shops in London", "restaurants in Paris"'
                }],
                'products': []
            }
        
        location_shops = {
            'Paris': [{'name': f'{search_term.capitalize()} at Galeries Lafayette', 'address': '40 Bd Haussmann, 75009 Paris', 'lat': 48.8738, 'lng': 2.3350}],
            'London': [{'name': f'{search_term.capitalize()} at Harrods', 'address': '87-135 Brompton Rd, London SW1X 7XL', 'lat': 51.4995, 'lng': -0.1626}],
            'New York': [{'name': f'{search_term.capitalize()} at Macy\'s', 'address': '151 W 34th St, New York, NY 10001', 'lat': 40.7508, 'lng': -73.9881}],
            'Larnaca': [{'name': f'{search_term.capitalize()} at Metropolis Mall', 'address': 'Λεωφόρος Αγίου Λαζάρου, Larnaca', 'lat': 34.9174, 'lng': 33.6237}],
            'Tokyo': [{'name': f'{search_term.capitalize()} at Shibuya 109', 'address': '2-29-1 Dogenzaka, Shibuya, Tokyo', 'lat': 35.6591, 'lng': 139.6983}],
            'Berlin': [{'name': f'{search_term.capitalize()} at KaDeWe', 'address': 'Tauentzienstraße 21-24, 10789 Berlin', 'lat': 52.5016, 'lng': 13.3414}],
        }
        
        if location in location_shops:
            shops = []
            for shop in location_shops[location]:
                shops.append({
                    'name': shop['name'],
                    'address': shop['address'],
                    'latitude': shop['lat'],
                    'longitude': shop['lng'],
                    'rating': 4.3
                })
            return {'shops': shops, 'products': [], 'location': location}
        else:
            return {
                'shops': [{
                    'name': f'{search_term.capitalize()} options in {location}',
                    'address': f'📍 Browse stores in {location}',
                    'latitude': None,
                    'longitude': None,
                    'note': f'Search Google Maps for "{search_term} in {location}"'
                }],
                'products': []
            }
    
    def find_nearby_shops(self, intent: Dict, user_location: str = None) -> List[Dict]:
        if user_location and user_location != 'current_location':
            temp_intent = intent.copy()
            temp_intent['location'] = user_location
            return self.search_location_specific(temp_intent).get('shops', [])
        
        return [{
            'name': 'Nearby Stores',
            'address': '📍 Type "shops in [city name]" for specific locations',
            'latitude': None,
            'longitude': None,
            'note': 'Examples: "shops in London", "cafes in Paris"'
        }]
    
    def search(self, user_query: str, user_location: str = None) -> Dict:
        intent = self.understand_intent(user_query)
        
        if user_location and user_location != 'current_location':
            intent['location'] = user_location
            intent['search_type'] = 'local_shops'
            print(f"\n📍 Using location: {user_location}")
        elif user_location == 'current_location':
            intent['location'] = 'current_location'
            intent['search_type'] = 'local_shops'
        
        print(f"\n{'='*50}")
        print(f"📝 Query: {user_query}")
        print(f"🎯 Product: {intent['product']}, Brand: {intent['brand'] or 'any'}")
        print(f"📍 Location: {intent['location'] or 'worldwide'}")
        
        results = {}
        
        if intent['search_type'] == 'online_worldwide':
            results['products'] = self.search_online_worldwide(intent)
            results['shops'] = []
        elif intent['search_type'] == 'location_specific':
            location_data = self.search_location_specific(intent)
            results['products'] = location_data.get('products', [])
            results['shops'] = location_data.get('shops', [])
        else:
            results['products'] = []
            results['shops'] = self.find_nearby_shops(intent, user_location or intent.get('location'))
        
        results['intent'] = intent
        
        if results.get('products') and len(results['products']) > 0:
            cheapest = results['products'][0]
            results['message'] = f"✅ Found {len(results['products'])} items. Cheapest: {cheapest['name']} at {cheapest['price']}"
        elif results.get('shops') and len(results['shops']) > 0:
            results['message'] = f"✅ Found {len(results['shops'])} shops"
        else:
            results['message'] = "❌ No results found"
        
        return results


# ============================================
# FLASK API ENDPOINTS
# ============================================

engine = SmartSearchEngine()

@app.route('/search', methods=['POST'])
def search():
    """Main endpoint for Flutter app"""
    data = request.json
    query = data.get('query', '')
    location = data.get('location', None)
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    result = engine.search(query, location)
    
    return jsonify({
        'success': True,
        'query': query,
        'message': result.get('message', ''),
        'products': result.get('products', []),
        'shops': result.get('shops', []),
        'intent': result.get('intent', {})
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Price Finder API is running!',
        'endpoints': {
            'search': 'POST /search',
            'health': 'GET /health'
        }
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'AI Price Finder API',
        'version': '1.0',
        'description': 'Backend for Flutter price comparison app',
        'instructions': 'Send POST request to /search with {"query": "shoes in London"}'
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 AI Price Finder API Starting...")
    print("="*50)
    print("📍 Local URL: http://localhost:5000")
    print("📍 Health check: http://localhost:5000/health")
    print("📍 Search endpoint: POST http://localhost:5000/search")
    print("\n📝 Example curl command:")
    print('curl -X POST http://localhost:5000/search -H "Content-Type: application/json" -d \'{"query": "shoes in London"}\'')
    print("\n" + "="*50)
    app.run(host='0.0.0.0', port=5001, debug=True)