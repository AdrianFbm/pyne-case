import asyncio
import threading

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
)

_session: ClientSession | None = None
_loop: asyncio.AbstractEventLoop | None = None
_ready = threading.Event()


async def _run_session():
    """Open the MCP session and keep it alive until the process exits."""
    global _session
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            _session = session
            _ready.set()               # signal: session is ready
            await asyncio.Event().wait()  # hold the context managers open forever


def _start_background_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(_run_session())


# Start the background thread immediately on import
_thread = threading.Thread(target=_start_background_loop, daemon=True)
_thread.start()
_ready.wait()  # block until the session is initialized


def get_session() -> ClientSession:
    """Return the live MCP session."""
    return _session


def mcp_run(coro):
    """Submit an async MCP coroutine from sync code and wait for the result."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()
