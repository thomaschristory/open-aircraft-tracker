#!/usr/bin/env python
"""
Command-line entry point for the Open Aircraft Tracker application.
"""
import asyncio
from typing import List, Optional

import typer
from rich.console import Console

from open_aircraft_tracker.main import AircraftTracker

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
        "opensky", "--api", "-a", help="API to use", 
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
):
    """
    Track aircraft near your location with a terminal-based radar display.
    
    The application displays a radar-like view of nearby aircraft and can alert you
    when new aircraft enter your specified radius.
    """
    # Validate API type
    if api.lower() not in ["opensky", "mock"]:
        console.print(f"[bold red]Error:[/] Unknown API type: {api}")
        raise typer.Exit(code=1)
    
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
