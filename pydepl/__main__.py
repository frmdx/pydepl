import os
# make it work when pydepl is not installed and is not in PYTHONPATH
try:
    import pydepl
except ImportError:
    import sys
    pydepl_root = os.path.join(os.path.dirname(__file__), os.path.pardir)
    sys.path.insert(0, pydepl_root)

from pydepl.main import run_main

run_main()
