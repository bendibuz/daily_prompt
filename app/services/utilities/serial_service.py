import serial
from time import sleep

PORT = "COM3"
BAUD = 9600
TIMEOUT = 1  # seconds

class SerialService:
    def __init__(self, port: str = PORT, baud: int = BAUD, timeout: float = TIMEOUT):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser = None
        self.last_button_state = None

    def open(self):
        if self.ser and self.ser.is_open:
            return
        self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        # If your Arduino prints "READY" on boot, you can wait for it here:
        # self._wait_for_ready()
        # self.ser.reset_input_buffer()

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    # -------- PC -> Arduino helpers --------
    def _send_byte(self, b: bytes):
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial port not open")
        self.ser.write(b)

    def send_led(self, on: bool):
        """Turn the Arduino LED on/off using the existing '1'/'0' protocol."""
        self._send_byte(b'1' if on else b'0')

    def blink_led(self, n: int = 3, on_ms: float = 100, off_ms: float = 100):
        """Blink Arduino LED n times (uses the existing protocol)."""
        for _ in range(n):
            self.send_led(True)
            sleep(on_ms / 1000.0)
            self.send_led(False)
            sleep(off_ms / 1000.0)

    # -------- Arduino -> PC handling --------
    def handle_button_state(self, state: bool):
        """Called only when the button state changes."""
        if state:
            print("Button Pressed")
            # Example reaction: blink once
            self.blink_led(n=1, on_ms=100, off_ms=100)
        else:
            print("Button Released")

    def _parse_line(self, line: str):
        """Parse one text line from Arduino."""
        if line.startswith("BTN:"):
            val = line.split(":", 1)[1]
            state = (val == "1")
            if state != self.last_button_state:
                self.handle_button_state(state)
                self.last_button_state = state

    def listen(self):
        """Continuous event loop reading newline-terminated lines."""
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial port not open")
        print(f"Listening on {self.port} @ {self.baud}… (Ctrl+C to exit)")
        while True:
            line = self.ser.readline().decode(errors="ignore").strip()
            if not line:
                continue
            self._parse_line(line)

    # Optional: wait for an initial READY banner from Arduino
    def _wait_for_ready(self):
        print("Waiting for READY…")
        while True:
            line = self.ser.readline().decode(errors="ignore").strip()
            if line == "READY":
                print("READY received.")
                break

if __name__ == "__main__":
    svc = SerialService()
    try:
        svc.open()
        svc.listen()
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        svc.close()
