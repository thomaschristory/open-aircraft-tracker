"""
AirLabs API client implementation.
Documentation: https://airlabs.co/docs/
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI


class AirLabsAPI(AircraftTrackerAPI):
    """AirLabs API client."""
    
    BASE_URL = "https://airlabs.co/api/v9"
    
    def __init__(self, api_key: str):
        """
        Initialize the AirLabs API client.
        
        Args:
            api_key: AirLabs API key
        """
        self.api_key = api_key
        if not api_key:
            raise ValueError("AirLabs API key is required")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make a request to the AirLabs API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response as a dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Add API key to parameters
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
    
    def _parse_aircraft(self, flight_data: Dict) -> Aircraft:
        """
        Parse flight data from the AirLabs API into an Aircraft object.
        
        Args:
            flight_data: Flight data from the AirLabs API
            
        Returns:
            Aircraft object
        """
        # AirLabs uses hex for ICAO24, but we need to ensure it's lowercase
        icao24 = flight_data.get("hex", "").lower()
        
        # Extract other fields
        callsign = flight_data.get("flight_iata") or flight_data.get("flight_icao")
        origin_country = flight_data.get("flag")
        latitude = flight_data.get("lat")
        longitude = flight_data.get("lng")
        altitude = flight_data.get("alt") * 0.3048 if flight_data.get("alt") else None  # Convert feet to meters
        velocity = flight_data.get("speed") * 0.514444 if flight_data.get("speed") else None  # Convert knots to m/s
        heading = flight_data.get("dir")
        vertical_rate = None  # AirLabs doesn't provide vertical rate
        
        # Use current time as last update if not provided
        last_update = datetime.now()
        
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
        # AirLabs API doesn't support filtering by radius directly
        # We'll get flights near the specified location and filter by distance
        params = {
            "lat": latitude,
            "lng": longitude,
            "distance": int(radius_km)  # AirLabs uses distance in km
        }
        
        # Make the request
        response = await self._make_request("flights", params)
        
        # Parse the response
        aircraft_list = []
        if response and "response" in response and response["response"]:
            center = (latitude, longitude)
            
            for flight in response["response"]:
                # Skip flights without position data
                if "lat" not in flight or "lng" not in flight:
                    continue
                
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
        
        # Query parameters
        params = {
            "flight_icao": normalized_callsign
        }
        
        # Make the request
        response = await self._make_request("flight", params)
        
        # Parse the response
        if response and "response" in response and response["response"]:
            flight = response["response"]
            return self._parse_aircraft(flight)
        
        # Try with IATA code if ICAO code didn't work
        params = {
            "flight_iata": normalized_callsign
        }
        
        # Make the request
        response = await self._make_request("flight", params)
        
        # Parse the response
        if response and "response" in response and response["response"]:
            flight = response["response"]
            return self._parse_aircraft(flight)
        
        return None
