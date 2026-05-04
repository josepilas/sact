#!/usr/bin/env python3
"""
SACT - Stupid Ass Controller Test
A ridiculously detailed, mega-comprehensive gamepad tester with a beautiful UI.
Built with Pygame for maximum compatibility and performance.
"""

import pygame
import sys
import math
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

# Initialize Pygame
pygame.init()
pygame.joystick.init()

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

@dataclass
class ColorScheme:
    """Modern dark theme color scheme"""
    bg_primary: Tuple[int, int, int] = (18, 18, 24)
    bg_secondary: Tuple[int, int, int] = (28, 28, 36)
    bg_tertiary: Tuple[int, int, int] = (38, 38, 48)
    accent_primary: Tuple[int, int, int] = (0, 200, 255)
    accent_secondary: Tuple[int, int, int] = (255, 100, 150)
    accent_success: Tuple[int, int, int] = (0, 255, 136)
    accent_warning: Tuple[int, int, int] = (255, 200, 0)
    accent_error: Tuple[int, int, int] = (255, 80, 80)
    text_primary: Tuple[int, int, int] = (255, 255, 255)
    text_secondary: Tuple[int, int, int] = (180, 180, 190)
    text_muted: Tuple[int, int, int] = (100, 100, 110)
    button_inactive: Tuple[int, int, int] = (60, 60, 75)
    button_active: Tuple[int, int, int] = (0, 200, 255)
    axis_low: Tuple[int, int, int] = (0, 100, 255)
    axis_high: Tuple[int, int, int] = (255, 50, 100)
    grid_line: Tuple[int, int, int] = (50, 50, 65)

COLORS = ColorScheme()

# Standard button mappings (Xbox layout as reference)
STANDARD_BUTTON_NAMES = {
    0: "A / Cross",
    1: "B / Circle", 
    2: "X / Square",
    3: "Y / Triangle",
    4: "LB / L1",
    5: "RB / R1",
    6: "LT / L2",
    7: "RT / R2",
    8: "Back / Select",
    9: "Start",
    10: "LS Click",
    11: "RS Click",
    12: "DPad Up",
    13: "DPad Down",
    14: "DPad Left",
    15: "DPad Right",
    16: "Guide / Home",
    17: "Extra 1",
    18: "Extra 2",
    19: "Extra 3",
}

# Standard axis mappings
STANDARD_AXIS_NAMES = {
    0: "Left Stick X",
    1: "Left Stick Y",
    2: "Right Stick X",
    3: "Right Stick Y",
    4: "LT / L2 Axis",
    5: "RT / R2 Axis",
}

# ============================================================================
# UI COMPONENTS
# ============================================================================

class RoundedRectangle:
    """Helper class for drawing rounded rectangles"""
    
    @staticmethod
    def draw(surface: pygame.Surface, color: Tuple[int, int, int], 
             rect: pygame.Rect, radius: int = 10) -> None:
        """Draw a filled rounded rectangle"""
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    
    @staticmethod
    def draw_outline(surface: pygame.Surface, color: Tuple[int, int, int],
                     rect: pygame.Rect, radius: int = 10, width: int = 2) -> None:
        """Draw an outlined rounded rectangle"""
        pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)


class ProgressBar:
    """Animated progress bar component"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 color: Tuple[int, int, int] = COLORS.accent_primary):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.value = 0.0
        self.target_value = 0.0
        
    def update(self, value: float, dt: float) -> None:
        """Smoothly interpolate to target value"""
        self.target_value = max(0.0, min(1.0, value))
        # Smooth interpolation
        self.value += (self.target_value - self.value) * min(1.0, dt * 10)
        
    def draw(self, surface: pygame.Surface, show_value: bool = True) -> None:
        """Draw the progress bar"""
        # Background
        RoundedRectangle.draw(surface, COLORS.bg_tertiary, self.rect, radius=6)
        
        # Fill
        fill_width = int(self.rect.width * self.value)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            RoundedRectangle.draw(surface, self.color, fill_rect, radius=6)
        
        # Border
        RoundedRectangle.draw_outline(surface, COLORS.text_muted, self.rect, radius=6, width=1)
        
        # Value text
        if show_value:
            font = pygame.font.Font(None, 20)
            text = font.render(f"{self.value * 100:.1f}%", True, COLORS.text_primary)
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)


class Button:
    """Interactive button component"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.clicked = False
        self.click_timer = 0
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and event.button == 1:
                self.clicked = True
                self.click_timer = 0.1
                if self.callback:
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False
        return False
    
    def update(self, dt: float) -> None:
        """Update button state"""
        if self.click_timer > 0:
            self.click_timer -= dt
            
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the button"""
        if self.clicked:
            color = COLORS.accent_primary
        elif self.hovered:
            color = (int(COLORS.button_inactive[0] * 1.3),
                    int(COLORS.button_inactive[1] * 1.3),
                    int(COLORS.button_inactive[2] * 1.3))
        else:
            color = COLORS.button_inactive
            
        RoundedRectangle.draw(surface, color, self.rect, radius=8)
        RoundedRectangle.draw_outline(surface, COLORS.text_muted, self.rect, radius=8, width=1)
        
        # Text
        font = pygame.font.Font(None, 24)
        text_color = COLORS.text_primary if not self.clicked else COLORS.bg_primary
        text = font.render(self.text, True, text_color)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)


class JoystickVisualizer:
    """Visual representation of joystick/stick position"""
    
    def __init__(self, center_x: int, center_y: int, radius: int = 60):
        self.center = pygame.Vector2(center_x, center_y)
        self.outer_radius = radius
        self.inner_radius = radius // 3
        self.position = pygame.Vector2(0, 0)  # Normalized -1 to 1
        self.target_position = pygame.Vector2(0, 0)
        
    def update(self, x: float, y: float, dt: float) -> None:
        """Update stick position with smoothing"""
        self.target_position.update(x, -y)  # Invert Y for display
        # Smooth movement
        lerp_factor = min(1.0, dt * 15)
        self.position.lerp(self.target_position, lerp_factor)
        # Clamp to circle
        if self.position.length() > 1:
            self.position.scale_to_length(1)
            
    def draw(self, surface: pygame.Surface, label: str = "") -> None:
        """Draw the joystick visualizer"""
        # Outer circle (boundary)
        pygame.draw.circle(surface, COLORS.bg_tertiary, 
                          (int(self.center.x), int(self.center.y)), 
                          self.outer_radius)
        pygame.draw.circle(surface, COLORS.grid_line,
                          (int(self.center.x), int(self.center.y)),
                          self.outer_radius, width=2)
        
        # Cross hairs
        pygame.draw.line(surface, COLORS.grid_line,
                        (self.center.x - self.outer_radius, self.center.y),
                        (self.center.x + self.outer_radius, self.center.y), width=1)
        pygame.draw.line(surface, COLORS.grid_line,
                        (self.center.x, self.center.y - self.outer_radius),
                        (self.center.x, self.center.y + self.outer_radius), width=1)
        
        # Inner stick
        stick_pos = self.center + self.position * (self.outer_radius - self.inner_radius)
        pygame.draw.circle(surface, COLORS.accent_primary,
                          (int(stick_pos.x), int(stick_pos.y)),
                          self.inner_radius)
        pygame.draw.circle(surface, COLORS.text_primary,
                          (int(stick_pos.x), int(stick_pos.y)),
                          self.inner_radius - 5, width=2)
        
        # Label
        if label:
            font = pygame.font.Font(None, 20)
            text = font.render(label, True, COLORS.text_secondary)
            text_rect = text.get_rect(center=(self.center.x, self.center.y + self.outer_radius + 15))
            surface.blit(text, text_rect)


class DPadVisualizer:
    """Visual representation of D-Pad state"""
    
    def __init__(self, center_x: int, center_y: int, size: int = 80):
        self.center = pygame.Vector2(center_x, center_y)
        self.size = size
        self.active_directions = set()
        
    def update(self, up: bool, down: bool, left: bool, right: bool) -> None:
        """Update active directions"""
        self.active_directions.clear()
        if up:
            self.active_directions.add("up")
        if down:
            self.active_directions.add("down")
        if left:
            self.active_directions.add("left")
        if right:
            self.active_directions.add("right")
            
    def draw(self, surface: pygame.Surface, label: str = "") -> None:
        """Draw the D-Pad"""
        # Draw base cross shape
        arm_length = self.size // 2
        arm_width = self.size // 3
        
        # Background arms
        for dx, dy, direction in [(0, -1, "up"), (0, 1, "down"), 
                                   (-1, 0, "left"), (1, 0, "right")]:
            x = self.center.x + dx * arm_length // 2
            y = self.center.y + dy * arm_length // 2
            rect = pygame.Rect(x - arm_width // 2, y - arm_width // 2,
                              arm_width if dx != 0 else arm_length,
                              arm_length if dx != 0 else arm_width)
            color = COLORS.bg_tertiary
            if direction in self.active_directions:
                color = COLORS.accent_success
            RoundedRectangle.draw(surface, color, rect, radius=5)
            
        # Center circle
        pygame.draw.circle(surface, COLORS.bg_secondary,
                          (int(self.center.x), int(self.center.y)),
                          arm_width // 2 + 2)
        
        # Label
        if label:
            font = pygame.font.Font(None, 20)
            text = font.render(label, True, COLORS.text_secondary)
            text_rect = text.get_rect(center=(self.center.x, self.center.y + self.size // 2 + 20))
            surface.blit(text, text_rect)


class TriggerVisualizer:
    """Visual representation of trigger buttons"""
    
    def __init__(self, x: int, y: int, width: int, height: int, label: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = 0.0
        self.target_value = 0.0
        
    def update(self, value: float, dt: float) -> None:
        """Update trigger value with smoothing"""
        self.target_value = max(0.0, min(1.0, value))
        lerp_factor = min(1.0, dt * 10)
        self.value += (self.target_value - self.value) * lerp_factor
        
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the trigger"""
        # Background slot
        slot_rect = pygame.Rect(self.rect.x, self.rect.y, 
                               self.rect.width, self.rect.height)
        RoundedRectangle.draw(surface, COLORS.bg_tertiary, slot_rect, radius=5)
        
        # Trigger fill (fills from bottom)
        fill_height = int(self.rect.height * self.value)
        if fill_height > 0:
            fill_rect = pygame.Rect(self.rect.x, 
                                   self.rect.y + self.rect.height - fill_height,
                                   self.rect.width, fill_height)
            # Gradient color based on value
            if self.value < 0.5:
                color = COLORS.axis_low
            else:
                color = COLORS.axis_high
            RoundedRectangle.draw(surface, color, fill_rect, radius=5)
        
        # Border
        RoundedRectangle.draw_outline(surface, COLORS.text_muted, self.rect, radius=5, width=1)
        
        # Label and value
        font = pygame.font.Font(None, 20)
        label_text = font.render(self.label, True, COLORS.text_secondary)
        label_rect = label_text.get_rect(centerx=self.rect.centerx, 
                                         bottom=self.rect.top - 5)
        surface.blit(label_text, label_rect)
        
        value_text = font.render(f"{self.value:.2f}", True, COLORS.text_primary)
        value_rect = value_text.get_rect(center=self.rect.center)
        surface.blit(value_text, value_rect)


class ButtonIndicator:
    """Visual indicator for button press state"""
    
    def __init__(self, x: int, y: int, width: int, height: int, label: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.pressed = False
        self.was_pressed = False
        self.press_count = 0
        self.press_time = 0
        self.total_presses = 0
        
    def update(self, pressed: bool, dt: float) -> None:
        """Update button state"""
        if pressed and not self.was_pressed:
            self.press_count += 1
            self.total_presses += 1
            self.press_time = 0.2
        self.pressed = pressed
        self.was_pressed = pressed
        if self.press_time > 0:
            self.press_time -= dt
            
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the button indicator"""
        if self.pressed:
            color = COLORS.accent_success
        elif self.press_time > 0:
            # Flash effect on press
            t = self.press_time / 0.2
            r = int(COLORS.accent_primary[0] * t + COLORS.button_inactive[0] * (1-t))
            g = int(COLORS.accent_primary[1] * t + COLORS.button_inactive[1] * (1-t))
            b = int(COLORS.accent_primary[2] * t + COLORS.button_inactive[2] * (1-t))
            color = (r, g, b)
        else:
            color = COLORS.button_inactive
            
        RoundedRectangle.draw(surface, color, self.rect, radius=6)
        
        # Border
        border_color = COLORS.accent_primary if self.pressed else COLORS.text_muted
        RoundedRectangle.draw_outline(surface, border_color, self.rect, radius=6, width=2)
        
        # Label
        if self.label:
            font = pygame.font.Font(None, 20)
            text = font.render(self.label, True, COLORS.text_primary)
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class SACTApplication:
    """Main SACT application class"""
    
    def __init__(self):
        # Window setup
        self.WIDTH = 1400
        self.HEIGHT = 900
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("SACT - Stupid Ass Controller Test")
        
        # Clock
        self.clock = pygame.time.Clock()
        self.dt = 0
        
        # Font setup
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Joystick state
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.joystick_id = -1
        self.button_indicators: Dict[int, ButtonIndicator] = {}
        self.axis_progress_bars: Dict[int, ProgressBar] = {}
        self.hat_values = {"up": False, "down": False, "left": False, "right": False}
        
        # Statistics
        self.stats = {
            "total_inputs": 0,
            "session_start": datetime.now(),
            "button_presses": defaultdict(int),
            "max_axis_values": defaultdict(float),
        }
        
        # UI Components
        self.setup_ui()
        
        # Tabs
        self.current_tab = "overview"
        self.tabs = ["overview", "buttons", "axes", "stats", "help"]
        
        # Messages
        self.messages: List[Tuple[str, float]] = []
        
        # Auto-detect joystick
        self.auto_detect_joystick()
        
    def setup_ui(self):
        """Initialize UI components"""
        # Tab buttons
        tab_y = 70
        tab_height = 40
        tab_width = 120
        tab_spacing = 10
        start_x = 20
        
        self.tab_buttons = {}
        for i, tab in enumerate(self.tabs):
            x = start_x + i * (tab_width + tab_spacing)
            btn = Button(x, tab_y, tab_width, tab_height, tab.upper())
            self.tab_buttons[tab] = btn
            
        # Refresh button
        self.refresh_btn = Button(self.WIDTH - 150, tab_y, 130, tab_height, "REFRESH")
        
        # Overview page components
        self.overview_components = self.create_overview_components()
        
    def create_overview_components(self) -> Dict[str, Any]:
        """Create components for overview tab"""
        components = {}
        
        # Main joystick visualizers (center)
        components["left_stick"] = JoystickVisualizer(400, 350, 70)
        components["right_stick"] = JoystickVisualizer(700, 350, 70)
        components["dpad"] = DPadVisualizer(550, 500, 90)
        
        # Triggers
        components["lt_trigger"] = TriggerVisualizer(250, 200, 40, 120, "LT")
        components["rt_trigger"] = TriggerVisualizer(850, 200, 40, 120, "RT")
        
        # Face buttons (ABXY arrangement)
        btn_size = 50
        spacing = 60
        bx, by = 950, 320
        components["btn_a"] = ButtonIndicator(bx, by + spacing, btn_size, btn_size, "A")
        components["btn_b"] = ButtonIndicator(bx + spacing, by + spacing//2, btn_size, btn_size, "B")
        components["btn_x"] = ButtonIndicator(bx - spacing, by + spacing//2, btn_size, btn_size, "X")
        components["btn_y"] = ButtonIndicator(bx, by, btn_size, btn_size, "Y")
        
        # Shoulder buttons
        components["btn_lb"] = ButtonIndicator(300, 180, 70, 35, "LB")
        components["btn_rb"] = ButtonIndicator(800, 180, 70, 35, "RB")
        
        # Center buttons
        components["btn_back"] = ButtonIndicator(480, 420, 50, 30, "BACK")
        components["btn_start"] = ButtonIndicator(620, 420, 50, 30, "START")
        components["btn_guide"] = ButtonIndicator(550, 420, 50, 30, "HOME")
        
        return components
        
    def auto_detect_joystick(self):
        """Auto-detect and initialize joystick"""
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.joystick_id = self.joystick.get_instance_id()
            self.add_message(f"Detected: {self.joystick.get_name()}", 3.0)
            self.setup_button_indicators()
        else:
            self.add_message("No controller detected. Connect one and press REFRESH", 5.0)
            
    def setup_button_indicators(self):
        """Setup button indicators based on detected joystick"""
        if not self.joystick:
            return
            
        num_buttons = self.joystick.get_numbuttons()
        
        # Create indicators for all buttons
        cols = 8
        rows = (num_buttons + cols - 1) // cols
        start_x = 50
        start_y = 150
        btn_width = 100
        btn_height = 35
        spacing_x = 10
        spacing_y = 10
        
        for i in range(num_buttons):
            col = i % cols
            row = i // cols
            x = start_x + col * (btn_width + spacing_x)
            y = start_y + row * (btn_height + spacing_y)
            
            label = STANDARD_BUTTON_NAMES.get(i, f"Btn {i}")
            self.button_indicators[i] = ButtonIndicator(x, y, btn_width, btn_height, label)
            
        # Setup axis progress bars
        num_axes = self.joystick.get_numaxes()
        for i in range(num_axes):
            self.axis_progress_bars[i] = ProgressBar(50, 150 + (i * 40), 300, 25, 
                                                     COLORS.accent_primary)
                                                     
    def add_message(self, message: str, duration: float = 2.0):
        """Add a temporary message"""
        self.messages.append((message, duration))
        
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            # Handle tab switching
            for tab, btn in self.tab_buttons.items():
                if btn.handle_event(event):
                    self.current_tab = tab
                    
            # Handle refresh
            if self.refresh_btn.handle_event(event):
                self.refresh_joystick()
                
            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                self.WIDTH = event.w
                self.HEIGHT = event.h
                self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
                
        return True
        
    def refresh_joystick(self):
        """Re-initialize joystick detection"""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        self.joystick = None
        self.button_indicators.clear()
        self.axis_progress_bars.clear()
        
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.joystick_id = self.joystick.get_instance_id()
            self.add_message(f"Connected: {self.joystick.get_name()}", 3.0)
            self.setup_button_indicators()
        else:
            self.add_message("No controller found", 3.0)
            
    def update(self):
        """Update game state"""
        # Update delta time
        self.dt = self.clock.tick(60) / 1000.0
        
        # Update messages
        for i in range(len(self.messages) - 1, -1, -1):
            msg, duration = self.messages[i]
            self.messages[i] = (msg, duration - self.dt)
            if self.messages[i][1] <= 0:
                self.messages.pop(i)
                
        # Update tab buttons
        for btn in self.tab_buttons.values():
            btn.update(self.dt)
        self.refresh_btn.update(self.dt)
        
        # Update joystick state
        if self.joystick:
            self.update_joystick_state()
            
        # Update UI components based on current tab
        if self.current_tab == "overview":
            self.update_overview_components()
            
    def update_joystick_state(self):
        """Read and process joystick input"""
        # Buttons
        for i in range(self.joystick.get_numbuttons()):
            pressed = self.joystick.get_button(i) > 0.5
            if i in self.button_indicators:
                self.button_indicators[i].update(pressed, self.dt)
                if pressed:
                    self.stats["total_inputs"] += 1
                    self.stats["button_presses"][i] += 1
                    
        # Axes
        for i in range(self.joystick.get_numaxes()):
            value = self.joystick.get_axis(i)
            abs_value = abs(value)
            
            # Track max values
            if abs_value > self.stats["max_axis_values"][i]:
                self.stats["max_axis_values"][i] = abs_value
                
            if abs_value > 0.1:  # Deadzone threshold
                self.stats["total_inputs"] += 1
                
            if i in self.axis_progress_bars:
                # Normalize for display (convert -1..1 to 0..1)
                normalized = (value + 1) / 2
                self.axis_progress_bars[i].update(normalized, self.dt)
                
        # Hat (D-Pad)
        if self.joystick.get_numhats() > 0:
            hat = self.joystick.get_hat(0)
            self.hat_values["up"] = hat[1] > 0
            self.hat_values["down"] = hat[1] < 0
            self.hat_values["left"] = hat[0] < 0
            self.hat_values["right"] = hat[0] > 0
            
            if any(self.hat_values.values()):
                self.stats["total_inputs"] += 1
                
    def update_overview_components(self):
        """Update overview visualization components"""
        if not self.joystick:
            return
            
        # Update sticks
        if self.joystick.get_numaxes() >= 2:
            lx = self.joystick.get_axis(0)
            ly = self.joystick.get_axis(1)
            self.overview_components["left_stick"].update(lx, ly, self.dt)
            
        if self.joystick.get_numaxes() >= 4:
            rx = self.joystick.get_axis(2)
            ry = self.joystick.get_axis(3)
            self.overview_components["right_stick"].update(rx, ry, self.dt)
            
        # Update triggers
        if self.joystick.get_numaxes() >= 5:
            lt = self.joystick.get_axis(4)
            # Some controllers use 0..1, others -1..1
            lt_normalized = (lt + 1) / 2 if lt < 0 else lt
            self.overview_components["lt_trigger"].update(lt_normalized, self.dt)
            
        if self.joystick.get_numaxes() >= 6:
            rt = self.joystick.get_axis(5)
            rt_normalized = (rt + 1) / 2 if rt < 0 else rt
            self.overview_components["rt_trigger"].update(rt_normalized, self.dt)
            
        # Update D-Pad
        self.overview_components["dpad"].update(
            self.hat_values["up"],
            self.hat_values["down"],
            self.hat_values["left"],
            self.hat_values["right"]
        )
        
        # Update face buttons (standard Xbox mapping)
        button_mapping = {
            "btn_a": 0,
            "btn_b": 1,
            "btn_x": 2,
            "btn_y": 3,
            "btn_lb": 4,
            "btn_rb": 5,
            "btn_back": 6,
            "btn_start": 7,
            "btn_guide": 8,
        }
        
        for comp_name, btn_id in button_mapping.items():
            if comp_name in self.overview_components and btn_id < self.joystick.get_numbuttons():
                pressed = self.joystick.get_button(btn_id) > 0.5
                self.overview_components[comp_name].update(pressed, self.dt)
                
    def draw(self):
        """Render everything"""
        # Clear screen
        self.screen.fill(COLORS.bg_primary)
        
        # Draw header
        self.draw_header()
        
        # Draw current tab
        if self.current_tab == "overview":
            self.draw_overview()
        elif self.current_tab == "buttons":
            self.draw_buttons_tab()
        elif self.current_tab == "axes":
            self.draw_axes_tab()
        elif self.current_tab == "stats":
            self.draw_stats_tab()
        elif self.current_tab == "help":
            self.draw_help_tab()
            
        # Draw messages
        self.draw_messages()
        
        # Update display
        pygame.display.flip()
        
    def draw_header(self):
        """Draw header section"""
        # Title
        title = self.font_large.render("SACT", True, COLORS.accent_primary)
        subtitle = self.font_small.render("Stupid Ass Controller Test", True, COLORS.text_secondary)
        self.screen.blit(title, (20, 15))
        self.screen.blit(subtitle, (20, 55))
        
        # Joystick info
        if self.joystick:
            name = self.joystick.get_name()
            axes = self.joystick.get_numaxes()
            buttons = self.joystick.get_numbuttons()
            hats = self.joystick.get_numhats()
            balls = self.joystick.get_numballs()
            
            info_text = f"{name} | Axes: {axes} | Buttons: {buttons} | Hats: {hats}"
            if balls > 0:
                info_text += f" | Balls: {balls}"
                
            info = self.font_small.render(info_text, True, COLORS.accent_success)
            self.screen.blit(info, (20, 85))
        else:
            no_device = self.font_small.render("NO CONTROLLER DETECTED", True, COLORS.accent_error)
            self.screen.blit(no_device, (20, 85))
            
        # Draw tabs
        for tab, btn in self.tab_buttons.items():
            if tab == self.current_tab:
                # Highlight active tab
                highlight_rect = pygame.Rect(btn.rect.x - 2, btn.rect.y - 2,
                                            btn.rect.width + 4, btn.rect.height + 4)
                RoundedRectangle.draw(self.screen, COLORS.accent_primary, highlight_rect, radius=10)
            btn.draw(self.screen)
            
        # Refresh button
        self.refresh_btn.draw(self.screen)
        
    def draw_overview(self):
        """Draw overview tab"""
        if not self.joystick:
            # Show placeholder
            placeholder = self.font_medium.render("Connect a controller to see visualization", 
                                                  True, COLORS.text_muted)
            rect = placeholder.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(placeholder, rect)
            return
            
        # Draw all overview components
        for component in self.overview_components.values():
            component.draw(self.screen)
            
        # Draw connection lines for visual flair
        if self.joystick.get_numaxes() >= 2:
            # Line from left stick to triggers
            pass  # Could add decorative lines here
            
    def draw_buttons_tab(self):
        """Draw detailed buttons tab"""
        if not self.joystick:
            self.draw_no_controller_message()
            return
            
        # Title
        title = self.font_medium.render("BUTTON MAPPING", True, COLORS.text_primary)
        self.screen.blit(title, (50, 120))
        
        # Draw all button indicators
        for btn in self.button_indicators.values():
            btn.draw(self.screen)
            
        # Legend
        legend_y = self.HEIGHT - 60
        legend = self.font_small.render("Green = Pressed | Blue = Recently Released | Gray = Inactive", 
                                        True, COLORS.text_secondary)
        self.screen.blit(legend, (50, legend_y))
        
    def draw_axes_tab(self):
        """Draw detailed axes tab"""
        if not self.joystick:
            self.draw_no_controller_message()
            return
            
        # Title
        title = self.font_medium.render("AXIS VALUES", True, COLORS.text_primary)
        self.screen.blit(title, (50, 120))
        
        # Draw axis information
        y_offset = 160
        for i in range(self.joystick.get_numaxes()):
            # Axis name
            axis_name = STANDARD_AXIS_NAMES.get(i, f"Axis {i}")
            name_text = self.font_small.render(f"{axis_name}:", True, COLORS.text_primary)
            self.screen.blit(name_text, (50, y_offset))
            
            # Current value
            value = self.joystick.get_axis(i)
            value_text = self.font_small.render(f"{value:+.4f}", True, COLORS.accent_primary)
            self.screen.blit(value_text, (250, y_offset))
            
            # Progress bar
            if i in self.axis_progress_bars:
                self.axis_progress_bars[i].draw(self.screen)
                
            # Max value
            max_val = self.stats["max_axis_values"].get(i, 0)
            max_text = self.font_tiny.render(f"Max: {max_val:.4f}", True, COLORS.text_muted)
            self.screen.blit(max_text, (380, y_offset + 5))
            
            y_offset += 45
            
        # Raw values table
        table_x = 500
        table_y = 160
        raw_title = self.font_small.render("RAW AXIS DATA", True, COLORS.text_secondary)
        self.screen.blit(raw_title, (table_x, table_y))
        
        # Draw grid
        grid_y = table_y + 30
        for i in range(self.joystick.get_numaxes()):
            value = self.joystick.get_axis(i)
            row_text = self.font_tiny.render(f"A{i}: {value:+.6f}", True, COLORS.text_muted)
            self.screen.blit(row_text, (table_x, grid_y))
            grid_y += 25
            
    def draw_stats_tab(self):
        """Draw statistics tab"""
        # Title
        title = self.font_medium.render("INPUT STATISTICS", True, COLORS.text_primary)
        self.screen.blit(title, (50, 120))
        
        # Session info
        session_duration = datetime.now() - self.stats["session_start"]
        duration_str = str(session_duration).split('.')[0]  # Remove microseconds
        
        stats = [
            f"Session Duration: {duration_str}",
            f"Total Input Events: {self.stats['total_inputs']}",
            f"Buttons Available: {len(self.button_indicators)}",
            f"Axes Available: {len(self.axis_progress_bars)}",
        ]
        
        y_offset = 170
        for stat in stats:
            text = self.font_small.render(stat, True, COLORS.text_secondary)
            self.screen.blit(text, (50, y_offset))
            y_offset += 35
            
        # Button press counts
        if self.stats["button_presses"]:
            presses_title = self.font_small.render("BUTTON PRESS COUNTS", True, COLORS.text_primary)
            self.screen.blit(presses_title, (50, y_offset + 20))
            y_offset += 55
            
            sorted_presses = sorted(self.stats["button_presses"].items(), 
                                   key=lambda x: x[1], reverse=True)
            
            for btn_id, count in sorted_presses[:15]:  # Show top 15
                btn_name = STANDARD_BUTTON_NAMES.get(btn_id, f"Button {btn_id}")
                press_text = self.font_tiny.render(f"{btn_name}: {count:,} presses", 
                                                   True, COLORS.text_muted)
                self.screen.blit(press_text, (50, y_offset))
                y_offset += 25
                
        # Axis max values
        if self.stats["max_axis_values"]:
            axes_title = self.font_small.render("MAXIMUM AXIS VALUES", True, COLORS.text_primary)
            self.screen.blit(axes_title, (450, 170))
            
            y_offset = 205
            for axis_id, max_val in sorted(self.stats["max_axis_values"].items()):
                axis_name = STANDARD_AXIS_NAMES.get(axis_id, f"Axis {axis_id}")
                axis_text = self.font_tiny.render(f"{axis_name}: {max_val:.4f}", 
                                                  True, COLORS.text_muted)
                self.screen.blit(axis_text, (450, y_offset))
                y_offset += 25
                
    def draw_help_tab(self):
        """Draw help/instructions tab"""
        # Title
        title = self.font_medium.render("HELP & INSTRUCTIONS", True, COLORS.text_primary)
        self.screen.blit(title, (50, 120))
        
        help_text = [
            "OVERVIEW TAB:",
            "  - Visual representation of your controller",
            "  - Shows sticks, triggers, buttons, and D-pad",
            "  - Real-time feedback on all inputs",
            "",
            "BUTTONS TAB:",
            "  - Detailed view of all button states",
            "  - Shows button ID numbers and names",
            "  - Tracks total presses per button",
            "",
            "AXES TAB:",
            "  - Real-time axis value display",
            "  - Shows both normalized and raw values",
            "  - Tracks maximum values reached",
            "",
            "STATS TAB:",
            "  - Session statistics and input counts",
            "  - Most-used buttons analysis",
            "  - Technical controller information",
            "",
            "TIPS:",
            "  - Press REFRESH if you connect/disconnect a controller",
            "  - All values update at 60 FPS for smooth visualization",
            "  - Deadzone threshold is set to 0.1 for axis inputs",
            "",
            "CONTROLLER SUPPORT:",
            "  - Works with any SDL2-compatible gamepad",
            "  - Xbox, PlayStation, Nintendo, and generic controllers",
            "  - Supports up to 32+ buttons and multiple axes",
        ]
        
        y_offset = 170
        for line in help_text:
            if line.endswith(":"):
                color = COLORS.accent_primary
                font = self.font_small
            elif line == "":
                y_offset += 10
                continue
            else:
                color = COLORS.text_secondary
                font = self.font_tiny
                
            text = font.render(line, True, color)
            self.screen.blit(text, (50, y_offset))
            y_offset += 28
            
    def draw_no_controller_message(self):
        """Draw 'no controller' placeholder"""
        msg = self.font_medium.render("NO CONTROLLER DETECTED - PRESS REFRESH", 
                                      True, COLORS.accent_error)
        rect = msg.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
        self.screen.blit(msg, rect)
        
    def draw_messages(self):
        """Draw temporary messages"""
        y_offset = self.HEIGHT - 40
        for msg, duration in self.messages:
            if duration > 0.5:
                alpha = 255
            else:
                alpha = int(255 * (duration / 0.5))
                
            # Create surface with alpha
            surf = pygame.Surface((self.WIDTH, 30), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*COLORS.bg_secondary, 200), 
                           (0, 0, self.WIDTH, 30), border_radius=5)
            
            text = self.font_small.render(msg, True, COLORS.text_primary)
            text_rect = text.get_rect(center=(self.WIDTH // 2, 15))
            surf.blit(text, text_rect)
            
            self.screen.blit(surf, (0, y_offset))
            y_offset -= 35
            
    def run(self):
        """Main application loop"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            
        pygame.quit()
        sys.exit()


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Application entry point"""
    print("=" * 60)
    print("SACT - Stupid Ass Controller Test")
    print("=" * 60)
    print("\nStarting application...")
    print("Make sure your controller is connected before launching.")
    print("Press ESC or close the window to exit.\n")
    
    try:
        app = SACTApplication()
        app.run()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure pygame is installed: pip install pygame")
        print("2. Connect your controller before running")
        print("3. Try running with sudo if on Linux")
        print("4. Check that SDL2 is properly installed\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
