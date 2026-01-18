"""
Animation System for Jarvis HUD

Provides smooth animations with easing functions.
"""

import time
import math


class Easing:
    """Easing functions for smooth animations."""
    
    @staticmethod
    def linear(t):
        return t
    
    @staticmethod
    def ease_in_out(t):
        return t * t * (3 - 2 * t)
    
    @staticmethod
    def ease_out_cubic(t):
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def bounce(t):
        if t < 0.5:
            return 8 * t * t * t * t
        else:
            f = t - 1
            return 1 - 8 * f * f * f * f


class AnimatedValue:
    """Animated value that smoothly transitions between states."""
    
    def __init__(self, initial_value=0.0, duration=1.0, easing=None):
        """
        Initialize animated value.
        
        Args:
            initial_value: Starting value
            duration: Animation duration in seconds
            easing: Easing function (default: ease_in_out)
        """
        self.current = initial_value
        self.target = initial_value
        self.start_value = initial_value
        self.duration = duration
        self.easing = easing or Easing.ease_in_out
        self.start_time = None
    
    def set_target(self, target):
        """Set new target value and start animation."""
        if target != self.target:
            self.start_value = self.current
            self.target = target
            self.start_time = time.time()
    
    def update(self):
        """Update current value based on animation progress."""
        if self.start_time is None or self.current == self.target:
            return self.current
        
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        if progress >= 1.0:
            self.current = self.target
            self.start_time = None
        else:
            eased = self.easing(progress)
            self.current = self.start_value + (self.target - self.start_value) * eased
        
        return self.current
    
    def get(self):
        """Get current value."""
        return self.current


class PulseAnimation:
    """Pulsing animation for indicators."""
    
    def __init__(self, frequency=1.0, amplitude=1.0):
        """
        Initialize pulse animation.
        
        Args:
            frequency: Pulse frequency in Hz
            amplitude: Pulse amplitude (0.0 to 1.0)
        """
        self.frequency = frequency
        self.amplitude = amplitude
        self.start_time = time.time()
    
    def get(self):
        """Get current pulse value (0.0 to 1.0)."""
        elapsed = time.time() - self.start_time
        value = (math.sin(elapsed * self.frequency * 2 * math.pi) + 1) / 2
        return value * self.amplitude


class FadeAnimation:
    """Fade in/out animation."""
    
    def __init__(self, duration=0.5):
        """
        Initialize fade animation.
        
        Args:
            duration: Fade duration in seconds
        """
        self.duration = duration
        self.alpha = AnimatedValue(0.0, duration, Easing.ease_in_out)
    
    def fade_in(self):
        """Start fade in animation."""
        self.alpha.set_target(1.0)
    
    def fade_out(self):
        """Start fade out animation."""
        self.alpha.set_target(0.0)
    
    def update(self):
        """Update fade animation."""
        return self.alpha.update()
    
    def get(self):
        """Get current alpha value (0.0 to 1.0)."""
        return self.alpha.get()
