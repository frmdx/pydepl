import os
from string import Formatter

from .depl_types import OptDict
from .depl_defaults import LOCAL_IP_ADDR


def parse_variable(var_name: str, context: OptDict = None) -> str:
    context = context or {}
    var_value = var_name
    if var_value:
        var_names = var_name.split(':')
        if len(var_names) > 1:
            var_context = var_names[0][1:]
            var_env_name = var_names[1][:-1]
            if var_context.lower().strip() != "env":
                raise Exception(
                    f"At the moment only env: variable context are supported, invalid context: {var_context}")
            var_value = os.environ.get(var_env_name)
        return Formatter().format(var_value, **context)
    return None


def is_local_addr(addr: str) -> bool:
    res = False
    if addr:
        res = addr.lower() in LOCAL_IP_ADDR
    return res
