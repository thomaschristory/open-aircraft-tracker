"""
Main entry point for the Open Aircraft Tracker application.
"""
import argparse
import asyncio
import os
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set

from blessed import Terminal

from open_aircraft_tracker.api.base import Aircraft, AircraftTrackerAPI
from open_aircraft_tracker.api.mock import MockAPI
from open_aircraft_tracker.api.opensky import OpenSkyAPI
from open_aircraft_tracker.display.radar import RadarDisplay
from open_aircraft_tracker.utils.sound import SoundAlert


class AircraftTracker:
    """Main application class for aircraft tracking."""
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        update_interval: float = 5.0,
        api_type: str = "opensky",
        api_username: Optional[str] = None,
        api_password: Optional[str] = None,
        callsigns: Optional[List[str]] = None,
        sound_file: Optional[str] = None,
        mock_aircraft_count: int = 20,
        interactive: bool = True
    ):
        """
        Initialize the aircraft tracker.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            update_interval: Update interval in seconds
            api_type: API type ("opensky" or "mock")
            api_username: API username (if required)
            api_password: API password (if required)
            callsigns: List of callsigns to highlight
            sound_file: Path to a WAV file to use for alerts
            mock_aircraft_count: Number of simulated aircraft for mock API
            interactive: Whether to run in interactive mode with radar display
        """
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km
        self.update_interval = update_interval
        self.callsigns = callsigns or []
        self.interactive = interactive
        
        # Initialize API client
        if api_type.lower() == "opensky":
            self.api = OpenSkyAPI(username=api_username, password=api_password)
        elif api_type.lower() == "mock":
            self.api = MockAPI(num_aircraft=mock_aircraft_count)
        else:
            raise ValueError(f"Unknown API type: {api_type}")
        
        # Initialize sound alert
        self.sound_alert = SoundAlert(sound_file)
        
        # Initialize terminal and radar display if in interactive mode
        if interactive:
            self.term = Terminal()
            self.radar = RadarDisplay(self.term, radius_km=radius_km)
            self.radar.set_center(latitude, longitude)
            
            # Highlight specified callsigns
            for callsign in self.callsigns:
                self.radar.highlight_callsign(callsign)
        else:
            self.term = None
            self.radar = None
        
        # Set up state variables
        self.running = False
        self.last_aircraft_set: Set[str] = set()  # Set of aircraft ICAOs in the last update
        self.known_aircraft: Dict[str, Aircraft] = {}  # Dict of known aircraft by ICAO
    
    async def update_aircraft(self):
        """Update aircraft positions from the API."""
        try:
            # Get aircraft within radius
            aircraft_list = await self.api.get_aircraft_in_radius(
                self.latitude, self.longitude, self.radius_km
            )
            
            # Update known aircraft
            current_aircraft_set = set()
            for aircraft in aircraft_list:
                current_aircraft_set.add(aircraft.icao24)
                self.known_aircraft[aircraft.icao24] = aircraft
            
            # Check for new aircraft
            new_aircraft = current_aircraft_set - self.last_aircraft_set
            if new_aircraft:
                # Play sound alert for new aircraft
                self.sound_alert.play()
                
                # Print information about new aircraft
                if not self.interactive:
                    print(f"\n=== New aircraft detected at {datetime.now().strftime('%H:%M:%S')} ===")
                    for icao in new_aircraft:
                        aircraft = self.known_aircraft[icao]
                        callsign = aircraft.callsign.strip() if aircraft.callsign else "Unknown"
                        print(f"Aircraft: {callsign} (ICAO: {aircraft.icao24})")
                        if aircraft.latitude is not None and aircraft.longitude is not None:
                            print(f"Position: {aircraft.latitude:.6f}, {aircraft.longitude:.6f}")
                        if aircraft.altitude is not None:
                            print(f"Altitude: {aircraft.altitude:.1f} meters")
                        if aircraft.heading is not None:
                            print(f"Heading: {aircraft.heading:.1f}°")
                        if aircraft.velocity is not None:
                            print(f"Speed: {aircraft.velocity * 3.6:.1f} km/h")
                        print()
            
            # Update radar display if in interactive mode
            if self.interactive and self.radar:
                self.radar.set_aircraft_list(aircraft_list)
                self.radar.draw()
            
            # Update last aircraft set
            self.last_aircraft_set = current_aircraft_set
            
        except Exception as e:
            if self.interactive:
                # Clear screen and display error
                print(self.term.clear())
                print(f"Error updating aircraft: {e}")
            else:
                print(f"Error updating aircraft: {e}")
    
    async def run(self):
        """Run the aircraft tracker."""
        self.running = True
        
        # Set up signal handlers
        def handle_signal(sig, frame):
            self.running = False
            if self.interactive:
                # Restore terminal
                print(self.term.normal_cursor())
                print(self.term.clear())
            
            print("Exiting...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        # Hide cursor in interactive mode
        if self.interactive:
            print(self.term.hide_cursor(), end="", flush=True)
        
        try:
            # Main loop
            while self.running:
                # Update aircraft
                await self.update_aircraft()
                
                # Handle user input in interactive mode
                if self.interactive:
                    # Check for keypress
                    if self.term.inkey(timeout=self.update_interval):
                        key = self.term.inkey()
                        
                        # Quit on 'q'
                        if key.lower() == "q":
                            self.running = False
                            break
                        
                        # Toggle info panel on 'i'
                        elif key.lower() == "i" and self.radar:
                            self.radar.toggle_info_panel()
                            self.radar.draw()
                else:
                    # Wait for update interval in non-interactive mode
                    await asyncio.sleep(self.update_interval)
        
        finally:
            # Restore terminal
            if self.interactive:
                print(self.term.normal_cursor())
                print(self.term.clear())


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Open Aircraft Tracker - Track aircraft near your location"
    )
    
    # Required arguments
    parser.add_argument(
        "--latitude", "-lat",
        type=float,
        required=True,
        help="Center latitude in decimal degrees"
    )
    parser.add_argument(
        "--longitude", "-lon",
        type=float,
        required=True,
        help="Center longitude in decimal degrees"
    )
    
    # Optional arguments
    parser.add_argument(
        "--radius", "-r",
        type=float,
        default=5.0,
        help="Radius in kilometers (default: 5.0)"
    )
    parser.add_argument(
        "--update-interval", "-u",
        type=float,
        default=5.0,
        help="Update interval in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--api", "-a",
        type=str,
        choices=["opensky", "mock"],
        default="opensky",
        help="API to use (default: opensky)"
    )
    parser.add_argument(
        "--username",
        type=str,
        help="API username (if required)"
    )
    parser.add_argument(
        "--password",
        type=str,
        help="API password (if required)"
    )
    parser.add_argument(
        "--callsign", "-c",
        type=str,
        action="append",
        help="Callsign to highlight (can be specified multiple times)"
    )
    parser.add_argument(
        "--sound-file", "-s",
        type=str,
        help="Path to a WAV file to use for alerts"
    )
    parser.add_argument(
        "--mock-aircraft-count", "-m",
        type=int,
        default=20,
        help="Number of simulated aircraft for mock API (default: 20)"
    )
    parser.add_argument(
        "--non-interactive", "-n",
        action="store_true",
        help="Run in non-interactive mode (no radar display)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_args()
    
    # Create aircraft tracker
    tracker = AircraftTracker(
        latitude=args.latitude,
        longitude=args.longitude,
        radius_km=args.radius,
        update_interval=args.update_interval,
        api_type=args.api,
        api_username=args.username,
        api_password=args.password,
        callsigns=args.callsign,
        sound_file=args.sound_file,
        mock_aircraft_count=args.mock_aircraft_count,
        interactive=not args.non_interactive
    )
    
    # Run tracker
    asyncio.run(tracker.run())


if __name__ == "__main__":
    main()
