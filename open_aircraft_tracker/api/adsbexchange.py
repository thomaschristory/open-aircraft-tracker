"""
ADSBexchange API client implementation.
Documentation: https://www.adsbexchange.com/data/
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI


class ADSBexchangeAPI(AircraftTrackerAPI):
    """ADSBexchange API client."""
    
    BASE_URL = "https://adsbexchange-com1.p.rapidapi.com/v2"
    
    def __init__(self, api_key: str):
        """
        Initialize the ADSBexchange API client.
        
        Args:
            api_key: ADSBexchange API key
        """
        self.api_key = api_key
        
        if not api_key:
            raise ValueError("ADSBexchange API key is required")
        
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com"
        }
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make a request to the ADSBexchange API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response as a dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
    
    def _parse_aircraft(self, flight_data: Dict) -> Aircraft:
        """
        Parse flight data from the ADSBexchange API into an Aircraft object.
        
        Args:
            flight_data: Flight data from the ADSBexchange API
            
        Returns:
            Aircraft object
        """
        # Extract ICAO24 (hex identifier)
        icao24 = flight_data.get("hex", "").lower()
        
        # Extract other fields
        callsign = flight_data.get("flight", "").strip()
        origin_country = flight_data.get("cou")
        latitude = flight_data.get("lat")
        longitude = flight_data.get("lon")
        altitude = flight_data.get("alt_baro") * 0.3048 if flight_data.get("alt_baro") else None  # Convert feet to meters
        velocity = flight_data.get("gs") * 0.514444 if flight_data.get("gs") else None  # Convert knots to m/s
        heading = flight_data.get("track")
        vertical_rate = flight_data.get("baro_rate") * 0.00508 if flight_data.get("baro_rate") else None  # Convert feet/min to m/s
        
        # Use timestamp or current time
        timestamp = flight_data.get("seen", 0)
        last_update = datetime.now()
        if timestamp:
            # ADSBexchange provides 'seen' as seconds ago, so we need to subtract from current time
            last_update = datetime.now().replace(microsecond=0) - datetime.timedelta(seconds=timestamp)
        
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
        # Query parameters for the search
        params = {
            "lat": latitude,
            "lon": longitude,
            "dist": radius_km  # ADSBexchange uses kilometers for radius
        }
        
        # Make the request to the lat/lon/dist endpoint
        response = await self._make_request("lat/lon/dist", params)
        
        # Parse the response
        aircraft_list = []
        if response and "ac" in response:
            center = (latitude, longitude)
            
            for flight in response["ac"]:
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
            "q": normalized_callsign
        }
        
        # Make the request to the callsign endpoint
        response = await self._make_request("callsign", params)
        
        # Parse the response
        if response and "ac" in response and response["ac"]:
            return self._parse_aircraft(response["ac"][0])
        
        return None
