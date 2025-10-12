# app/services/utilities/serial_service.py
import asyncio
import json
from typing import Optional, Callable, Awaitable, Union
import serial_asyncio

PORT = "COM3"
BAUD = 9600

class LineProtocol(asyncio.Protocol):
    def __init__(self, on_line: Callable[[str], None]):
        self.on_line = on_line
        self.transport: Optional[asyncio.Transport] = None
        self._buf = bytearray()

    def connection_made(self, transport: asyncio.BaseTransport):
        self.transport = transport  # keep to write later

    def data_received(self, data: bytes):
        self._buf.extend(data)
        while True:
            nl = self._buf.find(b"\n")
            if nl == -1:
                break
            line = self._buf[:nl]
            self._buf = self._buf[nl + 1:]
            text = line.decode(errors="ignore").rstrip("\r")
            self.on_line(text)

    def connection_lost(self, exc: Optional[Exception]):
        # (optional) log/notify here
        pass


ButtonCallback = Union[Callable[[bool], None], Callable[[bool], Awaitable[None]]]

class SerialServiceAsync:
    """
    Async serial service using pyserial-asyncio:
    - Non-blocking line parsing
    - Async writes guarded by a lock
    - Convenience methods for commands/events
    """
    def __init__(self, port: str = PORT, baud: int = BAUD):
        self.port = port
        self.baud = baud
        self.transport: Optional[asyncio.Transport] = None
        self.protocol: Optional[LineProtocol] = None

        self.write_lock = asyncio.Lock()
        self.last_button_state: Optional[bool] = None

        # Event fan-out
        self.line_queue: asyncio.Queue[str] = asyncio.Queue()
        self.button_queue: asyncio.Queue[bool] = asyncio.Queue()
        self._button_cb: Optional[ButtonCallback] = None

        # Banner waiter support
        self._banner_waiters: dict[str, asyncio.Future[None]] = {}

    # ---------- lifecycle ----------
    async def open(self):
        loop = asyncio.get_running_loop()
        def _make_proto():
            return LineProtocol(self._parse_line)
        transport, protocol = await serial_asyncio.create_serial_connection(
            loop, _make_proto, self.port, self.baud
        )
        
        self.transport = transport
        self.protocol = protocol  # type: ignore[assignment]
        print(f"✅ Serial connected on {self.port} @ {self.baud}")
                # ⬇️ wait up to 3s for the Arduino banner
        try:
            await self.wait_for_banner("READY", timeout=3.0)
            print("✅ READY banner received")
        except asyncio.TimeoutError:
            print("⛔ READY not seen; continuing anyway")

    async def close(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None
            self.protocol = None
            print("Serial connection closed")

    async def reconnect(self):
        await self.close()
        await self.open()

    @property
    def connected(self) -> bool:
        return self.transport is not None

    # ---------- writes ----------
    async def _write(self, data: bytes):
        if not self.transport:
            raise RuntimeError("Serial transport not open")
        async with self.write_lock:
            self.transport.write(data)

    async def send_led(self, on: bool):
        await self._write(b'1' if on else b'0')

    async def blink_led(self, n: int = 3, on_ms: float = 100, off_ms: float = 100):
        for _ in range(n):
            await self.send_led(True)
            await asyncio.sleep(on_ms / 1000.0)
            await self.send_led(False)
            await asyncio.sleep(off_ms / 1000.0)

    async def send_line(self, text: str):
        """Send ASCII line (adds '\\n')."""
        await self._write(text.encode() + b"\n")

    async def send_bytes(self, data: bytes):
        """Send raw bytes (no newline)."""
        await self._write(data)

    async def send_json(self, obj):
        """Send JSON line (adds '\\n')."""
        payload = json.dumps(obj, separators=(",", ":"))
        await self._write(payload.encode() + b"\n")

    # ---------- reads / events ----------
    def _parse_line(self, line: str):
        # Fan-out: every line goes to the queue
        try:
            self.line_queue.put_nowait(line)
        except asyncio.QueueFull:
            pass  # or drop/resize queue

        # Banner waiters (exact match)
        fut = self._banner_waiters.get(line)
        if fut and not fut.done():
            fut.set_result(None)

        # BTN:0/1 messages
        if line.startswith("BTN:"):
            _, val = line.split(":", 1)
            state = (val == "1")
            if state != self.last_button_state:
                self.last_button_state = state
                # queue event
                try:
                    self.button_queue.put_nowait(state)
                except asyncio.QueueFull:
                    pass
                # callback (sync or async)
                if self._button_cb:
                    cb = self._button_cb
                    if asyncio.iscoroutinefunction(cb):
                        asyncio.create_task(cb(state))
                    else:
                        # run sync callback without blocking loop
                        asyncio.get_running_loop().call_soon(cb, state)

    def on_button(self, callback: ButtonCallback):
        """Register a callback invoked on BTN state change."""
        self._button_cb = callback

    async def get_last_button_state(self) -> Optional[bool]:
        return self.last_button_state

    async def wait_for_button_change(self, timeout: Optional[float] = None) -> bool:
        """Await next BTN change; returns new state."""
        return await asyncio.wait_for(self.button_queue.get(), timeout=timeout)

    async def wait_for_banner(self, text: str, timeout: Optional[float] = 5.0):
        """
        Await a specific line (e.g., 'READY') within timeout.
        Call after `open()` if your Arduino prints a boot banner.
        """
        if text not in self._banner_waiters or self._banner_waiters[text].done():
            self._banner_waiters[text] = asyncio.get_running_loop().create_future()
        await asyncio.wait_for(self._banner_waiters[text], timeout=timeout)
