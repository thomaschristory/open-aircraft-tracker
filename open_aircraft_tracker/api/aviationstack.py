"""
AviationStack API client implementation.
Documentation: https://aviationstack.com/documentation
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI


class AviationStackAPI(AircraftTrackerAPI):
    """AviationStack API client."""
    
    BASE_URL = "http://api.aviationstack.com/v1"
    
    def __init__(self, api_key: str):
        """
        Initialize the AviationStack API client.
        
        Args:
            api_key: AviationStack API key
        """
        self.api_key = api_key
        if not api_key:
            raise ValueError("AviationStack API key is required")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make a request to the AviationStack API.
        
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
        params["access_key"] = self.api_key
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
    
    def _parse_aircraft(self, flight_data: Dict) -> Aircraft:
        """
        Parse flight data from the AviationStack API into an Aircraft object.
        
        Args:
            flight_data: Flight data from the AviationStack API
            
        Returns:
            Aircraft object
        """
        # Extract aircraft data
        aircraft = flight_data.get("aircraft", {})
        flight = flight_data.get("flight", {})
        live = flight_data.get("live", {})
        
        # Extract ICAO24 (transponder code)
        icao24 = aircraft.get("icao24", "").lower()
        if not icao24 and aircraft.get("registration"):
            # Use registration as fallback if ICAO24 is not available
            icao24 = aircraft.get("registration", "").lower()
        
        # Extract other fields
        callsign = flight.get("iata") or flight.get("icao") or flight.get("number", "")
        origin_country = flight_data.get("airline", {}).get("country_name")
        latitude = live.get("latitude")
        longitude = live.get("longitude")
        altitude = live.get("altitude") * 0.3048 if live.get("altitude") else None  # Convert feet to meters
        velocity = live.get("speed") * 0.514444 if live.get("speed") else None  # Convert knots to m/s
        heading = live.get("direction")
        vertical_rate = None  # AviationStack doesn't provide vertical rate
        
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
        # AviationStack doesn't support filtering by location directly
        # We'll get all flights and filter by distance
        params = {
            "flight_status": "active",  # Only get active flights
            "limit": 100  # Maximum number of results
        }
        
        # Make the request
        response = await self._make_request("flights", params)
        
        # Parse the response
        aircraft_list = []
        if response and "data" in response:
            center = (latitude, longitude)
            
            for flight in response["data"]:
                # Skip flights without live data
                if "live" not in flight or not flight["live"]:
                    continue
                
                # Skip flights without position data
                live = flight["live"]
                if "latitude" not in live or "longitude" not in live:
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
        
        # Try with IATA code
        params = {
            "flight_iata": normalized_callsign
        }
        
        # Make the request
        response = await self._make_request("flights", params)
        
        # Parse the response
        if response and "data" in response and response["data"]:
            for flight in response["data"]:
                # Skip flights without live data
                if "live" not in flight or not flight["live"]:
                    continue
                
                return self._parse_aircraft(flight)
        
        # Try with ICAO code if IATA code didn't work
        params = {
            "flight_icao": normalized_callsign
        }
        
        # Make the request
        response = await self._make_request("flights", params)
        
        # Parse the response
        if response and "data" in response and response["data"]:
            for flight in response["data"]:
                # Skip flights without live data
                if "live" not in flight or not flight["live"]:
                    continue
                
                return self._parse_aircraft(flight)
        
        # Try with flight number if ICAO code didn't work
        params = {
            "flight_number": normalized_callsign
        }
        
        # Make the request
        response = await self._make_request("flights", params)
        
        # Parse the response
        if response and "data" in response and response["data"]:
            for flight in response["data"]:
                # Skip flights without live data
                if "live" not in flight or not flight["live"]:
                    continue
                
                return self._parse_aircraft(flight)
        
        return None
