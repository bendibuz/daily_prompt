# app/services/utilities/serial_noop.py
class NoopSerialService:
    available = False

    async def open(self): pass
    async def close(self): pass
    async def blink_led(self, times: int): pass
    def on_button(self, cb): pass  # accept callback but don't wire anything