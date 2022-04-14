ncas-radar-wind-profiler-1-software
===================================

[![Documentation Status](https://readthedocs.org/projects/ncas-radar-wind-profiler-1-software/badge/?version=latest)](https://amof-docs-home-test.readthedocs.io/projects/ncas-radar-wind-profiler-1-software/en/latest/?badge=latest)

This repo contains code and scripts to make AMOF v2 netCDF files for the ncas-radar-wind-profiler-1 instrument from trw files.

Requirements
------------

* python 3.8 or above
* python modules:
  * netCDF4
  * numpy
  * pandas
  * requests


Installation
------------

To install, either clone the repo `git clone https://github.com/ncasuk/ncas-radar-wind-profiler-1-software.git` or download and extract a release version.

Download the required modules using `pip install -r requirements.txt`


Usage
-----

Three [scripts] are provided for easy use:
* `make_netcdf.sh` - makes netCDF file for a given date: `./make_netcdf.sh YYYYmmdd`
* `make_today_netcdf.sh` - makes netCDF file for today's data: `./make_today_netcdf.sh`
* `make_yesterday_netcdf.sh` - makes netCDF file for yesterday's data: `./make_yesterday_netcdf.sh`

Within `make_netcdf.sh`, the following may need adjusting:
* `conda activate netcdf_create`: replace `netcdf_create` with name of conda environment being used
* `netcdf_path="/gws/..."`: replace file path with where to write netCDF files
* `filepath_trt0="/gws/..."`: replace file path with path to data. The same applies to `filepath_trt1="/gws/..."`
* `logfilepath"/home/..."`: replace file path with path for where to write log files


For more detail on the actual python code, check out the [documentation].

[documentation]: https://amof-docs-home-test.readthedocs.io/projects/ncas-radar-wind-profiler-1-software/en/latest/
[scripts]: scripts
