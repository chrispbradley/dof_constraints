===============
dof_constraints
===============

Cantilever beam under gravity loading with constrained degrees of freedom 

Building the example
====================

Instructions on how to configure and build with CMake::

  git clone https://github.com/OpenCMISS-Examples/dof_constraints.git
  cd dof_constraints
  mkdir build
  cd build
  cmake -DOpenCMISS_INSTALL_ROOT=/path/to/opencmiss/install ../.
  make  # cmake --build . will also work here and is much more platform agnostic.

Running the example
===================

Explain how the example is run::

  ./src/fortran/dof_constraints.F90

or maybe it is a Python only example::

  source /path/to/opencmisslibs/install/virtaul_environments/oclibs_venv_pyXY_release/bin/activate
  python src/python/dof_constraints.py

where the XY in the path are the Python major and minor versions respectively.

Prerequisites
=============

None

License
=======

Apache 2.0 License
