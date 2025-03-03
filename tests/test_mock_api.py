"""
Tests for the MockAPI class.
"""
import asyncio
from datetime import datetime

import pytest

from open_aircraft_tracker.api.mock import MockAPI


@pytest.mark.asyncio
async def test_mock_api_get_aircraft_in_radius():
    """Test getting aircraft within a radius using the mock API."""
    # Create a mock API with a fixed seed for reproducible results
    api = MockAPI(num_aircraft=10, seed=42)
    
    # Get aircraft within a radius
    latitude = 47.3769
    longitude = 8.5417
    radius_km = 10.0
    
    aircraft_list = await api.get_aircraft_in_radius(latitude, longitude, radius_km)
    
    # Check that we got some aircraft
    assert len(aircraft_list) > 0
    
    # Check that all aircraft have the required fields
    for aircraft in aircraft_list:
        assert aircraft.icao24 is not None
        assert aircraft.callsign is not None
        assert aircraft.latitude is not None
        assert aircraft.longitude is not None
        assert aircraft.altitude is not None
        assert aircraft.velocity is not None
        assert aircraft.heading is not None
        assert aircraft.vertical_rate is not None
        assert aircraft.last_update is not None


@pytest.mark.asyncio
async def test_mock_api_get_aircraft_by_callsign():
    """Test getting an aircraft by callsign using the mock API."""
    # Create a mock API with a fixed seed for reproducible results
    api = MockAPI(num_aircraft=10, seed=42)
    
    # First get all aircraft to populate the cache
    latitude = 47.3769
    longitude = 8.5417
    radius_km = 100.0
    
    aircraft_list = await api.get_aircraft_in_radius(latitude, longitude, radius_km)
    
    # Get the callsign of the first aircraft
    callsign = aircraft_list[0].callsign
    
    # Get the aircraft by callsign
    aircraft = await api.get_aircraft_by_callsign(callsign)
    
    # Check that we got the correct aircraft
    assert aircraft is not None
    assert aircraft.callsign == callsign


@pytest.mark.asyncio
async def test_mock_api_aircraft_movement():
    """Test that aircraft positions are updated over time."""
    # Create a mock API with a fixed seed for reproducible results
    api = MockAPI(num_aircraft=10, seed=42)
    
    # Get aircraft within a radius
    latitude = 47.3769
    longitude = 8.5417
    radius_km = 100.0
    
    # Get initial positions
    aircraft_list1 = await api.get_aircraft_in_radius(latitude, longitude, radius_km)
    
    # Wait a bit to allow positions to update
    await asyncio.sleep(1)
    
    # Get updated positions
    aircraft_list2 = await api.get_aircraft_in_radius(latitude, longitude, radius_km)
    
    # Check that positions have changed
    for i in range(min(len(aircraft_list1), len(aircraft_list2))):
        aircraft1 = aircraft_list1[i]
        aircraft2 = None
        
        # Find the corresponding aircraft in the second list
        for a in aircraft_list2:
            if a.icao24 == aircraft1.icao24:
                aircraft2 = a
                break
        
        # Skip if the aircraft is no longer in the list
        if aircraft2 is None:
            continue
        
        # Check that at least one of the position components has changed
        assert (aircraft1.latitude != aircraft2.latitude or
                aircraft1.longitude != aircraft2.longitude or
                aircraft1.altitude != aircraft2.altitude)
