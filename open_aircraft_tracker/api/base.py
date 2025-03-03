"""
Base API client interface for aircraft tracking.
All API implementations should inherit from this base class.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Aircraft:
    """Data class representing an aircraft."""
    icao24: str  # ICAO 24-bit address of the aircraft
    callsign: Optional[str]  # Callsign of the aircraft
    origin_country: Optional[str]  # Country of origin
    latitude: Optional[float]  # WGS-84 latitude in decimal degrees
    longitude: Optional[float]  # WGS-84 longitude in decimal degrees
    altitude: Optional[float]  # Altitude in meters
    velocity: Optional[float]  # Velocity in m/s
    heading: Optional[float]  # Heading in decimal degrees (0 is north, 90 is east)
    vertical_rate: Optional[float]  # Vertical rate in m/s
    last_update: datetime  # Last update time


class AircraftTrackerAPI(ABC):
    """Base class for aircraft tracking APIs."""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_aircraft_by_callsign(self, callsign: str) -> Optional[Aircraft]:
        """
        Get information about a specific aircraft by callsign.
        
        Args:
            callsign: The callsign of the aircraft
            
        Returns:
            Aircraft object if found, None otherwise
        """
        pass
