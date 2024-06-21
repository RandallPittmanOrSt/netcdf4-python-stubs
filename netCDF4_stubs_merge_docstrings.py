"""netCDF4_stubs_merge_docstrings.py

This script is provided as part of the netCDF4-stubs package to add docstrings from the currently-installed netCDF4 package to the
type stubs so that they are available statically at runtime. This script requires libcst 1.1.0 or later to run.

If this script is run with argument "test", a file test_netCDF4.pyi will be output in the current directory rather than modifying
the type stubs file.
"""

import json
import shutil
import sys
import textwrap
from pathlib import Path
from types import ModuleType
from typing import Dict, Union

try:
    import libcst as cst
    import libcst._version
    import netCDF4
    from libcst.metadata import MetadataWrapper, PositionProvider
except ImportError:
    print("libcst and netCDF4 are required to run this script.", file=sys.stderr)
    sys.exit(1)
if libcst._version.__version_tuple__ < (1, 1, 0):
    print("libcst 1.1.0 or later is required", file=sys.stderr)
    sys.exit(1)

STUBS_DIR = Path(__file__).resolve().parent / "netCDF4-stubs"


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
        # strip trailing '.' if attrname is empty
        key = ".".join([module.__name__, membername, attrname]).strip(".")
        docs_dict[key] = docstring


def get_module_docstrings(module: ModuleType) -> Dict[str, str]:
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
        """e.g. module_name.MyClass.some_method"""
        return ".".join(self.stack)

    @property
    def body_indent(self) -> str:
        """The indent whitespace of a class or function body."""
        return " " * 4 * (len(self.stack) - 1)

    def on_visit(self, node: cst.CSTNode) -> bool:
        if isinstance(node, (cst.ClassDef, cst.FunctionDef)):
            self.stack.append(node.name.value)
        return super().on_visit(node)

    def on_leave(
        self, original_node: cst.CSTNode, updated_node: cst.CSTNode
    ) -> Union[cst.CSTNode, cst.RemovalSentinel, cst.FlattenSentinel]:
        if isinstance(updated_node, (cst.Module, cst.ClassDef, cst.FunctionDef)):
            retval = self._add_docstring_to_modclsfun(updated_node)
            self.stack.pop()
            return retval
        return updated_node

    def _indent_docstring(self, docstring: str) -> str:
        lines = docstring.strip().splitlines()
        if len(lines) <= 1:
            return lines[0] if lines else ""
        indented_body = textwrap.indent(textwrap.dedent("\n".join(lines[1:])), self.body_indent)
        return "\n".join([lines[0], indented_body])

    def _add_docstring_to_modclsfun(
        self,
        node: Union[cst.Module, cst.ClassDef, cst.FunctionDef],
        override_existing=False,
    ) -> Union[cst.Module, cst.ClassDef, cst.FunctionDef]:
        """Add a docstring (if there is one) to a class or function node.

        If there is an Ellipse for the class/function body it will be removed

        Parameters
        ----------
        node
            libcst ClassDef or FunctionDef node
        override_existing
            If there is already a docstring present and override_existing it False
            (default), do not replace it.

        Returns
        -------
        node
            The updated node
        """
        if (self.has_docstring(node) and not override_existing) or not (docstring := self._docstrings.get(self.dotted_stack, "")):
            return node
        docstring = self._indent_docstring(docstring)
        docstring_node = cst.SimpleStatementLine(body=[cst.Expr(cst.SimpleString(f'"""{docstring}"""'))])
        # If the first thing in it's an ellipsis, replace it in the series of statements.
        # Otherwise, prepend to the statements.
        statements = node.body if isinstance(node, cst.Module) else node.body.body
        if isinstance(expr := statements[0], cst.Expr) and isinstance(expr.value, cst.Ellipsis):
            new_statement_body = [docstring_node, *statements[1:]]
        else:
            new_statement_body = [docstring_node, *statements]
        # If it's a Module, there's no wrapper around the statements so we just update
        # the module with the new statements and return that.
        if isinstance(node, cst.Module):
            return node.with_changes(body=new_statement_body)
        # If the class/function body is on the same line as the parameters, replace it
        # with an IndentedBlock
        if isinstance(node.body, cst.SimpleStatementSuite):
            statements_wrapper = cst.IndentedBlock(body=new_statement_body)
        else:
            statements_wrapper = node.body.with_changes(body=new_statement_body)
        return node.with_changes(body=statements_wrapper)

    def has_docstring(self, node: Union[cst.Module, cst.ClassDef, cst.FunctionDef]):
        statements = node.body.body if isinstance(node.body, cst.BaseSuite) else node.body
        if not statements:
            return False
        first_statement = statements[0]
        if isinstance(first_statement, cst.SimpleStatementLine) and isinstance(first_statement.body[0], cst.Expr):
            expr = first_statement.body[0].value
            if isinstance(expr, cst.SimpleString):
                return True
        return False


def add_docstrings(docstrings: Dict[str, str], module_name: str, pyi_file):
    """Add docstrings to a type stub file"""
    tree = cst.parse_module(Path(pyi_file).read_text())
    wrapper = MetadataWrapper(tree)
    transformer = AddDocstrings(module_name, docstrings)
    modified_tree = wrapper.visit(transformer)
    Path(pyi_file).write_text(modified_tree.code)


def get_and_save_doctrings():
    """Get docstrings from a module and save them as JSON"""
    pyx_docstrings = get_module_docstrings(netCDF4._netCDF4)
    docstrings_path = (
        Path(__file__).parent / "docstrings" / f"netCDF4._netCDF4.{netCDF4.__version__}_docstrings.json"  # type: ignore
    )
    with open(docstrings_path, "w") as fobj:
        json.dump(pyx_docstrings, fobj, indent="  ")


def load_docstrings(netCDF4_version: str) -> Dict[str, str]:
    """Load docstrings from JSON"""
    docstrings_path = Path(__file__).parent / "docstrings" / f"netCDF4._netCDF4.{netCDF4_version}_docstrings.json"
    with open(docstrings_path, "r") as fobj:
        return json.load(fobj)


def merge_docstrings(test=True):
    pyx_docstrings = get_module_docstrings(netCDF4._netCDF4)
    pyi_file = STUBS_DIR / "_netCDF4.pyi"
    if test:
        outfile = "test_netCDF4.pyi"
        shutil.copyfile(pyi_file, outfile)
        pyi_file = outfile
    add_docstrings(pyx_docstrings, "netCDF4._netCDF4", pyi_file)


def cli():
    merge_docstrings("test" in sys.argv)


if __name__ == "__main__":
    cli()
