"""Seed the database by processing every log file in logs/ (and optionally
sample_logs/) through the real upload pipeline.

Usage (from the repo root):
    python -m backend.seed_logs            # logs/ only
    python -m backend.seed_logs --samples  # logs/ + sample_logs/
    python -m backend.seed_logs --reset    # wipe incidents first
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import create_app  # noqa: E402
from backend.database import db  # noqa: E402
from backend.models.incident import Incident, IncidentEvent  # noqa: E402
from backend.auth.decorators import get_or_create_demo_user  # noqa: E402
from backend.services.incident_service import create_incident_from_log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def seed(include_samples: bool = False, reset: bool = False) -> None:
    app = create_app()
    with app.app_context():
        if reset:
            IncidentEvent.query.delete()
            Incident.query.delete()
            db.session.commit()
            print('Cleared existing incidents and events.')

        user_id = get_or_create_demo_user().id

        directories = [ROOT / 'logs']
        if include_samples:
            directories.append(ROOT / 'sample_logs')

        for directory in directories:
            if not directory.is_dir():
                continue
            for path in sorted(directory.iterdir()):
                if not path.is_file() or path.suffix == '.md':
                    continue
                parent = create_incident_from_log(user_id, path.read_bytes(), path.name)
                print(
                    f'{parent.incident_code}  {parent.severity}  {parent.status:10}'
                    f'  events={len(parent.events):3}  children={len(parent.children)}'
                    f'  | {path.name}'
                )


if __name__ == '__main__':
    seed(
        include_samples='--samples' in sys.argv,
        reset='--reset' in sys.argv,
    )
