"""Process an unstructured incident log into the SQLite store.

Usage (run from the incidentiq/ directory):
    python scripts/process_log.py ../logs/Subscription Provisioning Failed
"""

import sys
from pathlib import Path

# Allow running as a script from the incidentiq/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import parser, store  # noqa: E402


def main(path: str) -> None:
    raw = Path(path).read_bytes()
    result = parser.parse(raw, filename=Path(path).name)

    incident_id = store.save(result, filename=Path(path).name)

    print(f"Parsed {len(result.events)} events (format={result.format}) from {path}")
    print(f"Banner metadata: {result.metadata}")
    print(f"Saved as incident {incident_id}\n")

    print("Structured events:")
    for ev, det in zip(result.events, result.details):
        ts = ev.ts.isoformat() if ev.ts else "—"
        print(f"  {ev.id} {ts} {ev.severity:5} {ev.service}")
        for k, v in det.items():
            print(f"        {k}: {v}")

    inc = store.get_incident(incident_id)
    print("\nIncident summary row:")
    for k, v in inc.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "../logs/Subscription Provisioning Failed"
    main(target)
