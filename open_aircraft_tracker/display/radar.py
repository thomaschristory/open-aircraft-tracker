"""
Terminal-based radar display for aircraft tracking.
Uses the blessed library to create an interactive radar-like display.
"""
import asyncio
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

from blessed import Terminal
from geopy.distance import geodesic

from open_aircraft_tracker.api.base import Aircraft


class RadarDisplay:
    """Terminal-based radar display for aircraft tracking."""
    
    # Characters for drawing the radar
    AIRCRAFT_CHAR = "✈"
    CENTER_CHAR = "+"
    RING_CHAR = "·"
    HIGHLIGHT_CHAR = "◉"
    
    # Colors
    NORMAL_COLOR = "white"
    HIGHLIGHT_COLOR = "bright_yellow"
    WARNING_COLOR = "bright_red"
    INFO_COLOR = "bright_cyan"
    
    def __init__(self, terminal: Terminal, radius_km: float = 5.0):
        """
        Initialize the radar display.
        
        Args:
            terminal: Blessed Terminal instance
            radius_km: Radar radius in kilometers
        """
        self.term = terminal
        self.radius_km = radius_km
        self.center_lat: Optional[float] = None
        self.center_lon: Optional[float] = None
        self.aircraft_list: List[Aircraft] = []
        self.highlighted_callsigns: Set[str] = set()
        self.last_update = datetime.now()
        self.show_info = True
        
        # Calculate radar dimensions
        self.center_x = self.term.width // 2
        self.center_y = self.term.height // 2
        self.radar_radius = min(self.center_x, self.center_y) - 5
    
    def set_center(self, latitude: float, longitude: float):
        """
        Set the center position of the radar.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
        """
        self.center_lat = latitude
        self.center_lon = longitude
    
    def set_aircraft_list(self, aircraft_list: List[Aircraft]):
        """
        Update the list of aircraft to display.
        
        Args:
            aircraft_list: List of Aircraft objects
        """
        self.aircraft_list = aircraft_list
        self.last_update = datetime.now()
    
    def highlight_callsign(self, callsign: str, highlight: bool = True):
        """
        Highlight or unhighlight an aircraft by callsign.
        
        Args:
            callsign: Aircraft callsign
            highlight: Whether to highlight (True) or unhighlight (False)
        """
        if highlight:
            self.highlighted_callsigns.add(callsign.strip().upper())
        else:
            self.highlighted_callsigns.discard(callsign.strip().upper())
    
    def _calculate_screen_position(self, aircraft: Aircraft) -> Tuple[int, int]:
        """
        Calculate the screen position of an aircraft based on its coordinates.
        
        Args:
            aircraft: Aircraft object
            
        Returns:
            Tuple of (x, y) screen coordinates
        """
        if (self.center_lat is None or self.center_lon is None or
            aircraft.latitude is None or aircraft.longitude is None):
            return (0, 0)
        
        # Calculate distance and bearing from center
        center = (self.center_lat, self.center_lon)
        aircraft_pos = (aircraft.latitude, aircraft.longitude)
        
        # Calculate distance in kilometers
        distance_km = geodesic(center, aircraft_pos).kilometers
        
        # Calculate bearing
        # Formula: θ = atan2(sin(Δlong).cos(lat2), cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
        lat1 = math.radians(self.center_lat)
        lat2 = math.radians(aircraft.latitude)
        lon1 = math.radians(self.center_lon)
        lon2 = math.radians(aircraft.longitude)
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.degrees(math.atan2(y, x))
        
        # Convert to 0-360 range
        bearing = (bearing + 360) % 360
        
        # Convert polar coordinates (distance, bearing) to screen coordinates
        # Note: In screen coordinates, y increases downward, so we negate the y component
        distance_ratio = distance_km / self.radius_km
        screen_radius = self.radar_radius * distance_ratio
        
        # Convert bearing to radians and adjust for screen coordinates
        # In screen coordinates, 0 degrees is up, 90 degrees is right
        bearing_rad = math.radians(90 - bearing)
        
        screen_x = self.center_x + int(screen_radius * math.cos(bearing_rad))
        screen_y = self.center_y - int(screen_radius * math.sin(bearing_rad))
        
        return (screen_x, screen_y)
    
    def _is_highlighted(self, aircraft: Aircraft) -> bool:
        """
        Check if an aircraft should be highlighted.
        
        Args:
            aircraft: Aircraft object
            
        Returns:
            True if the aircraft should be highlighted, False otherwise
        """
        if not aircraft.callsign:
            return False
        
        return aircraft.callsign.strip().upper() in self.highlighted_callsigns
    
    def _draw_radar_background(self):
        """Draw the radar background with concentric rings."""
        # Clear the screen
        print(self.term.clear())
        
        # Draw concentric rings
        for i in range(1, 4):
            radius = self.radar_radius * i / 3
            for angle in range(0, 360, 5):
                angle_rad = math.radians(angle)
                x = self.center_x + int(radius * math.cos(angle_rad))
                y = self.center_y + int(radius * math.sin(angle_rad))
                
                if 0 <= x < self.term.width and 0 <= y < self.term.height:
                    try:
                        print(self.term.move_xy(x, y) + self.term.color_rgb(200, 200, 200)(self.RING_CHAR))
                    except Exception:
                        # Fallback if color_rgb is not supported
                        print(self.term.move_xy(x, y) + self.RING_CHAR)
        
        # Draw center point
        try:
            print(self.term.move_xy(self.center_x, self.center_y) + 
                  self.term.color_rgb(0, 255, 255)(self.CENTER_CHAR))
        except Exception:
            # Fallback if color_rgb is not supported
            print(self.term.move_xy(self.center_x, self.center_y) + self.CENTER_CHAR)
        
        # Draw cardinal directions
        directions = [
            ("N", 0, -1), 
            ("E", 1, 0), 
            ("S", 0, 1), 
            ("W", -1, 0)
        ]
        
        for direction, dx, dy in directions:
            x = self.center_x + int(self.radar_radius * dx * 1.1)
            y = self.center_y + int(self.radar_radius * dy * 1.1)
            
            if 0 <= x < self.term.width and 0 <= y < self.term.height:
                try:
                    print(self.term.move_xy(x, y) + 
                          self.term.color_rgb(0, 255, 255)(direction))
                except Exception:
                    # Fallback if color_rgb is not supported
                    print(self.term.move_xy(x, y) + direction)
        
        # Draw range rings labels
        for i in range(1, 4):
            distance = self.radius_km * i / 3
            label = f"{distance:.1f}km"
            
            # Position at 45 degrees (northeast)
            angle_rad = math.radians(45)
            radius = self.radar_radius * i / 3
            x = self.center_x + int(radius * math.cos(angle_rad))
            y = self.center_y + int(radius * math.sin(angle_rad))
            
            if 0 <= x < self.term.width and 0 <= y < self.term.height:
                try:
                    print(self.term.move_xy(x, y) + 
                          self.term.color_rgb(0, 255, 255)(label))
                except Exception:
                    # Fallback if color_rgb is not supported
                    print(self.term.move_xy(x, y) + label)
    
    def _draw_aircraft(self):
        """Draw aircraft on the radar."""
        for aircraft in self.aircraft_list:
            # Skip aircraft without position data
            if aircraft.latitude is None or aircraft.longitude is None:
                continue
            
            # Calculate screen position
            x, y = self._calculate_screen_position(aircraft)
            
            # Skip if outside screen bounds
            if not (0 <= x < self.term.width and 0 <= y < self.term.height):
                continue
            
            # Determine color based on highlight status
            color = self.HIGHLIGHT_COLOR if self._is_highlighted(aircraft) else self.NORMAL_COLOR
            
            # Draw aircraft symbol
            try:
                # Use different colors for highlighted and normal aircraft
                if self._is_highlighted(aircraft):
                    print(self.term.move_xy(x, y) + 
                          self.term.color_rgb(255, 255, 0)(self.AIRCRAFT_CHAR))  # Yellow for highlighted
                else:
                    print(self.term.move_xy(x, y) + 
                          self.term.color_rgb(255, 255, 255)(self.AIRCRAFT_CHAR))  # White for normal
            except Exception:
                # Fallback if color_rgb is not supported
                print(self.term.move_xy(x, y) + self.AIRCRAFT_CHAR)
            
            # Draw callsign if available and info display is enabled
            if self.show_info and aircraft.callsign:
                callsign_x = x + 1
                callsign_y = y
                
                # Ensure callsign is within screen bounds
                if 0 <= callsign_x < self.term.width - len(aircraft.callsign) and 0 <= callsign_y < self.term.height:
                    try:
                        # Use different colors for highlighted and normal aircraft
                        if self._is_highlighted(aircraft):
                            print(self.term.move_xy(callsign_x, callsign_y) + 
                                  self.term.color_rgb(255, 255, 0)(aircraft.callsign.strip()))  # Yellow for highlighted
                        else:
                            print(self.term.move_xy(callsign_x, callsign_y) + 
                                  self.term.color_rgb(255, 255, 255)(aircraft.callsign.strip()))  # White for normal
                    except Exception:
                        # Fallback if color_rgb is not supported
                        print(self.term.move_xy(callsign_x, callsign_y) + aircraft.callsign.strip())
    
    def _draw_info_panel(self):
        """Draw information panel with aircraft details."""
        if not self.show_info:
            return
        
        # Draw panel border
        panel_width = 40
        panel_height = min(len(self.aircraft_list) + 4, self.term.height - 2)
        panel_x = self.term.width - panel_width - 1
        panel_y = 1
        
        # Draw panel title
        title = " Aircraft Information "
        try:
            print(self.term.move_xy(panel_x + (panel_width - len(title)) // 2, panel_y) + 
                  self.term.color_rgb(0, 255, 255)(title))
        except Exception:
            # Fallback if color_rgb is not supported
            print(self.term.move_xy(panel_x + (panel_width - len(title)) // 2, panel_y) + title)
        
        # Draw column headers
        headers = ["Callsign", "Alt(m)", "Hdg", "Spd(km/h)"]
        header_line = " ".join(f"{h:<10}" for h in headers)
        try:
            print(self.term.move_xy(panel_x + 1, panel_y + 2) + 
                  self.term.color_rgb(0, 255, 255)(header_line))
        except Exception:
            # Fallback if color_rgb is not supported
            print(self.term.move_xy(panel_x + 1, panel_y + 2) + header_line)
        
        # Draw separator
        separator = "-" * (panel_width - 2)
        try:
            print(self.term.move_xy(panel_x + 1, panel_y + 3) + 
                  self.term.color_rgb(0, 255, 255)(separator))
        except Exception:
            # Fallback if color_rgb is not supported
            print(self.term.move_xy(panel_x + 1, panel_y + 3) + separator)
        
        # Sort aircraft by distance from center
        sorted_aircraft = sorted(
            [a for a in self.aircraft_list if a.latitude is not None and a.longitude is not None],
            key=lambda a: geodesic(
                (self.center_lat, self.center_lon), 
                (a.latitude, a.longitude)
            ).kilometers
        )
        
        # Draw aircraft information
        for i, aircraft in enumerate(sorted_aircraft):
            if i >= panel_height - 5:
                break
            
            row_y = panel_y + 4 + i
            
            # Determine color based on highlight status
            color = self.HIGHLIGHT_COLOR if self._is_highlighted(aircraft) else self.NORMAL_COLOR
            
            # Format aircraft information
            callsign = aircraft.callsign.strip() if aircraft.callsign else "Unknown"
            altitude = f"{int(aircraft.altitude)}" if aircraft.altitude is not None else "N/A"
            heading = f"{int(aircraft.heading)}°" if aircraft.heading is not None else "N/A"
            speed = f"{int(aircraft.velocity * 3.6)}" if aircraft.velocity is not None else "N/A"
            
            row_data = [callsign, altitude, heading, speed]
            row_text = " ".join(f"{d:<10}" for d in row_data)
            
            try:
                # Use different colors for highlighted and normal aircraft
                if self._is_highlighted(aircraft):
                    print(self.term.move_xy(panel_x + 1, row_y) + 
                          self.term.color_rgb(255, 255, 0)(row_text))  # Yellow for highlighted
                else:
                    print(self.term.move_xy(panel_x + 1, row_y) + 
                          self.term.color_rgb(255, 255, 255)(row_text))  # White for normal
            except Exception:
                # Fallback if color_rgb is not supported
                print(self.term.move_xy(panel_x + 1, row_y) + row_text)
    
    def _draw_status_bar(self):
        """Draw status bar with general information."""
        status_y = self.term.height - 1
        
        # Format current time
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # Format center coordinates
        if self.center_lat is not None and self.center_lon is not None:
            coords_str = f"Center: {self.center_lat:.6f}, {self.center_lon:.6f}"
        else:
            coords_str = "Center: Not set"
        
        # Format aircraft count
        count_str = f"Aircraft: {len(self.aircraft_list)}"
        
        # Format last update time
        update_str = f"Updated: {self.last_update.strftime('%H:%M:%S')}"
        
        # Combine status elements
        status_elements = [time_str, coords_str, count_str, update_str]
        status_text = " | ".join(status_elements)
        
        # Draw status bar
        try:
            print(self.term.move_xy(0, status_y) + 
                  self.term.color_rgb(0, 255, 255)(status_text))
        except Exception:
            # Fallback if color_rgb is not supported
            print(self.term.move_xy(0, status_y) + status_text)
    
    def _draw_help_text(self):
        """Draw help text at the bottom of the screen."""
        help_y = self.term.height - 2
        help_text = "Press 'q' to quit, 'i' to toggle info panel, 'h' to toggle help"
        
        try:
            print(self.term.move_xy(0, help_y) + 
                  self.term.color_rgb(0, 255, 255)(help_text))
        except Exception:
            # Fallback if color_rgb is not supported
            print(self.term.move_xy(0, help_y) + help_text)
    
    def draw(self):
        """Draw the complete radar display."""
        self._draw_radar_background()
        self._draw_aircraft()
        self._draw_info_panel()
        self._draw_status_bar()
        self._draw_help_text()
        
        # Flush output
        print(self.term.move_xy(0, 0), end="", flush=True)
    
    def toggle_info_panel(self):
        """Toggle the information panel visibility."""
        self.show_info = not self.show_info
