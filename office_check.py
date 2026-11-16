import subprocess
import sys
import time
from datetime import datetime

OFFICE_HOST = "techkraftinc.net"


def is_office_network(
    host: str = OFFICE_HOST,
    retries: int = 3,
    timeout_sec: int = 2,
    retry_delay: float = 2.0,
) -> bool:
    """Return True if the internal office host responds to ping."""
    for attempt in range(1, retries + 1):
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout_sec), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return True
        if attempt < retries:
            time.sleep(retry_delay)
    return False


def require_office_network(
    action_name: str,
    host: str = OFFICE_HOST,
    retries: int = 3,
    timeout_sec: int = 2,
    retry_delay: float = 2.0,
) -> None:
    """Exit cleanly (code 0) if not connected to the office network, unless --force is passed."""
    if "--force" in sys.argv:
        print(
            f"[{datetime.now()}] --force specified, bypassing office network check for {action_name}."
        )
        return

    if not is_office_network(
        host=host, retries=retries, timeout_sec=timeout_sec, retry_delay=retry_delay
    ):
        print(
            f"[{datetime.now()}] Outside office network ({host} unreachable) — skipping {action_name}."
        )
        sys.exit(0)

    print(
        f"[{datetime.now()}] Office network verified ({host} reachable) — proceeding with {action_name}."
    )
