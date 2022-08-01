from netCDF4 import Dataset
import numpy as np
import datetime as dt
import argparse
import os

import read_wp
from ncas_amof_netcdf_template import create_netcdf, util, remove_empty_variables




def get_data(trw_file):
    data, attrs = read_wp.main(trw_file, verbose=0)
    return data, attrs



def make_netcdf_snr_winds(trw_files, metadata_file = None, ncfile_location = '.', verbose = True, options = ''):
    """
    trw_files - list
    """
    all_data = {}
    all_attrs = {}
    all_unix_times = []
    all_doy = []
    all_years = []
    all_months = []
    all_days = []
    all_hours = []
    all_minutes = []
    all_seconds = []
    all_time_coverage_start_dt = []
    all_time_coverage_end_dt = []
    all_file_date = []
    
    for i in range(len(trw_files)):
        if verbose: print(f'Reading {i+1} of {len(trw_files)} files')
        data, attrs = get_data(trw_files[i])
        this_unix_times, this_doy, this_years, this_months, this_days, this_hours, this_minutes, this_seconds, this_time_coverage_start_dt, this_time_coverage_end_dt, this_file_date = util.get_times([dt.datetime.fromtimestamp(data['time'], dt.timezone.utc)])
        all_unix_times.append(this_unix_times[0])
        all_doy.append(this_doy[0])
        all_years.append(this_years[0])
        all_months.append(this_months[0])
        all_days.append(this_days[0])
        all_hours.append(this_hours[0])
        all_minutes.append(this_minutes[0])
        all_seconds.append(this_seconds[0])
        all_time_coverage_start_dt.append(this_time_coverage_start_dt)
        all_time_coverage_end_dt.append(this_time_coverage_end_dt)
        all_file_date.append(this_file_date)
        if i == 0:
            for key, value in data.items():
                if isinstance(value, np.ndarray):
                    all_data[key] = value
                else:
                    all_data[key] = [value]
            for key, value in attrs.items():
                if isinstance(value, np.ndarray):
                    all_attrs[key] = value
                else:
                    all_attrs[key] = [value]
        else:
            for key, value in data.items():
                if isinstance(value, np.ndarray):
                    all_data[key] = np.vstack((all_data[key],value))
                else:
                    all_data[key].append(value)
            for key, value in attrs.items():
                if isinstance(value, np.ndarray):
                    all_attrs[key] = np.vstack((all_attrs[key],value))
                else:
                    all_attrs[key].append(value)
                    
                    
    if len(set(all_file_date)) == 1:
        file_date = all_file_date[0]
    else:
        msg = "More than one date found in input files, quiting..."
        raise ValueError(msg)
        
    # check all altitudes are the same, and same check for lats and lons
    if not (all_data['altitude'][1:,:] == all_data['altitude'][:-1,:]).all():
        msg = "Changing altitudes, needs some manual intervention I expect"
        raise ValueError(msg)
        
    if len(set(all_data['latitude'])) != 1:
        msg = "Changing latitude"
        raise ValueError(msg)
        
    if len(set(all_data['longitude'])) != 1:
        msg = "Changing longitude"
        raise ValueError(msg)
    #
    #
    #
    
    # snr-winds has an extra time variable - time_minutes_since_start_of_day
    time_minutes_since_start_of_day = np.array(all_hours)*60 + np.array(all_minutes) + np.array(all_seconds)/60
        
    
    if verbose: print('Creating netCDF file')
    if options == '':
        create_netcdf.main('ncas-radar-wind-profiler-1', date = file_date, dimension_lengths = {'time':len(all_data['time']), 'altitude': all_data['altitude'].shape[1]}, loc = 'land', products = ['snr-winds'], file_location = ncfile_location)
    else:
        create_netcdf.main('ncas-radar-wind-profiler-1', date = file_date, dimension_lengths = {'time':len(all_data['time']), 'altitude': all_data['altitude'].shape[1]}, loc = 'land', products = ['snr-winds'], file_location = ncfile_location, options = options[:-1])
    os.rename(f'{ncfile_location}/ncas-radar-wind-profiler-1_mobile_{file_date}_snr-winds_{options}v1.0.nc',f'{ncfile_location}/ncas-radar-wind-profiler-1_cdao_{file_date}_snr-winds_{options}v1.0.nc')
    ncfile = Dataset(f'{ncfile_location}/ncas-radar-wind-profiler-1_cdao_{file_date}_snr-winds_{options}v1.0.nc', 'a')
    
    if verbose: print('Adding variable data to file')
    util.update_variable(ncfile, 'altitude', all_data['altitude'][0])
    util.update_variable(ncfile, 'latitude', all_data['latitude'][0])
    util.update_variable(ncfile, 'longitude', all_data['longitude'][0])
    util.update_variable(ncfile, 'wind_speed', all_data['wind_speed'])
    util.update_variable(ncfile, 'wind_from_direction', all_data['wind_from_direction'])
    util.update_variable(ncfile, 'eastward_wind', all_data['eastward_wind'])
    util.update_variable(ncfile, 'northward_wind', all_data['northward_wind'])
    util.update_variable(ncfile, 'upward_air_velocity', all_data['upward_air_velocity'])
    util.update_variable(ncfile, 'signal_to_noise_ratio_of_beam_1', all_data['signal_to_noise_ratio_of_beam_1'])
    util.update_variable(ncfile, 'signal_to_noise_ratio_of_beam_2', all_data['signal_to_noise_ratio_of_beam_2'])
    util.update_variable(ncfile, 'signal_to_noise_ratio_of_beam_3', all_data['signal_to_noise_ratio_of_beam_3'])
    util.update_variable(ncfile, 'signal_to_noise_ratio_minimum', all_data['signal_to_noise_ratio_minimum'])
    util.update_variable(ncfile, 'spectral_width_of_beam_1', all_data['spectral_width_of_beam_1'])
    util.update_variable(ncfile, 'spectral_width_of_beam_2', all_data['spectral_width_of_beam_2'])
    util.update_variable(ncfile, 'spectral_width_of_beam_3', all_data['spectral_width_of_beam_3'])
    util.update_variable(ncfile, 'skew_of_beam_1', all_data['skew_of_beam_1'])
    util.update_variable(ncfile, 'skew_of_beam_2', all_data['skew_of_beam_2'])
    util.update_variable(ncfile, 'skew_of_beam_3', all_data['skew_of_beam_3'])
    util.update_variable(ncfile, 'size_of_gate', all_data['size_of_gate'])
    util.update_variable(ncfile, 'qc_flag_beam_1', all_data['qc_flag_beam_1'])
    util.update_variable(ncfile, 'qc_flag_beam_2', all_data['qc_flag_beam_2'])
    util.update_variable(ncfile, 'qc_flag_beam_3', all_data['qc_flag_beam_3'])
    util.update_variable(ncfile, 'qc_flag_rain_detected', all_data['qc_flag_rain_detected'])
    util.update_variable(ncfile, 'qc_flag_wind', all_data['qc_flag_wind'])
    
    util.update_variable(ncfile, 'time', all_unix_times)
    util.update_variable(ncfile, 'year', all_years)
    util.update_variable(ncfile, 'month', all_months)
    util.update_variable(ncfile, 'day', all_days)
    util.update_variable(ncfile, 'hour', all_hours)
    util.update_variable(ncfile, 'minute', all_minutes)
    util.update_variable(ncfile, 'second', all_seconds)
    util.update_variable(ncfile, 'day_of_year', all_doy)
    
    util.update_variable(ncfile, 'time_minutes_since_start_of_day', time_minutes_since_start_of_day)
    
    
    ncfile.setncattr('time_coverage_start', dt.datetime.fromtimestamp(min(all_time_coverage_start_dt), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    ncfile.setncattr('time_coverage_end', dt.datetime.fromtimestamp(max(all_time_coverage_end_dt), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    ncfile.setncattr('platform', 'cdao')
    ncfile.setncattr('platform_altitude', all_attrs['platform_altitude'][0])
    ncfile.setncattr('geospatial_bounds', all_attrs['geospatial_bounds'][0])
    ncfile.setncattr('instrument_software_version', all_attrs['instrument_software_version'][0])
    ncfile.setncattr('averaging_interval', all_attrs['averaging_interval'][0])
    ncfile.setncattr('sampling_interval', all_attrs['sampling_interval'][0])
    
    util.add_metadata_to_netcdf(ncfile, metadata_file)
    
    ncfile.close()
    
    if verbose: print('Removing empty variables')
    remove_empty_variables.main(f'{ncfile_location}/ncas-radar-wind-profiler-1_cdao_{file_date}_snr-winds_{options}v1.0.nc', verbose = verbose, skip_check = True)
    
    
    
    
    
def main():
    import argparse
    parser = argparse.ArgumentParser(description = 'Create AMOF-compliant netCDF file for ncas-radar-wind-profiler-1 instrument.')
    parser.add_argument('input_file', nargs='*', help = 'Raw wind profiler data from instrument.')
    parser.add_argument('-v','--verbose', action='store_true', help = 'Print out additional information.', dest = 'verbose')
    parser.add_argument('-m','--metadata', type = str, help = 'csv file with global attributes and additional metadata. Default is None', dest='metadata')
    parser.add_argument('-o','--ncfile-location', type=str, help = 'Path for where to save netCDF file. Default is .', default = '.', dest="ncfile_location")
    parser.add_argument('-t','--options', type=str, help = 'Options allowed by standard in netCDF file name, e.g. "high-mode_15min".', default = '', dest="options")
    # there is only one data product at the moment - snr-winds - but this code will stay here commented out in case of future need
    #parser.add_argument('-p','--products', nargs = '*', help = 'Products of ncas-radar-wind-profiler-1 to make netCDF files for. Options are snr-winds. One or many can be given (space separated), default is "snr-winds".', default = ['snr-winds'])
    args = parser.parse_args()
    
    if args.options != '' and args.options[-1] != '_':
        options = args.options + '_'
    else:
        options = args.options
    
    # again this code is still here for any potential future use
    '''
    for prod in args.products:
        if prod == 'snr-winds':
            make_netcdf_snr_winds(args.input_file, metadata_file = args.metadata, ncfile_location = args.ncfile_location, verbose = args.verbose)
        print(f'WARNING: {prod} is not recognised for this instrument, continuing with other prodcuts...')
    '''
    make_netcdf_snr_winds(args.input_file, metadata_file = args.metadata, ncfile_location = args.ncfile_location, verbose = args.verbose, options = options)
    
    
if __name__ == "__main__":
    main()