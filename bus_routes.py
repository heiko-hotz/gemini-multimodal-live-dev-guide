import requests
import json
from typing import Optional, List, Dict, Tuple
from datetime import datetime

def get_bus_routes(bus_number: str) -> Optional[dict]:
    """
    Fetch route information for a given bus number from the TfL API.
    """
    base_url = "https://api.tfl.gov.uk/Line"
    endpoint = f"{base_url}/{bus_number}/Route"
    
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def get_line_stops(bus_number: str) -> Optional[list]:
    """
    Fetch all stops for a given bus number from the TfL API.
    """
    base_url = "https://api.tfl.gov.uk/Line"
    endpoint = f"{base_url}/{bus_number}/StopPoints"
    
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching stops: {e}")
        return None

def search_stop_point(query: str) -> Optional[List[Dict]]:
    """
    Search for a stop point by name.
    """
    base_url = "https://api.tfl.gov.uk/StopPoint/Search"
    endpoint = f"{base_url}/{query}"
    
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json().get('matches', [])
    except requests.RequestException as e:
        print(f"Error searching for stop: {e}")
        return None

def select_stop_from_matches(matches: List[Dict], bus_number: str) -> Optional[Tuple[str, str]]:
    """
    Let user select a stop from multiple matches.
    Returns a tuple of (stop_id, stop_name) or None if no selection made.
    """
    if not matches:
        print("No matching stops found.")
        return None
    
    # Filter stops that serve our bus line
    valid_stops = []
    for match in matches:
        lines = match.get('lines', [])
        if any(line.get('id') == bus_number for line in lines):
            valid_stops.append(match)
    
    if not valid_stops:
        print(f"None of the matching stops serve bus {bus_number}")
        return None
    
    print("\nMatching stops that serve this bus line:")
    for i, stop in enumerate(valid_stops, 1):
        print(f"{i}. {stop.get('name')} ({stop.get('id')})")
        if stop.get('stopType'):
            print(f"   Type: {stop.get('stopType')}")
        if stop.get('zone'):
            print(f"   Zone: {stop.get('zone')}")
    
    while True:
        try:
            choice = input("\nSelect a stop number (or press Enter to cancel): ").strip()
            if not choice:
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(valid_stops):
                selected_stop = valid_stops[index]
                return (selected_stop.get('id'), selected_stop.get('name'))
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def get_arrival_times(bus_number: str, stop_id: str) -> Optional[list]:
    """
    Fetch arrival predictions for a specific bus at a specific stop.
    """
    base_url = "https://api.tfl.gov.uk/Line"
    endpoint = f"{base_url}/{bus_number}/Arrivals/{stop_id}"
    
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching arrival times: {e}")
        return None

def display_arrival_times(arrivals_data: list, stop_name: str) -> None:
    """
    Display arrival predictions in a readable format.
    """
    if not arrivals_data:
        print(f"No arrival information available for {stop_name}.")
        return

    print(f"\n=== Arrival Predictions for {stop_name} ===")
    
    # Sort arrivals by time to station
    sorted_arrivals = sorted(arrivals_data, key=lambda x: x.get('timeToStation', 0))
    
    for arrival in sorted_arrivals:
        # Convert seconds to minutes
        mins_to_arrival = arrival.get('timeToStation', 0) // 60
        
        print(f"\nDestination: {arrival.get('destinationName', 'N/A')}")
        print(f"Platform/Stop: {arrival.get('platformName', 'N/A')}")
        print(f"Arriving in: {mins_to_arrival} minutes")
        
        # Show expected arrival time
        expected_arrival = arrival.get('expectedArrival')
        if expected_arrival:
            arrival_time = datetime.fromisoformat(expected_arrival.replace('Z', '+00:00'))
            print(f"Expected at: {arrival_time.strftime('%H:%M:%S')}")
        
        # Show current location if available
        current_location = arrival.get('currentLocation')
        if current_location:
            print(f"Current Location: {current_location}")

def display_stops_info(stops_data: list, show_ids: bool = False) -> None:
    """
    Display all stops information in a readable format.
    """
    if not stops_data:
        print("No stops data available.")
        return

    print("\n=== Stops Information ===")
    print(f"Total stops: {len(stops_data)}")
    
    for i, stop in enumerate(stops_data, 1):
        print(f"\nStop {i}:")
        print(f"Name: {stop.get('commonName', 'N/A')}")
        if show_ids:
            print(f"Stop ID: {stop.get('id', 'N/A')}")
        print(f"Stop Letter: {stop.get('stopLetter', 'N/A')}")
        print(f"Zone: {stop.get('zone', 'N/A')}")
        
        # Show accessibility information if available
        accessibility = stop.get('accessibilitySummary')
        if accessibility:
            print(f"Accessibility: {accessibility}")
        
        # Show modes available at this stop
        modes = stop.get('modes', [])
        if modes:
            print(f"Available modes: {', '.join(modes)}")

def display_route_info(route_data: dict) -> None:
    """
    Display route information in a readable format.
    """
    if not route_data:
        print("No route data available.")
        return

    print("\n=== Route Information ===")
    
    # Display basic line information
    print(f"Line: {route_data.get('name', 'N/A')}")
    print(f"Mode: {route_data.get('modeName', 'N/A')}")
    
    # Display route sections
    route_sections = route_data.get('routeSections', [])
    if route_sections:
        print("\nRoute Sections:")
        for section in route_sections:
            print(f"\nDirection: {section.get('direction', 'N/A')}")
            print(f"From: {section.get('originationName', 'N/A')}")
            print(f"To: {section.get('destinationName', 'N/A')}")
            
            # Display service type and validity
            print(f"Service Type: {section.get('serviceType', 'N/A')}")
            
            valid_from = section.get('validFrom')
            valid_to = section.get('validTo')
            if valid_from:
                print(f"Valid From: {datetime.fromisoformat(valid_from.replace('Z', '+00:00')).strftime('%Y-%m-%d')}")
            if valid_to:
                print(f"Valid To: {datetime.fromisoformat(valid_to.replace('Z', '+00:00')).strftime('%Y-%m-%d')}")
    else:
        print("\nNo route sections available.")

def main():
    """
    Main function to run the program.
    """
    print("TfL Bus Route Information")
    print("------------------------")
    
    while True:
        print("\nOptions:")
        print("1. View route information")
        print("2. View all stops on route")
        print("3. View arrival times for a stop")
        print("q. Quit")
        
        choice = input("\nEnter your choice: ").strip().lower()
        
        if choice == 'q':
            print("Goodbye!")
            break
            
        if choice not in ['1', '2', '3']:
            print("Please enter a valid option (1, 2, 3, or q).")
            continue
            
        bus_number = input("Enter bus number: ").strip()
        if not bus_number:
            print("Please enter a valid bus number.")
            continue
            
        if choice == '1':
            print(f"\nFetching route information for bus {bus_number}...")
            route_data = get_bus_routes(bus_number)
            if route_data:
                display_route_info(route_data)
            else:
                print(f"Could not find route information for bus {bus_number}")
        
        elif choice == '2':
            print(f"\nFetching stops information for bus {bus_number}...")
            stops_data = get_line_stops(bus_number)
            if stops_data:
                # Show stop IDs when listing stops, as they'll be needed for arrival times
                display_stops_info(stops_data, show_ids=True)
            else:
                print(f"Could not find stops information for bus {bus_number}")
        
        else:  # choice == '3'
            stop_name = input("Enter stop name (e.g., 'Warren Street Station'): ").strip()
            if not stop_name:
                print("Please enter a valid stop name.")
                continue
            
            print(f"\nSearching for stops matching '{stop_name}'...")
            matches = search_stop_point(stop_name)
            
            if matches:
                result = select_stop_from_matches(matches, bus_number)
                if result:
                    stop_id, selected_stop_name = result
                    print(f"\nFetching arrival times for bus {bus_number} at {selected_stop_name}...")
                    arrivals_data = get_arrival_times(bus_number, stop_id)
                    if arrivals_data:
                        display_arrival_times(arrivals_data, selected_stop_name)
                    else:
                        print(f"Could not find arrival times for bus {bus_number} at {selected_stop_name}")
            else:
                print("No stops found matching your search.")

if __name__ == "__main__":
    main() 