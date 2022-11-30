#!/bin/bash

#
# ./make_netcdf.sh YYYYmmdd
#

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

gws_path=/gws/pw/j07/ncas_obs_vol2

netcdf_path=${gws_path}/cdao/processing/ncas-radar-wind-profiler-1/netcdf_files
filepath_trt0=${gws_path}/cdao/raw_data/ncas-radar-wind-profiler-1/incoming/TRT0
filepath_trt1=${gws_path}/cdao/raw_data/ncas-radar-wind-profiler-1/incoming/TRT1
logfilepath=${gws_path}/cdao/logs/ncas-radar-wind-profiler-1
metadata_file=${SCRIPT_DIR}/../metadata.csv


datadate=$1  # YYYYmmdd

year=${datadate:0:4}
month=${datadate:4:2}
day=${datadate:6:2}


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


trt0_files=$(ls ${filepath_trt0}/${year}/${month}/${year}${anmonth}${day}.trt/*.trw)
no_trt0_files=$(ls ${filepath_trt0}/${year}/${month}/${year}${anmonth}${day}.trt/*.trw | wc -l)
trt1_files=$(ls ${filepath_trt1}/${year}/${month}/${year}${anmonth}${day}.trt/*.trw)
no_trt1_files=$(ls ${filepath_trt1}/${year}/${month}/${year}${anmonth}${day}.trt/*.trw | wc -l)

python ${SCRIPT_DIR}/../process_wp.py ${trt0_files} -o ${netcdf_path} -t high-mode_15min -m ${metadata_file}
python ${SCRIPT_DIR}/../process_wp.py ${trt1_files} -o ${netcdf_path} -t low-mode_15min -m ${metadata_file}


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
