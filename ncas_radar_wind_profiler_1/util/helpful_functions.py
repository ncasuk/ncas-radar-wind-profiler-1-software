"""
Various useful functions which so far have no other home.
"""

import requests
from netCDF4 import Dataset
import numpy as np
import os

def create_dimension(ncfile, name, dimlen = None):
    """
    Creates the dimension `name` of size `dimlen`.
    
    Args:
        ncfile (netCDF Dataset object): Name of netCDF Dataset.
        name (str): Name of variable to create.
        dimlen (int or None): Optional. Length of dimension. If None, then unlimited dimensions. Default None.
        
    """
       
    # Create dimension
    dim = ncfile.createDimension(name, dimlen)

    
    
def create_variable(ncfile, name, datatype, dimensions = (), metadata = {}):
    """
    Creates new variable `name` with dimensions `dimensions` in ncfile.
    
    Args:
        ncfile (netCDF Dataset object): Name of netCDF Dataset.
        name (str): Name of variable to create.
        datatype (class): Type of the data that will be stored, e.g. int, np.float32
        dimensions (tuple): Dimensions of the variable.
        metadata (dict): Dictionary of metadata and attributes for the variable. Valid metadata for each variable can be found at https://github.com/ncasuk/AMF_CVs/tree/main/AMF_CVs
        
    """
    
    # Check correct data type for dimensions and kw
    if not isinstance(dimensions, tuple):
        msg = f"Dimensions should be tuple, not {type(dimensions)}"
        raise TypeError(msg)
    if not isinstance(metadata, dict):
        msg = f"Metadata should be dictionary, not {type(metadata)}"
        raise TypeError(msg)
    
    # Create variables
    # need to extract fill value from metadata and define in createVariable
    if '_FillValue' in metadata.keys():
        fillvalue = metadata.pop('_FillValue')
        var = ncfile.createVariable(name, datatype, dimensions, fill_value = fillvalue)
    else:
        var = ncfile.createVariable(name, datatype, dimensions)
        
    for mdat in metadata.keys():
        var.setncattr(mdat, metadata[mdat])
    
    
    
    
def write_global_attributes(ncfile, attrs):
    """
    Writes global attributes to netCDF file.
    
    Args:
        ncfile (netCDF Dataset object): Name of netCDF Dataset.
        attrs (dict): Attributes to write to netCDF file. If value of attribute is not yet known, write as an empty string.
        
    """
    if not isinstance(attrs, dict):
        msg = f"Attributes should be in dictionary, not {type(attrs)}"
        raise ValueError(msg)
    
    for key in attrs.keys():
        ncfile.setncattr(key, attrs[key])

    
    
def get_json_from_github(url):
    """
    Returns desired json file from https://github.com/ncasuk/AMF_CVs/tree/main/AMF_CVs
    URL should be in form https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/___.json,
    otherwise a JSONDecodeError will be returned by the r.json() call
      
    Args:
        url (str): URL of json file
        
    Returns:
        dict: JSON data from URL
        
    """
    r = requests.get(url)
    return r.json()



def get_instrument_id_description(instrument_name):
    """
    Returns information on instrument from https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_ncas_instrument.json
    
    Args:
        instrument_name (str): Name of instrument
        
    Returns:
        dict: ID and description of instrument.
        
    """
    j = get_json_from_github("https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_ncas_instrument.json")
    if instrument_name in j["ncas_instrument"].keys():
        return j["ncas_instrument"][instrument_name]
    else:
        msg = f"{instrument_name} not in https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_ncas_instrument.json"
        raise ValueError(msg)



def get_scientist_by_email(scientist_email):
    """
    Returns information on scientist from https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_scientist.json
    
    Args:
        scientist_email (str): Primary email address of scientist.
        
    Returns:
        dict: Name, primary email, and orcid of scientist
        
    """
    j = get_json_from_github("https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_scientist.json")
    if scientist_email in j["scientist"].keys():
        return j["scientist"][scientist_email]
    else:
        msg = f"{scientist_email} not in https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_scientist.json"
        raise ValueError(msg)
        

        
def get_product_dimensions_metadata(product):
    """
    Get dimensions and their metadata associated with a product.
    `product` should be in https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_product.json
    
    Args:
        product (str): Product describing the data from the instrument for the netCDF file.
        
    Returns:
        list: All product-specific dimensions.
        dict: Dictionary of dimensions and their attributes.
        
    """
    product_list = get_json_from_github("https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product.json")["product"]
    
    # Check for valid product
    if product not in product_list:
        msg = f"product {product} is not in https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_product.json"
        raise ValueError(msg)
     
    # Get the stuff
    response = requests.get(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_{product}_dimension.json")
    if response.status_code == 200:
        # Get the stuff
        dim_dict = get_json_from_github(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_{product}_dimension.json")[f"product_{product}_dimension"]
        dimensions = dim_dict.keys()
    else:
        print("Product does not have specific dimensions file, continuing...")
        dimensions = []
        dim_dict = {}
    
    return dimensions, dim_dict
        

        
def get_product_variables_metadata(product):
    """
    Get variables and their metadata associated with a product.
    `product` should be in https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_product.json
    
    Args:
        product (str): Product describing the data from the instrument for the netCDF file.
        
    Returns:
        list: All product-specific variables.
        dict: Dictionary of variables and their attributes.
        
    """
    product_list = get_json_from_github("https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product.json")["product"]
    
    # Check for valid product
    if product not in product_list:
        msg = f"product {product} is not in https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_product.json"
        raise ValueError(msg)
     
    # Get the stuff
    var_dict = get_json_from_github(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_{product}_variable.json")[f"product_{product}_variable"]
    variables = var_dict.keys()
    
    return variables, var_dict
        

        
def get_product_global_attrs(product):
    """
    Get global attributes associated with a product.
    `product` should be in https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_product.json
    
    Args:
        product (str): Product describing the data from the instrument for the netCDF file.
        
    Returns:
        list: All product-specific global attributes.
        dict: Dictionary of attributes and realted information, including fixed_value.
        
    """
    product_list = get_json_from_github("https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product.json")["product"]
    
    # Check for valid product
    if product not in product_list:
        msg = f"product {product} is not in https://github.com/ncasuk/AMF_CVs/blob/main/AMF_CVs/AMF_product.json"
        raise ValueError(msg)
     
    # Check file exists
    response = requests.get(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_{product}_global-attributes.json")
    if response.status_code == 200:
        # Get the stuff
        attr_dict = get_json_from_github(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_{product}_global-attributes.json")[f"product_{product}_global-attributes"]
        attributes = attr_dict.keys()
    else:
        print("Product does not have specific attrs file, continuing...")
        attributes = []
        attr_dict = {}
    
    return attributes, attr_dict
        

        
def get_common_dimensions_metadata(loc = "land"):
    """
    Get common dimensions and their metadata associated with a location.
    `loc` should be "land", "sea", "air", or "trajectory"
    
    Args:
        loc (str): Optional. Location of instrument - 'land', 'sea', 'air', 'trajectory'. Default 'land'.
        
    Returns:
        list: All common dimensions.
        dict: Dictionary of common dimensions and their attributes.
        
    """
    # Check valid location
    if loc not in ["land", "sea", "air", "trajectory"]:
        msg = f"Invalid loc: {loc}"
        raise ValueError(msg)
     
    # Get the stuff
    dim_dict = get_json_from_github(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_common_dimension_{loc}.json")[f"product_common_dimension_{loc}"]
    dimensions = dim_dict.keys()
    
    return dimensions, dim_dict
        

        
def get_common_variables_metadata(loc = "land"):
    """
    Get common variables and their metadata associated with a location.
    `loc` should be "land", "sea", "air", or "trajectory"
    
    Args:
        loc (str): Optional. Location of instrument - 'land', 'sea', 'air', 'trajectory'. Default 'land'.
        
    Returns:
        list: All common variables.
        dict: Dictionary of common variables and their attributes.
        
    """
    # Check valid location
    if loc not in ["land", "sea", "air", "trajectory"]:
        msg = f"Invalid loc: {loc}"
        raise ValueError(msg)
     
    # Get the stuff
    var_dict = get_json_from_github(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_common_variable_{loc}.json")[f"product_common_variable_{loc}"]
    variables = var_dict.keys()
    
    return variables, var_dict
        

        
def get_common_global_attrs(loc = "land"):
    """
    Get common global attributes associated with a location.
    `loc` should be "land", "sea", "air", or "trajectory"
    
    Args:
        loc (str): Optional. Location of instrument - 'land', 'sea', 'air', 'trajectory'. Default 'land'.
        
    Returns:
        list: All common global attributes.
        dict: Dictionary of common global attributes and their  realted information, including fixed_value.
        
    """
    # Check valid location
    if loc not in ["land", "sea", "air", "trajectory"]:
        msg = f"Invalid loc: {loc}"
        raise ValueError(msg)
     
    # Get the stuff
    attr_dict = get_json_from_github(f"https://raw.githubusercontent.com/ncasuk/AMF_CVs/main/AMF_CVs/AMF_product_common_global-attributes_{loc}.json")[f"product_common_global-attributes_{loc}"]
    attributes = attr_dict.keys()
    
    return attributes, attr_dict
    
    
    
def remove_empty_whole(infile, outfile, product, overwrite = True, verbose=0):
    """
    If a product-specific variable is empty, we want to remove it.
    However, removing a variable from a netcdf file is not possible, 
    so we have to create a new one, and just not copy over the 
    empty variable.
      
    Args:
        infile (str): File path and name of current netCDF file.
        outfile (str): Name of temporary netCDF file to create (or not so temporary, see overwrite).
        product (str): Name of product for data in file.
        overwrite (any): Optional. If truthy, outfile overwrites infile. If falsy, both outfile and infile remain. Default True.
        verbose (any): Optional. If truthy, prints variables that are being removed from infile. Default 0.
        
    """
    
    in_ncfile = Dataset(infile, "r")
    product = infile.split('/')[-1].split('_')[3]
    
    toexclude = []
    product_vars, _ = get_product_variables_metadata(product)

    for var in in_ncfile.variables.keys():
        if var in product_vars:
            if 'valid_min' in in_ncfile[var].ncattrs() and in_ncfile[var].valid_min == '<derived from file>':
                toexclude.append(var)
            elif np.all(in_ncfile[var][:].mask) == True:
                toexclude.append(var)
    
    if verbose:
        print(f'variables being removed: {toexclude}')
    
    dst = Dataset(outfile, "w", format='NETCDF4_CLASSIC')
    # copy global attributes all at once via dictionary
    dst.setncatts(in_ncfile.__dict__)
    # copy dimensions
    for name, dimension in in_ncfile.dimensions.items():
        dst.createDimension(name, (len(dimension)))
    # copy all file data except for the excluded
    for name, variable in in_ncfile.variables.items():
        if name not in toexclude:
            if verbose:
                print(name)
            in_ncfile_name_attrs = in_ncfile[name].__dict__
            if '_FillValue' in in_ncfile_name_attrs:
                fill_value = in_ncfile_name_attrs.pop('_FillValue')
                dst.createVariable(name, variable.datatype, variable.dimensions, fill_value = fill_value)
            else:
                dst.createVariable(name, variable.datatype, variable.dimensions)
            # copy variable attributes all at once via dictionary
            dst[name].setncatts(in_ncfile_name_attrs)
            dst[name][:] = in_ncfile[name][:]
            
    dst.close()            
    in_ncfile.close()
    
    if overwrite:
        os.rename(outfile, infile)
                    
            
def zero_pad_number(n):
    """
    Returns single digit number n as '0n'
    Returns multiple digit number n as 'n'
    Used for date or month strings
    
    Args:
        n (int): Number
        
    Returns:
        str: Number with zero padding if single digit.
        
    """
    if len(f'{n}') == 1:
        return f'0{n}'
    else:
        return f'{n}'
