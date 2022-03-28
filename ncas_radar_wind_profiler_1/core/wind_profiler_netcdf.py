"""
Create AMOF compliant netCDF file for ncas-radar-wind-profiler-1 from trw files.

"""

import sys
from pathlib import Path

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]

    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError: # Already removed
        pass

    import ncas_radar_wind_profiler_1.core
    __package__ = 'ncas_radar_wind_profiler_1.core'

from netCDF4 import Dataset

import numpy as np
import datetime as dt


from ..util import create_netcdf as create_netcdf
from ..util import add_datasets as add_datasets
from ..util import helpful_functions as hf
from . import wpufambinary_read33 as read33


    

#################################
# Set a few things here for now #
#################################

# which amof version?
amof_version = "2.0"

# These are all attributes so far
processing_software_version = 'v1.0'  # version of this code?
#processing_software_url = 'not applicable'  # for now

# hopefully I can work out how to get this from the release itself
amf_vocabularies_release = 'https://github.com/ncasuk/AMF_CVs/releases/tag/v2.0.0'

platform = 'cdao'
platform_type = 'stationary_platform'  # One of: stationary_platform, moving_platform
comment = 'None'
featureType = 'timeSeriesProfile'
processing_level = 1
location_keywords = 'Capel Dewi, Wales, UK'
project = 'Capel Dewi'  # okay, this is probably not right...
title = 'profiles of wind speeds, wind direction, snr, width and skew'

# copied straight from IDL
instrument_manufacturer = 'degreane horizon'
instrument_model = 'degrewind pcl1300'
instrument_serial_number = '02 28 01'
instrument_software = 'radtrt'
calibration_sensitivity = 'not applicable'
calibration_certification_date = 'not applicable'
calibration_certification_url = 'not applicable'


# stuff for create_netcdf.main_vX
netcdf_file_location = '/home/users/earjham/bin/writing_netcdf/test_nc_files'
instrument_name = 'ncas-radar-wind-profiler-1'
pi_scientist = {'name': 'Geraint Vaughan',
                'primary_email': 'geraint.vaughan@manchester.ac.uk',
                'orcid': 'https://orcid.org/0000-0002-0885-0398'
                }
creator_scientist = 'emily.norton@ncas.ac.uk'
dimensions_product = 'snr-winds'
variables_product = 'snr-winds'
attrs_product = 'snr-winds'
common_loc = 'land'
options = '15min'  # the high-mode or low-mode option is prepended automatically within main()
product_version = '1.0'


def main(all_trw_files, processing_software_version=processing_software_version, 
         amf_vocabularies_release=amf_vocabularies_release, platform=platform, 
         platform_type=platform_type, comment=comment, featureType=featureType, 
         processing_level=processing_level, location_keywords=location_keywords, 
         project=project, title=title, instrument_manufacturer=instrument_manufacturer, 
         instrument_model=instrument_model, instrument_serial_number=instrument_serial_number, 
         instrument_software=instrument_software, calibration_sensitivity=calibration_sensitivity, 
         calibration_certification_date=calibration_certification_date, 
         calibration_certification_url=calibration_certification_url, 
         netcdf_file_location=netcdf_file_location, instrument_name=instrument_name, 
         pi_scientist=pi_scientist, creator_scientist=creator_scientist, 
         dimensions_product=dimensions_product, variables_product=variables_product, 
         attrs_product=attrs_product, location=platform, common_loc=common_loc, 
         options=options, product_version=product_version, amof_version=amof_version):
    """
    Creates AMOF compliant netCDF file with the data from multiple trw files for ncas-radar-wind-profiler-1
    
    Args:
        all_trw_files (list): Full path names to all of the trw files from the wind profiler to be included in netCDF file. Expected structre of file name is YYmddHMM, where m and H are alpha-numeric (0-9,a-n/c).
        processing_software_version (str): Version number of the software used to process and QC the data. Global attribute for netCDF file.
        amf_vocabularies_release (str): URL to AMF Vocabularies repository. Global attribute for netCDF file.
        platform (str): Name of the platform on which the instrument was deployed. Global attribute for netCDF file.
        platform_type (str): Type of platform on which the instrument was deployed. Global attribute for netCDF file.
        comment (str): Any other text that might be useful. Use "None" if no comment needed. Global attribute for netCDF file.
        featureType (str): Feature Type of measurements (set for each instrument type). Global attribute for netCDF file.
        processing_level (int): Data product level. Possible values: 0: native, 1: basic QC, 2: high-level QC, 3: product derived from levels 1 and 2 data. Global attribute for netCDF file.
        location_keywords (str): Comma-separated words to help locate the geographical positon of the deployment site. Global attribute for netCDF file.
        project (str): Full name and acronym of the project. Global attribute for netCDF file.
        title (str): Name and general description of the data set. Global attribute for netCDF file.
        instrument_manufacturer (str): Manufacturer of instrument and key sub components. Global attribute for netCDF file.
        instrument_model (str): Model number of instrument and key sub components. Global attribute for netCDF file.
        instrument_serial_number (str): Serial number of instrument and key sub components. Global attribute for netCDF file.
        instrument_software (str): Name of the native software running the measurement. Global attribute for netCDF file.
        calibration_sensitivity (str): Calibrated sensitivity/measurement range. Global attribute for netCDF file.
        calibration_certification_date (str): Calibrated sensitivity/measurement range. Global attribute for netCDF file.
        calibration_certification_url (str): URL to calibration file or certificate. Global attribute for netCDF file.
        netcdf_file_location (str): Location where to save netCDF file to. Supplied to :py:func:`create_netcdf.main_v2`.
        instrument_name (str): Name of instrument, should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_ncas_instrument.json. Supplied to :py:func:`create_netcdf.main_v2`.
        pi_scientist (str or dict): Either the email of the project principal investigator (should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs), or a dictionary with keys name, primary_email, and orcid. Supplied to :py:func:`create_netcdf.main_v2`.
        creator_scientist (str or dict): Either the email of the creator (should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs), or a dictionary with keys name, primary_email, and orcid. Supplied to :py:func:`create_netcdf.main_v2`.
        dimensions_product (str): Name of product for product-specific dimensions. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json. Supplied to :py:func:`create_netcdf.main_v2`.
        variables_product (str): Name of product for product-specific variables. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json. Supplied to :py:func:`create_netcdf.main_v2`.
        attrs_product (str): Name of product for product-specific general attributes. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json. Supplied to :py:func:`create_netcdf.main_v2`.
        location (str): Where is the instrument (wao, cao, cdao, e.t.c.). Supplied to :py:func:`create_netcdf.main_v2`.
        common_loc (str): Location of instrument for common dimensions, variables and attributes. One of 'land', 'sea', 'air', 'trajectory'. Supplied to :py:func:`create_netcdf.main_v2`.
        options (str): Comma separated string of options for name of netCDF file. For ncas-radar-wind-profiler-1, high-mode/low-mode is determined from the file path - TRT1 is high-mode, TRT0 is low-mode - and as such does not need to be given here. Supplied to :py:func:`create_netcdf.main_v2`.
        product_version (str): Product version of data in netCDF file.
        amof_version (str): Version of AMOF convention.

    """    
    
    #################
    # Do the stuff #
    ################
    
    # Okay, really we dont want to define too much below that we can grab from data
    # we should be able to grab date and alt_length, at least
    # read in first file, that should get us some data
    first_data, _ = read33.main(all_trw_files[0])
    date = f"{first_data['year']}{hf.zero_pad_number(first_data['month'])}{hf.zero_pad_number(first_data['day'])}"
    no_heights = np.size(first_data['altitude'])  # for AMOF v1.1, this could be called no_index
    
    if 'TRT0' in all_trw_files[0]:
        mode = 'high-mode'
    elif 'TRT1' in all_trw_files[0]:
        mode = 'low-mode'
    else:
        msg = 'Unexpected mode, not sure how to cope, giving up...'
        raise ValueError(msg)
        
    # create the netcdf
    # the options used in here need to be moved somewhere more accessible
    if amof_version == "2.0":
        filename = create_netcdf.main_v2(netcdf_file_location, instrument_name, pi_scientist, creator_scientist, variables_product, platform, common_loc, date, len(all_trw_files), product_version, alt_length = no_heights, options=f'{mode},{options}', dimensions_product=dimensions_product, attrs_product=attrs_product)
    elif amof_version == "1.1":
        filename = create_netcdf.main_v1_1(netcdf_file_location, instrument_name, pi_scientist, creator_scientist, variables_product, platform, common_loc, date, len(all_trw_files), product_version, index_length = no_heights, options=f'{mode},{options}', dimensions_product=dimensions_product, attrs_product=attrs_product)
    
    # open the netcdf to append the data to
    ncfile = Dataset(filename, 'a')
    
    # also, need to add variables that don't vary with time, i.e. altitude, latitude, longitude
    # can account for them in the following loop
    
    # for the moment, I'm assuming all files are in time order. Makes my life easier
    for i,trw in enumerate(all_trw_files):
        # read trw file
        #v = 1 if i == 0 else 0
        v=0
        data, attrs = read33.main(trw, verbose=v)
        # all keys in data should match variable names in ncfile
        for data_name in data.keys():
            add_datasets.add_dataset(ncfile, data_name, data, i)
        for attr in attrs.keys():
            if ncfile.getncattr(attr) == '':
                ncfile.setncattr(attr, attrs[attr])
            elif ncfile.getncattr(attr) != attrs[attr]:
                print(f'Global attribute {attr} changes with time, i={i}')
    
                
    # sampling_interval attribute, go through all time in ncfile, take difference
                
                
    # where possible, should start to fill in the empty attributes
    # I'll leave that for another day  
    ncfile.processing_level = processing_level
    ncfile.featureType = featureType
    ncfile.platform = platform
    ncfile.platform_type = platform_type
    ncfile.comment = comment
    ncfile.instrument_manufacturer = instrument_manufacturer
    ncfile.instrument_model = instrument_model
    ncfile.instrument_serial_number = instrument_serial_number
    ncfile.instrument_software = instrument_software
    ncfile.calibration_sensitivity = calibration_sensitivity
    ncfile.calibration_certification_date = calibration_certification_date
    ncfile.calibration_certification_url = calibration_certification_url
    ncfile.location_keywords = location_keywords
    ncfile.project = project
    ncfile.processing_software_version = processing_software_version
    ncfile.amf_vocabularies_release = amf_vocabularies_release
    ncfile.title = title
    ncfile.product_version = f'v{product_version}'
    
    #ncfile.processing_software_url = 'https://www.github.com'
    #ncfile.product_version = 'v1.0'
    
    # I think this should be in the json files, but it's not, so for now...
    ncfile.institution = 'National Centre for Atmospheric Science (NCAS)'
    
                    
    # Can now add in values to time_coverage_start and time_coverage_end global attrs
    #2016-07-06T00:00:00
    first_time = ncfile['time'][0]  # should be unix time
    first_time = dt.datetime.fromtimestamp(int(first_time))
    ncfile.time_coverage_start = first_time.strftime('%Y-%m-%dT%H:%M:%S')
    last_time = ncfile['time'][-1]  # should be unix time
    last_time = dt.datetime.fromtimestamp(int(last_time))
    ncfile.time_coverage_end = last_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    
    
    
    # Check for still empty attributes
    for attr in ncfile.ncattrs():
        if ncfile.getncattr(attr) == '':
            print(f'Empty attribute: {attr}')
            
    
    ncfile.close()    
    
    # Create a new file without the empty, product-specific variables,
    # then rename the new file to remove the old file
    hf.remove_empty_whole(filename, f'{filename[:-3]}-removed.nc', 'snr-winds', verbose = 0)
    
    
    
if __name__ == "__main__":
    all_trw_files = sys.argv[1:]
    main(all_trw_files)
