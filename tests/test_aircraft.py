"""
Tests for the Aircraft class in the base API module.
"""
from datetime import datetime

import pytest

from open_aircraft_tracker.api.base import Aircraft


def test_aircraft_creation():
    """Test creating an Aircraft object with all fields."""
    now = datetime.now()
    aircraft = Aircraft(
        icao24="abc123",
        callsign="SWR123",
        origin_country="Switzerland",
        latitude=47.3769,
        longitude=8.5417,
        altitude=1000.0,
        velocity=200.0,
        heading=90.0,
        vertical_rate=0.0,
        last_update=now
    )
    
    assert aircraft.icao24 == "abc123"
    assert aircraft.callsign == "SWR123"
    assert aircraft.origin_country == "Switzerland"
    assert aircraft.latitude == 47.3769
    assert aircraft.longitude == 8.5417
    assert aircraft.altitude == 1000.0
    assert aircraft.velocity == 200.0
    assert aircraft.heading == 90.0
    assert aircraft.vertical_rate == 0.0
    assert aircraft.last_update == now


def test_aircraft_with_optional_fields():
    """Test creating an Aircraft object with optional fields set to None."""
    now = datetime.now()
    aircraft = Aircraft(
        icao24="abc123",
        callsign=None,
        origin_country=None,
        latitude=None,
        longitude=None,
        altitude=None,
        velocity=None,
        heading=None,
        vertical_rate=None,
        last_update=now
    )
    
    assert aircraft.icao24 == "abc123"
    assert aircraft.callsign is None
    assert aircraft.origin_country is None
    assert aircraft.latitude is None
    assert aircraft.longitude is None
    assert aircraft.altitude is None
    assert aircraft.velocity is None
    assert aircraft.heading is None
    assert aircraft.vertical_rate is None
    assert aircraft.last_update == now
