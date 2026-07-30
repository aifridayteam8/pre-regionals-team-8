"""Process an unstructured incident log into the SQLite store.

Parses a file into a parent incident + child incidents and prints the tree.

Usage (run from the incidentiq/ directory):
    python scripts/process_log.py "../logs/multiple incidents 1"
    python scripts/process_log.py --all        # process every file in ../logs
"""

import sys
from pathlib import Path

# Allow running as a script from the incidentiq/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import parser, store  # noqa: E402


def process(path: Path) -> None:
    parsed = parser.parse_file(path.read_bytes(), filename=path.name)
    saved = store.save_file(parsed, filename=path.name)

    parent = store.get_incident(saved["parent_id"])
    print(f"\n=== {path.name} (format={parsed.format}) ===")
    print(
        f"PARENT {parent['incident_id']}  sev={parent['severity']}  "
        f"events={parent['event_count']}  errors={parent['error_count']}  "
        f"duration={parent['duration_s']}s  children={len(saved['child_ids'])}"
    )
    if parent.get("root_cause"):
        print(f"  root_cause: {parent['root_cause'][:100]}...")
    for child in store.get_children(saved["parent_id"]):
        print(
            f"  |- CHILD {child['incident_id']}  sev={child['severity']}  "
            f"events={child['event_count']}  errors={child['error_count']}  "
            f"| {child['title']}"
        )


def main(argv: list[str]) -> None:
    logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    if argv and argv[0] == "--all":
        for f in sorted(logs_dir.iterdir()):
            if f.is_file():
                process(f)
    else:
        target = Path(argv[0]) if argv else logs_dir / "multiple incidents 1"
        process(target)


if __name__ == "__main__":
    main(sys.argv[1:])
