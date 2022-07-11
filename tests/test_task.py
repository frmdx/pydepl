import unittest
from unittest.mock import MagicMock
from context import TaskResult, Task


class ConnectionMock:
    def __init__(self, host, **kwargs):
        self.host = host
        for key, value in kwargs:
            setattr(self, key, value)


class Test_Task(unittest.TestCase):

    def test_task_props(self):
        t = Task(name="task1", cmd="ls")
        self.assertFalse(t.is_dry)
        self.assertTrue(t.is_local)
        t._get_connection = MagicMock()


if __name__ == "__main__":
    unittest.main()
