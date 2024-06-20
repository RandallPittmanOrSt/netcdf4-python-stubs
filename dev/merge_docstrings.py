import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, TypeVar, Union

import libcst as cst
import netCDF4
from libcst.metadata import MetadataWrapper, PositionProvider

PROJROOT = Path(__file__).resolve().parent.parent


def _is_from_module(obj, modname):
    """Check that a class, function, or descriptor is part of the netCDF4._netCDF4 module"""
    if modulename := getattr(obj, "__module__", ""):  # classes and functions/methods
        return modulename == modname
    if objclass := getattr(obj, "__objclass__", ""):  # descriptors (properties etc.)
        return modname in str(objclass)
    return False


def _add_docstring(docs_dict: Dict[str, str], module: ModuleType, membername: str, attrname: str = ""):
    """If obj is a function, class, or descriptor, add its docstring to docs_dict with key obj_name"""
    obj = getattr(getattr(module, membername), attrname) if attrname else getattr(module, membername)
    if (
        # functions, classes, descriptors
        (callable(obj) or isinstance(obj, type) or hasattr(obj, "__get__"))
        and _is_from_module(obj, module.__name__)
        and (docstring := getattr(obj, "__doc__", ""))
    ):
        key = ".".join([module.__name__, membername, attrname]).strip(".")  # strips trailing '.' if attrname is empty
        docs_dict[key] = docstring


def get_docstrings(module: ModuleType) -> Dict[str, str]:
    """Get dict of docstrings for top-level classes, their members, and functions"""
    docs_dict = {}
    if mod_doc := getattr(module, "__doc__", ""):
        docs_dict[module.__name__] = mod_doc
    for membername in dir(module):
        _add_docstring(docs_dict, module, membername)
        member = getattr(module, membername)
        if isinstance(member, type):
            for attrname in dir(member):
                _add_docstring(docs_dict, module, membername, attrname)
    return docs_dict


ClsFnDefT = TypeVar("ClsFnDefT", cst.ClassDef, cst.FunctionDef)


class AddDocstrings(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, module_name: str, docstrings: Dict[str, str]):
        """Set up the transformer

        `module_name` must match the the __name__ of the module passed to get_docstrings
        """
        # stack for storing the canonical name of the current function
        self.stack: list[str] = [module_name]
        self._module_name = module_name
        self._docstrings = docstrings

    @property
    def dotted_stack(self) -> str:
        return ".".join(self.stack)

    def on_visit(self, node: cst.CSTNode) -> bool:
        if isinstance(node, (cst.ClassDef, cst.FunctionDef)):
            self.stack.append(node.name.value)
        return super().on_visit(node)

    def on_leave(
        self, original_node: cst.CSTNode, updated_node: cst.CSTNode
    ) -> Union[cst.CSTNode, cst.RemovalSentinel, cst.FlattenSentinel]:
        retval = super().on_leave(original_node, updated_node)
        if isinstance(updated_node, (cst.ClassDef, cst.FunctionDef)):
            self.stack.pop()
        return retval

    def _update_clsfndef(self, updated_node: ClsFnDefT) -> ClsFnDefT:
        if not self.has_docstring(updated_node.body.body) and (docstring := self._docstrings.get(self.dotted_stack, "")):
            new_docstring = cst.SimpleStatementLine(body=[cst.Expr(cst.SimpleString(f'"""{docstring.strip()}"""'))])
            new_body = [new_docstring] + list(updated_node.body.body)
            return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))
        return updated_node

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        return self._update_clsfndef(updated_node)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        return self._update_clsfndef(updated_node)

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        if not self.has_docstring(updated_node.body):
            new_docstring = cst.SimpleStatementLine([cst.Expr(cst.SimpleString(f'"""{self._docstrings[self._module_name]}"""'))])
            new_body = [new_docstring] + list(updated_node.body)
            return updated_node.with_changes(body=new_body)
        return updated_node

    def has_docstring(self, body):
        if not body:
            return False
        first_statement = body[0]
        if isinstance(first_statement, cst.SimpleStatementLine) and isinstance(first_statement.body[0], cst.Expr):
            expr = first_statement.body[0].value
            if isinstance(expr, cst.SimpleString):
                return True
        return False


def prep_for_docstrings(pyi_file):
    """Prepare the pyi file for merging the docstrings.

    Due to my lack of a full understanding of libcst, it doesn't work to run the
    AddDocstrings transformer on the pyi file with function signatures ending in ": ...".
    Rather, the ellipsis must be on the next line. This function makes that modification.
    """
    subprocess.run(shlex.split(f'ruff format "{pyi_file}"'), check=True)
    subprocess.run(shlex.split(f'ruff check --select I --fix "{pyi_file}"'), check=True)  # sort imports
    with open(pyi_file, "r") as pyi:
        lines = pyi.readlines()
    # Undo ruff formatting of ellipsis at the end of the line of a function or class def
    for i, line in enumerate(lines):
        lines[i] = re.sub(r"^( *)([^#].*:) \.\.\.( *(?:#.*))?$", r"\1\2\3\n\1    ...", line)
    with open(pyi_file, "w") as tmp_pyi:
        tmp_pyi.write("".join(lines))


def add_docstrings(docstrings: Dict[str, str], module_name: str, pyi_file):
    tree = cst.parse_module(Path(pyi_file).read_text())
    wrapper = MetadataWrapper(tree)
    transformer = AddDocstrings(module_name, docstrings)
    modified_tree = wrapper.visit(transformer)
    Path(pyi_file).write_text(modified_tree.code)


def post_docstrings(pyi_file):
    """Use ruff to fix formatting and remove extra ellipses (easier for me than figuring
    it out with libcst)
    """
    subprocess.run(shlex.split(f'ruff format "{pyi_file}"'), check=True)
    subprocess.run(
        shlex.split(f'ruff check --select ALL --fix-only --fixable PIE790,D209,D212 -s "{pyi_file}"'),
        check=True,
    )


def get_netCDF4_version_from_pyproject() -> str:
    section = ""
    with open(PROJROOT / "pyproject.toml") as fobj:
        for line in fobj:
            if match := re.match(r"^\[+(.+)\]+$", line):
                section = match[1]
            if section == "tool.poetry.dependencies" and (match := re.match(r'^netCDF4 = "([^"]+)"', line)):
                return match[1]
    raise RuntimeError("Couldn't get netCDF4 version from pyproject.toml")


def get_and_save_doctrings():
    pyx_docstrings = get_docstrings(netCDF4._netCDF4)
    docstrings_path = Path(__file__).parent / "docstrings" / f"netCDF4._netCDF4.{netCDF4.__version__}_docstrings.json"  # type: ignore
    with open(docstrings_path, "w") as fobj:
        json.dump(pyx_docstrings, fobj, indent="  ")


def load_docstrings(netCDF4_version):
    docstrings_path = Path(__file__).parent / "docstrings" / f"netCDF4._netCDF4.{netCDF4_version}_docstrings.json"
    with open(docstrings_path, "r") as fobj:
        return json.load(fobj)


def merge_docstrings(test=True):
    netCDF4_version = get_netCDF4_version_from_pyproject()
    pyx_docstrings = load_docstrings(netCDF4_version)
    pyi_file = PROJROOT / "netCDF4-stubs/_netCDF4.pyi"
    if test:
        outfile = PROJROOT / "test_netCDF4.pyi"
        shutil.copyfile(pyi_file, outfile)
        pyi_file = outfile
    prep_for_docstrings(pyi_file)
    add_docstrings(pyx_docstrings, "netCDF4._netCDF4", pyi_file)
    post_docstrings(pyi_file)


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        merge_docstrings("test" in sys.argv)
    elif sys.argv[1] == "save":
        get_and_save_doctrings()
