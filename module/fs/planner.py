import requests
import json
from typing import Optional, Dict, Any

# Scraper to fetch flight plan data from Microsoft Flight Simulator's flight planner

BASE_URL = "https://planner.flightsimulator.com/share"

def fetch_flight_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches flight plan data from Microsoft Flight Simulator's flight planner.
    
    Args:
        plan_id: The unique identifier of the flight plan to fetch
        
    Returns:
        Flight plan data as a dictionary, or None if the request fails
    """
    print(f"Fetching flight plan: {plan_id}")
    url = f"{BASE_URL}/{plan_id}"
    print(f"Fetching flight plan from {url}")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Flight plan retrieved successfully.")
            return process_flight_plan(response.text)
        else:
            print(f"Error: Status code {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching flight plan: {e}")
        return None

def process_flight_plan(data: str) -> Optional[Dict[str, Any]]:
    """
    Processes the flight plan response data.
    
    Args:
        data: Raw response data from the flight planner
        
    Returns:
        Parsed flight plan data, or None if parsing fails
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Error parsing flight plan data: {e}")
        return None

# Example usage
flight_plan = fetch_flight_plan("13882360-7e5b-485f-acc0-d0e38c301216")
if flight_plan:
    print(flight_plan)
