import unittest
import os
from context import SimplePipeline, Task, TaskResult
from io import StringIO


class Test_Pipeline_I(unittest.TestCase):

    def setUp(self) -> None:
        yaml_data = u"""
        version: 1
        context:
            my-host: localhost
            my-remote: neo
            destdir: $HOME
        task_list:
            - task:
                task_name: task1
                host: "{my-host}"
                type: shellout
                out_var: file_name
                cmd: echo "prova"
            - task:
                task_name: task2
                host: "{my-host}"
                type: shell
                cmd: echo "{file_name}" | tee "{file_name}".txt
            - task:
                task_name: task3
                host: "{my-remote}"
                dest: "{my-host}"
                type: scp
                cmd: '{file_name}.txt'
        """
        pipeline = SimplePipeline.from_file(file_data=StringIO(
            initial_value=yaml_data).read(), file_type="yaml")
        self.yaml_data = yaml_data
        self.pipeline = pipeline
        return super().setUp()

    def test_task_list(self):
        self.assertEqual(self.pipeline.task_number, 3)
        t: Task = self.pipeline.task_list[0]
        self.assertEqual(t.name, "task1")
        print(f"-> {self.pipeline.context=}")
        ctx = self.pipeline.context
        self.assertFalse('file_name' in ctx)
        self.assertEqual(ctx['destdir'], os.environ['HOME'])
        task_res = t.run(override_cmds=ctx)
        pipeline_res = self.pipeline.run()
        self.assertTrue('file_name' in self.pipeline.context)
        self.assertEqual(self.pipeline.context['file_name'], "prova")
        # for key, value in pipeline_res.items():
        #     print(f"[PW] {key=} {value=}")
        task2_res: TaskResult = pipeline_res['task2']
        self.assertTrue(task2_res.is_ok)
        self.assertEqual("prova", task2_res.stdout.strip())
        self.assertIsNotNone(pipeline_res.get('task3'))
        self.assertTrue(pipeline_res['task3'].is_ok)


if __name__ == "__main__":
    unittest.main()
