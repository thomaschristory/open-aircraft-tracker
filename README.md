# Open Aircraft Tracker

A terminal-based application for tracking aircraft near your location in real-time. The application displays a radar-like view of nearby aircraft and can alert you when new aircraft enter your specified radius.

![Open Aircraft Tracker Screenshot](https://via.placeholder.com/800x500?text=Open+Aircraft+Tracker+Screenshot)

## Features

- Track aircraft within a specified radius of your location
- Interactive radar display with aircraft positions
- Sound alerts when new aircraft enter the tracking radius
- Highlight specific aircraft by callsign
- Support for multiple aircraft tracking APIs (currently OpenSky Network and a mock API for testing)
- Both interactive (radar display) and non-interactive (console output) modes
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
usage: aircraft-tracker [-h] --latitude LATITUDE --longitude LONGITUDE [--radius RADIUS]
                        [--update-interval UPDATE_INTERVAL] [--api {opensky,mock}]
                        [--username USERNAME] [--password PASSWORD] [--callsign CALLSIGN]
                        [--sound-file SOUND_FILE] [--mock-aircraft-count MOCK_AIRCRAFT_COUNT]
                        [--non-interactive]

Open Aircraft Tracker - Track aircraft near your location

required arguments:
  --latitude LATITUDE, -lat LATITUDE
                        Center latitude in decimal degrees
  --longitude LONGITUDE, -lon LONGITUDE
                        Center longitude in decimal degrees

optional arguments:
  --radius RADIUS, -r RADIUS
                        Radius in kilometers (default: 5.0)
  --update-interval UPDATE_INTERVAL, -u UPDATE_INTERVAL
                        Update interval in seconds (default: 5.0)
  --api {opensky,mock}, -a {opensky,mock}
                        API to use (default: opensky)
  --username USERNAME   API username (if required)
  --password PASSWORD   API password (if required)
  --callsign CALLSIGN, -c CALLSIGN
                        Callsign to highlight (can be specified multiple times)
  --sound-file SOUND_FILE, -s SOUND_FILE
                        Path to a WAV file to use for alerts
  --mock-aircraft-count MOCK_AIRCRAFT_COUNT, -m MOCK_AIRCRAFT_COUNT
                        Number of simulated aircraft for mock API (default: 20)
  --non-interactive, -n
                        Run in non-interactive mode (no radar display)
```

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

### Interactive Mode Controls

When running in interactive mode (the default), the following keyboard controls are available:

- `q`: Quit the application
- `i`: Toggle the information panel
- `h`: Toggle help text

## API Information

### OpenSky Network API

The OpenSky Network provides a free API for tracking aircraft. By default, the application uses the public API, which has rate limits. For higher rate limits, you can create an account at [OpenSky Network](https://opensky-network.org/) and provide your username and password.

```bash
aircraft-tracker --latitude 47.4582 --longitude 8.5555 --username your_username --password your_password
```

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
- [blessed](https://github.com/jquast/blessed) for the terminal interface
- [geopy](https://github.com/geopy/geopy) for distance calculations
