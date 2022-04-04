#!/bin/bash

#
# ./make_netcdf.sh YYYYmmdd
#


netcdf_path="/home/users/earjham/bin/writing_netcdf/test_nc_files"
filepath_trt0="/home/users/earjham/data/ncas-radar-wind-profiler-1/TRT/TRT0"
filepath_trt1="/home/users/earjham/data/ncas-radar-wind-profiler-1/TRT/TRT1"
logfilepath="/home/users/earjham/nrwp1logs"

conda activate netcdf_create

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

datadate=$1

year=${datadate:0:4}
month=${datadate:4:2}
day=${datadata:6:2}


# month needs to be alpha-numeric-ised (I'm going with it)

case $month in
  10)
    anmonth=a
  ;;
  11)
    anmonth=b
  ;;
  12)
    anmonth=c
  ;;
  *)
    anmonth=${month:1:1}
  ;;
esac


trt0_files=$(ls ${filepath_trt0}/${year}/${month}/${year}${anmonth}${day}.TRT/*)
no_trt0_files=$(ls ${filepath_trt0}/${year}/${month}/${year}${anmonth}${day}.TRT/* | wc -l)
trt1_files=$(ls ${filepath_trt1}/${year}/${month}/${year}${anmonth}${day}.TRT/*)
no_trt1_files=$(ls ${filepath_trt1}/${year}/${month}/${year}${anmonth}${day}.TRT/* | wc -l)

python ${SCRIPT_DIR}/../ncas_radar_wind_profiler_1/core/wind_profiler_netcdf.py ${trt0_files} -o ${netcdf_path}
python ${SCRIPT_DIR}/../ncas_radar_wind_profiler_1/core/wind_profiler_netcdf.py ${trt1_files} -o ${netcdf_path}


if [ -f ${netcdf_path}/ncas-radar-wind-profiler-1_cdao_${year}${month}${day}_snr-winds_low-mode_*.nc ]
then 
  low_file_exists=True
else
  low_file_exists=False
fi

if [ -f ${netcdf_path}/ncas-radar-wind-profiler-1_cdao_${year}${month}${day}_snr-winds_high-mode_*.nc ]
then 
  high_file_exists=True
else
  high_file_exists=False
fi



cat << EOF | sed -e 's/#.*//; s/  *$//' > ${logfilepath}/${year}${month}${day}.txt
Date: $(date -u)
Number of trt0 files: ${no_trt0_files}
Number of trt1 files: ${no_trt1_files}
low-mode file created: ${low_file_exists}
high-mode file created: ${high_file_exists}
EOF
