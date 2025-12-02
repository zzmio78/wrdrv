import argparse
import json
import os
import subprocess
import time

from commands import BaseCommand
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


class ScanCommand(BaseCommand):
    @classmethod
    def get_name(cls): return "scan"

    @classmethod
    def configure_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument('interface', nargs='?', help='Interface (Managed or Monitor mode OK)', metavar='INTERFACE',)
        parser.add_argument('-l', '--loops', type=int, default=1, help='number of scan loops to perform', metavar='LOOPS')
        parser.add_argument('-r', '--reverse', action='store_true', help='reverse output')
        parser.add_argument('-o', '--out', help='specify file to save results (default results.json)', metavar='OUTPUT')
        parser.epilog = "Example: sudo main.py scan wlan0 -l 3 -r -o results"

    def execute(self, **kwargs) -> str:
        repeats = kwargs.get('loops')
        interface = kwargs.get('interface')
        reverse = kwargs.get('reverse')
        output = kwargs.get('out')
        if interface is None:
            interfaces = ', '.join(list_interfaces())
            print(f"[ERROR] Interface is required.\nAvailable interfaces: {interfaces}")
            raise SystemExit(1)


        monitor = WirelessMonitor(interface=interface)

        print(f"[*] Starting Discovery Scan on '{interface}'")

        for i in range(repeats):
            if repeats > 1:
                print(f"    Loop {i+1}/{repeats}...")
            msg = monitor.perform_scan()

            if "[FAILURE]" in msg:
                return msg

            if i < repeats - 1:
                time.sleep(0.5)

        results = monitor.get_results(reverse_scan=reverse)

        if not results:
            return "[FAILURE] No networks found. Check interface state."

        if output:
            output = get_unique_filename(output)
            try:
                serializable_results = {
                    str(k): v for k, v in results.items()
                }
                with open(output, 'w') as f:
                    json.dump(serializable_results, f, indent=4)
                    print(f"\n[*] Results saved to '{output}'")
            except Exception as e:
                print(f"[WARNING] Failed to save JSON: {e}")

        return f"Scan complete."

