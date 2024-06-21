# netCDF4-python-stubs

This is a type stub package for the Python netCDF4 package
\[[GH](https://github.com/Unidata/netcdf4-python)\]
\[[PyPI](https://pypi.org/project/netCDF4/)\].
The Unidata team is welcome to merge this into netCDF4-python if and when they see fit.

I am in no way affiliated with Unidata.

I am indebted to efforts begun by others to jump-start this project:

- Jarrod Colburn: <https://github.com/python/typing/discussions/1335>,
<https://github.com/jarrodcolburn/typeshed/tree/netcdf4/stubs/netCDF4>
- Lars Hanssen: <https://github.com/Unidata/netcdf4-python/pull/1279>,
<https://github.com/Woefie/netcdf4-python/tree/dev>

I have endeavored to match types as closely as possible to the code, e.g. using overloads
and `numpy.typing.NDArray[<numpy type>]` where possible.

I have endeavored to follow the guidance at
<https://typing.readthedocs.io/en/latest/spec/distributing.html> and
<https://typing.readthedocs.io/en/latest/source/stubs.html> as closely as possible.

When the package is installed, a script `netCDF4_stubs_merge_docstrings` is made
available installed that users can use to add docstrings from the netCDF4 runtime to
their stubs file, if so desired (for pop-up help in IDEs).
