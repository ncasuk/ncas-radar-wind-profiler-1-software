#!/bin/bash

# yesterday date

year=$(date --date="yesterday" +"%Y")
month=$(date --date="yesterday" +"%m")
day=$(date --date="yesterday" +"%d")

# call make_netcdf script
./make_netcdf.sh ${year}${month}${day}
