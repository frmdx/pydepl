import json
import logging
import os
import yaml
from yaml.loader import SafeLoader
from typing import Union, TextIO
from .depl_types import Any, Dict, List, OptDict, Optional
from .task import Task, TaskResult, TaskType
from functools import partial
logger = logging.getLogger(__name__)

# Hardcoded!!!
yaml_open_func = partial(yaml.load, Loader=SafeLoader)


class SimplePipeline:

    @classmethod
    def from_file(cls, file_name: str = None, file_data: Union[str, TextIO] = None, file_type: str = None, encoding="utf8") -> "SimplePipeline":
        if not file_name and not file_data:
            raise ValueError(f"Please provide a file_name or file_data value")
        data = file_data
        open_file_func = None

        if not file_type and file_name:
            file_type = file_name.split('.')[-1]
            print(f"No file_type provided it is interpreted as {file_type=}")
        file_type = file_type.lower()
        # print(f"{file_type=}")
        if file_type == "json":
            open_file_func = json.load
        elif file_type in ["yaml", "yml"]:
            file_type = "yaml"  # force yml type to yaml
            open_file_func = yaml_open_func
        if not open_file_func:
            raise Exception(f"Cannot find open function")
        if not data:
            with open(file_name, 'r') as fin:
                data = open_file_func(fin)
        elif isinstance(data, str):
            if file_type == "json":
                data = json.loads(data)
            elif file_type == "yaml":
                data = yaml_open_func(data)
            else:
                raise ValueError(f"Invalid {file_type=} for data")
        if data:
            pipeline_version = data.get('version', 1)
            pipeline_context = data.get('context')
            pipeline_task_list = data.get('task_list', [])
            task_list = []
            for o in pipeline_task_list:
                # print(f"[DEBUG] {o=}")
                res = Task.from_data(
                    data=o, data_type=file_type, parse_context=pipeline_context)
                if res:
                    task_list.append(res)
                else:
                    print(f"Error cannot create task from json_object: {o}")
            return SimplePipeline(task_list=task_list, version=pipeline_version, context=pipeline_context)
        raise Exception(f"Cannot read from {file_name=}")

    def __init__(self, task_list: Optional[List[Task]] = None, version: int = 1, context: OptDict = None):
        self._task_list = task_list or []
        self._res_map = {}
        self.version = version
        self._context = context.copy() if context else {}

    @property
    def raw_context(self):
        return self._context.copy()

    @property
    def context(self):
        ctx = self.raw_context
        for key, value in ctx.items():
            if value.startswith('$'):
                ctx[key] = os.environ.get(value[1:])
        return ctx

    def run(self, exit_on_error: bool = False) -> Dict[str, Any]:
        print(f"Running Pipeline with {self.context=}")
        res = None
        for t in self._task_list:
            try:
                if t.is_dry:
                    # print(f"DryRun!!\n{t.formatted_cmd(with_context=self.context)=}")
                    # print(f"{t.get_parsed_cmd_args()=}")
                    logger.info(
                        f"DryRun, {t.formatted_cmd(with_context=self.context)=}")
                else:
                    res = t.run(override_cmds=self.context)
                    if not res:
                        logger.warning(f"Task {t} has not produced result")
                        continue
                    # print(f"{res=}")
                    if res.is_invoke_result and res.is_ok:
                        logger.info(f"[Ok] {res.stdout=}")
                    if t.task_type == TaskType.SHELLOUT:
                        logger.debug(f"[SHELLOUT] {res.get_out_var_dict()=}")
                        self._context.update(**res.get_out_var_dict())
            except Exception as e:
                print(f"got Exception {e} for {t=}")
                if exit_on_error:
                    break
            else:
                self._res_map[t.name] = res
        return self._res_map

    @ property
    def task_number(self) -> int:
        return len(self._task_list)

    @ property
    def task_list(self) -> List[Task]:
        return self._task_list
