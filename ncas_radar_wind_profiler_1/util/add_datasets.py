"""
Add datasets to netCDF file
"""

import numpy as np


def add_1d_dataset_one_file_time(ncfile, data_name, data, i):
    """
    Called by :py:func:`add_dataset`
    For a dataset that has one value per time (e.g., time), such that 
    here data is an int or float
    Takes a dataset 'data' and adds to variable 'data_name' in 'ncfile' at location 'i'.
    Updates valid_min and valid_max
    
    Args:
        ncfile (netCDF Dataset object): Name of netCDF Dataset.
        data_name (str): Name of variable in netCDF file.
        data (int or float): Data to be added to ncfile[data_name]. NOTE, this is data[data_name] from :py:func:`add_dataset`
        i (int): Time step in netCDF file where data belongs, in range (0,len(ncfile['time'])).
        
    """
    # check valid_min and valid_max exist
    if 'valid_min' in ncfile[data_name].ncattrs():
        # if valid_min and valid_max not set, then set to value of this dataset,
        # else compare and update if necessary
        if type(ncfile[data_name].valid_min) != ncfile[data_name].datatype:
            ncfile[data_name].valid_min = data
            ncfile[data_name].valid_max = data
        elif data < ncfile[data_name].valid_min:
            ncfile[data_name].valid_min = data
        elif data > ncfile[data_name].valid_max:
            ncfile[data_name].valid_max = data
    ncfile[data_name][i] = data


def add_1d_dataset_all_time_file(ncfile, data_name, data):
    """
    Called by :py:func:`add_dataset`
    For a dataset that has all the times in one file, such that 
    here data is an array
    Takes a dataset 'data' and adds to variable 'data_name' in 'ncfile' at location 'i'.
    Updates valid_min and valid_max
    
    Args:
        ncfile (netCDF Dataset object): Name of netCDF Dataset.
        data_name (str): Name of variable in netCDF file.
        data (int or float): Data to be added to ncfile[data_name]. NOTE, this is data[data_name] from :py:func:`add_dataset`
        
    """
    # check valid_min and valid_max exist
    if 'valid_min' in ncfile[data_name].ncattrs():
        # if valid_min and valid_max not set, then set to value of this dataset,
        # else compare and update if necessary
        if type(ncfile[data_name].valid_min) != ncfile[data_name].datatype:
            ncfile[data_name].valid_min = np.min(data)
            ncfile[data_name].valid_max = np.max(data)
        elif data < ncfile[data_name].valid_min:
            ncfile[data_name].valid_min = np.min(data)
        elif data > ncfile[data_name].valid_max:
            ncfile[data_name].valid_max = np.max(data)
    try:
        ncfile[data_name][:] = data
    except:
        print(data)
        print(data_name)
        print(data.shape)
        raise

    
def add_2d_dataset(ncfile, data_name, data, i):
    """
    Called by :py:func:`add_dataset`
    For a dataset that has dimensions time and altitude
    Takes a dataset 'data' and adds to variable 'data_name' in 'ncfile' at location 'i'.
    Updates valid_min and valid_max
    
    Args:
        ncfile (netCDF Dataset object): Name of netCDF Dataset.
        data_name (str): Name of variable in netCDF file.
        data (int or float): Data to be added to ncfile[data_name]. NOTE, this is data[data_name] from :py:func:`add_dataset`
        i (int): Time step in netCDF file where data belongs, in range (0,len(ncfile['time'])).
        
    """
    # check valid_min and valid_max exist
    if 'valid_min' in ncfile[data_name].ncattrs():
        if type(ncfile[data_name].valid_min) != ncfile[data_name].datatype:
            ncfile[data_name].valid_min = np.nanmin(data)
            ncfile[data_name].valid_max = np.nanmax(data)
        elif np.nanmin(data) < ncfile[data_name].valid_min:
            ncfile[data_name].valid_min = np.nanmin(data)
        elif np.nanmax(data) > ncfile[data_name].valid_max:
            ncfile[data_name].valid_max = np.nanmax(data)
    for j,_ in enumerate(data):
        if np.isnan(data[j]):
            data[j] = ncfile[data_name]._FillValue
    ncfile[data_name][i] = data   

    
def add_dataset(ncfile, data_name, data, i):
    """
    Adds data[data_name] to ncfile[data_name] at time i, or for all time, depending on the data given. If required, valid_min and valid_max attributes are updated.
    Note on i: Applicable for a single value per time (a variable where time is the only dimension, example could be one temperature measurement in a time series), for data at one time step with altitude dimension (for example, a height profile of wind speed), or for data with values for all times (for example, all temperature measurements in a time series). If data[data_name] is all the values for the whole time range (i.e. the final of the three options), then i could be any value, but needs to be given 
    
    Args:
        ncfile (netCDF Dataset object): Name of netCDF Dataset.
        data_name (str): Name of variable in netCDF file.
        data (int or float): Data to be added to ncfile[data_name]. NOTE, this is data[data_name] from :py:func:`add_dataset`
        i (int): Time step in netCDF file where data belongs, in range (0,len(ncfile['time'])). See note in description above.
        
    """
    if data_name == 'time':  # sort out time 
        # okay, again (see below), does the data have on file per time, or all time in one file?
        if '__len__' not in dir(data[data_name]):
            add_1d_dataset_one_file_time(ncfile, data_name, data[data_name], i)
        else:
            add_1d_dataset_all_time_file(ncfile, data_name, data[data_name])
    elif data_name in ncfile.dimensions.keys(): # i.e. all dimensions except time
        # if data is already present in ncfile, check match
        # how to tell if data is not present, either valid_min is a 
        # string or all data is masked
        if ('valid_min' in ncfile[data_name].ncattrs() and ncfile[data_name].valid_min == '<derived from file>') or np.all(ncfile[data_name][:].mask) == True:
            # data not present, add it in
            # again, could be 1 value or array of values
            if '__len__' not in dir(data[data_name]):
                add_1d_dataset_one_file_time(ncfile, data_name, data[data_name], i)
            # all time in one file
            else:
                add_1d_dataset_all_time_file(ncfile, data_name, data[data_name])
        else:
            # data is present, check it matches
            # the data stored in the ncfile is an array of data, so need to make sure 
            # that our data is an array (altitude is an array, longitude and latitude 
            # are singular values. Normally...
            if not isinstance(data[data_name], np.ndarray):
                data_compare = np.array([data[data_name]])
            else:
                data_compare = data[data_name]
            if not np.array_equal(ncfile[data_name][:].data, data_compare):
                print(i)
                print(type(data[data_name]))
                print(f'WARNING!: variable "{data_name}" with no time dimension appears to change with time. Consider switching to AMOF v1.1')
                print(ncfile[data_name][:].data, np.array([data[data_name]]))
        
    else: # all other variables, check dimensions of variable
        if len(ncfile[data_name].dimensions) == 1:
            # if dimension is time, easy. If anything else, not.
            if 'time' in ncfile[data_name].dimensions:
                # okay, not as easy as I first though
                # does our raw data have one file per time, or all time in one file?
                # one file per time
                if '__len__' not in dir(data[data_name]):
                    add_1d_dataset_one_file_time(ncfile, data_name, data[data_name], i)
                # all time in one file
                else:
                    add_1d_dataset_all_time_file(ncfile, data_name, data[data_name])
            else:
                # decide what to do here later
                pass
        elif len(ncfile[data_name].dimensions) == 2:
            # check those dimensions are time and altitude
            # not expecting any other 2 dimensions yet
            if ('time', 'altitude') == ncfile[data_name].dimensions:  # v2.0
                add_2d_dataset(ncfile, data_name, data[data_name], i)
            elif ('time', 'index') == ncfile[data_name].dimensions:  # v1.1
                add_2d_dataset(ncfile, data_name, data[data_name], i)
            else:
                print(f'Unexpected dimensions {ncfile[data_name].dimensions}, skipping variable {data_name}')
        else:
            print(f'Unexpected number of dimensions {len(ncfile[data_name].dimensions)}, skipping variable {data_name}')
