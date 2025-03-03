"""
Mock API client for testing purposes.
Generates simulated aircraft data without making actual API calls.
"""
import asyncio
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI


class MockAPI(AircraftTrackerAPI):
    """Mock API client that generates simulated aircraft data."""
    
    # Sample airline codes for generating realistic callsigns
    AIRLINES = ["SWR", "DLH", "BAW", "AFR", "KLM", "UAE", "QTR", "SIA", "AAL", "UAL"]
    
    def __init__(self, num_aircraft: int = 20, seed: Optional[int] = None):
        """
        Initialize the mock API client.
        
        Args:
            num_aircraft: Number of simulated aircraft to generate
            seed: Random seed for reproducible results
        """
        self.num_aircraft = num_aircraft
        self.aircraft_cache: Dict[str, Aircraft] = {}
        self.last_update = datetime.now()
        
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
    
    def _generate_callsign(self) -> str:
        """Generate a random airline callsign."""
        airline = random.choice(self.AIRLINES)
        flight_num = random.randint(100, 9999)
        return f"{airline}{flight_num}"
    
    def _generate_icao24(self) -> str:
        """Generate a random ICAO 24-bit address."""
        return ''.join(random.choices('0123456789abcdef', k=6))
    
    def _update_aircraft_positions(self, center_lat: float, center_lon: float, max_radius_km: float):
        """
        Update aircraft positions based on their current heading and velocity.
        
        Args:
            center_lat: Center latitude for generating new aircraft
            center_lon: Center longitude for generating new aircraft
            max_radius_km: Maximum radius for generating new aircraft
        """
        current_time = datetime.now()
        time_diff = (current_time - self.last_update).total_seconds()
        
        # Don't update if less than 1 second has passed
        if time_diff < 1:
            return
        
        # Update existing aircraft positions
        for icao24, aircraft in list(self.aircraft_cache.items()):
            # Skip aircraft without position or velocity data
            if (aircraft.latitude is None or aircraft.longitude is None or 
                aircraft.heading is None or aircraft.velocity is None):
                continue
            
            # Calculate new position based on heading and velocity
            # Convert velocity from m/s to km/h
            velocity_kmh = aircraft.velocity * 3.6
            
            # Calculate distance traveled in km
            distance_km = velocity_kmh * time_diff / 3600
            
            # Calculate new position
            # This is a simplified calculation that doesn't account for Earth's curvature
            # For more accuracy, we would use the haversine formula
            heading_rad = math.radians(aircraft.heading)
            lat_km = 110.574  # km per degree of latitude
            lon_km = 111.320 * math.cos(math.radians(aircraft.latitude))  # km per degree of longitude
            
            new_lat = aircraft.latitude + (distance_km * math.cos(heading_rad)) / lat_km
            new_lon = aircraft.longitude + (distance_km * math.sin(heading_rad)) / lon_km
            
            # Update aircraft position
            self.aircraft_cache[icao24] = Aircraft(
                icao24=aircraft.icao24,
                callsign=aircraft.callsign,
                origin_country=aircraft.origin_country,
                latitude=new_lat,
                longitude=new_lon,
                altitude=aircraft.altitude,
                velocity=aircraft.velocity,
                heading=aircraft.heading,
                vertical_rate=aircraft.vertical_rate,
                last_update=current_time
            )
            
            # Remove aircraft that are too far from the center
            aircraft_pos = (new_lat, new_lon)
            center_pos = (center_lat, center_lon)
            distance = geodesic(center_pos, aircraft_pos).kilometers
            
            if distance > max_radius_km * 2:
                del self.aircraft_cache[icao24]
        
        # Generate new aircraft if needed
        while len(self.aircraft_cache) < self.num_aircraft:
            # Generate a random position within the maximum radius
            distance = random.uniform(max_radius_km * 0.8, max_radius_km * 1.5)
            bearing = random.uniform(0, 360)
            
            # Convert bearing to radians
            bearing_rad = math.radians(bearing)
            
            # Calculate new position
            lat_km = 110.574  # km per degree of latitude
            lon_km = 111.320 * math.cos(math.radians(center_lat))  # km per degree of longitude
            
            new_lat = center_lat + (distance * math.cos(bearing_rad)) / lat_km
            new_lon = center_lon + (distance * math.sin(bearing_rad)) / lon_km
            
            # Generate random aircraft data
            icao24 = self._generate_icao24()
            callsign = self._generate_callsign()
            altitude = random.uniform(3000, 12000)  # meters
            velocity = random.uniform(200, 300)  # m/s
            heading = random.uniform(0, 360)  # degrees
            vertical_rate = random.uniform(-5, 5)  # m/s
            
            # Add aircraft to cache
            self.aircraft_cache[icao24] = Aircraft(
                icao24=icao24,
                callsign=callsign,
                origin_country="Mock Country",
                latitude=new_lat,
                longitude=new_lon,
                altitude=altitude,
                velocity=velocity,
                heading=heading,
                vertical_rate=vertical_rate,
                last_update=current_time
            )
        
        self.last_update = current_time
    
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
        # Update aircraft positions
        self._update_aircraft_positions(latitude, longitude, radius_km * 3)
        
        # Filter aircraft by distance
        result = []
        center = (latitude, longitude)
        
        for aircraft in self.aircraft_cache.values():
            # Skip aircraft without position data
            if aircraft.latitude is None or aircraft.longitude is None:
                continue
            
            # Calculate distance
            aircraft_pos = (aircraft.latitude, aircraft.longitude)
            distance = geodesic(center, aircraft_pos).kilometers
            
            # Only include aircraft within the specified radius
            if distance <= radius_km:
                result.append(aircraft)
        
        # Simulate network delay
        await asyncio.sleep(0.2)
        
        return result
    
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
        
        # Search for aircraft with matching callsign
        for aircraft in self.aircraft_cache.values():
            if aircraft.callsign and aircraft.callsign.strip().upper() == normalized_callsign:
                return aircraft
        
        # Simulate network delay
        await asyncio.sleep(0.2)
        
        return None
