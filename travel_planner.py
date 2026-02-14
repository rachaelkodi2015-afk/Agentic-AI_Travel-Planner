import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GOOGLE_MAPS_API_KEY:
    raise ValueError("Please set GOOGLE_MAPS_API_KEY in your .env file")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env file")

# Imports for LangChain 1.2.7
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def get_weather_forecast(location: str) -> str:
    """Get weather forecast for a specific location."""
    try:
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geocode_params = {"address": location, "key": GOOGLE_MAPS_API_KEY}
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_data = geocode_response.json()
        
        if geocode_data.get("status") != "OK":
            return f"Error: Could not find location '{location}'"
        
        lat = geocode_data["results"][0]["geometry"]["location"]["lat"]
        lng = geocode_data["results"][0]["geometry"]["location"]["lng"]
        
        weather_url = "https://weather.googleapis.com/v1/currentConditions:lookup"
        weather_headers = {"X-Goog-Api-Key": GOOGLE_MAPS_API_KEY}
        weather_body = {"location": {"latitude": lat, "longitude": lng}}
        weather_response = requests.post(weather_url, headers=weather_headers, json=weather_body)
        
        if weather_response.status_code != 200:
            return f"Weather API error: HTTP {weather_response.status_code}"
        
        weather_data = weather_response.json()
        if "currentWeather" in weather_data:
            weather = weather_data["currentWeather"]
            return str({
                "location": location,
                "temperature_celsius": weather.get("temperature", {}).get("celsius"),
                "temperature_fahrenheit": weather.get("temperature", {}).get("fahrenheit"),
                "condition": weather.get("weatherCondition"),
                "humidity": weather.get("humidity")
            })
        return f"Weather data not available for {location}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_air_quality(location: str) -> str:
    """Get air quality information for a location."""
    try:
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geocode_params = {"address": location, "key": GOOGLE_MAPS_API_KEY}
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_data = geocode_response.json()
        
        if geocode_data.get("status") != "OK":
            return f"Error: Could not find location '{location}'"
        
        lat = geocode_data["results"][0]["geometry"]["location"]["lat"]
        lng = geocode_data["results"][0]["geometry"]["location"]["lng"]
        
        air_quality_url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
        air_quality_headers = {"X-Goog-Api-Key": GOOGLE_MAPS_API_KEY}
        air_quality_body = {"location": {"latitude": lat, "longitude": lng}}
        air_quality_response = requests.post(air_quality_url, headers=air_quality_headers, json=air_quality_body)
        
        if air_quality_response.status_code != 200:
            return f"Air Quality API error: HTTP {air_quality_response.status_code}"
        
        air_quality_data = air_quality_response.json()
        result = {"location": location, "current_conditions": {}}
        
        if "indexes" in air_quality_data:
            for index in air_quality_data["indexes"]:
                if index.get("code") == "uaqi":
                    result["current_conditions"] = {
                        "aqi": index.get("aqi"),
                        "category": index.get("category"),
                        "dominant_pollutant": index.get("dominantPollutant")
                    }
                    break
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def find_tourist_attractions(city: str, num_results: int = 5) -> str:
    """Find tourist attractions in a city."""
    try:
        text_search_url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.types"
        }
        body = {"textQuery": f"tourist attractions in {city}"}
        response = requests.post(text_search_url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        
        attractions = []
        if "places" in data:
            for place in data["places"][:num_results]:
                attractions.append({
                    "name": place.get("displayName", {}).get("text"),
                    "address": place.get("formattedAddress"),
                    "types": place.get("types", [])
                })
        return str({"city": city, "attractions": attractions})
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    print("=" * 80)
    print("Michael's Retirement Travel Planner")
    print("Using LangChain v1.2+ with built-in agent functions")
    print("=" * 80 + "\n")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)
    tools = [get_weather_forecast, get_air_quality, find_tourist_attractions]
    
    # Create agent with LangGraph
    agent = create_react_agent(llm, tools)
    
    print("Example 1: Toronto → Chicago")
    print("-" * 80)
    
    # Include system instructions in the user message
    example_input = """You are a helpful travel planning assistant for Michael Zhang, a retiree who wants to travel around the world.

For each city, get weather forecast, air quality information, suggest tourist attractions, recommend clothing based on weather, and recommend masks if AQI > 100.

Please create a travel plan for the following cities:

City1: Toronto 2025-01-31
CN Tower; 290 Bremner Blvd, Toronto, ON M5V 3L9; 8am-9am
Royal Ontario Museum; 100 Queens Park, Toronto, ON M5S 2C6; 10am-11am

City2: Chicago 2025-02-01
The Art Institute of Chicago; 111 S Michigan Ave, Chicago, IL 60603, United States; 9am-11am
Griffin Museum of Science and Industry; 5700 S DuSable Lake Shore Dr, Chicago, IL 60637, United States; 12pm-1pm
"""
    
    print(example_input)
    print("\nGenerating travel plan...\n")
    
    try:
        for chunk in agent.stream({"messages": [("human", example_input)]}, stream_mode="values"):
            if "messages" in chunk:
                chunk["messages"][-1].pretty_print()
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Interactive Mode - Test with any cities!")
    print("Type 'quit' to exit")
    print("=" * 80 + "\n")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using Michael's Travel Planner!")
            break
        if not user_input:
            continue
        
        try:
            # Add context to user input
            full_input = f"""You are a travel planning assistant. For each location, get weather, air quality, and attractions. Recommend clothing and masks (if AQI > 100).

User request: {user_input}"""
            
            for chunk in agent.stream({"messages": [("human", full_input)]}, stream_mode="values"):
                if "messages" in chunk:
                    chunk["messages"][-1].pretty_print()
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()