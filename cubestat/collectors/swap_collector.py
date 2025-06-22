import logging
import re
import subprocess
from typing import Any, Dict

from cubestat.collectors.base_collector import BaseCollector
from cubestat.metrics_registry import collector_registry


class SwapCollector(BaseCollector):
    """Base swap collector."""

    @classmethod
    def collector_id(cls) -> str:
        return "swap"


@collector_registry.register("darwin")
class MacOSSwapCollector(SwapCollector):
    """macOS-specific swap collector using sysctl."""

    def _parse_memstr(self, size_str: str) -> float:
        """Parse memory size string (e.g., '1.5G', '512M') to bytes."""
        match = re.match(r"(\d+(\.\d+)?)([KMG]?)", size_str)
        if not match:
            raise ValueError("Invalid memory size format")
        number_str, _, unit = match.groups()
        number = float(number_str)

        if unit == "G":
            return number * 1024 * 1024 * 1024
        elif unit == "M":
            return number * 1024 * 1024
        elif unit == "K":
            return number * 1024
        else:
            return number

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect swap usage from macOS sysctl."""
        try:
            result = subprocess.run(
                ["sysctl", "vm.swapusage"], capture_output=True, text=True, check=True
            )
            tokens = result.stdout.strip().split(" ")
            if len(tokens) < 8:
                raise IndexError("Invalid sysctl output")
            
            return {"used_bytes": self._parse_memstr(tokens[7])}
            
        except subprocess.CalledProcessError as e:
            logging.error(f"sysctl command failed: {e}")
            return {"used_bytes": 0.0}
        except (IndexError, ValueError) as e:
            logging.error(f"Invalid sysctl output: {e}")
            return {"used_bytes": 0.0}
        except Exception as e:
            logging.error(f"Unexpected error collecting swap data: {e}")
            return {"used_bytes": 0.0}


@collector_registry.register("linux")
class LinuxSwapCollector(SwapCollector):
    """Linux-specific swap collector reading /proc/meminfo."""

    def collect(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Collect swap usage from /proc/meminfo."""
        try:
            with open("/proc/meminfo", "r") as file:
                meminfo = file.readlines()

            swap_total = 0
            swap_free = 0

            for line in meminfo:
                if "SwapTotal:" in line:
                    swap_total = int(line.split()[1])
                elif "SwapFree:" in line:
                    swap_free = int(line.split()[1])

            # Convert from KB to bytes and calculate used
            used_bytes = 1024 * float(swap_total - swap_free)
            return {"used_bytes": used_bytes}
            
        except (OSError, IOError, ValueError) as e:
            logging.error(f"Error reading swap data: {e}")
            return {"used_bytes": 0.0}
        except Exception as e:
            logging.error(f"Unexpected error collecting swap data: {e}")
            return {"used_bytes": 0.0}