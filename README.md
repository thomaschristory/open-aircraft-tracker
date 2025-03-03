# Open Aircraft Tracker

A terminal-based application for tracking aircraft near your location in real-time. The application displays a radar-like view of nearby aircraft and can alert you when new aircraft enter your specified radius.

![Open Aircraft Tracker Screenshot](https://via.placeholder.com/800x500?text=Open+Aircraft+Tracker+Screenshot)

## Features

- Track aircraft within a specified radius of your location
- Interactive radar display with aircraft positions
- Sound alerts when new aircraft enter the tracking radius
- Highlight specific aircraft by callsign
- Support for multiple aircraft tracking APIs:
  - Free APIs: OpenSky Network, AirLabs, AviationStack
  - Premium APIs: FlightAware, FlightRadar24, ADSBexchange
  - Mock API for testing
- Both interactive (radar display) and non-interactive (console output) modes
- Extensive logging options for debugging and monitoring:
  - Multiple log levels (DEBUG, INFO, WARNING, ERROR)
  - Console and file logging
  - Detailed API response logging
  - Real-time monitoring with `tail -f`
- Easily extensible to support additional aircraft tracking APIs

## Installation

### Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)

### Install from GitHub

```bash
# Clone the repository
git clone https://github.com/thomaschristory/open-aircraft-tracker.git
cd open-aircraft-tracker

# Install with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Install from PyPI (coming soon)

```bash
pip install open-aircraft-tracker
```

## Usage

### Basic Usage

```bash
# Using the command-line entry point
aircraft-tracker --latitude 47.3769 --longitude 8.5417 --radius 10

# Or directly using the module
python -m open_aircraft_tracker.main --latitude 47.3769 --longitude 8.5417 --radius 10
```

### Command-line Options

```
Usage: aircraft-tracker [OPTIONS]

 Track aircraft near your location with a terminal-based radar display.
 The application displays a radar-like view of nearby aircraft and can alert you when new aircraft enter your specified radius.

╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --latitude             -lat      FLOAT    Center latitude in decimal degrees [default: None] [required]                                                                                                    │
│ *  --longitude            -lon      FLOAT    Center longitude in decimal degrees [default: None] [required]                                                                                                   │
│    --radius               -r        FLOAT    Radius in kilometers [default: 5.0]                                                                                                                              │
│    --update-interval      -u        FLOAT    Update interval in seconds [default: 5.0]                                                                                                                        │
│    --api                  -a        TEXT     API to use (opensky, airlabs, aviationstack, flightaware, flightradar24, adsbexchange, mock) [default: opensky]                                                  │
│    --username                       TEXT     API username (if required) [default: None]                                                                                                                       │
│    --password                       TEXT     API password (if required) [default: None]                                                                                                                       │
│    --callsign             -c        TEXT     Callsign to highlight (can be specified multiple times) [default: None]                                                                                          │
│    --sound-file           -s        TEXT     Path to a WAV file to use for alerts [default: None]                                                                                                             │
│    --mock-aircraft-count  -m        INTEGER  Number of simulated aircraft for mock API [default: 20]                                                                                                          │
│    --non-interactive      -n                 Run in non-interactive mode (no radar display)                                                                                                                   │
│    --log-level            -l        TEXT     Log level (DEBUG, INFO, WARNING, ERROR) [default: INFO]                                                                                                          │
│    --log-file             -f        TEXT     Path to log file (if not specified, log to console only) [default: None]                                                                                         │
│    --install-completion                      Install completion for the current shell.                                                                                                                        │
│    --show-completion                         Show completion for the current shell to copy it or customize the installation.                                                                                 │
│    --help                                    Show this message and exit.                                                                                                                                      │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Note: The CLI is now powered by [Typer](https://typer.tiangolo.com/), which provides a more modern and user-friendly interface with features like:
- Rich formatting for help text
- Automatic shell completion
- Better error messages and validation

### Examples

#### Track aircraft within 5km of Zurich Airport

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --radius 5
```

#### Track specific flights (by callsign)

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --callsign SWR123 --callsign LX38
```

#### Use the mock API for testing

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api mock
```

#### Run in non-interactive mode (console output only)

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --non-interactive
```

#### Enable detailed logging to a file

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --log-level DEBUG --log-file /path/to/aircraft.log
```

You can then monitor the log file in real-time using:

```bash
tail -f /path/to/aircraft.log
```

This is especially useful for debugging when nothing appears to be happening, as it shows all API responses and aircraft tracking details.

### Interactive Mode Controls

When running in interactive mode (the default), the following keyboard controls are available:

- `q`: Quit the application
- `i`: Toggle the information panel
- `h`: Toggle help text

## API Information

The application supports multiple aircraft tracking APIs:

### OpenSky Network API

The OpenSky Network provides a free API for tracking aircraft. By default, the application uses the public API, which has rate limits. For higher rate limits, you can create an account at [OpenSky Network](https://opensky-network.org/) and provide your username and password.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api opensky --username your_username --password your_password
```

Note: OpenSky Network is currently closed for registration. If you don't have an account, you can use the AirLabs API instead.

### AirLabs API

AirLabs provides a comprehensive flight tracking API with real-time data. You need to sign up for an API key at [AirLabs](https://airlabs.co/) to use this API. The free tier allows up to 1,000 requests per month.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api airlabs --username your_api_key
```

Note: For AirLabs, the API key should be provided using the `--username` parameter. AirLabs is currently closed for new registrations.

### AviationStack API

AviationStack provides real-time global aviation data including flights, airlines, and airports. You need to sign up for an API key at [AviationStack](https://aviationstack.com/) to use this API. The free tier allows up to 500 requests per month.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api aviationstack --username your_api_key
```

Note: For AviationStack, the API key should be provided using the `--username` parameter. AviationStack still accepts new registrations (as of March 2025).

### Mock API

The application also includes a mock API for testing purposes. This API generates random aircraft positions around the specified location.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api mock --mock-aircraft-count 30
```

### Premium API Integrations

The application now supports the following premium aircraft tracking APIs:

1. **FlightAware (FlightXML)** - One of the most comprehensive flight tracking services with extensive global coverage and detailed flight information.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api flightaware --username your_username --password your_api_key
```

2. **FlightRadar24** - Very popular flight tracking service with real-time tracking of thousands of aircraft around the world.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api flightradar24 --username your_api_key
```

3. **ADSBexchange** - Provides unfiltered flight data with no censorship, including military and sensitive flights that might be filtered on other platforms.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --api adsbexchange --username your_api_key
```

These premium APIs require paid subscriptions but offer higher quality data, better reliability, and more features than the free alternatives. For pricing information, visit the respective websites:

- FlightAware: https://flightaware.com/commercial/flightxml/
- FlightRadar24: https://www.flightradar24.com/premium/
- ADSBexchange: https://www.adsbexchange.com/data/

### Adding Support for Additional APIs

The application is designed to be easily extensible with additional aircraft tracking APIs. To add support for a new API:

1. Create a new class that inherits from `AircraftTrackerAPI` in `open_aircraft_tracker/api/base.py`
2. Implement the required methods: `get_aircraft_in_radius` and `get_aircraft_by_callsign`
3. Add the new API to the available options in `open_aircraft_tracker/main.py`

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/thomaschristory/open-aircraft-tracker.git
cd open-aircraft-tracker

# Install development dependencies
poetry install --with dev

# Activate the virtual environment
poetry shell
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code with Black
black open_aircraft_tracker

# Sort imports with isort
isort open_aircraft_tracker
```

### Type Checking

```bash
mypy open_aircraft_tracker
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [OpenSky Network](https://opensky-network.org/) for providing the free aircraft tracking API
- [AirLabs](https://airlabs.co/) for providing the flight tracking API
- [AviationStack](https://aviationstack.com/) for providing the aviation data API
- [FlightAware](https://flightaware.com/) for providing the FlightXML API
- [FlightRadar24](https://www.flightradar24.com/) for providing flight tracking data
- [ADSBexchange](https://www.adsbexchange.com/) for providing unfiltered flight data
- [blessed](https://github.com/jquast/blessed) for the terminal interface
- [geopy](https://github.com/geopy/geopy) for distance calculations
