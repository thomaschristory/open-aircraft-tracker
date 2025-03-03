#!/usr/bin/env python
"""
Command-line entry point for the Open Aircraft Tracker application.
"""
import asyncio
from typing import List, Optional

import typer
from rich.console import Console

from open_aircraft_tracker.main import AircraftTracker
from open_aircraft_tracker.utils.logging import LogLevel, setup_logging

# Create a Typer app instance
app = typer.Typer(
    name="aircraft-tracker",
    help="Track aircraft near your location with a terminal-based radar display",
    add_completion=True,
)

# Create a rich console for better output formatting
console = Console()


@app.command()
def main(
    latitude: float = typer.Option(
        ..., "--latitude", "-lat", help="Center latitude in decimal degrees"
    ),
    longitude: float = typer.Option(
        ..., "--longitude", "-lon", help="Center longitude in decimal degrees"
    ),
    radius: float = typer.Option(
        5.0, "--radius", "-r", help="Radius in kilometers"
    ),
    update_interval: float = typer.Option(
        5.0, "--update-interval", "-u", help="Update interval in seconds"
    ),
    api: str = typer.Option(
        "opensky", "--api", "-a", 
        help="API to use (opensky, airlabs, aviationstack, flightaware, flightradar24, adsbexchange, mock)", 
        show_choices=True, case_sensitive=False
    ),
    username: Optional[str] = typer.Option(
        None, "--username", help="API username (if required)"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", help="API password (if required)"
    ),
    callsign: Optional[List[str]] = typer.Option(
        None, "--callsign", "-c", help="Callsign to highlight (can be specified multiple times)"
    ),
    sound_file: Optional[str] = typer.Option(
        None, "--sound-file", "-s", help="Path to a WAV file to use for alerts"
    ),
    mock_aircraft_count: int = typer.Option(
        20, "--mock-aircraft-count", "-m", help="Number of simulated aircraft for mock API"
    ),
    non_interactive: bool = typer.Option(
        False, "--non-interactive", "-n", help="Run in non-interactive mode (no radar display)"
    ),
    log_level: LogLevel = typer.Option(
        LogLevel.INFO, "--log-level", "-l", help="Log level (DEBUG, INFO, WARNING, ERROR)"
    ),
    log_file: Optional[str] = typer.Option(
        None, "--log-file", "-f", help="Path to log file (if not specified, log to console only)"
    ),
):
    """
    Track aircraft near your location with a terminal-based radar display.
    
    The application displays a radar-like view of nearby aircraft and can alert you
    when new aircraft enter your specified radius.
    """
    # Validate API type
    if api.lower() not in ["opensky", "airlabs", "aviationstack", "flightaware", "flightradar24", "adsbexchange", "mock"]:
        console.print(f"[bold red]Error:[/] Unknown API type: {api}")
        raise typer.Exit(code=1)
    
    # Validate API-specific requirements
    if api.lower() == "airlabs" and not username:
        console.print("[bold red]Error:[/] AirLabs API requires an API key (use --username to provide it)")
        raise typer.Exit(code=1)
    
    if api.lower() == "aviationstack" and not username:
        console.print("[bold red]Error:[/] AviationStack API requires an API key (use --username to provide it)")
        raise typer.Exit(code=1)
    
    if api.lower() == "flightaware" and (not username or not password):
        console.print("[bold red]Error:[/] FlightAware API requires both username and API key (use --username and --password)")
        raise typer.Exit(code=1)
    
    if api.lower() == "flightradar24" and not username:
        console.print("[bold red]Error:[/] FlightRadar24 API requires an API key (use --username to provide it)")
        raise typer.Exit(code=1)
    
    if api.lower() == "adsbexchange" and not username:
        console.print("[bold red]Error:[/] ADSBexchange API requires an API key (use --username to provide it)")
        raise typer.Exit(code=1)
    
    # Set up logging
    logger = setup_logging(log_level=log_level, log_file=log_file)
    logger.info(f"Starting Open Aircraft Tracker with API: {api}")
    logger.debug(f"Parameters: latitude={latitude}, longitude={longitude}, radius={radius}, update_interval={update_interval}")
    
    # Create aircraft tracker
    tracker = AircraftTracker(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius,
        update_interval=update_interval,
        api_type=api,
        api_username=username,
        api_password=password,
        callsigns=callsign,
        sound_file=sound_file,
        mock_aircraft_count=mock_aircraft_count,
        interactive=not non_interactive
    )
    
    try:
        # Run tracker
        asyncio.run(tracker.run())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interrupted by user. Exiting...[/]")
        raise typer.Exit()
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
