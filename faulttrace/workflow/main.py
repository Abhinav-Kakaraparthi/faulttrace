import os
from pathlib import Path

from .api import create_app
from .storage import DEFAULT_DATA

# Optional fresh local run; the default historical data directory is unchanged.
app = create_app(directory=Path(os.environ.get('FAULTTRACE_DATA_DIR', str(DEFAULT_DATA))))
