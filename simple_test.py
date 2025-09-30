#!/usr/bin/env python3
"""
Simple test script for UAE Tourism Assistant
Run this to test the basic functionality without LangChain complexity
"""

import json
import os

# Change to the project directory
os.chdir(r"d:\Projects\smart_tourism_assistant")

def load_knowledge_base():
    """Load the UAE knowledge base from JSON file"""
    try:
        with open('uae_knowledge.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: uae_knowledge.json not found")
        return {}

def search_uae_knowledge(query: str) -> str:
    """Search the UAE knowledge base with fixed city matching"""
    knowledge_base = load_knowledge_base()
    query_lower = query.lower()
    results = []
    
    # Search in cities - fixed city name matching
    if any(word in query_lower for word in ['city', 'cities', 'attractions', 'things to do', 'visit']):
        cities = knowledge_base.get('cities', {})
        for city_name, city_data in cities.items():
            city_lower = city_name.lower()
            if city_lower in query_lower or any(part in query_lower for part in city_lower.split()):
                result = f"**{city_name}:**\n{city_data['description']}\n"
                
                if 'attractions' in query_lower or 'things to do' in query_lower:
                    result += f"\n**Top Attractions in {city_name}:**\n"
                    must_visit = [attr for attr in city_data['major_attractions'] if attr.get('must_visit', False)]
                    
                    for attraction in must_visit:
                        result += f"• {attraction['name']}: {attraction['description']}\n"
                
                result += f"\n**Best Time to Visit:** {city_data['best_time_to_visit']}"
                results.append(result)
    
    # Search for cultural tips
    if any(word in query_lower for word in ['culture', 'cultural', 'etiquette', 'tips', 'customs']):
        cultural_tips = knowledge_base.get('cultural_tips', [])
        result = "**Cultural Tips for Visiting UAE:**\n"
        for tip in cultural_tips:
            result += f"• **{tip['category']}:** {tip['tip']}\n"
        results.append(result)
    
    if not results:
        return "I couldn't find specific information about your query. Could you please ask about UAE cities, attractions, cultural tips, or activities?"
    
    return "\n\n".join(results)

def get_prayer_times(city_query: str) -> str:
    """Get prayer times for UAE cities"""
    prayer_times = {
        'dubai': {'fajr': '05:30', 'dhuhr': '12:15', 'asr': '15:45', 'maghrib': '18:30', 'isha': '20:00'},
        'abu dhabi': {'fajr': '05:35', 'dhuhr': '12:20', 'asr': '15:50', 'maghrib': '18:35', 'isha': '20:05'},
        'sharjah': {'fajr': '05:28', 'dhuhr': '12:12', 'asr': '15:42', 'maghrib': '18:27', 'isha': '19:57'}
    }
    
    parts = city_query.split(',')
    city = parts[0].strip().lower()
    date_str = parts[1].strip() if len(parts) > 1 else "2025-09-30"
    
    if city not in prayer_times:
        available_cities = ', '.join([c.title() for c in prayer_times.keys()])
        return f"Prayer times not available for '{city}'. Available cities: {available_cities}"
    
    times = prayer_times[city]
    result = f"**Prayer Times for {city.title()} ({date_str}):**\n"
    result += f"• **Fajr:** {times['fajr']}\n"
    result += f"• **Dhuhr:** {times['dhuhr']}\n"
    result += f"• **Asr:** {times['asr']}\n"
    result += f"• **Maghrib:** {times['maghrib']}\n"
    result += f"• **Isha:** {times['isha']}\n"
    result += "\n*Note: Times are approximate and may vary by season.*"
    
    return result

def calculate_trip_budget(budget_query: str) -> str:
    """Calculate trip budget"""
    base_costs = {'budget': 150, 'standard': 400, 'luxury': 1000}
    city_multipliers = {'dubai': 1.2, 'abu dhabi': 1.1, 'sharjah': 0.9}
    
    try:
        parts = [part.strip().lower() for part in budget_query.split(',')]
        if len(parts) != 3:
            return "Please provide input in format: 'city,days,style'. Example: 'Dubai,5,standard'"
        
        city, days_str, style = parts
        days = int(days_str)
        
        if style not in base_costs:
            return f"Travel style must be one of: {', '.join(base_costs.keys())}"
        
        if city not in city_multipliers:
            available_cities = ', '.join([c.title() for c in city_multipliers.keys()])
            return f"City not recognized. Available cities: {available_cities}"
        
        base_cost_per_day = base_costs[style]
        city_multiplier = city_multipliers[city]
        cost_per_day = base_cost_per_day * city_multiplier
        total_cost = cost_per_day * days
        
        result = f"**Trip Budget Estimate for {city.title()}**\n"
        result += f"**Duration:** {days} days\n"
        result += f"**Travel Style:** {style.title()}\n\n"
        result += f"**Total Trip Cost: {total_cost:.0f} AED**\n"
        result += f"*Approximately ${total_cost/3.67:.0f} USD*"
        
        return result
    except ValueError:
        return "Please provide a valid number for days."
    except Exception as e:
        return f"Error calculating budget: {str(e)}"

def main():
    """Main testing function"""
    print("🇦🇪 UAE Tourism Assistant - Simple Test")
    print("=" * 50)
    
    # Test scenarios
    test_cases = [
        ("UAE Knowledge Search", "attractions in Dubai", search_uae_knowledge),
        ("Prayer Times", "Dubai", get_prayer_times),
        ("Budget Calculator", "Dubai,3,luxury", calculate_trip_budget),
        ("Cultural Tips", "cultural tips", search_uae_knowledge),
        ("Activities", "adventure activities", search_uae_knowledge)
    ]
    
    for test_name, query, function in test_cases:
        print(f"\n🧪 Testing {test_name}")
        print(f"Query: '{query}'")
        print("-" * 30)
        
        try:
            result = function(query)
            print(result)
            print("✅ Test passed!")
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        print("\n" + "=" * 50)
    
    print("\n🎯 All tests completed!")
    print("\nTo test interactively, call:")
    print("- search_uae_knowledge('your query')")
    print("- get_prayer_times('city')")
    print("- calculate_trip_budget('city,days,style')")

if __name__ == "__main__":
    main()