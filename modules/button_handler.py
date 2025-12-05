"""
Button Handler Module
Handles physical button inputs with configurable GPIO pins.
"""

import logging
import time
from threading import Thread

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False


class ButtonHandler:
    """Manages physical button inputs"""

    def __init__(self, config, audio_player, display_manager):
        self.config = config
        self.audio_player = audio_player
        self.display_manager = display_manager
        self.logger = logging.getLogger(__name__)

        self.enabled = config.get('buttons.enabled', True)
        if not self.enabled:
            self.logger.info("Buttons disabled in config")
            return

        if not GPIO_AVAILABLE:
            self.logger.warning("RPi.GPIO not available - buttons disabled")
            self.enabled = False
            return

        # Button GPIO pins
        self.button_a = config.get('buttons.button_a', 5)
        self.button_b = config.get('buttons.button_b', 6)
        self.button_x = config.get('buttons.button_x', 16)
        self.button_y = config.get('buttons.button_y', 24)

        # Debounce time
        self.debounce_time = config.get('buttons.debounce_time', 0.02)

        # Button press tracking
        self.last_press_time = {}

        # Running state
        self.running = False
        self.button_thread = None

    def start(self):
        """Initialize and start button monitoring"""
        if not self.enabled:
            return

        try:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Setup buttons as inputs with pull-up resistors
            GPIO.setup(self.button_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.button_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.button_x, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.button_y, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Add event detection
            GPIO.add_event_detect(self.button_a, GPIO.FALLING,
                                callback=self._button_a_callback,
                                bouncetime=int(self.debounce_time * 1000))

            GPIO.add_event_detect(self.button_b, GPIO.FALLING,
                                callback=self._button_b_callback,
                                bouncetime=int(self.debounce_time * 1000))

            GPIO.add_event_detect(self.button_x, GPIO.FALLING,
                                callback=self._button_x_callback,
                                bouncetime=int(self.debounce_time * 1000))

            GPIO.add_event_detect(self.button_y, GPIO.FALLING,
                                callback=self._button_y_callback,
                                bouncetime=int(self.debounce_time * 1000))

            self.running = True
            self.logger.info("Button handler started")

        except Exception as e:
            self.logger.error(f"Error starting button handler: {e}", exc_info=True)
            self.enabled = False

    def _debounce_check(self, button_name: str) -> bool:
        """
        Check if enough time has passed since last button press

        Args:
            button_name: Name of button

        Returns:
            True if enough time passed
        """
        current_time = time.time()
        last_time = self.last_press_time.get(button_name, 0)

        if current_time - last_time < self.debounce_time:
            return False

        self.last_press_time[button_name] = current_time
        return True

    def _button_a_callback(self, channel):
        """Button A callback - Play/Pause"""
        if not self._debounce_check('A'):
            return

        self.logger.info("Button A pressed - Play/Pause")
        try:
            self.audio_player.toggle_play_pause()
        except Exception as e:
            self.logger.error(f"Error in button A callback: {e}")

    def _button_b_callback(self, channel):
        """Button B callback - Next Track"""
        if not self._debounce_check('B'):
            return

        self.logger.info("Button B pressed - Next")
        try:
            self.audio_player.next()
        except Exception as e:
            self.logger.error(f"Error in button B callback: {e}")

    def _button_x_callback(self, channel):
        """Button X callback - Previous Track"""
        if not self._debounce_check('X'):
            return

        self.logger.info("Button X pressed - Previous")
        try:
            self.audio_player.previous()
        except Exception as e:
            self.logger.error(f"Error in button X callback: {e}")

    def _button_y_callback(self, channel):
        """Button Y callback - Volume Up"""
        if not self._debounce_check('Y'):
            return

        self.logger.info("Button Y pressed - Volume Up")
        try:
            self.audio_player.volume_up(0.1)
            volume = int(self.audio_player.volume * 100)
            self.display_manager.show_message("Volume", f"{volume}%", duration=1)
        except Exception as e:
            self.logger.error(f"Error in button Y callback: {e}")

    def stop(self):
        """Stop button monitoring and cleanup GPIO"""
        if not self.enabled:
            return

        try:
            self.running = False

            if GPIO_AVAILABLE:
                GPIO.cleanup()

            self.logger.info("Button handler stopped")

        except Exception as e:
            self.logger.error(f"Error stopping button handler: {e}")


class KeyboardButtonHandler(ButtonHandler):
    """
    Alternative button handler using keyboard input for testing.
    Useful when developing without hardware.
    """

    def __init__(self, config, audio_player, display_manager):
        # Don't call super().__init__ to avoid GPIO setup
        self.config = config
        self.audio_player = audio_player
        self.display_manager = display_manager
        self.logger = logging.getLogger(__name__)

        self.enabled = True
        self.running = False
        self.input_thread = None

    def start(self):
        """Start keyboard input monitoring"""
        self.running = True
        self.input_thread = Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        self.logger.info("Keyboard button handler started")
        print("\nKeyboard Controls:")
        print("  SPACE - Play/Pause")
        print("  N     - Next track")
        print("  P     - Previous track")
        print("  +     - Volume up")
        print("  -     - Volume down")
        print("  Q     - Quit\n")

    def _input_loop(self):
        """Input loop for keyboard monitoring"""
        try:
            import sys
            import tty
            import termios

            old_settings = termios.tcgetattr(sys.stdin)

            try:
                tty.setcbreak(sys.stdin.fileno())

                while self.running:
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        char = sys.stdin.read(1)
                        self._handle_key(char)

            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        except ImportError:
            # Fallback for systems without termios (Windows)
            while self.running:
                try:
                    char = input().lower()
                    self._handle_key(char)
                except:
                    time.sleep(0.1)

    def _handle_key(self, key: str):
        """Handle keyboard input"""
        key = key.lower()

        if key == ' ':
            self.audio_player.toggle_play_pause()
        elif key == 'n':
            self.audio_player.next()
        elif key == 'p':
            self.audio_player.previous()
        elif key == '+' or key == '=':
            self.audio_player.volume_up()
        elif key == '-':
            self.audio_player.volume_down()
        elif key == 'q':
            self.running = False
            import sys
            sys.exit(0)

    def stop(self):
        """Stop keyboard handler"""
        self.running = False
        self.logger.info("Keyboard handler stopped")
