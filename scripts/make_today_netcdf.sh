#!/bin/bash

# today date

year=$(date +"%Y")
month=$(date +"%m")
day=$(date +"%d")

# call make_netcdf script
./make_netcdf.sh ${year}${month}${day}
