"""Module to import optional dependencies.

Source: Taken from pandas/compat/_optional.pysample.df
"""

from __future__ import annotations

import importlib
import sys
import warnings
from typing import TYPE_CHECKING, List

import matplotlib.pyplot as plt
import numpy as np
from pandas.util.version import Version
import io
import traceback
import re

import pandas as pd
WHITELISTED_BUILTINS = [
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "bytearray",
    "bytes",
    "callable",
    "chr",
    "classmethod",
    "complex",
    "delattr",
    "dict",
    "dir",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "getattr",
    "hasattr",
    "hash",
    "help",
    "hex",
    "id",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "locals",
    "map",
    "max",
    "memoryview",
    "min",
    "next",
    "object",
    "oct",
    "ord",
    "pow",
    "print",
    "property",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "setattr",
    "slice",
    "sorted",
    "staticmethod",
    "str",
    "sum",
    "super",
    "tuple",
    "type",
    "vars",
    "zip",
]

if TYPE_CHECKING:
    import types

# Minimum version required for each optional dependency

VERSIONS = {
    "sklearn": "1.2.2",
    "statsmodels": "0.14.0",
    "seaborn": "0.12.2",
    "plotly": "5.14.1",
    "ggplot": "0.11.5",
    "scipy": "1.9.0",
    "streamlit": "1.23.1",
}

# A mapping from import name to package name (on PyPI) for packages where
# these two names are different.

INSTALL_MAPPING = {}


def get_version(module: types.ModuleType) -> str:
    """Get the version of a module."""
    version = getattr(module, "__version__", None)

    if version is None:
        raise ImportError(f"Can't determine version for {module.__name__}")

    return version


def get_environment(additional_deps: List[dict]) -> dict:
    """
    Returns the environment for the code to be executed.

    Returns (dict): A dictionary of environment variables
    """
    
    
    # res = {
    #     "pd": pd,
    #     "plt": plt,
    #     "np": np,
    #     **{
    #         lib["alias"]: (
    #             getattr(import_dependency(lib["module"]), lib["name"])
    #             if hasattr(import_dependency(lib["module"]), lib["name"])
    #             else import_dependency(lib["module"])
    #         )
    #         for lib in additional_deps
    #     },
    #     "__builtins__": {
    #         **{builtin: getattr(__builtins__, builtin) for builtin in WHITELISTED_BUILTINS},
    #         "__build_class__": __build_class__,
    #         "__name__": "__main__",
    #     },
    # }
    
    res = {
        "pd": pd,
        "plt": plt,
        "np": np,
        **{
            lib["alias"]: (
                getattr(import_dependency(lib["module"]), lib["name"])
                if hasattr(import_dependency(lib["module"]), lib["name"])
                else import_dependency(lib["module"])
            )
            for lib in additional_deps
        },
        "__builtins__": {
            **__builtins__,
            "__build_class__": __build_class__,
            "__name__": "__main__",
        },
    }
    # print('bug get2')
    return res


def import_dependency(
    name: str,
    extra: str = "",
    errors: str = "raise",
    min_version: str | None = None,
):
    """
    Import an optional dependency.

    By default, if a dependency is missing an ImportError with a nice
    message will be raised. If a dependency is present, but too old,
    we raise.

    Args:
        name (str): The module name.
        extra (str): An additional text to include in the ImportError message.
        errors (str): Representing an action to do when a dependency
            is not found or its version is too old.
            Possible values: "raise", "warn", "ignore":
                * raise : Raise an ImportError
                * warn : Only applicable when a module's version is too old.
                  Warns that the version is too old and returns None
                * ignore: If the module is not installed, return None, otherwise,
                  return the module, even if the version is too old.
                  It's expected that users validate the version locally when
                  using ``errors="ignore"`` (see. ``io/html.py``)
        min_version (str): Specify a minimum version that is different from
            the global pandas minimum version required. Defaults to None.

    Returns:
         Optional[module]:
            The imported module, when found and the version is correct.
            None is returned when the package is not found and `errors`
            is False, or when the package's version is too old and `errors`
            is `'warn'`.
    """

    assert errors in {"warn", "raise", "ignore"}

    package_name = INSTALL_MAPPING.get(name)
    install_name = package_name if package_name is not None else name

    msg = (
        f"Missing optional dependency '{install_name}'. {extra} "
        f"Use pip or conda to install {install_name}."
    )
    try:
        module = importlib.import_module(name)
    except ImportError as exc:
        if errors == "raise":
            raise ImportError(msg) from exc
        return None

    # Handle submodules: if we have submodule, grab parent module from sys.modules
    parent = name.split(".")[0]
    if parent != name:
        install_name = parent
        module_to_get = sys.modules[install_name]
    else:
        module_to_get = module
    minimum_version = min_version if min_version is not None else VERSIONS.get(parent)
    if minimum_version:
        version = get_version(module_to_get)
        if version and Version(version) < Version(minimum_version):
            msg = (
                f"Pandas requires version '{minimum_version}' or newer of '{parent}' "
                f"(version '{version}' currently installed)."
            )
            if errors == "warn":
                warnings.warn(
                    msg,
                    UserWarning,
                )
                return None
            if errors == "raise":
                raise ImportError(msg)

    return module


def execute_code(specify_environment, code) -> Any:
    """
    Execute the python code generated by LLMs to answer the question
    about the input dataframe. Run the code in the current context and return the
    result.

    Args:
        code (str): Python code to execute.

    Returns:
        Any: The result of the code execution. The type of the result depends
            on the generated code.

    """
    
    environment: dict = get_environment([])

    for key in specify_environment:
        environment[key] = specify_environment[key]

    captured_output = io.StringIO()
    
    original_stdout = sys.stdout
    
    try:
        sys.stdout = captured_output
        exec(code, environment)

        output = captured_output.getvalue()
    finally:
        sys.stdout = original_stdout
    
    return output

def get_nth_line(input_string, n):
    lines = input_string.splitlines()
    if 1 <= n <= len(lines):
        return lines[n - 1]
    else:
        return None

def execute_code_with_exception(specify_environment, code) -> Any:
    try:
        detail_result = execute_code(specify_environment, code)
        return detail_result
    except Exception as e:
        # print(e)
        tb = traceback.format_exc()
        match = re.search(r'File "<string>", line (\d+)', tb)
        code_error_esg = ""
        if match:
            error_line = int(match.group(1))
            code_error_esg += f"Error code: {get_nth_line(code, error_line)}\nError message: {type(e).__name__}: {e}"
        else:
            code_error_esg = "No line number found in the traceback."
        return code_error_esg

    
class MyBox:
    def __init__(self, config=None):
        self.config = config
        
    def run(self, code, custom_locals={}, custom_globals={}):
        envs = {**custom_locals, **custom_globals}
        # print(envs)
        observation = execute_code_with_exception(envs, code)
        return observation
    

if __name__ == '__main__':
    df = pd.read_csv('/root/work/filestorage/Datasets/ETTh1.csv')
    code = """print(df.info())"""
    # print(getattr(__builtins__, 'print'))
    res = execute_code({'df': df}, code)
    print('res:', type(res), res, '--end--')

    # print(df.info())