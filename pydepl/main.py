from __future__ import annotations

import argparse
import json
import logging
import os
import os.path
from typing import Any, Callable, Dict, List, Optional, Union

from fabric import Connection, Result

# make it work when pydepl is not installed and is not in PYTHONPATH
try:
    import pydepl
except ImportError:
    import sys
    pydepl_root = os.path.join(os.path.dirname(__file__), os.path.pardir)
    sys.path.insert(0, pydepl_root)
from pydepl.depl_types import OptDict
from pydepl.pipeline import SimplePipeline

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
log_format = logging.Formatter("[{levelname} - {asctime}]: {msg}", style="{")
out_handler = logging.StreamHandler()
out_handler.setFormatter(log_format)
logger.addHandler(out_handler)

HOST_MAP = {'localhost': 'localhost'}
DEFAULT_HOST = 'localhost'

# types
# OptDict = Optional[Dict[str, Any]]
ArgParser = argparse.ArgumentParser
Args = argparse.Namespace


def read_pipeline(filename: str = "pipeline.json", base_dir: str = None):
    pass


def get_repo_archive(conn: Connection, base_dir: str, dirlist: List[str] = None, dest_dir: str = None, archive_file_name: str = None,
                     archive_file_clb: Callable[[Any], str] = None, callable_args: Optional[Dict[str, Any]] = None):
    if not archive_file_name and not archive_file_clb:
        raise Exception(f"You must provide a file_name or file_name callable")
    callable_args = callable_args or {}
    file_name = archive_file_name or archive_file_clb(**callable_args)
    dirlist = " ".join(str(l) for l in dirlist or ["."])
    tar_cmd = f"tar -C {base_dir} --exclude=__pycache__ --exclude=*.pyc --exclude=data/ -zcvf {file_name} {dirlist}"
    print(f"would execute:\n{tar_cmd}")
    return None


def get_host_info(conn: Connection, is_local: bool = False) -> Result:
    res = None
    if conn:
        run_cmd = conn.run if not is_local else conn.local
        res = run_cmd('uname -a', hide="stdout")
    return res


def parse_args(initial_args: OptDict = None, prog_name: str = None, description: str = None) -> Args:
    initial_args = initial_args or {}
    args: Args = Args(**initial_args)
    p: ArgParser = ArgParser(prog=prog_name, description=description)
    p.add_argument("-p", "--pipeline", help="pipeline file")
    res = p.parse_args(namespace=args)
    return res


def run_main():

    args = parse_args()
    pipeline_file = args.pipeline
    if not pipeline_file:
        print(f"You must provide a pipeline file")
        return 1
    if not os.path.isfile(pipeline_file):
        raise OSError(f"Cannot read pipeline file: {pipeline_file}")
    p: SimplePipeline = SimplePipeline.from_file(file_name=pipeline_file)
    print(f"Found {p.task_number} tasks in {pipeline_file}")
    p.run()
    # for t in p.task_list:
    #     print(f"Running Task {t}:")
    #     if t.is_dry:
    #         print(f"DryRun!!\n{t.formatted_cmd()=}")
    #         print(f"{t.get_parsed_cmd_args()=}")
    #     else:
    #         res = t.run()
    #         print(f"{res=}")
    # host_w = HOST_MAP[DEFAULT_HOST]
    # c: Connection = Connection(host_w)
    # res: Result = get_host_info(conn=c, is_local=host_w == DEFAULT_HOST)
    # print(f"{res.command=} executed on {c.host} has result {res.ok}")
    # res2 = get_repo_archive(conn=c, base_dir="$HOME", archive_file_name="dest.tar.gz")
    # simple_task = Task(name="simple_task", cmd="uname -r", host=DEFAULT_HOST)
    # res = simple_task.run()
    # print(f"Simple Task result: {res}")


if __name__ == "__main__":
    run_main()
