# core/scan.py
import json
import os
import subprocess

from core.wireless_monitor import WirelessMonitor

def get_unique_filename(base_path: str) -> str:
    """
    If base_path exists, append _1, _2, etc. until a free filename is found.
    """
    if not os.path.exists(base_path):
        return base_path

    name, ext = os.path.splitext(base_path)
    counter = 1
    while True:
        new_path = f"{name}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def list_interfaces():
    result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
    interfaces = []
    for line in result.stdout.splitlines():
        if ': ' in line:
            iface = line.split(': ')[1].split('@')[0]
            interfaces.append(iface)
    return interfaces


def perform_scan(interface: str, bssid: str = 'None', loops: int = 1, reverse: bool = False, output: str = None) -> dict:
    monitor = WirelessMonitor(interface=interface)

    for i in range(loops):
        msg = monitor.perform_scan()
        if "[FAILURE]" in msg:
            raise RuntimeError(msg)

    results = monitor.get_results(reverse_scan=reverse)

    if output:
        output_file = get_unique_filename(output)
        with open(output_file, 'w') as f:
            json.dump({str(k): v for k, v in results.items()}, f, indent=4)

    return results
