"""
OpenSky Network API client implementation.
Documentation: https://openskynetwork.github.io/opensky-api/rest.html
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI


class OpenSkyAPI(AircraftTrackerAPI):
    """OpenSky Network API client."""
    
    BASE_URL = "https://opensky-network.org/api"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the OpenSky API client.
        
        Args:
            username: Optional OpenSky Network username for authenticated requests
            password: Optional OpenSky Network password for authenticated requests
        """
        self.username = username
        self.password = password
        self.auth = None
        if username and password:
            self.auth = aiohttp.BasicAuth(username, password)
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make a request to the OpenSky Network API.
        
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
    
    def _parse_state_vector(self, state_vector: List, time_position: int) -> Aircraft:
        """
        Parse a state vector from the OpenSky API into an Aircraft object.
        
        Args:
            state_vector: State vector from the OpenSky API
            time_position: Time of the position in seconds since epoch
            
        Returns:
            Aircraft object
        """
        return Aircraft(
            icao24=state_vector[0],
            callsign=state_vector[1].strip() if state_vector[1] else None,
            origin_country=state_vector[2],
            latitude=state_vector[6],
            longitude=state_vector[5],
            altitude=state_vector[7],
            velocity=state_vector[9],
            heading=state_vector[10],
            vertical_rate=state_vector[11],
            last_update=datetime.fromtimestamp(time_position or 0)
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
        # Calculate bounding box for the query
        # This is an approximation to reduce the number of results
        # We'll filter more precisely using the actual distance later
        lat_km = 110.574  # km per degree of latitude
        lon_km = 111.320 * abs(float(latitude))  # km per degree of longitude
        
        lat_diff = radius_km / lat_km
        lon_diff = radius_km / lon_km
        
        # Query parameters for the bounding box
        params = {
            "lamin": latitude - lat_diff,
            "lamax": latitude + lat_diff,
            "lomin": longitude - lon_diff,
            "lomax": longitude + lon_diff
        }
        
        # Make the request
        response = await self._make_request("states/all", params)
        
        # Parse the response
        aircraft_list = []
        if response and "states" in response and response["states"]:
            center = (latitude, longitude)
            time_position = response.get("time", 0)
            
            for state in response["states"]:
                aircraft = self._parse_state_vector(state, time_position)
                
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
        # Normalize callsign (OpenSky stores callsigns with padding)
        normalized_callsign = callsign.upper().ljust(8)
        
        # Get all states (no filtering by callsign is available in the API)
        response = await self._make_request("states/all")
        
        if response and "states" in response and response["states"]:
            time_position = response.get("time", 0)
            
            for state in response["states"]:
                if state[1] and state[1].strip() == callsign.strip():
                    return self._parse_state_vector(state, time_position)
        
        return None
