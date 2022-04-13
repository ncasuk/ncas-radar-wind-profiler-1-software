'''
Creates a netcdf file for ncas instruments, with all variables, dimensions and attributes pulled from https://github.com/ncasuk/AMF_CVs/tree/main/AMF_CVs
'''

# Created 1 March 2022
# v. 0.1 - created


import datetime as dt
from netCDF4 import Dataset

from . import helpful_functions as hf


def main_v2(file_location, instrument_name, pi_scientist, creator_scientist, variables_product, location, common_loc, time, time_length, product_version, alt_length = 0, options = None, dimensions_product = None, attrs_product = None):
    """
    Creates a netCDF file, initialised with all needed attributes, variables, and dimensions, to meet the AMOF standard. Where attributes have fixed values, these are assigned.
    
    Args:
        file_location (str): Location where to save netCDF file to.
        instrument_name (str): Name of instrument, should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_ncas_instrument.json
        pi_scientist (str or dict): Either the email of the project principal investigator (should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs), or a dictionary with keys name, primary_email, and orcid.
        creator_scientist (str or dict): Either the email of the creator (should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs), or a dictionary with keys name, primary_email, and orcid.
        variables_product (str): Name of product for product-specific dimensions. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json 
        location (str): Where is the instrument (wao, cao, cdao, e.t.c.)
        common_loc (str): Location of instrument for common dimensions, variables and attributes. One of 'land', 'sea', 'air', 'trajectory'
        time (str): String of format 'YYYYmmDDHHMMSS', shorter strings are accepted in same format (i.e. 20120214 is accepted as 14th February 2012, not 14Z 2nd December 20)
        time_length (int): Length of time dimension for netCDF file.
        product_version (str): Product version of data in netCDF file.
        alt_length (int): Optional. Length of altitude dimension for netCDF file. Default 0 (no altitude dimensions).
        options (str): Optional. Comma separated string of options for name of netCDF file, e.g. 'low-mode,15min'
        dimensions_product (str or None): Optional. Name of product for product-specific dimensions. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json 
        attrs_product (str or None): Optional. Name of product for product-specific general attributes. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json 
        
    Returns:
        str: Name of netCDF file
        
    """
    # make sure time is of expected type and length, reformatting if needed
    if not isinstance(time, str):
        msg = f'Invalid type for time, should be string of form YYYYmmDDHHMMSS, not type {type(time)}'
        raise TypeError(msg)
    if len(time) > 14:
        msg = f'Invalid time structure, should be string of form YYYYmmDDHHMMSS'
        raise ValueError(msg)
    elif len(time) > 8:
        time = f'{time[:8]}-{time[8:]}'
    
    # if options are given, check they are string re-arrange to '_<option-1>_<option-2>_<option-3>'
    if options != None:  # in case someone tries options = 0 instead of options = '0'
        if not isinstance(options, str):
            msg = f'Invalid type for options, should be string with each option (up to 3) comma separated, not type {type(options)}'
            raise TypeError(msg)
        options = options.split(',')
        if len(options) > 3:
            msg = f'Too many options, maximum allowed 3, given {len(options)}'
            raise ValueError(msg)
        options = f"_{'_'.join(options)}"
    else:
        options = ''
    
    ############################################################
    ############################################################
    # add checks that instrument_name, scientist_email, dimensions_product, variables_product, attrs_product all exist
    ############################################################
    ############################################################
    
    
    # netcdf file name
    filename = f'{instrument_name}_{location}_{time}_{variables_product}{options}_v{product_version}.nc'  
    
    # get dimensions, common and product specific
    common_dims, common_dims_dict = hf.get_common_dimensions_metadata(loc = common_loc)
    if dimensions_product != None:
        product_dims, product_dims_dict = hf.get_product_dimensions_metadata(dimensions_product)
    else:
        product_dims = []
        product_dims_dict = {}
    
    # get variables, common and product specific
    common_vars, common_vars_dict = hf.get_common_variables_metadata(loc = common_loc)
    product_vars, product_vars_dict = hf.get_product_variables_metadata(variables_product)
    
    # get attributes, common and product specific
    common_attrs, common_attrs_dict = hf.get_common_global_attrs(loc = common_loc)
    if attrs_product != None:
        product_attrs, product_attrs_dict = hf.get_product_global_attrs(attrs_product)
    else:
        product_attrs = []
        product_attrs_dict = {}
    
    # get instrument info
    instrument_info_dict = hf.get_instrument_id_description(instrument_name)
    #scientist_info_dict = hf.get_scientist_by_email(scientist_email)
    
    # pi_scientist and creator_scientist could be email address or dictionary. 
    # If email, need to get from github, if dictionary then we are good
    if isinstance(pi_scientist, str):
        pi_scientist_info_dict = hf.get_scientist_by_email(pi_scientist)
    else: 
        pi_scientist_info_dict = pi_scientist
    if isinstance(creator_scientist, str):
        creator_scientist_info_dict = hf.get_scientist_by_email(creator_scientist)
    else: 
        creator_scientist_info_dict = creator_scientist
        
    
    
    # create netcdf file
    ncfile = Dataset(f'{file_location}/{filename}', 'w', format='NETCDF4_CLASSIC')
    
    # add dimensions
    for dim in common_dims:
        length = common_dims_dict[dim].pop('length')
        if dim == 'time':
            hf.create_dimension(ncfile, dim, dimlen = time_length)#,  metadata = common_dims_dict[dim])
        elif dim == 'altitude':
            hf.create_dimension(ncfile, dim, dimlen = alt_length)#,  metadata = common_dims_dict[dim])
        else:
            hf.create_dimension(ncfile, dim, dimlen = int(length))#,  metadata = common_dims_dict[dim])
            
    for dim in product_dims:
        length = product_dims_dict[dim].pop('length')
        if dim == 'time':
            hf.create_dimension(ncfile, dim, dimlen = time_length)#,  metadata = product_dims_dict[dim])
        elif dim == 'altitude':
            hf.create_dimension(ncfile, dim, dimlen = alt_length)#,  metadata = product_dims_dict[dim])
        else:
            hf.create_dimension(ncfile, dim, dimlen = int(length))#,  metadata = product_dims_dict[dim])
            
    
    # add variables
    for var in common_vars:
        # get dimensions
        #dims = common_vars_dict[var].pop('dimension')
        dims = common_vars_dict[var]['dimension']
        # remove all whitespace
        while ' ' in dims:
            dims = dims.replace(' ','')
        dims = tuple(dims.split(','))
        
        # data type
        #datatype = common_vars_dict[var].pop('type')
        datatype = common_vars_dict[var]['type']
        
        hf.create_variable(ncfile, var, datatype, dimensions = dims, metadata = common_vars_dict[var])
        
    for var in product_vars:
        # get dimensions
        #dims = product_vars_dict[var].pop('dimension')
        dims = product_vars_dict[var]['dimension']
        # remove all whitespace
        while ' ' in dims:
            dims = dims.replace(' ','')
        dims = tuple(dims.split(','))
        
        # data type
        #datatype = product_vars_dict[var].pop('type')
        datatype = product_vars_dict[var]['type']
        
        hf.create_variable(ncfile, var, datatype, dimensions = dims, metadata = product_vars_dict[var])
        
        
    # add attributes
    # dict of attr:fixed_value pairs. Where the value is not fixed, fixed_value returns '' (i.e. empty)
    attrs_to_add = {}
    for key, value in common_attrs_dict.items():
        for key2, value2 in common_attrs_dict[key].items():
            if key2 == 'fixed_value':
                attrs_to_add[key] = value2
    for key, value in product_attrs_dict.items():
        for key2, value2 in product_attrs_dict[key].items():
            if key2 == 'fixed_value':
                attrs_to_add[key] = value2
                
    # compare with data from get_instrument_id_description and get_scientist_by_email
    attrs_to_add['source'] = instrument_info_dict['description']
    
    attrs_to_add['project_principal_investigator'] = pi_scientist_info_dict['name']
    attrs_to_add['project_principal_investigator_email'] = pi_scientist_info_dict['primary_email']
    attrs_to_add['project_principal_investigator_url'] = pi_scientist_info_dict['orcid']
    
    attrs_to_add['creator_name'] = creator_scientist_info_dict['name']
    attrs_to_add['creator_email'] = creator_scientist_info_dict['primary_email']
    attrs_to_add['creator_url'] = creator_scientist_info_dict['orcid']
    
    # start the history attr
    attrs_to_add['history'] = f'{(now_datetime := dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))} - file created'
    # set last revised date attr
    attrs_to_add['last_revised_date'] = now_datetime
    # deployment mode will match common_loc
    attrs_to_add['deployment_mode'] = common_loc
    
    
    # print still empty attributes
    #for key, value in attrs_to_add.items():
    #    if value == '': 
    #        print(f'Currently empty attribute: {key}')
    
    hf.write_global_attributes(ncfile, attrs_to_add)
    
    
    
    
    # close file for now, maybe one day return it instead
    ncfile.close()
    
    return f'{file_location}/{filename}'




def main_v1_1(file_location, instrument_name, pi_scientist, creator_scientist, variables_product, location, common_loc, time, time_length, product_version, index_length = 0, options = None, dimensions_product = None, attrs_product = None):
    """
    Creates a netCDF file, initialised with all needed attributes, variables, and dimensions, to meet the AMOF standard. Where attributes have fixed values, these are assigned.
    
    Args:
        file_location (str): Location where to save netCDF file to.
        instrument_name (str): Name of instrument, should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_ncas_instrument.json
        pi_scientist (str or dict): Either the email of the project principal investigator (should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs), or a dictionary with keys name, primary_email, and orcid.
        creator_scientist (str or dict): Either the email of the creator (should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs), or a dictionary with keys name, primary_email, and orcid.
        variables_product (str): Name of product for product-specific dimensions. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json 
        location (str): Where is the instrument (wao, cao, cdao, e.t.c.)
        common_loc (str): Location of instrument for common dimensions, variables and attributes. One of 'land', 'sea', 'air', 'trajectory'
        time (str): String of format 'YYYYmmDDHHMMSS', shorter strings are accepted in same format (i.e. 20120214 is accepted as 14th February 2012, not 14Z 2nd December 20)
        time_length (int): Length of time dimension for netCDF file.
        product_version (str): Product version of data in netCDF file.
        index_length (int): Optional. Length of index dimension for netCDF file. Default 0 (no index dimensions).
        options (str): Optional. Comma separated string of options for name of netCDF file, e.g. 'low-mode,15min'
        dimensions_product (str or None): Optional. Name of product for product-specific dimensions. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json 
        attrs_product (str or None): Optional. Name of product for product-specific general attributes. Should be in https://github.com/ncasuk/AMF_CVs/blob/v2.0.0/AMF_CVs/AMF_product.json 
        
    Returns:
        str: Name of netCDF file
        
    """
    # make sure time is of expected type and length, reformatting if needed
    if not isinstance(time, str):
        msg = f'Invalid type for time, should be string of form YYYYmmDDHHMMSS, not type {type(time)}'
        raise TypeError(msg)
    if len(time) > 14:
        msg = f'Invalid time structure, should be string of form YYYYmmDDHHMMSS'
        raise ValueError(msg)
    elif len(time) > 8:
        time = f'{time[:8]}-{time[8:]}'
    
    # if options are given, check they are string re-arrange to '_<option-1>_<option-2>_<option-3>'
    if options != None:  # in case someone tries options = 0 instead of options = '0'
        if not isinstance(options, str):
            msg = f'Invalid type for options, should be string with each option (up to 3) comma separated, not type {type(options)}'
            raise TypeError(msg)
        options = options.split(',')
        if len(options) > 3:
            msg = f'Too many options, maximum allowed 3, given {len(options)}'
            raise ValueError(msg)
        options = f"_{'_'.join(options)}"
    else:
        options = ''
    
    ############################################################
    ############################################################
    # add checks that instrument_name, scientist_email, dimensions_product, variables_product, attrs_product all exist
    ############################################################
    ############################################################
    
    
    # netcdf file name
    filename = f'{instrument_name}_{location}_{time}_{variables_product}{options}_v{product_version}.nc'  
    
    # get dimensions, common and product specific
    common_dims, common_dims_dict = hf.get_common_dimensions_metadata(loc = common_loc)
    if dimensions_product != None:
        product_dims, product_dims_dict = hf.get_product_dimensions_metadata(dimensions_product)
    else:
        product_dims = []
        product_dims_dict = {}
    
    # get variables, common and product specific
    common_vars, common_vars_dict = hf.get_common_variables_metadata(loc = common_loc)
    product_vars, product_vars_dict = hf.get_product_variables_metadata(variables_product)
    
    # because we've only got v2.0.0 json, need to change all variables with 'altitude' dim to 'index'. Also need to change altitude var to have time dim
    for var in common_vars:
        if 'altitude' in common_vars_dict[var]['dimension']:
            common_vars_dict[var]['dimension'] = common_vars_dict[var]['dimension'].replace('altitude', 'index')
            
    for var in product_vars:
        if 'altitude' == var:
            product_vars_dict['altitude']['dimension'] = 'time, index'
        elif 'altitude' in product_vars_dict[var]['dimension']:
            product_vars_dict[var]['dimension'] = product_vars_dict[var]['dimension'].replace('altitude', 'index')
    
    # get attributes, common and product specific
    common_attrs, common_attrs_dict = hf.get_common_global_attrs(loc = common_loc)
    if attrs_product != None:
        product_attrs, product_attrs_dict = hf.get_product_global_attrs(attrs_product)
    else:
        product_attrs = []
        product_attrs_dict = {}
    
    # get instrument info
    instrument_info_dict = hf.get_instrument_id_description(instrument_name)
    #scientist_info_dict = hf.get_scientist_by_email(scientist_email)
    
    # pi_scientist and creator_scientist could be email address or dictionary. 
    # If email, need to get from github, if dictionary then we are good
    if isinstance(pi_scientist, str):
        pi_scientist_info_dict = hf.get_scientist_by_email(pi_scientist)
    else: 
        pi_scientist_info_dict = pi_scientist
    if isinstance(creator_scientist, str):
        creator_scientist_info_dict = hf.get_scientist_by_email(creator_scientist)
    else: 
        creator_scientist_info_dict = creator_scientist
        
    
    
    # create netcdf file
    ncfile = Dataset(f'{file_location}/{filename}', 'w', format='NETCDF4_CLASSIC')
    
    # add dimensions
    for dim in common_dims:
        length = common_dims_dict[dim].pop('length')
        if dim == 'time':
            hf.create_dimension(ncfile, dim, dimlen = time_length)#,  metadata = common_dims_dict[dim])
        elif dim in ['index','altitude']:  # because we can only look at v2.0 jsons, we have to cope
            hf.create_dimension(ncfile, 'index', dimlen = index_length)#,  metadata = common_dims_dict[dim])
        else:
            hf.create_dimension(ncfile, dim, dimlen = int(length))#,  metadata = common_dims_dict[dim])
            
    for dim in product_dims:
        length = product_dims_dict[dim].pop('length')
        if dim == 'time':
            hf.create_dimension(ncfile, dim, dimlen = time_length)#,  metadata = product_dims_dict[dim])
        elif dim in ['index','altitude']:  # because we can only look at v2.0 jsons, we have to cope
            hf.create_dimension(ncfile, 'index', dimlen = index_length)#,  metadata = product_dims_dict[dim])
        else:
            hf.create_dimension(ncfile, dim, dimlen = int(length))#,  metadata = product_dims_dict[dim])
            
    
    # add variables
    for var in common_vars:
        # get dimensions
        #dims = common_vars_dict[var].pop('dimension')
        dims = common_vars_dict[var]['dimension']
        # remove all whitespace
        while ' ' in dims:
            dims = dims.replace(' ','')
        dims = tuple(dims.split(','))
        
        # data type
        #datatype = common_vars_dict[var].pop('type')
        datatype = common_vars_dict[var]['type']
        
        hf.create_variable(ncfile, var, datatype, dimensions = dims, metadata = common_vars_dict[var])
        
    for var in product_vars:
        # get dimensions
        #dims = product_vars_dict[var].pop('dimension')
        dims = product_vars_dict[var]['dimension']
        # remove all whitespace
        while ' ' in dims:
            dims = dims.replace(' ','')
        dims = tuple(dims.split(','))
        
        # data type
        #datatype = product_vars_dict[var].pop('type')
        datatype = product_vars_dict[var]['type']
        
        hf.create_variable(ncfile, var, datatype, dimensions = dims, metadata = product_vars_dict[var])
        
        
    # add attributes
    # dict of attr:fixed_value pairs. Where the value is not fixed, fixed_value returns '' (i.e. empty)
    attrs_to_add = {}
    for key, value in common_attrs_dict.items():
        for key2, value2 in common_attrs_dict[key].items():
            if key2 == 'fixed_value':
                attrs_to_add[key] = value2
    for key, value in product_attrs_dict.items():
        for key2, value2 in product_attrs_dict[key].items():
            if key2 == 'fixed_value':
                attrs_to_add[key] = value2
                
    # compare with data from get_instrument_id_description and get_scientist_by_email
    attrs_to_add['source'] = instrument_info_dict['description']
    
    attrs_to_add['project_principal_investigator'] = pi_scientist_info_dict['name']
    attrs_to_add['project_principal_investigator_email'] = pi_scientist_info_dict['primary_email']
    attrs_to_add['project_principal_investigator_url'] = pi_scientist_info_dict['orcid']
    
    attrs_to_add['creator_name'] = creator_scientist_info_dict['name']
    attrs_to_add['creator_email'] = creator_scientist_info_dict['primary_email']
    attrs_to_add['creator_url'] = creator_scientist_info_dict['orcid']
    
    # start the history attr
    attrs_to_add['history'] = f'{(now_datetime := dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))} - file created'
    # set last revised date attr
    attrs_to_add['last_revised_date'] = now_datetime
    # deployment mode will match common_loc
    attrs_to_add['deployment_mode'] = common_loc
    
    
    # print still empty attributes
    #for key, value in attrs_to_add.items():
    #    if value == '': 
    #        print(f'Currently empty attribute: {key}')
    
    hf.write_global_attributes(ncfile, attrs_to_add)
    
    # correct conventions global attribute
    ncfile.Conventions = ncfile.Conventions.replace('NCAS-AMF-2.0.0','NCAS-AMF-1.1.0')
    
    
    
    
    # close file for now, maybe one day return it instead
    ncfile.close()
    
    return f'{file_location}/{filename}'
