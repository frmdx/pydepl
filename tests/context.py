# Test Context
#
# utility module to allow importing project modules from tests
try:
    import pydepl
except ImportError:
    # package not installed, add project folder to module's path
    import os.path
    import sys
    proj_dir = os.path.join(os.path.dirname(__file__), os.path.pardir)
    sys.path.insert(0, proj_dir)
from pydepl.task import Task, TaskResult, TaskType
from pydepl.pipeline import SimplePipeline
