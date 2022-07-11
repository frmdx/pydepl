from __future__ import annotations
from typing import Union, Dict, List
from fabric import Connection, Result
from fabric.executor import invoke
from fabric.transfer import Result as ScpResult
from fabric.transfer import Transfer
from enum import Enum, unique
from .depl_types import OptDict, Any, Dict
from .depl_defaults import LOCAL_IP_ADDR, DEFAULT_HOST
from .utils import parse_variable, is_local_addr
import os
import json
import logging
import yaml
from yaml.loader import SafeLoader
from functools import partial

from string import Formatter

logger = logging.getLogger(__name__)


class TaskResult:

    def __init__(self, invoke_result: Union[Result, ScpResult], is_ok: bool = False, exception: Exception = None):
        self._invoke_result = invoke_result
        self._out_var_dict = {}
        self._scp_is_ok = is_ok
        self._scp_exception = exception
        self._scp_res = isinstance(invoke_result, ScpResult)

    @property
    def is_scp_result(self) -> bool:
        return self._scp_res

    @property
    def exited(self) -> int:
        return self._invoke_result.exited if not self.is_scp_result else -1

    @property
    def stdout(self) -> str:
        return self._invoke_result.stdout if not self.is_scp_result else ''

    @property
    def stderr(self) -> str:
        return self._invoke_result.stderr if not self.is_scp_result else (self._scp_exception if self._scp_exception else '')

    def get_out_var(self, var_name, default: None) -> str:
        return self._out_var_dict.get(var_name, default)

    @property
    def is_ok(self) -> bool:
        if self.is_scp_result:
            return self._scp_is_ok
        return self._invoke_result.ok

    @property
    def is_invoke_result(self) -> bool:
        return isinstance(self._invoke_result, Result)

    def set_out_var(self, var_name: str, value):
        self._out_var_dict[var_name] = value

    def get_out_var_dict(self) -> Dict[str, str]:
        return self._out_var_dict


@unique
class TaskType(Enum):
    SHELL = 1,
    SHELLOUT = 2,
    SCP = 3

    @classmethod
    def names(cls, to_upper: bool = True) -> List[str]:
        value_names = [e.name for e in TaskType]
        if to_upper:
            value_names = map(lambda x: x.upper(), value_names)
        return value_names

    @classmethod
    def as_dict(cls, ignore_case: bool = False) -> Dict[str, str]:
        res_dict = {}
        for item in TaskType:
            key = item.name.upper() if ignore_case else item.name
            res_dict[key] = item
        return res_dict

    @classmethod
    def from_string(cls, value: str, default_if_missing=None, ignore_case: bool = False) -> TaskType:
        enum_dict = TaskType.as_dict(ignore_case=ignore_case)
        return enum_dict.get(value.upper() if value and ignore_case else value, default_if_missing)

    def __str__(self) -> str:
        return self.name


class Task:

    @classmethod
    def from_data(cls, data: str, data_type: str = "json", parse_context: OptDict = None) -> "Task":
        load_func = None
        res = None
        if data_type == "json":
            load_func = json.loads
        elif data_type == "yaml":
            load_func = partial(yaml.load, Loader=SafeLoader)
        if not load_func:
            raise ValueError(f"Invalid {data_type=}")
        # print(f"DEBUG: before load_func {data=}")
        data = load_func(str(data))
        # print(f"DEBUG: {data=}")
        if data:
            if data_type == "yaml":
                data = data['task']
            parse_context = parse_context or {}
            task_name = data['task_name']
            task_host = parse_variable(data['host'], context=parse_context)
            task_cmd = data.get('cmd')
            task_cmd_args = data.get('context', {})
            task_options = data.get('options', {})
            task_type = data.get('type', "shell")
            task_args = {}
            for task_arg in ["out_var", "dest"]:
                task_args[task_arg] = parse_variable(
                    data.get(task_arg), context=parse_context)
            if task_cmd_args:
                for key, value in task_cmd_args.items():
                    task_cmd_args[key] = parse_variable(
                        value, context=parse_context)
            res = Task(name=task_name, cmd=task_cmd, host=task_host, cmd_args=task_cmd_args,
                       options=task_options, task_type=TaskType.from_string(value=task_type, ignore_case=True), **task_args)
        return res

    @ classmethod
    def from_json(cls, json_data: Union[str, object], parse_context: OptDict = None) -> "Task":
        res = None
        data = None
        if isinstance(json_data, str):
            data = json.loads(s=json_data)
        elif isinstance(json_data, object):
            data = json_data
        else:
            raise TypeError(
                f"[from_json] Invalid data for json_data: {type(json_data)}, expected string or json_object")
        if data:
            parse_context = parse_context or {}
            task_name = data['task_name']
            task_host = parse_variable(data['host'], context=parse_context)
            task_cmd = data.get('cmd')
            task_cmd_args = data.get('context', {})
            task_options = data.get('options', {})
            task_type = data.get('type', "shell")
            task_args = {}
            for task_arg in ["out_var", "dest"]:
                task_args[task_arg] = parse_variable(
                    data.get(task_arg), context=parse_context)
            if task_cmd_args:
                for key, value in task_cmd_args.items():
                    task_cmd_args[key] = parse_variable(
                        value, context=parse_context)
            res = Task(name=task_name, cmd=task_cmd, host=task_host, cmd_args=task_cmd_args,
                       options=task_options, task_type=TaskType.from_string(value=task_type, ignore_case=True), **task_args)
        return res

    def __init__(self, name: str, cmd: str, host: str = DEFAULT_HOST,
                 cmd_args: OptDict = None, connection_args: OptDict = None,
                 options: OptDict = None, task_type: TaskType = TaskType.SHELL, **kwargs):
        self.name = name
        self.host = host
        self.cmd = cmd
        self.cmd_args = cmd_args if cmd_args is not None else {}
        self.connection_args = connection_args or {}
        self.options = options or {}
        self.task_type = task_type
        self._parsed_cmd_args = None
        self._task_args = {}
        self._connection = None
        if kwargs:
            self._task_args.update(**kwargs)
        if self.task_type == TaskType.SHELLOUT and not self.get_task_arg('out_var'):
            raise Exception(
                f"Task of type {self.task_type} must have a \"out_var\" variable")
        if self.task_type == TaskType.SCP and not self.get_task_arg('dest'):
            raise Exception("SCP Task must have a <host,dest> pair")

    @ property
    def is_dry(self) -> bool:
        return self.options.get('dryrun', False)

    @ property
    def is_local(self) -> bool:
        # return self.host == DEFAULT_HOST
        return self.host in LOCAL_IP_ADDR

    def get_task_arg(self, arg: str, default: Any = None) -> Any:
        return self._task_args.get(arg, default)

    def get_parsed_cmd_args(self) -> Dict[str, Any]:
        if self._parsed_cmd_args:
            return [item[1] for item in self._parsed_cmd_args]
        return []

    def _get_connection(self) -> Connection:
        if not self._connection:
            self._connection = Connection(
                host=self.host, **self.connection_args)
        return self._connection

    def get_connection(self) -> Connection:
        return self._get_connection()

    def build_args(self, override_args: OptDict = None) -> Dict[str, Any]:
        cmd_args = {key: None for key in self.get_parsed_cmd_args()}
        cmd_args.update(**self.cmd_args)
        if override_args:
            cmd_args.update(**override_args)
        return cmd_args

    def build_cmd(self, override_args: OptDict = None) -> str:
        cmd_base = self.cmd
        self._parsed_cmd_args = Formatter().parse(cmd_base)
        cmd_args = self.build_args(override_args=override_args)
        cmd = cmd_base.format(**(cmd_args))
        return cmd

    def _run(self, conn: Connection, cmd: str) -> TaskResult:
        if self.is_local:
            return TaskResult(conn.local(cmd))
        else:
            return TaskResult(conn.run(cmd))

    def formatted_cmd(self, with_context: OptDict = None) -> str:
        cmd = self.build_cmd(override_args=with_context)
        return cmd

    def run(self, override_cmds: OptDict = None) -> TaskResult:
        c = self.get_connection()
        res = None
        override_cmds = override_cmds if override_cmds is not None else {}
        cmd = self.build_cmd(override_args=override_cmds)
        if self.task_type == TaskType.SCP:
            origin = self.host
            dest = self.get_task_arg('dest')
            if not is_local_addr(origin) and not is_local_addr(dest):
                raise Exception(f"scp is supported only to or from localhost")
            logger.debug(f"copying {cmd} from {self.host} to {dest}")
            b_args = self.build_args(override_args=override_cmds)
            if not self.is_dry:
                t: Transfer = Transfer(c)
                if dest == 'localhost':
                    try:
                        logger.debug(
                            f"Invoking scp task with {cmd=}(remote), local={os.path.join(b_args.get('destdir','.'),cmd)}")
                        # you can't do that, ScpResult has no ok or stderr/stdin behaviour
                        # if an Exception is raised then it will ko else consider it ok
                        scp_res = t.get(remote=cmd,
                                        local=os.path.join(b_args.get('destdir', "."), cmd))
                        res = TaskResult(invoke_result=scp_res, is_ok=True)
                    # except OSError as e:
                    #     logger.error(
                    #         f"Cannot execute task copy file {cmd} from {origin} to {dest}: {e=}")
                    except Exception as e:
                        logger.error(f"Cannot execute copy task {t}: {e=}")
                        res = TaskResult(invoke_result=scp_res,
                                         is_ok=False, exception=e)
                else:
                    try:
                        logger.info(f"Invoking scp from {self.host} to {dest}")
                        res = TaskResult(invoke_result=t.put(local=cmd,
                                                             remote=cmd))
                    except OSError as e:
                        logger.error(f"OsError while copying {cmd}: {e=}")
                    except Exception as e:
                        logger.error(f"General Error: {e=}")
            else:
                return None
        else:
            res = self._run(conn=c, cmd=cmd)
            if self.task_type == TaskType.SHELLOUT:
                res.set_out_var(var_name=self.get_task_arg(
                    'out_var'), value=res.stdout.strip())
        return res

    def __str__(self) -> str:
        return f"Task [{self.task_type}] {self.name} on {self.host}"
