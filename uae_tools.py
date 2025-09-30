"""
Custom LangChain tools for the Smart UAE Tourism Assistant
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class UAEKnowledgeSearchTool(BaseTool):
    """Tool for searching UAE tourism knowledge base"""
    
    name = "uae_knowledge_search"
    description = """Search the UAE knowledge base for information about cities, attractions, cultural tips, activities, and travel information. 
    Use this tool when users ask about:
    - Tourist attractions in specific UAE cities
    - Cultural tips and etiquette
    - Activities and things to do
    - Transportation information
    - Food and dining
    - Weather information
    - General UAE facts
    
    Input should be a search query like 'attractions in Dubai' or 'cultural tips for UAE'"""
    
    def __init__(self):
        super().__init__()
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load the UAE knowledge base from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, 'uae_knowledge.json')
            
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: uae_knowledge.json not found. Using empty knowledge base.")
            return {}
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in uae_knowledge.json. Using empty knowledge base.")
            return {}
    
    def _run(self, query: str) -> str:
        """Execute the search in the knowledge base"""
        query_lower = query.lower()
        results = []
        
        # Search in cities
        if any(word in query_lower for word in ['city', 'cities', 'attractions', 'things to do', 'visit']):
            city_results = self._search_cities(query_lower)
            if city_results:
                results.extend(city_results)
        
        # Search for cultural tips
        if any(word in query_lower for word in ['culture', 'cultural', 'etiquette', 'tips', 'customs']):
            cultural_results = self._search_cultural_tips(query_lower)
            if cultural_results:
                results.extend(cultural_results)
        
        # Search for activities
        if any(word in query_lower for word in ['activities', 'activity', 'adventure', 'luxury', 'family']):
            activity_results = self._search_activities(query_lower)
            if activity_results:
                results.extend(activity_results)
        
        # Search for transportation
        if any(word in query_lower for word in ['transport', 'transportation', 'metro', 'taxi', 'bus', 'travel']):
            transport_results = self._search_transportation(query_lower)
            if transport_results:
                results.extend(transport_results)
        
        # Search for food information
        if any(word in query_lower for word in ['food', 'restaurant', 'dining', 'eat', 'cuisine']):
            food_results = self._search_food(query_lower)
            if food_results:
                results.extend(food_results)
        
        # Search for weather information
        if any(word in query_lower for word in ['weather', 'temperature', 'climate', 'season']):
            weather_results = self._search_weather(query_lower)
            if weather_results:
                results.extend(weather_results)
        
        if not results:
            return "I couldn't find specific information about your query. Could you please be more specific or ask about UAE cities, attractions, cultural tips, activities, transportation, food, or weather?"
        
        return "\n\n".join(results)
    
    def _search_cities(self, query: str) -> List[str]:
        """Search for city-specific information"""
        results = []
        cities = self.knowledge_base.get('cities', {})
        
        # Check for specific city mentions
        for city_name, city_data in cities.items():
            if city_name.lower() in query:
                result = f"**{city_name}:**\n{city_data['description']}\n"
                
                if 'attractions' in query or 'things to do' in query or 'visit' in query:
                    result += f"\n**Top Attractions in {city_name}:**\n"
                    must_visit = [attr for attr in city_data['major_attractions'] if attr.get('must_visit', False)]
                    other_attractions = [attr for attr in city_data['major_attractions'] if not attr.get('must_visit', False)]
                    
                    if must_visit:
                        result += "Must-Visit:\n"
                        for attraction in must_visit:
                            result += f"• {attraction['name']}: {attraction['description']}\n"
                    
                    if other_attractions and len(must_visit) < 5:  # Show others if we have space
                        result += "\nOther Notable Attractions:\n"
                        for attraction in other_attractions[:3]:  # Limit to 3 additional
                            result += f"• {attraction['name']}: {attraction['description']}\n"
                
                result += f"\n**Best Time to Visit:** {city_data['best_time_to_visit']}"
                result += f"\n**Average Temperature:** {city_data['average_temperature']}"
                results.append(result)
        
        # If no specific city found, provide general overview
        if not results and any(word in query for word in ['cities', 'emirates', 'overview']):
            result = "**UAE Emirates Overview:**\n"
            for city_name, city_data in cities.items():
                result += f"• **{city_name}:** {city_data['description']}\n"
            results.append(result)
        
        return results
    
    def _search_cultural_tips(self, query: str) -> List[str]:
        """Search for cultural tips and etiquette"""
        cultural_tips = self.knowledge_base.get('cultural_tips', [])
        
        if not cultural_tips:
            return []
        
        # Filter tips based on query
        relevant_tips = []
        for tip in cultural_tips:
            if any(keyword in query for keyword in [tip['category'].lower(), 'all', 'general']):
                relevant_tips.append(tip)
        
        if not relevant_tips:
            relevant_tips = cultural_tips  # Return all if no specific match
        
        result = "**Cultural Tips for Visiting UAE:**\n"
        for tip in relevant_tips:
            result += f"• **{tip['category']}:** {tip['tip']}\n"
        
        return [result]
    
    def _search_activities(self, query: str) -> List[str]:
        """Search for activities and things to do"""
        activities = self.knowledge_base.get('activities', {})
        results = []
        
        for category in ['adventure', 'culture', 'luxury', 'family']:
            if category in query or 'all' in query or 'activities' in query:
                if category in activities:
                    result = f"**{category.title()} Activities:**\n"
                    for activity in activities[category]:
                        result += f"• {activity}\n"
                    results.append(result)
        
        return results
    
    def _search_transportation(self, query: str) -> List[str]:
        """Search for transportation information"""
        transportation = self.knowledge_base.get('transportation', {})
        results = []
        
        # Check for specific city transport
        for city in ['dubai', 'abu_dhabi']:
            if city in query and city in transportation:
                result = f"**Transportation in {city.replace('_', ' ').title()}:**\n"
                for transport_type, info in transportation[city].items():
                    result += f"• **{transport_type.replace('_', ' ').title()}:** {info}\n"
                results.append(result)
        
        # General transportation info
        if 'general' in query or not results:
            if 'general' in transportation:
                result = "**General Transportation Information:**\n"
                for transport_type, info in transportation['general'].items():
                    result += f"• **{transport_type.replace('_', ' ').title()}:** {info}\n"
                results.append(result)
        
        return results
    
    def _search_food(self, query: str) -> List[str]:
        """Search for food and dining information"""
        food_info = self.knowledge_base.get('food', {})
        results = []
        
        if 'traditional' in query and 'traditional_dishes' in food_info:
            result = "**Traditional UAE Dishes:**\n"
            for dish in food_info['traditional_dishes']:
                result += f"• **{dish['name']}:** {dish['description']}\n"
            results.append(result)
        
        if 'international' in query and 'popular_international' in food_info:
            result = "**Popular International Cuisines:**\n"
            for cuisine in food_info['popular_international']:
                result += f"• {cuisine}\n"
            results.append(result)
        
        if 'etiquette' in query and 'dining_etiquette' in food_info:
            result = "**Dining Etiquette:**\n"
            for rule in food_info['dining_etiquette']:
                result += f"• {rule}\n"
            results.append(result)
        
        # If no specific category, show traditional dishes
        if not results and 'traditional_dishes' in food_info:
            result = "**Traditional UAE Dishes:**\n"
            for dish in food_info['traditional_dishes'][:5]:  # Limit to 5
                result += f"• **{dish['name']}:** {dish['description']}\n"
            results.append(result)
        
        return results
    
    def _search_weather(self, query: str) -> List[str]:
        """Search for weather information"""
        weather_info = self.knowledge_base.get('weather', {})
        
        if 'seasons' in weather_info:
            result = "**UAE Weather by Season:**\n"
            for season, info in weather_info['seasons'].items():
                result += f"• **{season.title()} ({info['months']}):** {info['temperature']}, {info['description']}\n"
            return [result]
        
        return []

    async def _arun(self, query: str) -> str:
        """Async version of the tool"""
        return self._run(query)


class PrayerTimeTool(BaseTool):
    """Tool for getting prayer times in UAE cities"""
    
    name = "prayer_times"
    description = """Get Islamic prayer times for UAE cities. 
    Input should be in format: 'city_name' or 'city_name,date' (date in YYYY-MM-DD format).
    Example: 'Dubai' or 'Dubai,2024-03-15'
    
    Available cities: Dubai, Abu Dhabi, Sharjah, Ajman, Ras Al Khaimah, Fujairah, Umm Al Quwain"""
    
    def __init__(self):
        super().__init__()
        # Static prayer times for UAE cities (approximate times, vary by season)
        self.static_prayer_times = {
            'dubai': {
                'fajr': '05:30',
                'dhuhr': '12:15', 
                'asr': '15:45',
                'maghrib': '18:30',
                'isha': '20:00'
            },
            'abu dhabi': {
                'fajr': '05:35',
                'dhuhr': '12:20',
                'asr': '15:50', 
                'maghrib': '18:35',
                'isha': '20:05'
            },
            'sharjah': {
                'fajr': '05:28',
                'dhuhr': '12:12',
                'asr': '15:42',
                'maghrib': '18:27',
                'isha': '19:57'
            },
            'ajman': {
                'fajr': '05:29',
                'dhuhr': '12:13',
                'asr': '15:43',
                'maghrib': '18:28',
                'isha': '19:58'
            },
            'ras al khaimah': {
                'fajr': '05:25',
                'dhuhr': '12:10',
                'asr': '15:40',
                'maghrib': '18:25',
                'isha': '19:55'
            },
            'fujairah': {
                'fajr': '05:20',
                'dhuhr': '12:05',
                'asr': '15:35',
                'maghrib': '18:20',
                'isha': '19:50'
            },
            'umm al quwain': {
                'fajr': '05:27',
                'dhuhr': '12:12',
                'asr': '15:42',
                'maghrib': '18:27',
                'isha': '19:57'
            }
        }
    
    def _run(self, query: str) -> str:
        """Get prayer times for the specified city and date"""
        parts = query.split(',')
        city = parts[0].strip().lower()
        date_str = parts[1].strip() if len(parts) > 1 else datetime.now().strftime('%Y-%m-%d')
        
        # Check if API is enabled
        api_enabled = os.getenv('ALADHAN_API_ENABLED', 'false').lower() == 'true'
        
        if api_enabled:
            return self._get_api_prayer_times(city, date_str)
        else:
            return self._get_static_prayer_times(city, date_str)
    
    def _get_static_prayer_times(self, city: str, date_str: str) -> str:
        """Get prayer times from static data"""
        if city not in self.static_prayer_times:
            available_cities = ', '.join(self.static_prayer_times.keys()).title()
            return f"Prayer times not available for '{city}'. Available cities: {available_cities}"
        
        times = self.static_prayer_times[city]
        
        result = f"**Prayer Times for {city.title()} ({date_str}):**\n"
        result += f"• **Fajr:** {times['fajr']}\n"
        result += f"• **Dhuhr:** {times['dhuhr']}\n"  
        result += f"• **Asr:** {times['asr']}\n"
        result += f"• **Maghrib:** {times['maghrib']}\n"
        result += f"• **Isha:** {times['isha']}\n"
        result += "\n*Note: Times are approximate and may vary by season. For precise times, consult local Islamic centers.*"
        
        return result
    
    def _get_api_prayer_times(self, city: str, date_str: str) -> str:
        """Get prayer times from Aladhan API"""
        try:
            # Map city names to coordinates (approximate)
            city_coords = {
                'dubai': (25.2048, 55.2708),
                'abu dhabi': (24.4539, 54.3773),
                'sharjah': (25.3463, 55.4209),
                'ajman': (25.4052, 55.5136),
                'ras al khaimah': (25.7896, 55.9429),
                'fujairah': (25.1164, 56.3265),
                'umm al quwain': (25.5641, 55.5552)
            }
            
            if city not in city_coords:
                return self._get_static_prayer_times(city, date_str)
            
            lat, lng = city_coords[city]
            
            url = f"http://api.aladhan.com/v1/timings/{date_str}"
            params = {
                'latitude': lat,
                'longitude': lng,
                'method': 2  # Islamic Society of North America (ISNA) method
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                timings = data['data']['timings']
                
                result = f"**Prayer Times for {city.title()} ({date_str}):**\n"
                result += f"• **Fajr:** {timings['Fajr']}\n"
                result += f"• **Dhuhr:** {timings['Dhuhr']}\n"
                result += f"• **Asr:** {timings['Asr']}\n"
                result += f"• **Maghrib:** {timings['Maghrib']}\n"
                result += f"• **Isha:** {timings['Isha']}\n"
                
                return result
            else:
                return self._get_static_prayer_times(city, date_str)
                
        except Exception as e:
            print(f"Error fetching prayer times from API: {e}")
            return self._get_static_prayer_times(city, date_str)
    
    async def _arun(self, query: str) -> str:
        """Async version of the tool"""
        return self._run(query)


class TripBudgetPlanner(BaseTool):
    """Tool for calculating trip budget estimates"""
    
    name = "trip_budget_planner"
    description = """Calculate estimated budget for UAE trips based on city, duration, and travel style.
    Input format: 'city,days,style' where:
    - city: UAE city name (Dubai, Abu Dhabi, etc.)
    - days: number of days (integer)
    - style: budget, standard, or luxury
    
    Example: 'Dubai,5,standard' or 'Abu Dhabi,3,luxury'"""
    
    def __init__(self):
        super().__init__()
        # Base costs per day in AED
        self.base_costs = {
            'budget': 150,
            'standard': 400, 
            'luxury': 1000
        }
        
        # City multipliers (Dubai and Abu Dhabi are more expensive)
        self.city_multipliers = {
            'dubai': 1.2,
            'abu dhabi': 1.1,
            'sharjah': 0.9,
            'ajman': 0.8,
            'ras al khaimah': 0.85,
            'fujairah': 0.8,
            'umm al quwain': 0.75
        }
    
    def _run(self, query: str) -> str:
        """Calculate trip budget estimate"""
        try:
            parts = [part.strip().lower() for part in query.split(',')]
            
            if len(parts) != 3:
                return "Please provide input in format: 'city,days,style'. Example: 'Dubai,5,standard'"
            
            city, days_str, style = parts
            
            # Validate inputs
            try:
                days = int(days_str)
                if days <= 0:
                    return "Number of days must be a positive integer."
            except ValueError:
                return "Number of days must be a valid integer."
            
            if style not in self.base_costs:
                return f"Travel style must be one of: {', '.join(self.base_costs.keys())}"
            
            if city not in self.city_multipliers:
                available_cities = ', '.join([c.title() for c in self.city_multipliers.keys()])
                return f"City not recognized. Available cities: {available_cities}"
            
            # Calculate budget
            base_cost_per_day = self.base_costs[style]
            city_multiplier = self.city_multipliers[city]
            cost_per_day = base_cost_per_day * city_multiplier
            total_cost = cost_per_day * days
            
            # Create detailed breakdown
            result = f"**Trip Budget Estimate for {city.title()}**\n"
            result += f"**Duration:** {days} days\n"
            result += f"**Travel Style:** {style.title()}\n\n"
            
            result += f"**Daily Cost Breakdown:**\n"
            result += f"• Base cost ({style}): {base_cost_per_day} AED/day\n"
            result += f"• City adjustment ({city.title()}): {city_multiplier}x\n"
            result += f"• Daily total: {cost_per_day:.0f} AED/day\n\n"
            
            result += f"**Total Trip Cost: {total_cost:.0f} AED**\n"
            result += f"*Approximately ${total_cost/3.67:.0f} USD*\n\n"
            
            # Add style-specific inclusions
            result += self._get_style_inclusions(style)
            
            result += "\n*Note: This is an estimate. Actual costs may vary based on specific choices, season, and exchange rates.*"
            
            return result
            
        except Exception as e:
            return f"Error calculating budget: {str(e)}. Please use format: 'city,days,style'"
    
    def _get_style_inclusions(self, style: str) -> str:
        """Get what's included in each travel style"""
        inclusions = {
            'budget': """**Budget Travel Includes:**
• Basic accommodation (hostels, budget hotels)
• Local transportation (metro, bus)
• Street food and casual dining
• Free attractions and beaches
• Basic shopping""",
            
            'standard': """**Standard Travel Includes:**
• Mid-range hotels (3-4 star)
• Mix of public transport and taxis
• Restaurant dining with some fine dining
• Major paid attractions and activities
• Moderate shopping and souvenirs""",
            
            'luxury': """**Luxury Travel Includes:**
• 5-star hotels and resorts
• Private transportation and chauffeurs
• Fine dining and exclusive restaurants
• Premium attractions and VIP experiences
• High-end shopping and spa treatments"""
        }
        
        return inclusions.get(style, "")
    
    async def _arun(self, query: str) -> str:
        """Async version of the tool"""
        return self._run(query)


# Export all tools
__all__ = ['UAEKnowledgeSearchTool', 'PrayerTimeTool', 'TripBudgetPlanner']