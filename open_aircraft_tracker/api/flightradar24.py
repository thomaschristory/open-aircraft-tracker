"""
FlightRadar24 API client implementation.
Note: This uses the unofficial API endpoints as FlightRadar24 doesn't have a fully public API.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import math

import aiohttp
from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI


class FlightRadar24API(AircraftTrackerAPI):
    """FlightRadar24 API client."""
    
    BASE_URL = "https://data-live.flightradar24.com/zones/fcgi/feed.js"
    AIRCRAFT_URL = "https://data-live.flightradar24.com/clickhandler/"
    
    def __init__(self, api_key: str):
        """
        Initialize the FlightRadar24 API client.
        
        Args:
            api_key: FlightRadar24 API key
        """
        self.api_key = api_key
        
        if not api_key:
            raise ValueError("FlightRadar24 API key is required")
    
    async def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make a request to the FlightRadar24 API.
        
        Args:
            url: API URL
            params: Query parameters
            
        Returns:
            JSON response as a dictionary
        """
        if params is None:
            params = {}
        
        # Add API key to parameters
        params["apiKey"] = self.api_key
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
    
    def _parse_aircraft(self, flight_data: Dict) -> Aircraft:
        """
        Parse flight data from the FlightRadar24 API into an Aircraft object.
        
        Args:
            flight_data: Flight data from the FlightRadar24 API
            
        Returns:
            Aircraft object
        """
        # For detailed aircraft data (from clickhandler endpoint)
        if "aircraft" in flight_data:
            aircraft_data = flight_data["aircraft"]
            
            # Extract ICAO24 (hex identifier)
            icao24 = aircraft_data.get("hex", "").lower()
            
            # Extract other fields
            callsign = aircraft_data.get("identification", {}).get("callsign", "")
            origin_country = aircraft_data.get("airline", {}).get("country", "")
            latitude = aircraft_data.get("latitude")
            longitude = aircraft_data.get("longitude")
            altitude = aircraft_data.get("altitude", {}).get("meters")
            velocity = aircraft_data.get("speed", {}).get("kmh") / 3.6 if aircraft_data.get("speed", {}).get("kmh") else None  # Convert km/h to m/s
            heading = aircraft_data.get("heading")
            vertical_rate = aircraft_data.get("verticalSpeed", {}).get("ms")  # Already in m/s
            
            # Use timestamp or current time
            timestamp = aircraft_data.get("time", 0)
            last_update = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
        # For basic aircraft data (from feed.js endpoint)
        else:
            # FlightRadar24 feed.js returns an array with specific indices
            # [0]: ICAO24, [1]: Latitude, [2]: Longitude, [3]: Heading, [4]: Altitude (feet),
            # [5]: Ground speed (knots), [6]: Callsign, [7]: Aircraft code, [8]: Registration,
            # [9]: Timestamp, [10]: Origin airport IATA, [11]: Destination airport IATA,
            # [12]: Flight number, [13]: Vertical speed (feet/min), [14]: Squawk
            
            # Extract ICAO24 (hex identifier)
            icao24 = str(flight_data.get(0, "")).lower()
            
            # Extract other fields
            latitude = flight_data.get(1)
            longitude = flight_data.get(2)
            heading = flight_data.get(3)
            altitude = flight_data.get(4) * 0.3048 if flight_data.get(4) else None  # Convert feet to meters
            velocity = flight_data.get(5) * 0.514444 if flight_data.get(5) else None  # Convert knots to m/s
            callsign = flight_data.get(6, "")
            origin_country = None  # Not available in basic data
            vertical_rate = flight_data.get(13) * 0.00508 if flight_data.get(13) else None  # Convert feet/min to m/s
            
            # Use timestamp or current time
            timestamp = flight_data.get(9, 0)
            last_update = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
        return Aircraft(
            icao24=icao24,
            callsign=callsign,
            origin_country=origin_country,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            velocity=velocity,
            heading=heading,
            vertical_rate=vertical_rate,
            last_update=last_update
        )
    
    async def get_aircraft_in_radius(self, latitude: float, longitude: float, radius_km: float) -> List[Aircraft]:
        """
        Get all aircraft within a specified radius of a location.
        
        Args:
            latitude: WGS-84 latitude in decimal degrees
            longitude: WGS-84 longitude in decimal degrees
            radius_km: Radius in kilometers
            
        Returns:
            List of Aircraft objects within the specified radius
        """
        # Calculate bounding box for the search (FlightRadar24 requires a bounding box)
        # 1 degree of latitude is approximately 111 km
        # 1 degree of longitude varies with latitude, approximately 111 * cos(latitude) km
        lat_km = 111.0
        lon_km = 111.0 * math.cos(math.radians(latitude))
        
        lat_delta = radius_km / lat_km
        lon_delta = radius_km / lon_km
        
        # Create bounding box
        bounds = {
            "lomin": longitude - lon_delta,
            "lomax": longitude + lon_delta,
            "lamin": latitude - lat_delta,
            "lamax": latitude + lat_delta
        }
        
        # Query parameters for the search
        params = {
            "bounds": f"{bounds['lamin']},{bounds['lamax']},{bounds['lomin']},{bounds['lomax']}",
            "faa": 1,
            "satellite": 1,
            "mlat": 1,
            "flarm": 1,
            "adsb": 1,
            "gnd": 1,
            "air": 1,
            "vehicles": 1,
            "estimated": 1,
            "maxage": 14400,  # 4 hours
            "gliders": 1,
            "stats": 1
        }
        
        # Make the request to the feed.js endpoint
        response = await self._make_request(self.BASE_URL, params)
        
        # Parse the response
        aircraft_list = []
        if response:
            center = (latitude, longitude)
            
            # Filter out metadata fields (they start with underscore)
            for key, value in response.items():
                if not key.startswith("_") and isinstance(value, (list, dict)):
                    # Parse flight data
                    aircraft = self._parse_aircraft(value)
                    
                    # Skip aircraft without position data
                    if aircraft.latitude is None or aircraft.longitude is None:
                        continue
                    
                    # Calculate actual distance
                    aircraft_pos = (aircraft.latitude, aircraft.longitude)
                    distance = geodesic(center, aircraft_pos).kilometers
                    
                    # Only include aircraft within the specified radius
                    if distance <= radius_km:
                        aircraft_list.append(aircraft)
        
        return aircraft_list
    
    async def get_aircraft_by_callsign(self, callsign: str) -> Optional[Aircraft]:
        """
        Get information about a specific aircraft by callsign.
        
        Args:
            callsign: The callsign of the aircraft
            
        Returns:
            Aircraft object if found, None otherwise
        """
        # Normalize callsign
        normalized_callsign = callsign.strip().upper()
        
        # First, we need to search for the aircraft to get its ID
        # Query parameters for the search (use a large bounding box to find the aircraft)
        params = {
            "bounds": "-90,90,-180,180",  # Whole world
            "faa": 1,
            "satellite": 1,
            "mlat": 1,
            "flarm": 1,
            "adsb": 1,
            "gnd": 1,
            "air": 1,
            "vehicles": 1,
            "estimated": 1,
            "maxage": 14400,  # 4 hours
            "gliders": 1,
            "stats": 1
        }
        
        # Make the request to the feed.js endpoint
        response = await self._make_request(self.BASE_URL, params)
        
        # Find the aircraft with the matching callsign
        aircraft_id = None
        if response:
            for key, value in response.items():
                if not key.startswith("_") and isinstance(value, (list, dict)):
                    if isinstance(value, list) and len(value) > 6 and value[6] == normalized_callsign:
                        aircraft_id = key
                        break
        
        # If we found the aircraft, get detailed information
        if aircraft_id:
            # Make the request to the clickhandler endpoint
            aircraft_url = f"{self.AIRCRAFT_URL}?id={aircraft_id}"
            detailed_response = await self._make_request(aircraft_url, {})
            
            # Parse the detailed response
            if detailed_response:
                return self._parse_aircraft(detailed_response)
        
        return None
