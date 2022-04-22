"""
Re-write take 1 of IDL code for reading in trw files from ncas-radar-wind-profiler
Write for 1 file

"""

import sys
import numpy as np
import datetime as dt
import struct

#####################
##### FUNCTIONS #####
#####################

def decimalToBinary(n):
    """
    Returns 8 bit binary value of a decimal number, i.e. 1 returns as 00000001 
    
    Args:
        n (int): Decimal number between 0 and 255 inclusive
        
    Returns:
        str: Binary number
        
    """
    if n < 0 or n > 255:
        msg = f'Invalid decimal value {n}, should be between 0 and 255. Would be relatively simple to implement larger number, assuming need for byte sized binary numbers.'
        raise ValueError(msg)
    bin_number = bin(n).replace("0b", "")
    if len(bin_number) < 8:
        number_preceeding_zeros = 8 - len(bin_number)
        bin_number = f"{'0'*number_preceeding_zeros}{bin_number}"
    return bin_number



def bin_to_float32(binary):
    '''
    Returns float from binary. Signed.
    
    Args:
        binary (str): 32 bit binary number
        
    Returns:
        float: Signed number.
        
    '''
    return struct.unpack('!f',struct.pack('!I', int(binary, 2)))[0]



def main(full_filename, verbose=0, classification=0, variance_test=1):
    """
    Reads trw files from ncas-radar-wind-profiler-1 produced by the Degreane software.
    Written directly from original IDL code.
    
    Args:
        full_filename (str): Path and name of trw file.
        verbose (any): If truthy, prints out data as it is being read.
        classification (any): If truthy, prints classification of wind speeds for speeds > 13.9
        variance_test (any): If truthy, reads various standard deviation and skewness data from trw files.
        
    Returns:
        dict: Data from trw file needed for AMOF standard netCDF file variables.
        dict: Global attributes from trw file for AMOF standard netCDF file variables.
        
    """
    
    #####################
    ## SET SOME STUFF ###
    #####################
    
    letters_as_numbers = {'a':10, 'b':11, 'c':12, 'd':13, 
                          'e':14, 'f':15, 'g':16, 'h':17, 
                          'i':18, 'j':19, 'k':20, 'l':21, 
                          'm':22, 'n':23}
    
    
    #####################
    ###### DO STUFF #####
    #####################
    
    
    # work out date and time from filename
    filename = full_filename.split('/')[-1] # filename should be YYMDDHMM.trw
    
    year = int(f"20{filename[:2]}")
    
    month = filename[2]
    if month in letters_as_numbers.keys():
        month_num = letters_as_numbers[month]
        if month_num > 12:
            msg = f'Invalid month: {month}'
            raise ValueError(msg)
        else:
            month = month_num
    else:
        month = int(month)
    
    day = int(f"{filename[3:5]}")
    
    hour = filename[5]
    if hour in letters_as_numbers.keys():
        hour = letters_as_numbers[hour]
    else:
        hour = int(hour)
    
    minutes = int(filename[6:8])
    
    # create datetime object
    date_time_from_filename = dt.datetime(year, month, day, hour, minutes, tzinfo=dt.timezone.utc)
    
    time_in_minutes_since_start_of_day = date_time_from_filename.hour*60 + date_time_from_filename.minute
    time_in_seconds_since_start_of_day = time_in_minutes_since_start_of_day*60
    
    
    
    #####################
    ### READ THE FILE ###
    #####################
    
    with open(full_filename, "rb") as f:
        data = f.readlines() 
    
    data = b''.join(data)
        
    ######################
    # TRANSLATE THE FILE #
    ######################
    
    # idl code lines 364 - 434
    # first line
    
    # first two bytes are ignored
    # third and fourth bytes might be heading_size, or might be ignored, if third and fourth bytes is > 20 then heading_size is fifth and sixth bytes
    heading_size = int(f"0b{decimalToBinary(data[3])}{decimalToBinary(data[2])}",2)
    if heading_size > 20:
        heading_size = int(f"0b{decimalToBinary(data[5])}{decimalToBinary(data[4])}",2)
    
    # seventh byte is header type, 2 includes parameter table 3 doppler type file
    header_type = data[6]
    
    # eigth byte is dummy
    # ninth and tenth - version number. Kind of
    version_no = int(f"0b{decimalToBinary(data[9])}{decimalToBinary(data[8])}",2)
    # this is here. From IDL implementation
    convert_version_no_uint = np.uint16(-1 * version_no)
    
    #print(version_no)
    #print(np.uint16(-1 * version_no)) # this conversion is used in the idl code
    
    
    # 11th and 12th bytes are ignored
    # start date - 13th-16th bytes (well, 16th-13th), unix time
    start_date_unix = int(f"0b{decimalToBinary(data[15])}{decimalToBinary(data[14])}{decimalToBinary(data[13])}{decimalToBinary(data[12])}",2)
    start_date = dt.datetime.fromtimestamp(start_date_unix, dt.timezone.utc)
    
    # get day of year from this time stamp
    day_of_year = start_date.timetuple().tm_yday
    
    # end date is 17th-20th bytes
    end_date_unix = int(f"0b{decimalToBinary(data[19])}{decimalToBinary(data[18])}{decimalToBinary(data[17])}{decimalToBinary(data[16])}",2)
    end_date = dt.datetime.fromtimestamp(end_date_unix, dt.timezone.utc)
    
    # 21st and 22nd bytes - update rate
    update_rate = int(f"0b{decimalToBinary(data[21])}{decimalToBinary(data[20])}",2)
    
    # 23rd and 24th bytes - m_TrtParametersize
    m_TrtParametersize = int(f"0b{decimalToBinary(data[23])}{decimalToBinary(data[22])}",2)
    
    # idl code line 468
    version2_2a = 1 if m_TrtParametersize == 704 else 0
    
    # idl code lines 436 - 465
    
    # convert version_no to operational_software_version
    if convert_version_no_uint == 5:
        operational_software_version = '1.2'
    elif convert_version_no_uint == 6:
        operational_software_version = '2.0'
    elif convert_version_no_uint == 7:
        operational_software_version = '2.1'
    elif convert_version_no_uint == 8:
        operational_software_version = '2.2'
    elif convert_version_no_uint == 10:
        operational_software_version = '3.31'
    elif convert_version_no_uint == 11:
        operational_software_version = '5.34'
    elif convert_version_no_uint == 13:
        operational_software_version = '5.36'
    elif convert_version_no_uint == 14:
        operational_software_version = '5.37'
    elif convert_version_no_uint == 16:
        operational_software_version = '5.39'
    elif convert_version_no_uint == 19:
        operational_software_version = '5.43'
    elif convert_version_no_uint == 21:
        operational_software_version = '5.45'  # note this is also compatible with 6.45
    elif convert_version_no_uint == 22:
        operational_software_version = '7.47'
    elif convert_version_no_uint == 24:
        operational_software_version = '7.49'
    
        
    ############################
    ## Come back and check if ##
    # this is really necessary #
    ############################
    program_version_no = float(operational_software_version)
    
    
    
    
    ###############################################
    # Depending on which program version we have, #
    ### the next bit of data could be anywhere ####
    ############ IDL code line 534-548 ############
    ###############################################
    
    if program_version_no in [1.2]:
        read_pos = 98
    elif program_version_no in [2.0,2.1,2.2]:
        read_pos = 158
    elif program_version_no in [3.31, 5.34]:
        read_pos = 158+(4*12)
    elif program_version_no in [5.36,5.37]:
        read_pos = 158+(4*12)+(4*11)
    elif program_version_no in [5.39]:
        read_pos = 158+(4*12)+(4*22)
    elif program_version_no in [5.43, 5.45, 7.47]:
        read_pos = 26
    elif program_version_no in [7.49]:
        read_pos = 24
    else:
        msg = f"Unexpected program version no: {program_version_no}"
        raise ValueError(msg)
        
    
    ############################################
    ########### Read the next bits, ############
    ########### advance the read_pos ###########
    ############################################
    
    north_correction = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")  # 32 bit float
    read_pos += 4
    
    alt_correction = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")  # 32 bit float
    read_pos += 4
    
    time_correction = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
    read_pos += 2


    # some more jumping, part to jump the colour structure information
    
    if program_version_no < 3.31:
        read_pos += 8
    
    if program_version_no < 5.43:
        colour = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos += 2
    elif program_version_no == 5.43:
        read_pos += 16
    elif program_version_no in [5.45,7.47]:
        read_pos += 52
    elif program_version_no == 7.49:
        read_pos += 54
    else:
        msg = f"Unexpected program version no: {program_version_no}"
        raise ValueError(msg)
    
        
    #########################
    ### More reading data ###
    #########################
    
    
    # IDL lines 478 (program_version_no type), 599-600
    if program_version_no < 3.31:
        Processing_dur = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos += 2
    else:
        Processing_dur = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        read_pos += 4
        
    Lag_between_processing = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
    read_pos += 2
    
    
    #########################
    # Moving position again #
    ### IDL lines 607-619 ###
    #########################
    
    if program_version_no < 5.36:
        byte_position = read_pos
        print("WARNING: program version not recently tested")
    elif program_version_no == 5.36:
        read_pos = 250
    elif program_version_no == 5.43:
        read_pos = 24+(8+4)*4+272+40
    else:
        read_pos = 24+(8+13)*4+272+40
        
    ########################################
    # Read dir vector, antenna, elev stuff #
    ########## IDL lines 625-681 ###########
    ####### This is going to be long #######
    ######### Do we need 4 and 5? ##########
    ########################################
    
    if program_version_no >= 5.39 and program_version_no < 5.43:
        no_radials = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_vector1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_vector2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_vector3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_vector4 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_vector5 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        
        if program_version_no > 5.39:
            read_pos += 4
            
        Dir_antenna1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna4 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna5 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev4 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev5 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        
        if program_version_no > 5.39:
            read_pos += 2 #line 665-667
        
    elif program_version_no >= 5.43:
        no_radials = int(f"0b{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=4
        Dir_vector1 = int(f"0b{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=4
        Dir_vector2 = int(f"0b{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=4
        Dir_vector3 = int(f"0b{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=4
        Dir_vector4 = int(f"0b{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=4
        Dir_vector5 = int(f"0b{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=4
        
        read_pos += 4
        
        Dir_antenna1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna4 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna5 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev4 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev5 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        
        read_pos += 2 #line 665-667
        
    else:
        Dir_vector1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev1 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_vector2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev2 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_vector3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Dir_antenna3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2
        Angle_elev3 = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos+=2

    # Told you it would be long
    
    #####################################
    # Once again, set the read position #
    ######### IDL lines 705-721 #########
    #####################################
    
    if program_version_no in [1.2]:
        read_pos = 550
    elif program_version_no in [2.0,2.1]:
        read_pos = 554+60
    elif program_version_no in [2.2]:
        read_pos = 550+72
    elif program_version_no in [3.31]:
        read_pos = 554+72+(23*4)
    elif program_version_no in [5.34, 5.36,5.37]:
        read_pos = 554+72+(23*4)+(8*4)
    elif program_version_no in [5.39]:
        read_pos = 554+72+(23*4)+(8*4)+(4*111)
    elif program_version_no in [5.43]:
        read_pos = 24+(8+4)*4+272+40+48+48+20+16+808+2*2
    elif program_version_no in [5.45]:
        read_pos = 24+(8+13)*4+272+40+48+48+20+16+808+2*2
    elif program_version_no in [7.47, 7.49]:
        read_pos = 24+(8+13)*4+272+40+2156+48+20+16+808+2*2
    else:
        msg = f"Unexpected program version no: {program_version_no}"
        raise ValueError(msg)
    
    ######################################################
    ##### Okay, we're going to skip lines 723 - 742 ######
    # for the moment, I don't think they add any value. ##
    ############## Start agin from line 744 ##############
    ######################################################
    
    read_pos = m_TrtParametersize + heading_size + 2 # there's a jump on line 746
    
    
    if program_version_no < 5.43:
        size_profile_info_rangegates = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos += 2
    else:
        read_pos += 2 # line 750
        # signed
        size_profile_info_rangegates = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        size_profile_info_rangegates_sign = 1 if size_profile_info_rangegates[0] == '0' else -1
        size_profile_info_rangegates = size_profile_info_rangegates_sign * int(size_profile_info_rangegates[1:],2)
        read_pos += 4  
        
    ###################
    # Line 767 onward #
    # Well, line 790 ##
    ###################
    
    # signed 32 bit
    processing_type = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
    processing_type_sign = 1 if processing_type[0] == '0' else -1
    processing_type = processing_type_sign * int(f"{processing_type[1:]}",2)
    read_pos += 4

    # line 793
    if program_version_no > 3.31:
        # signed 32 bit
        m_nProcessingFlags = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        m_nProcessingFlags_sign = 1 if m_nProcessingFlags[0] == '0' else -1
        m_nProcessingFlags = m_nProcessingFlags_sign * int(f"{m_nProcessingFlags[1:]}",2)
        read_pos += 4
    elif program_version_no > 1.2:
        # unsigned 16 bit
        m_nProcessingFlags = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2)
        read_pos += 2
    
    # line 797
    # signed 16 bit
    mode_no = f"{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
    mode_no_sign = 1 if mode_no[0] == '0' else -1
    mode_no = mode_no_sign * int(f"{mode_no[1:]}",2)
    read_pos += 2
    
    # line 800
    # signed 32 bit
    profile_date = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
    profile_date_sign = 1 if profile_date[0] == '0' else -1
    profile_date = profile_date_sign * int(f"{profile_date[1:]}",2)
    read_pos += 4

    # line 802 & 803
    # signed 32 bit
    start_date_profile = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
    start_date_profile_sign = 1 if start_date_profile[0] == '0' else -1
    start_date_profile = start_date_profile_sign * int(f"{start_date_profile[1:]}",2)
    read_pos += 4

    end_date_profile = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
    end_date_profile_sign = 1 if end_date_profile[0] == '0' else -1
    end_date_profile = end_date_profile_sign * int(f"{end_date_profile[1:]}",2)
    read_pos += 4


    # line 807
    if program_version_no < 3.31:
        # signed 16 bit
        processing_duration_actual = f"{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        processing_duration_actual_sign = 1 if processing_duration_actual[0] == '0' else -1
        processing_duration_actual = processing_duration_actual_sign * int(f"{processing_duration_actual[1:]}",2)
        read_pos += 2
    else:
        # 32 bit single precision float
        processing_duration_actual = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        read_pos += 4

    
    # line 808 
    # signed 16
    lag_between_processing_actual = f"{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
    lag_between_processing_actual_sign = 1 if lag_between_processing_actual[0] == '0' else -1
    lag_between_processing_actual = lag_between_processing_actual_sign * int(f"{lag_between_processing_actual[1:]}",2)
    read_pos += 2
    
    # line 823, unsigned 16 bit
    no_heights = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 2
    
    # line 824, 32 bit single prec float
    min_height = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    # line 825, 32 bit single prec float
    height_increment = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4


    # line 833
    # aahhh, what is this a2? Best guess at the moment, float
    a2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    
    # line 893-899, unsigned 16
    blocknumber = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 2
    country = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 2
    agency = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 2
    station_no = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 2
    station_type = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 2
    instrument_type = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 2
    antenna_type = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 4 # includes jump on line 900
    
    
    # line 901 32 bit float
    beamwidth = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    # line 902 unsigned 32 bit
    frequency = int(f"0b{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
    read_pos += 4

    #line 903-904 32 bit float
    latitude_file = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4
    longitude_file = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4
    altitude_site = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    # line 922-926 unsigned 16 bit
    if program_version_no > 2.0:
        time_difference = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
        read_pos += 2
        dlst = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
        read_pos += 2
    
    
    # lines 930 - 981
    if program_version_no >= 2.0:
        read_pos += 4
        if program_version_no >= 3.1:
            # signed 32
            voltage1 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            voltage1_sign = 1 if voltage1[0] == '0' else -1
            voltage1 = voltage1_sign * int(f"{voltage1[1:]}",2)
            read_pos += 4
            
            voltage2 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            voltage2_sign = 1 if voltage2[0] == '0' else -1
            voltage2 = voltage2_sign * int(f"{voltage2[1:]}",2)
            read_pos += 4
            
            voltage3 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            voltage3_sign = 1 if voltage3[0] == '0' else -1
            voltage3 = voltage3_sign * int(f"{voltage3[1:]}",2)
            read_pos += 4
            
            voltage4 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            voltage4_sign = 1 if voltage4[0] == '0' else -1
            voltage4 = voltage4_sign * int(f"{voltage4[1:]}",2)
            read_pos += 4
        
            overheating = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            overheating_sign = 1 if overheating[0] == '0' else -1
            overheating = overheating_sign * int(f"{overheating[1:]}",2)
            read_pos += 4
        
            preheating = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            preheating_sign = 1 if preheating[0] == '0' else -1
            preheating = preheating_sign * int(f"{preheating[1:]}",2)
            read_pos += 4
        
            vswr = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            vswr_sign = 1 if vswr[0] == '0' else -1
            vswr = vswr_sign * int(f"{vswr[1:]}",2)
            read_pos += 4
        
            if program_version_no > 5.43:
                rain_detection = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
                rain_detection_sign = 1 if rain_detection[0] == '0' else -1
                rain_detection = rain_detection_sign * int(f"{rain_detection[1:]}",2)
                read_pos += 4
    
            attenuation = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            attenuation_sign = 1 if attenuation[0] == '0' else -1
            attenuation = attenuation_sign * int(f"{attenuation[1:]}",2)
            read_pos += 4
            
            # 32 bit float
            current = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            if program_version_no > 5.43:
                # 32 bit float
                shelter_temp = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
                read_pos += 4
    
    
    # lines 985 - 1019    
    if program_version_no < 5.34:
        read_pos += 2 # line 1005
    elif program_version_no < 5.43:
        read_pos += 18  # lines 987 - 944 & 1005
    else:  # >= 5.43
        # signed 32
        sun_rise = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        sun_rise_sign = 1 if sun_rise[0] == '0' else -1
        sun_rise = sun_rise_sign * int(f"{sun_rise[1:]}",2)
        read_pos += 4
    
        read_pos += 4  # lines 999-1000
        
        # signed 32
        sun_set = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        sun_set_sign = 1 if sun_set[0] == '0' else -1
        sun_set = sun_set_sign * int(f"{sun_set[1:]}",2)
        read_pos += 4
    
        read_pos += 18
    

    # line 1021 signed 32
    rain_junk = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
    rain_junk_sign = 1 if rain_junk[0] == '0' else -1
    rain_junk = rain_junk_sign * int(f"{rain_junk[1:]}",2)
    read_pos += 4   
    
    # from IDL, correct up to here for v1.2
    current_position = read_pos  # IDL checks current position, line 1027


    # next up, various jumps from reading in CinfoSol (apparently)
    # line 1036-1038
    if program_version_no == 5.43:
        read_pos += 2

    # lines 1040-1067    
    if program_version_no >= 5.45:
        read_pos += 38  # lines 1044-1046
        for i in range(6):   # this is here while testing, replace with read_pos += n
            # 32 bit float
            junk = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
            #print(junk)
    
        if program_version_no >= 7.49:
            for i in range(4):  # see above about replacement
                junk = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
                read_pos += 4
                #print(junk)

    else:   
        for i in range(6):  # see above about replacement
            junk = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
            #print(junk)

        
    # lines 1072-1091
    # 32 bit floats
    DBZ_coeff = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    proc_gain = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    pulse_length_metres = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    boundary_layer_height = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4

    if boundary_layer_height == 999999.:
        boundary_layer_height=-1e20 

    # lines 1102-1108
    if program_version_no >= 5.34:    # who know why this appears a second time...
        # signed 32 bits
        pbl_time = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        pbl_time_sign = 1 if pbl_time[0] == '0' else -1
        pbl_time = pbl_time_sign * int(f"{pbl_time[1:]}",2)
        read_pos += 4   
        
        read_pos += 4  # lines 1103+1104
        
        sun_rise = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        sun_rise_sign = 1 if sun_rise[0] == '0' else -1
        sun_rise = sun_rise_sign * int(f"{sun_rise[1:]}",2)
        read_pos += 4   
        
        read_pos += 4  # lines 1103+1104
        
        sun_set = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        sun_set_sign = 1 if sun_set[0] == '0' else -1
        sun_set = sun_set_sign * int(f"{sun_set[1:]}",2)
        read_pos += 4   


    
    # lines 1127-1133
    speed = (74.9475/(500e-9)) *2
    distance = ((3e8)*(500e-9))/2
    pulse_length_time = (pulse_length_metres/speed)*2.0
    pulse_length_time_ns = int(pulse_length_time * 1e9)
    
    
    # line 1140    
    ################################################
    ################################################
    ##### WHAT I AM ABOUT TO DO IS TERRIBLE!!! #####
    ################################################
    ################################################
    if 'wp' in locals() or 'wp' in globals():
        # assumed wp is dict
        if wp['delay_correction'] == 1:
            if pulse_length_time_ns == 500:
                alt_correction = 102
            elif pulse_length_time_ns == 599:
                alt_correction = 122.1
            elif pulse_length_time_ns == 999:
                alt_correction = 214.5
            elif pulse_length_time_ns == 1000:
                alt_correction = 214.5
            elif pulse_length_time_ns == 1568:
                alt_correction = 250
            elif pulse_length_time_ns == 1604:
                alt_correction = 250
            elif pulse_length_time_ns == 1700:
                alt_correction = 250
            elif pulse_length_time_ns == 2500:
                alt_correction = 270
            elif pulse_length_time_ns == 2499:
                alt_correction = 270
            else:
                alt_correction = 250
        
    # line 1157-1167    
    if pulse_length_time_ns == 599:
        pulse_length_time_ns = 500
    elif pulse_length_time_ns == 2499:
        pulse_length_time_ns = 500
        
    
    current_position2 = read_pos  # IDL checks current position, line 1175    
        
    # linnes 1184-1192    junk not jump!
    if program_version_no >= 5.36:
        read_pos += 4
    
    # 32 bit floats
    max_doppler_1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4
    
    max_doppler_2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4    
    
    max_doppler_3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4    
    
    max_doppler_4 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4  
    
    max_doppler_5 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
    read_pos += 4     
    
    if program_version_no >= 5.34:
        bright_band = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        read_pos += 4    
        
    
        
    # Loop over heights, starting at line 1248
    # I think I need to define some arrays here first
    altitude = np.zeros(no_heights)
    u_east = np.zeros(no_heights)
    v_north = np.zeros(no_heights)
    w_vert = np.zeros(no_heights)
    wp_winddir = np.zeros(no_heights)
    wp_windspeed = np.zeros(no_heights)
    Ascii_colour_info = np.zeros(no_heights)
    radial_velocity_1 = np.zeros(no_heights)
    radial_velocity_2 = np.zeros(no_heights)
    radial_velocity_3 = np.zeros(no_heights)
    width_1 = np.zeros(no_heights)
    width_2 = np.zeros(no_heights)
    width_3 = np.zeros(no_heights)
    width_min = np.zeros(no_heights)
    width_median = np.zeros(no_heights)
    signal_1 = np.zeros(no_heights)
    signal_2 = np.zeros(no_heights)
    signal_3 = np.zeros(no_heights)
    noise_1 = np.zeros(no_heights)
    noise_2 = np.zeros(no_heights)
    noise_3 = np.zeros(no_heights)
    vel_sd_1 = np.zeros(no_heights)
    vel_sd_2 = np.zeros(no_heights)
    vel_sd_3 = np.zeros(no_heights)
    sig_sd_1 = np.zeros(no_heights)
    sig_sd_2 = np.zeros(no_heights)
    sig_sd_3 = np.zeros(no_heights)
    width_sd_1 = np.zeros(no_heights)
    width_sd_2 = np.zeros(no_heights)
    width_sd_3 = np.zeros(no_heights)
    skew_1 = np.zeros(no_heights)
    skew_2 = np.zeros(no_heights)
    skew_3 = np.zeros(no_heights)
    qualit_1 = np.zeros(no_heights)
    qualit_2 = np.zeros(no_heights)
    qualit_3 = np.zeros(no_heights)
    popula_1 = np.zeros(no_heights)
    popula_2 = np.zeros(no_heights)
    popula_3 = np.zeros(no_heights)
    absskew_1 = np.zeros(no_heights)
    absskew_2 = np.zeros(no_heights)
    absskew_3 = np.zeros(no_heights)
    skew_sd_1 = np.zeros(no_heights)
    skew_sd_2 = np.zeros(no_heights)
    skew_sd_3 = np.zeros(no_heights)
    absskew_sd_1 = np.zeros(no_heights)
    absskew_sd_2 = np.zeros(no_heights)
    absskew_sd_3 = np.zeros(no_heights)
    noise_sd_1 = np.zeros(no_heights)
    noise_sd_2 = np.zeros(no_heights)
    noise_sd_3 = np.zeros(no_heights)
    skewvel_1 = np.zeros(no_heights)
    skewvel_2 = np.zeros(no_heights)
    skewvel_3 = np.zeros(no_heights)
    skewwidth_1 = np.zeros(no_heights)
    skewwidth_2 = np.zeros(no_heights)
    skewwidth_3 = np.zeros(no_heights)
    skewsig_1 = np.zeros(no_heights)
    skewsig_2 = np.zeros(no_heights)
    skewsig_3 = np.zeros(no_heights)
    skewskew_1 = np.zeros(no_heights)
    skewskew_2 = np.zeros(no_heights)
    skewskew_3 = np.zeros(no_heights)
    skewabsskew_1 = np.zeros(no_heights)
    skewabsskew_2 = np.zeros(no_heights)
    skewabsskew_3 = np.zeros(no_heights)
    skewnoise_1 = np.zeros(no_heights)
    skewnoise_2 = np.zeros(no_heights)
    skewnoise_3 = np.zeros(no_heights)
    validation_1 = np.zeros(no_heights)
    validation_2 = np.zeros(no_heights)
    validation_3 = np.zeros(no_heights)
    qc_flag_beam_1 = np.zeros(no_heights)
    qc_flag_beam_2 = np.zeros(no_heights)
    qc_flag_beam_3 = np.zeros(no_heights)
    SNR_1 = np.zeros(no_heights)
    SNR_2 = np.zeros(no_heights)
    SNR_3 = np.zeros(no_heights)
    SNR_min = np.zeros(no_heights)
    overall_validation = np.zeros(no_heights)
    qc_flag_wind = np.zeros(no_heights)
    dshort = 0
    m_fDuree_Measure_1 = np.zeros(no_heights)
    m_fDuree_Measure_2 = np.zeros(no_heights)
    m_fDuree_Measure_3 = np.zeros(no_heights)
    consensus_1 = np.zeros(no_heights)
    consensus_2 = np.zeros(no_heights)
    consensus_3 = np.zeros(no_heights)
    shear_width = np.zeros(no_heights)
    turbulence_width = np.zeros(no_heights)
    epsilon = np.zeros(no_heights)
    
    for k in range(no_heights):
        mini_array = np.zeros(3)
        if verbose:
            print('###################################################')
            
        altitude[k] = height_increment * k + min_height
        
        # 32 bit floats
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        u_east[k] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        v_north[k] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        w_vert[k] = d1
        read_pos += 4
        
        # lines 1278-1284
        # wind direction 'from', wind speed 'horizontal'
        # AMOF standard states wind speed and direction should be 32bit floats
        wp_winddir[k] = np.arctan(-u_east[k]/-v_north[k]) * (180/np.pi)
        if wp_winddir[k] < 0:
            wp_winddir[k] += 360
        # here's a fix
        if u_east[k] > 0 and v_north[k] > 0 and wp_winddir[k] < 90:
            wp_winddir[k] += 180
        wp_winddir[k] = np.float32(wp_winddir[k])
            
        wp_windspeed[k] = np.float32(((u_east[k] ** 2) + (v_north[k] ** 2)) ** 0.5)

        
        if verbose:
            print(f"altitude: {altitude[k]}")
            print(f"loop no: {k}")
            print(f"east north vert: {u_east[k]} {v_north[k]} {w_vert[k]}")
            print(f"wp_winddir wp_windspeed: {wp_winddir[k]} {wp_windspeed[k]}")
            
        if classification == 1:
            if wp_windspeed[k] >= 13.9:
                print(f"{day}/{month}/{year}")
                if wp_windspeed[k] >= 32.7:
                    print("HURRICANE FORCE")
                elif wp_windspeed[k] >= 28.5:
                    print("VIOLENT STORM")
                elif wp_windspeed[k] >= 24.5:
                    print("whole GALE, STORM")
                elif wp_windspeed[k] >= 20.8:
                    print("STRONG GALE")
                elif wp_windspeed[k] >= 17.2:
                    print("FRESH GALE")
                else:
                    print("NEAR GALE")
                    
        # line 1306-7
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        Ascii_colour_info[k] = d1
        read_pos += 4
        
        # line 1311 - 1363
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        radial_velocity_1[k] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        radial_velocity_2[k] = d1
        read_pos += 4
    
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        radial_velocity_3[k] = d1
        read_pos += 4
        
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        width_1[k] = d1
        mini_array[0] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        width_2[k] = d1
        mini_array[1] = d1
        read_pos += 4
    
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        width_3[k] = d1
        mini_array[2] = d1
        read_pos += 4
        
        width_min[k] = np.min(mini_array)
        width_median[k] = np.median(mini_array)
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        signal_1[k] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        signal_2[k] = d1
        read_pos += 4
    
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        signal_3[k] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        noise_1[k] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        noise_2[k] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        noise_3[k] = d1
        read_pos += 4
        
        if verbose:
            print(f"radial velocity: {radial_velocity_1[k]} {radial_velocity_2[k]} {radial_velocity_3[k]}")
            print(f"width: {width_1[k]} {width_2[k]} {width_3[k]}")
            print(f"signal 1,2,3: {signal_1[k]} {signal_2[k]} {signal_3[k]}")
            print(f"noise: {noise_1[k]} {noise_2[k]} {noise_3[k]}")
        
        
        # line 1373-1614
        if not variance_test:
            skip = 60 - 13  # no idea why this is a sum rather than a fixed number
            if program_version_no >= 2.2:
                for z in range(skip+1):  # skip chunks
                    read_pos += 4  # could just do read_pos += 4*(skip+1) outside loop
        else:
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            vel_sd_1[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            vel_sd_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            vel_sd_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            sig_sd_1[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            sig_sd_2[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            sig_sd_3[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            width_sd_1[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            width_sd_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            width_sd_3[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skew_1[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skew_2[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skew_3[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            qualit_1[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            qualit_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            qualit_3[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            popula_1[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            popula_2[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            popula_3[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            absskew_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            absskew_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            absskew_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skew_sd_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skew_sd_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skew_sd_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            absskew_sd_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            absskew_sd_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            absskew_sd_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            noise_sd_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            noise_sd_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            noise_sd_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewvel_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewvel_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewvel_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewwidth_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewwidth_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewwidth_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewsig_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewsig_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewsig_3[k] = d1
            read_pos += 4
         
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewskew_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewskew_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewskew_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewabsskew_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewabsskew_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewabsskew_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewnoise_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewnoise_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            if d1 == 999999:
                d1 = np.nan
            skewnoise_3[k] = d1
            read_pos += 4
                
            if verbose:
                print(f'vel_sd123 : {vel_sd_1[k]} {vel_sd_2[k]} {vel_sd_3[k]}')
                print(f'sig_sd123 : {sig_sd_1[k]} {sig_sd_2[k]} {sig_sd_3[k]}')
                print(f'width_sd123 : {width_sd_1[k]} {width_sd_2[k]} {width_sd_3[k]}')
                print(f'skew : {skew_1[k]} {skew_2[k]} {skew_3[k]}')
                print(f'qualit : {qualit_1[k]} {qualit_2[k]} {qualit_3[k]}')
                print(f'population : {popula_1[k]} {popula_2[k]} {popula_3[k]}')
                print(f'absskew : {absskew_1[k]} {absskew_2[k]} {absskew_3[k]}')
                print(f'skew_sd : {skew_sd_1[k]} {skew_sd_2[k]} {skew_sd_3[k]}')   
                print(f'absskew_sd : {absskew_sd_1[k]} {absskew_sd_2[k]} {absskew_3[k]}')
                print(f'noise_sd : {noise_sd_1[k]} {noise_sd_2[k]} {noise_sd_3[k]}')
                print(f'skewvel : {skewvel_1[k]} {skewvel_2[k]} {skewvel_3[k]}')
                print(f'skewwidth : {skewwidth_1[k]} {skewwidth_2[k]} {skewwidth_3[k]}')
                print(f'skewsig : {skewsig_1[k]} {skewsig_2[k]} {skewsig_3[k]}')
                print(f'skewskew : {skewskew_1[k]} {skewskew_2[k]} {skewskew_3[k]}')
                print(f'skewabsskew : {skewabsskew_1[k]} {skewabsskew_2[k]} {skewabsskew_3[k]}')
                print(f'skewnoise : {skewnoise_1[k]} {skewnoise_2[k]} {skewnoise_3[k]}')
                   
                    
        # line 1619 - 1651
        if program_version_no < 100:  # yes...
            #  signed 32 bits...
            d2 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            d2_sign = 1 if d2[0] == '0' else -1
            d2 = d2_sign * int(f"{d2[1:]}",2)
            validation_1[k] = d2
            read_pos += 4
            
            if d2 == 999999:
                d2 = np.nan
            # qc_flag_beam_1 (& 2 & 3) - from IDL, 
            #     0 no data, 1 good data, 2 bad
            # should be 0 not used, 1 good, 2 bad, 3 no data
            # in idl, this resulted in 1 or 0. so here, 1 or 3.
            if d2 == 1:
                qc_flag_beam_1[k] = 1
            else:
                qc_flag_beam_1[k] = 3
                
            d2 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            d2_sign = 1 if d2[0] == '0' else -1
            d2 = d2_sign * int(f"{d2[1:]}",2)
            validation_2[k] = d2
            read_pos += 4
        
            if d2 == 999999:
                d2 = np.nan
            if d2 == 1:
                qc_flag_beam_2[k] = 1
            else:
                qc_flag_beam_2[k] = 3
                
            d2 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            d2_sign = 1 if d2[0] == '0' else -1
            d2 = d2_sign * int(f"{d2[1:]}",2)
            validation_3[k] = d2
            read_pos += 4
            
            if d2 == 999999:
                d2 = np.nan
            if d2 == 1:
                qc_flag_beam_3[k] = 1
            else:
                qc_flag_beam_3[k] = 3
        else:
            #  32 bit floats...
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            validation_1[k] = d1
            read_pos += 4
            
            if d1 == 999999:
                d1 = np.nan
            # qc_flag_beam_1 (& 2 & 3) - from IDL, 
            #     0 no data, 1 good data, 2 bad
            # should be 0 not used, 1 good, 2 bad, 3 no data
            # in idl, this resulted in 1 or 0. so here, 1 or 3.
            if d1 == 1:
                qc_flag_beam_1[k] = 1
            else:
                qc_flag_beam_1[k] = 3
                
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            validation_2[k] = d1
            read_pos += 4
            
            if d1 == 999999:
                d1 = np.nan
            if d2 == 1:
                qc_flag_beam_2[k] = 1
            else:
                qc_flag_beam_2[k] = 3
                
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            validation_3[k] = d1
            read_pos += 4
            
            if d1 == 999999:
                d1 = np.nan
            if d2 == 1:
                qc_flag_beam_3[k] = 1
            else:
                qc_flag_beam_3[k] = 3
        
        # line 1653 - 1672
        # reset this
        mini_array = np.zeros(3)
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        SNR_1[k] = d1
        mini_array[0] = d1
        read_pos += 4
    
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        SNR_2[k] = d1
        mini_array[1] = d1
        read_pos += 4
        
        d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
        if d1 == 999999:
            d1 = np.nan
        SNR_3[k] = d1
        mini_array[2] = d1
        read_pos += 4
    
        SNR_min[k] = np.min(mini_array)
    
        d2 = f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
        d2_sign = 1 if d2[0] == '0' else -1
        d2 = d2_sign * int(f"{d2[1:]}",2)
        overall_validation[k] = d2
        read_pos += 4
        
        # see same note as above re: qc_flag_beam_1,2,3
        qc_flag_wind[k] = 1 if dshort == 1 else  3
    
    
        if verbose:
            print(f'validation: {validation_1[k]} {validation_2[k]} {validation_3[k]}')
            print(f'qc flag: {qc_flag_beam_1[k]}  {qc_flag_beam_2[k]} {qc_flag_beam_3[k]}')
            print(f'overall validation: {overall_validation[k]}')
            print(f'SNR: {SNR_1[k]} {SNR_2[k]} {SNR_3[k]}')
            print(f'windspeed: {wp_windspeed[k]}')
      
        # line 1684
        if program_version_no > 1.2:
            if verbose:
                print(f'byte point: {read_pos}')
            if program_version_no > 3.0:
                # 32 bit float
                m_dureeTraitment = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
                read_pos += 4
            else:
                # signed 16 bit
                m_dureeTraitment = f"{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
                m_dureeTraitment_sign = 1 if m_dureeTraitment[0] == '0' else -1
                m_dureeTraitment = m_dureeTraitment_sign * int(f"{m_dureeTraitment[1:]}",2)
                read_pos += 2
            
            # signed 16
            m_DecalageTraitment = f"{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
            m_DecalageTraitment_sign = 1 if m_DecalageTraitment[0] == '0' else -1
            m_DecalageTraitment = m_DecalageTraitment_sign * int(f"{m_DecalageTraitment[1:]}",2)
            read_pos += 2
            
            if program_version_no > 5.34:
                # signed 16
                dShort = f"{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}"
                dShort_sign = 1 if dShort[0] == '0' else -1
                dShort = dShort_sign * int(f"{dShort[1:]}",2)
                read_pos += 2
                if verbose:
                    print(f'dShort: {dShort}')
        
            # line 1704, 32 bit float
            m_fLargeurFen = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
            
            if verbose:
                print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                print(f'm_dureeTraitment (consensus duration): {m_dureeTraitment}')
                print(f'm_DecalageTraitment (update rate): {m_DecalageTraitment}')
                print(f'm_fLargeurFen (window width): {m_fLargeurFen}')
            
            # from lines 1713-1716
            if m_dureeTraitment > 120:
                msg = f'Value m_dureeTraitment {m_dureeTraitment} is greater than 120'
                raise ValueError(msg)
            if m_DecalageTraitment < 0:
                msg = f'Value m_DecalageTraitment {m_DecalageTraitment} is less than 0'
                raise ValueError(msg)
            elif m_DecalageTraitment > 60:
                msg = f'Value m_DecalageTraitment {m_DecalageTraitment} is greater than 60'
                raise ValueError(msg)
            
        # line 1722
        if program_version_no > 2.1:
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            m_fDuree_Measure_1[k] = d1
            read_pos += 4
            
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            m_fDuree_Measure_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            m_fDuree_Measure_3[k] = d1
            read_pos += 4
        
            if verbose:
                print(f'dur1: {m_fDuree_Measure_1[k]}')
                print(f'dur2: {m_fDuree_Measure_2[k]}')
                print(f'dur3: {m_fDuree_Measure_3[k]}')
    
        # line 1738
        if verbose:
            print(f'loop k: {k}')
        
        # line 1740
        if program_version_no > 5.34:
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            consensus_1[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            consensus_2[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            consensus_3[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            shear_width[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            turbulence_width[k] = d1
            read_pos += 4
        
            d1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            epsilon[k] = d1
            read_pos += 4
        
            if verbose:
                print(f'consensus: {consensus_1[k]} {consensus_2[k]} {consensus_3[k]}')
                print(f'shear width: {shear_width[k]}')
                print(f'turbulence width: {turbulence_width[k]}')
                print(f'epsilon: {epsilon[k]}')
        
        # line 1769    
        if program_version_no > 2.0:
            # unsigned 16 bit
            qc_override = int(f"0b{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}",2) 
            read_pos += 2
            if verbose:
                print(f'qc override: {qc_override}')
            read_pos += 2
        
        # line 1789
        if program_version_no >= 5.45:
            # 32bit floats
            fivebeam_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_w = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_var_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_var_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_var_w = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_skew_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_skew_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_skew_w = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_pop_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_pop_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_pop_w = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
        elif program_version_no >= 5.36:
            # 32bit floats
            fivebeam_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_var_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_var_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_skew_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_skew_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_pop_w14 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            fivebeam_pop_w25 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
        
        # line 1834    
        if program_version_no >= 5.43:
            # 32 bit floats
            corrected_horiz_velocity_1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
            
            corrected_horiz_velocity_2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            corrected_horiz_velocity_3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            corrected_horiz_velocityxW_1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            corrected_horiz_velocityxW_2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            corrected_horiz_velocityxW_3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            std_corrected_horiz_velocity_1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            std_corrected_horiz_velocity_2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            std_corrected_horiz_velocity_3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            std_corrected_horiz_velocityxW_1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            std_corrected_horiz_velocityxW_2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            std_corrected_horiz_velocityxW_3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            skew_corrected_horiz_velocity_1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            skew_corrected_horiz_velocity_2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            skew_corrected_horiz_velocity_3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            skew_corrected_horiz_velocityxW_1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            skew_corrected_horiz_velocityxW_2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            skew_corrected_horiz_velocityxW_3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
        
            if verbose:
                print(f'corrected horiz velocity: {corrected_horiz_velocity_1} {corrected_horiz_velocity_2} {corrected_horiz_velocity_3}')
                print(f'corrected horiz velocity xW: {corrected_horiz_velocityxW_1} {corrected_horiz_velocityxW_2} {corrected_horiz_velocityxW_3}')
                print(f'std cor horiz vel: {std_corrected_horiz_velocity_1} {std_corrected_horiz_velocity_2} {std_corrected_horiz_velocity_3}')
            
        # line 1862    
        if program_version_no > 5.45:
            # 32 bit float
            display_colour1 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
            
            display_colour2 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
            
            display_colour3 = bin_to_float32(f"{decimalToBinary(data[read_pos+3])}{decimalToBinary(data[read_pos+2])}{decimalToBinary(data[read_pos+1])}{decimalToBinary(data[read_pos])}")
            read_pos += 4
            
            if verbose:
                print(f'display colour: {display_colour1} {display_colour2} {display_colour3}')
                print('###################################################')
        
    
    #print(bin_to_float32(f"{decimalToBinary(data[91])}{decimalToBinary(data[90])}{decimalToBinary(data[89])}{decimalToBinary(data[88])}"))
    
    
    
    
    ############################
    ##### Print everything #####
    ############################
    if verbose:
        print(f"heading size: {heading_size}")
        print(f"header type: {header_type}")
        print(f"version no from file: {version_no}")
        print(f"version no converted: {convert_version_no_uint}")
        print(f"start date unix: {start_date_unix}")
        print(f"end date unix: {end_date_unix}")
        print(f"start date: {start_date}")
        print(f"end date: {end_date}")
        print(f"date time from filename: {date_time_from_filename}")
        print(f"update rate: {update_rate}")
        print(f"m_TrtParametersize: {m_TrtParametersize}")
        print(f"operational software version: {operational_software_version}")
        print(f"program version number: {program_version_no}")
        print(f"version2_2a: {version2_2a}")
        print(f"north correction: {north_correction}")
        print(f"alt correction: {alt_correction}")
        print(f"time correction: {time_correction}")
        print(f"processing duration: {Processing_dur}")
        print(f"update rate (lag between processing): {Lag_between_processing}")
        print(f"no radials: {no_radials}")
        print(f"Dir vector 1: {Dir_vector1}")
        print(f"Dir vector 2: {Dir_vector2}")
        print(f"Dir vector 3: {Dir_vector3}")
        print(f"Dir vector 4: {Dir_vector4}")
        print(f"Dir vector 5: {Dir_vector5}")
        print(f"Dir antenna 1: {Dir_antenna1}")
        print(f"Dir antenna 2: {Dir_antenna2}")
        print(f"Dir antenna 3: {Dir_antenna3}")
        print(f"Dir antenna 4: {Dir_antenna4}")
        print(f"Dir antenna 5: {Dir_antenna5}")
        print(f"Angle elev 1: {Angle_elev1}")
        print(f"Angle elev 2: {Angle_elev2}")
        print(f"Angle elev 3: {Angle_elev3}")
        print(f"Angle elev 4: {Angle_elev4}")
        print(f"Angle elev 5: {Angle_elev5}")
        print(f"size profile info rangegates: {size_profile_info_rangegates}")
        print(f"processing type: {processing_type}")
        print(f"m_nProcessingFlags: {m_nProcessingFlags}")
        print(f"mode_no: {mode_no}")
        print(f"profile date: {profile_date}")
        print(f"start date profile: {start_date_profile}")
        print(f"end date profile: {end_date_profile}")
        print(f"processing duration actual: {processing_duration_actual}")
        print(f"lag between processing actual: {lag_between_processing_actual}")
        print(f"no heights: {no_heights}")
        print(f"min height: {min_height}")
        print(f"height increment: {height_increment}")
        print(f"a2: {a2}")
        print(f"blocknumber: {blocknumber}")
        print(f"country: {country}")
        print(f"agency: {agency}")
        print(f"station no: {station_no}")
        print(f"station type: {station_type}")
        print(f"instrument type: {instrument_type}")
        print(f"antenna type: {antenna_type}")
        print(f"beamwidth: {beamwidth}")
        print(f"frequency: {frequency}")
        print(f"latitude file: {latitude_file}")
        print(f"longitude file: {longitude_file}")
        print(f"altitude site: {altitude_site}")
        print(f"time difference: {time_difference}")
        print(f"dlst: {dlst}")
        print(f"voltage1: {voltage1}")
        print(f"voltage2: {voltage2}")
        print(f"voltage3: {voltage3}")
        print(f"voltage4: {voltage4}")
        print(f"overheating: {overheating}")
        print(f"preheating: {preheating}")
        print(f"vswr: {vswr}")
        print(f"rain detection: {rain_detection}")
        print(f"attenuation: {attenuation}")
        print(f"current: {current}")
        print(f"shelter temp: {shelter_temp}")
        print(f"rain junk: {rain_junk}")
        print(f"current position: {current_position}")
        print(f"DBZ coeff: {DBZ_coeff}")
        print(f"proc gain: {proc_gain}")
        print(f"pulse length metres: {pulse_length_metres}")
        print(f"boundary layer height: {boundary_layer_height}")
        print(f"PBL time: {pbl_time}")
        print(f"sun rise: {sun_rise}")
        print(f"sun set: {sun_set}")
        print(f"pulse_length_time_ns: {pulse_length_time_ns}")
        print(f"current position2: {current_position2}")
        print(f"max_doppler_1: {max_doppler_1}")
        print(f"max_doppler_2: {max_doppler_2}")
        print(f"max_doppler_3: {max_doppler_3}")
        print(f"max_doppler_4: {max_doppler_4}")
        print(f"max_doppler_5: {max_doppler_5}")
        print(f"bright_band: {bright_band}")
        print(f"wind speed: {wp_windspeed}")
        print(f"wind direction: {wp_winddir}")
        
        print(read_pos)

        print("Data successfully read in.")
    
    # i'm sure more will join...
    # keys should match name of variable in netcdf4 file
    all_data = {'time': start_date_unix,
                'altitude': np.float32(altitude),
                'latitude': latitude_file,
                'longitude': longitude_file,
                'time_minutes_since_start_of_day': time_in_minutes_since_start_of_day,
                'size_of_gate': height_increment,
                'qc_flag_rain_detected': rain_detection+1,  # +1 so 1, not 0, is good data
                'wind_speed': wp_windspeed,
                'wind_from_direction': wp_winddir,
                'eastward_wind': u_east,
                'northward_wind': v_north,
                'upward_air_velocity': w_vert,
                'signal_to_noise_ratio_of_beam_1': SNR_1,
                'signal_to_noise_ratio_of_beam_2': SNR_2,
                'signal_to_noise_ratio_of_beam_3': SNR_3,
                'signal_to_noise_ratio_minimum': SNR_min,
                'spectral_width_of_beam_1': width_1,
                'spectral_width_of_beam_2': width_2,
                'spectral_width_of_beam_3': width_3,
                'skew_of_beam_1': skew_1,
                'skew_of_beam_2': skew_2,
                'skew_of_beam_3': skew_3,
                'qc_flag_wind': qc_flag_wind,
                'qc_flag_beam_1': qc_flag_beam_1,
                'qc_flag_beam_2': qc_flag_beam_2,
                'qc_flag_beam_3': qc_flag_beam_3,
                'day_of_year': day_of_year,
                'year': year,
                'month': month,
                'day': day,
                'hour': hour,
                'minute': minutes,
                'second': np.float32(0.)
               }
    
    all_attrs = {'platform_altitude': f'{altitude_site} m',  # this should be deployment position above MSL, check with Emily what altitude_site is
                 'geospatial_bounds': f'{latitude_file}N, {longitude_file}E',
                 'instrument_software_version': operational_software_version,
                 'averaging_interval' : f'{Processing_dur} minutes',
                 'sampling_interval': f'{Lag_between_processing} minutes'
                }  
    
    return all_data, all_attrs
