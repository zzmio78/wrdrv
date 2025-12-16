import subprocess
from enum import Enum

class InterfaceMode(str, Enum):
    MONITOR = "monitor"
    MANAGED = "managed"


class InterfaceAction(str, Enum):
    UP = "up"
    DOWN = "down"

class InterfaceManagement:
    """
    Provides low-level control over a wireless network interface.

    This class manages both the operational state (UP/DOWN) and the
    operating mode (managed/monitor) of a network interface using
    standard Linux networking tools (`ip`, `iw`)

    Responsibilities:
        - Bring the interface link state up or down
        - Switch interface mode between managed and monitor
    """

    def __init__(self, interface: str):
        self._interface = interface

    def _get_phy(self) -> str:
        """
        Gets the physical device name (phy0, phy1) needed to re-create the interface.
        """
        try:
            cmd = ['iw', self._interface, 'info']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            for line in result.stdout.splitlines():
                if 'wiphy' in line:
                    idx = line.split()[-1]
                    return f"phy{idx}"
            raise ValueError("No wiphy index found in iw info")

        except subprocess.CalledProcessError:
            raise ValueError(f"Interface {self._interface} not found or 'iw' command failed.")

    def _set_interface_mode(self, mode: InterfaceMode):
        """
        Reliably switches mode by deleting the interface and re-creating it.
        """
        try:
            phy = self._get_phy()
            mode_str = mode.value

            subprocess.run(['ip', 'link', 'set', self._interface, InterfaceAction.DOWN],
                           check=False, capture_output=True)
            subprocess.run(['iw', 'dev', self._interface, 'del'],
                           check=True, capture_output=True)
            subprocess.run(
                ['iw', 'phy', phy, 'interface', 'add', self._interface, 'type', mode_str],
                check=True, capture_output=True
            )
            self.up()

        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode().strip() if e.stderr else "Unknown error"
            raise RuntimeError(f"Failed to set {mode_str} mode: {err_msg}")

    def down(self):
        """
        Bring the network interface down.
        """
        subprocess.run(['ip', 'link', 'set', self._interface, InterfaceAction.DOWN], check=True)

    def up(self):
        """
        Bring the network interface up.
        """
        subprocess.run(['ip', 'link', 'set', self._interface, InterfaceAction.UP], check=True)

    def monitor(self):
        """
        Switch the interface to monitor mode using `iw`.
        """
        return self._set_interface_mode(InterfaceMode.MONITOR)

    def managed(self):
        """
        Switch the interface to managed mode using `iw`.
        """
        return self._set_interface_mode(InterfaceMode.MANAGED)

__all__ = ["InterfaceManagement"]