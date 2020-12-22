
from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    ext_modules=cythonize("buffer.pyx", annotate=True),
    package_dir={'geo_agent': ''},
    include_dirs=[numpy.get_include()]
)

