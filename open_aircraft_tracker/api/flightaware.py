"""
FlightAware FlightXML API client implementation.
Documentation: https://flightaware.com/commercial/flightxml/documentation/
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI


class FlightAwareAPI(AircraftTrackerAPI):
    """FlightAware FlightXML API client."""
    
    BASE_URL = "https://flightxml.flightaware.com/json/FlightXML3"
    
    def __init__(self, username: str, api_key: str):
        """
        Initialize the FlightAware API client.
        
        Args:
            username: FlightAware username
            api_key: FlightAware API key
        """
        self.username = username
        self.api_key = api_key
        
        if not username or not api_key:
            raise ValueError("FlightAware API requires both username and API key")
        
        self.auth = aiohttp.BasicAuth(username, api_key)
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make a request to the FlightAware API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response as a dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, auth=self.auth) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
    
    def _parse_aircraft(self, flight_data: Dict) -> Aircraft:
        """
        Parse flight data from the FlightAware API into an Aircraft object.
        
        Args:
            flight_data: Flight data from the FlightAware API
            
        Returns:
            Aircraft object
        """
        # Extract data from the FlightAware response
        position = flight_data.get("last_position", {})
        flight_info = flight_data.get("flight", {})
        
        # Extract ICAO24 (hex identifier)
        icao24 = flight_data.get("hex_ident", "").lower()
        
        # Extract other fields
        callsign = flight_info.get("ident", "")
        origin_country = flight_info.get("origin", {}).get("country_name")
        latitude = position.get("latitude")
        longitude = position.get("longitude")
        altitude = position.get("altitude") * 0.3048 if position.get("altitude") else None  # Convert feet to meters
        velocity = position.get("groundspeed") * 0.514444 if position.get("groundspeed") else None  # Convert knots to m/s
        heading = position.get("heading")
        vertical_rate = position.get("vertical_speed") * 0.00508 if position.get("vertical_speed") else None  # Convert feet/min to m/s
        
        # Use timestamp from position data or current time
        timestamp = position.get("timestamp", 0)
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
        # Convert radius from km to nautical miles (FlightAware uses nm)
        radius_nm = radius_km * 0.539957
        
        # Query parameters for the search
        params = {
            "query": f"-latlong \"{latitude} {longitude} {radius_nm}\"",
            "howMany": 100,  # Maximum number of results
            "offset": 0
        }
        
        # Make the request to the SearchBirdseyeInFlight endpoint
        response = await self._make_request("SearchBirdseyeInFlight", params)
        
        # Parse the response
        aircraft_list = []
        if response and "SearchBirdseyeInFlightResult" in response:
            result = response["SearchBirdseyeInFlightResult"]
            if "aircraft" in result:
                center = (latitude, longitude)
                
                for flight in result["aircraft"]:
                    # Parse flight data
                    aircraft = self._parse_aircraft(flight)
                    
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
        
        # Query parameters for the search
        params = {
            "ident": normalized_callsign,
            "howMany": 1
        }
        
        # Make the request to the SearchBirdseyeInFlight endpoint
        response = await self._make_request("SearchBirdseyeInFlight", params)
        
        # Parse the response
        if response and "SearchBirdseyeInFlightResult" in response:
            result = response["SearchBirdseyeInFlightResult"]
            if "aircraft" in result and result["aircraft"]:
                return self._parse_aircraft(result["aircraft"][0])
        
        return None
