import unittest
from context import SimplePipeline
from io import StringIO


class Test_Pipeline(unittest.TestCase):

    def test_from_file_yaml(self):
        yaml_data = u"""
        version: 1
        context:
            neo-remote: neo-remote
            destdir: $HOME
        """
        yaml_file_wrapper = StringIO(initial_value=yaml_data)
        pipeline = SimplePipeline.from_file(
            file_data=yaml_file_wrapper.read(), file_type="yaml")
        self.assertEqual(pipeline.version, 1)
        self.assertEqual(pipeline.task_list, [])
        self.assertEqual(pipeline.task_number, 0)
        yaml_data = u"""
        version: 1
        context:
            my-host: localhost
            destdir: $HOME
        task_list:
            - task:
                task_name: task1
                host: "{my-host}"
                type: shellout
                out_var: file_name
                cmd: echo "prova"
        """
        pipeline = SimplePipeline.from_file(file_data=StringIO(
            initial_value=yaml_data).read(), file_type="yaml")
        self.assertEqual(pipeline.task_number, 1)


if __name__ == "__main__":
    unittest.main()
