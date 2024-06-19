import datetime
import os
from collections.abc import KeysView, Sequence
from typing import Any, Literal, NoReturn, Type, TypedDict, overload

import cftime  # type: ignore
import numpy as np
import numpy.typing as npt
from typing_extensions import Buffer, LiteralString, Self, TypeAlias

# fmt: off
Datatype: TypeAlias = Literal[
    "S1", "c",       # NC_CHAR
    "i1", "b", "B",  # NC_BYTE
    "u1",            # NC_UBYTE
    "i2", "h", "s",  # NC_SHORT
    "u2",            # NC_USHORT
    "i4", "i", "l",  # NC_INT
    "u4",            # NC_UINT
    "i8",            # NC_INT64
    "u8",            # NC_UINT64
    "f4", "f",       # NC_FLOAT
    "f8", "d",       # NC_DOUBLE
]
"""Valid datatype specifiers"""
# fmt: on

Compression: TypeAlias = Literal[
    "zlib",
    "szip",
    "zstd",
    "blosc_lz",
    "blosc_lz4",
    "blosc_lz4hc",
    "blosc_zlib",
    "blosc_zstd",
]
"""Compression type"""

AccessMode: TypeAlias = Literal["r", "w", "r+", "a", "x", "rs", "ws", "r+s", "as"]
"""File access mode"""

Format: TypeAlias = Literal["NETCDF4", "NETCDF4_CLASSIC", "NETCDF3_CLASSIC", "NETCDF3_64BIT_OFFSET", "NETCDF3_64BIT_DATA"]
"""NetCDF file format"""

DiskFormat: TypeAlias = Literal["NETCDF3", "HDF5", "HDF4", "PNETCDF", "DAP2", "DAP4", "UNDEFINED"]
"""Underlying file format"""

QuantMode: TypeAlias = Literal["BitGroom", "BitRound", "GranularBitRound"]
"""Quantization algorithm"""

GetSetItemIdx: TypeAlias = (
    int
    | slice
    | ellipsis
    | list[int | bool]
    | npt.NDArray[np.integer | np.bool_]
    | tuple[int | slice | ellipsis | Sequence[int | bool] | npt.NDArray[np.integer | np.bool_], ...]
)
"""Valid 'index' type for Variable.__getitem__ or Variable.__setitem__"""

DateTimeArr: TypeAlias = npt.NDArray[np.object_]
"""numpy array of datetime.datetime or cftime.datetime"""

CfCalendar: TypeAlias = Literal[
    "standard",
    "gregorian",
    "proleptic_gregorian",
    "noleap",
    "365_day",
    "360_day",
    "julian",
    "all_leap",
    "366_day",
]
"""Calendar names usable by cftime.datetime -- defined in the CF metadata conventions"""

class BloscInfo(TypedDict):
    compressor: Literal["blosc_lz", "blosc_lz4", "blosc_lz4hc", "blosc_zlib", "blosc_zstd"]
    shuffle: Literal[0, 1, 2]

class SzipInfo(TypedDict):
    coding: Literal["nn", "ec"]
    pixels_per_block: Literal[4, 8, 16, 32]

class FiltersDict(TypedDict):
    """Dict returned from netCDF4.Variable.filters()"""

    zlib: bool
    szip: Literal[False] | SzipInfo
    zstd: bool
    bzip2: bool
    blosc: Literal[False] | BloscInfo
    shuffle: bool
    complevel: int
    fletcher32: bool

default_fillvals: dict[str, str | int | float]
"""Mapping of data types to default values to be used for _FillValue"""

__version__: str
__netcdf4libversion__: str
__hdf5libversion__: str
__has_rename_grp__: int
__has_nc_inq_path__: int
__has_nc_inq_format_extended__: int
__has_nc_open_mem__: int
__has_nc_create_mem__: int
__has_cdf5_format__: int
__has_parallel4_support__: int
__has_pnetcdf_support__: int
# __has_parallel_support__: bool
__has_quantization_support__: int
__has_zstandard_support__: int
__has_bzip2_support__: int
__has_blosc_support__: int
__has_szip_support__: int
__has_set_alignment__: int
# __has_ncfilter__: bool
is_native_little: bool
is_native_big: bool
default_encoding: str
unicode_error: str

# class NetCDF4MissingFeatureException(Exception):
#     def __init__(self, feature: str, version: str): ...

class Dataset:
    @property
    def groups(self) -> dict[str, Group]: ...
    @property
    def dimensions(self) -> dict[str, Dimension]: ...
    @property
    def variables(self) -> dict[str, Variable]: ...
    @property
    def cmptypes(self) -> dict[str, CompoundType]: ...
    @property
    def vltypes(self) -> dict[str, VLType]: ...
    @property
    def enumtypes(self) -> dict[str, EnumType]: ...
    @property
    def data_model(self) -> Format: ...
    @property
    def file_format(self) -> Format: ...
    @property
    def disk_format(self) -> DiskFormat: ...
    @property
    def parent(self) -> Dataset | None: ...
    @property
    def path(self) -> str: ...
    @property
    def keepweakref(self) -> bool: ...
    @property
    def _ncstring_attrs__(self) -> bool: ...
    @property
    def __orthogonal_indexing__(self) -> Literal[True]: ...
    def __init__(
        self,
        filename: str | os.PathLike,
        mode: AccessMode = "r",
        clobber: bool = True,
        format: Format = "NETCDF4",
        diskless: bool = False,
        persist: bool = False,
        keepweakref: bool = False,
        memory: Buffer | int | None = None,
        encoding: str | None = None,
        parallel: bool = False,
        comm=None,
        info=None,
        # auto_complex: bool = False,
        **kwargs,
    ): ...
    def filepath(self, encoding: str | None = None) -> str: ...
    def isopen(self) -> bool: ...
    def close(self) -> memoryview | None: ...
    def sync(self) -> None: ...
    def set_fill_on(self) -> None: ...
    def set_fill_off(self) -> None: ...
    def createDimension(self, dimname: str, size: int | None = None) -> Dimension: ...
    def renameDimension(self, oldname: str, newname: str) -> None: ...
    def createCompoundType(self, datatype: np.dtype | list[tuple[str, npt.DTypeLike]], datatype_name: str) -> CompoundType: ...
    def createVLType(self, datatype: npt.DTypeLike, datatype_name: str) -> VLType: ...
    def createEnumType(
        self, datatype: np.dtype[np.integer] | Type[np.integer], datatype_name: str, enum_dict: dict[str, int]
    ) -> EnumType: ...
    def createVariable(
        self,
        varname: str,
        datatype: Datatype | npt.DTypeLike | str | CompoundType | VLType,
        dimensions: tuple[str, ...] | tuple[Dimension, ...] | str | Dimension = (),
        compression: Compression | None = None,
        zlib: bool = False,
        complevel: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9] = 4,
        shuffle: bool = True,
        szip_coding: Literal["nn", "ec"] = "nn",
        szip_pixels_per_block: Literal[4, 8, 16, 32] = 8,
        blosc_shuffle: Literal[0, 1, 2] = 1,
        fletcher32: bool = False,
        contiguous: bool = False,
        chunksizes: tuple[int, ...] | None = None,
        endian: Literal["native", "little", "big"] = "native",
        least_significant_digit: int | None = None,
        significant_digits: int | None = None,
        quantize_mode: QuantMode = "BitGroom",
        fill_value: Any | None = None,  # should be instance of `datatype`
        chunk_cache: int | None = None,
    ) -> Variable: ...
    def renameVariable(self, oldname: str, newname: str) -> None: ...
    def createGroup(self, groupname: str) -> Group: ...
    def ncattrs(self) -> list[str]: ...
    def setncattr_string(self, name: str, value) -> None: ...
    def setncattr(self, name: str, value: Any) -> None: ...
    def setncatts(self, attdict: dict[str, Any]) -> None: ...
    def getncattr(self, name: str, encoding: str = "utf-8") -> Any: ...
    def delncattr(self, name: str) -> None: ...
    def renameAttribute(self, oldname: str, newname: str) -> None: ...
    def renameGroup(self, oldname: str, newname: str) -> None: ...
    def set_auto_chartostring(self, value: bool) -> None: ...
    def set_auto_maskandscale(self, value: bool) -> None: ...
    def set_auto_mask(self, value: bool) -> None: ...
    def set_auto_scale(self, value: bool) -> None: ...
    def set_always_mask(self, value: bool) -> None: ...
    def set_ncstring_attrs(self, value: bool) -> None: ...
    def get_variables_by_attributes(self, **kwargs) -> list[Variable]: ...
    @property
    def name(self) -> str: ...
    @staticmethod
    def fromcdl(
        cdlfilename: str,
        ncfilename: str | None = None,
        mode: AccessMode = "a",
        format: Format = "NETCDF4",
    ) -> Dataset: ...
    def tocdl(self, coordvars: bool = False, data: bool = False, outfile: str | os.PathLike | None = None) -> None | str: ...
    def has_blosc_filter(self) -> bool: ...
    def has_zstd_filter(self) -> bool: ...
    def has_bzip2_filter(self) -> bool: ...
    def has_szip_filter(self) -> bool: ...
    def __setattr__(self, name: str, value) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __delattr__(self, name: str) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, atype, value, traceback) -> bool: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> NoReturn: ...

class Group(Dataset):
    def __init__(self, parent: Group | Dataset, name: str, **kwargs): ...
    def close(self) -> NoReturn: ...

class Dimension:
    def __init__(self, grp: Group | Dataset, name: str, size: int | None = None, **kwargs): ...
    @property
    def name(self) -> str: ...
    @property
    def size(self) -> int: ...
    def group(self) -> Group | Dataset: ...
    def isunlimited(self) -> bool: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> NoReturn: ...

class Variable:
    @property
    def dimensions(self) -> tuple[str, ...]: ...
    @property
    def dtype(self) -> np.dtype | Type[str]: ...
    @property
    def ndim(self) -> int: ...
    @property
    def shape(self) -> tuple[int, ...]: ...
    @property
    def scale(self) -> bool: ...
    @property
    def mask(self) -> bool: ...
    @property
    def chartostring(self) -> bool: ...
    @property
    def always_mask(self) -> bool: ...
    def __init__(
        self,
        grp: Group,
        name: str,
        datatype: Datatype | npt.DTypeLike | str | CompoundType | VLType,
        dimensions: tuple[str, ...] | tuple[Dimension, ...] | str | Dimension = (),
        compression: Compression | None = None,
        zlib: bool = False,
        complevel: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9] = 4,
        shuffle: bool = True,
        szip_coding: Literal["nn", "ec"] = "nn",
        szip_pixels_per_block: Literal[4, 8, 16, 32] = 8,
        blosc_shuffle: Literal[0, 1, 2] = 1,
        fletcher32: bool = False,
        contiguous: bool = False,
        chunksizes: tuple[int, ...] | None = None,
        endian: Literal["native", "little", "big"] = "native",
        least_significant_digit: int | None = None,
        significant_digits: int | None = None,
        quantize_mode: QuantMode = "BitGroom",
        fill_value: Any | None = None,  # should be instance of `datatype`
        chunk_cache: int | None = None,
        **kwargs,
    ): ...
    def group(self) -> Group | Dataset: ...
    def ncattrs(self) -> list[str]: ...
    def setncattr(self, name: str, value) -> None: ...
    def setncattr_string(self, name: str, value: Any) -> None: ...
    def setncatts(self, attdict: dict[str, Any]) -> None: ...
    def getncattr(self, name: str, encoding: str = "utf-8") -> Any: ...
    def delncattr(self, name: str) -> None: ...
    def filters(self) -> FiltersDict: ...
    def quantization(self) -> tuple[int, QuantMode] | None: ...
    def endian(self) -> str: ...
    def chunking(self) -> Literal["contiguous"] | list[int]: ...
    def get_var_chunk_cache(self) -> tuple[int, int, float]: ...
    def set_var_chunk_cache(
        self,
        size: int | None = None,
        nelems: int | None = None,
        preemption: float | None = None,
    ) -> None: ...
    def renameAttribute(self, oldname: str, newname: str) -> None: ...
    def assignValue(self, val: Any) -> None: ...
    def getValue(self) -> Any: ...
    def set_auto_chartostring(self, chartostring: bool) -> None: ...
    def use_nc_get_vars(self, use_nc_get_vars: bool) -> None: ...
    def set_auto_maskandscale(self, maskandscale: bool) -> None: ...
    def set_auto_scale(self, scale: bool) -> None: ...
    def set_auto_mask(self, mask: bool) -> None: ...
    def set_always_mask(self, always_mask: bool) -> None: ...
    def set_ncstring_attrs(self, ncstring_attrs: bool) -> None: ...
    def set_collective(self, value: bool) -> None: ...
    def get_dims(self) -> tuple[Dimension, ...]: ...
    @property
    def name(self) -> str: ...
    @property
    def datatype(self) -> np.dtype | CompoundType | VLType | EnumType: ...
    @property
    def size(self) -> int: ...
    @property
    def __orthogonal_indexing__(self) -> Literal[True]: ...
    def __setitem__(self, elem: GetSetItemIdx, data: Any): ...
    def __len__(self) -> int: ...
    def __array__(self) -> npt.ArrayLike: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __delattr__(self, name: str): ...
    def __setattr__(self, name: str, value): ...
    def __getattr__(self, name: str): ...
    def __getitem__(self, elem: GetSetItemIdx) -> int | float | str | np.ndarray | np.void: ...  # np.void for scalar cmptype
    def __reduce__(self) -> NoReturn: ...

class CompoundType:
    @property
    def dtype(self) -> np.dtype: ...
    @property
    def name(self) -> str: ...
    @property
    def dtype_view(self) -> np.dtype: ...
    def __init__(self, grp: Group | Dataset, datatype: np.dtype | list[tuple[str, npt.DTypeLike]], dtype_name: str, **kwargs): ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> NoReturn: ...

class VLType:
    @property
    def dtype(self) -> np.dtype | Type[str]: ...
    @property
    def name(self) -> str: ...
    def __init__(self, grp: Group | Dataset, datatype: npt.DTypeLike, dtype_name: str, **kwargs): ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> NoReturn: ...

class EnumType:
    @property
    def dtype(self) -> np.dtype: ...
    @property
    def name(self) -> str: ...
    @property
    def enum_dict(self) -> dict[str, int]: ...
    def __init__(
        self,
        grp: Group | Dataset,
        datatype: np.dtype[np.integer] | Type[np.integer],
        dtype_name: str,
        enum_dict: dict[str, int],
        **kwargs,
    ): ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> NoReturn: ...

class MFDataset(Dataset):
    def __init__(
        self,
        files: str | list[str | os.PathLike],
        check: bool = False,
        aggdim: str | None = None,
        exclude: list[str] = [],
        master_file: str | os.PathLike | None = None,
    ): ...
    def __setattr__(self, name: str, value: Any): ...
    def __getattribute__(self, name: str) -> Any: ...
    def ncattrs(self) -> KeysView[str]: ...  # type: ignore  # (LSP violation)
    def close(self): ...
    def isopen(self) -> bool: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> NoReturn: ...
    # dimensions, variables come from __getattribute__
    @property
    def dimensions(self) -> dict[str, _Dimension]: ...  # type: ignore  # (LSP violation)
    @property
    def variables(self) -> dict[str, _Variable]: ...  # type: ignore  # (LSP violation)

class _Dimension:
    def __init__(self, dimname: str, dim: Dimension, dimlens: list[int], dimtotlen: int): ...
    def __len__(self) -> int: ...
    def isunlimited(self) -> bool: ...
    def __repr__(self) -> str: ...

class _Variable:
    def __init__(self, dset: Dataset, varname: str, var: Variable, recdimname: str): ...
    def __getattr__(self, name: str) -> Any: ...
    def __repr__(self) -> str: ...
    def __len__(self) -> int: ...
    def __getitem__(self, elem: GetSetItemIdx) -> int | float | str | np.ndarray | np.void: ...
    def typecode(self) -> np.dtype | Type[str]: ...  # type of Variable.dtype
    def ncattrs(self) -> KeysView[str]: ...
    # shape, ndim, and name actually come from __getattr__
    @property
    def shape(self) -> tuple[int, ...]: ...
    @property
    def ndim(self) -> int: ...
    @property
    def name(self) -> str: ...
    def set_auto_chartostring(self, val: bool): ...
    def set_auto_maskandscale(self, val: bool): ...
    def set_auto_mask(self, val: bool): ...
    def set_auto_scale(self, val: bool): ...
    def set_always_mask(self, val: bool): ...

class MFTime(_Variable):
    def __init__(
        self,
        time: Variable,
        units: str | None = None,
        calendar: CfCalendar | None = None,
    ): ...
    # __getitem__() has same signature as a _Variable

@overload
def stringtoarr(
    string: str,
    NUMCHARS: int,
    dtype: Literal["S"] = "S",
) -> npt.NDArray[np.bytes_]: ...
@overload
def stringtoarr(
    string: str,
    NUMCHARS: int,
    dtype: Literal["U"],
) -> npt.NDArray[np.str_]: ...
@overload
def stringtochar(
    a: npt.NDArray[np.character],
    encoding: Literal["none", "None", "bytes"],
) -> npt.NDArray[np.bytes_]: ...
@overload
def stringtochar(
    a: npt.NDArray[np.character],
    encoding: LiteralString = "utf-8",  # anything that's not 'none', 'None', or 'bytes'
) -> npt.NDArray[np.str_]: ...
@overload
def stringtochar(
    a: npt.NDArray[np.character],
    encoding: str = ...,
) -> npt.NDArray[np.str_ | np.bytes_]: ...
@overload
def chartostring(
    b: npt.NDArray[np.character],
    encoding: Literal["none", "None", "bytes"] = ...,
) -> npt.NDArray[np.bytes_]: ...
@overload
def chartostring(
    b: npt.NDArray[np.character],
    encoding: LiteralString = "utf-8",  # anything that's not 'none', 'None', or 'bytes'
) -> npt.NDArray[np.str_]: ...
@overload
def chartostring(
    b: npt.NDArray[np.character],
    encoding: str = ...,
) -> npt.NDArray[np.str_ | np.bytes_]: ...
def getlibversion() -> str: ...
def set_alignment(threshold: int, alignment: int): ...
def get_alignment() -> tuple[int, int]: ...
def set_chunk_cache(size: int | None = None, nelems: int | None = None, preemption: float | None = None): ...
def get_chunk_cache() -> tuple[int, int, float]: ...

# date2index, date2num, and num2date are actually provided by cftime and if stubs for
# cftime are completed these should be removed.
def date2index(
    dates: (datetime.datetime | cftime.datetime | Sequence[datetime.datetime | cftime.datetime] | DateTimeArr),
    nctime: Variable,
    calendar: CfCalendar | None = None,
    select: Literal["exact", "before", "after", "nearest"] = "exact",
    has_year_zero: bool | None = None,
) -> int | npt.NDArray[np.int_]: ...
def date2num(
    dates: (datetime.datetime | cftime.datetime | Sequence[datetime.datetime | cftime.datetime] | DateTimeArr),
    units: str,
    calendar: CfCalendar | None = None,
    has_year_zero: bool | None = None,
    longdouble: bool = False,
) -> np.number | npt.NDArray[np.number]: ...
def num2date(
    times: Sequence[int | float | np.number] | npt.NDArray[np.number],
    units: str,
    calendar: CfCalendar = "standard",
    only_use_cftime_datetimes: bool = True,
    only_use_python_datetimes: bool = False,
    has_year_zero: bool | None = None,
) -> datetime.datetime | DateTimeArr: ...
