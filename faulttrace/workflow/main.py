import os
from pathlib import Path

from .api import create_app
profile = os.environ.get('FAULTTRACE_PROFILE')
directory = os.environ.get('FAULTTRACE_DATA_DIR')
if profile not in ('local', 'release') or not directory:
    raise ValueError('explicit_profile_and_data_directory_required')
app = create_app(directory=Path(directory), profile=profile,
                 auth_registry=os.environ.get('FAULTTRACE_AUTH_REGISTRY'))
