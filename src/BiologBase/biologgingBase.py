import re

import numpy as np
import pandas as pd

import lesserCalculation

""" Importing of AxyTrek Marine data.

This function is built to read in the default output from XManager.

One or multiple files can be listed.

ARGUMENTS:
    filenames : str, path object or file-like object
    This follows the pandas.read_csv() filepath_or_buffer convention, however, a vector of multiple filenames can be passed.

    sep : str, default '/t', optional
    Delimiter, as per pandas.read_csv(). Defaults to tab-separated.

    columns : list-like or callable, optional
    List of columns to be returned - must match the column names listed in XManager output. Defaults to None (return all columns).
"""

def readAxyGPS(filename, delim = "\t", cols = None, datetimeFormat = "%d/%m/%Y %H:%M:%S"): 
    """
    Read in AxyTrek GPS data (txt files) as output by X Manager

    Args:

        filename:   path to AxyTrek txt file
        cols:       string to denote if acceleration and GPS ('acc') or GPS only ('gps') should be read in
        colnames:   list of string column names to be assigned. Must be of same length as cols. Defaults to ['Date', 'Time', 'lat', 'lon']

    Returns:
        Pandas dataframe of columns `colnames`. A formatted DateTime column (named DT) is generated.
    """

    colnames = ['Date', 'Time', 'lat', 'lon']


    df = pd.read_csv(filename, sep = delim, usecols = cols,
    names = colnames)
    df.DT = [dtFormat(x) for x in df.DT] # ensure correct datetime formats
    df['DT'] = pd.to_datetime(df['Date'] + " " + df['Time'], format = datetimeFormat)
    return df

def readBIP(filename,cols=None):
    """
    Read in BiP-formatted data

    Args:

        filename:   string of full path to file
        cols:       string value indicating if number of columns to read in can be reduced. For GPS and acceleration, use 'acc', for GPS only, use 'gps'. Defaults to None.

    Returns:
        Pandas dataframe of BIP system formatted data. Columns returned depend on `cols` argument. 'acc' returns formatted datetime (DT), latitude (lat), longitude (lon), longitudinal acceleration (X), lateral acceleration (Y), and dorsoventral acceleration (Z). 'gps' returns datetime, latitude, and longitude. If no cols argument given, all data is read in, including pressure (pressure), temperature (temp), height about sea level (altitude), and ground speed (spd).
    """

    accCols = ['time','latitude','longitude','acceleration_longitudinal','acceleration_lateral','acceleration_dorso_ventral']
    gpsCols = ['time','latitude','longitude']

    # read in based on requested columns
    if cols.lower() == 'gps':
        df = pd.read_csv(filename, sep = ",", header = 0, usecols = gpsCols)
    elif cols.lower() == 'acc':
        df = pd.read_csv(filename, sep = ",", header = 0, usecols = accCols)
    else:
        df = pd.read_csv(filename, sep = ",", header = 0)
         
    # df = pd.read_csv(filename, sep = ",", header = 0, usecols = cols)
    # rename columns for later use
    df.rename(columns = {'time':'DT','latitude':'lat','longitude':'lon','acceleration_longitudinal':'X','acceleration_lateral':'Y','acceleration_dorso_ventral':'Z','pressure':'pressure','temperature':'temp','height_above_mean_sea_level':'altitude','ground_speed':'spd'}, inplace = True)
    
    df.DT = [dtFormat(x) for x in df.DT] # ensure correct datetime formats
    df['DT'] = pd.to_datetime(df['DT'], format = "%Y-%m-%d %H:%M:%S.%f")

    return df

def gps_distanceSingle(longitudes, latitudes, latVal, lonVal):                                                                       
    # taken from https://www.tjansson.dk/2021/03/vectorized-gps-distance-speed-calculation-for-pandas/, thanks to Thomas Jansson for use of this function
    """                                                                                                                 
    Calculates distances between an array of GPS points and a single position via a vectorized haversine calculation the great circle distance between two arrays of points on the earth (specified in decimal degrees). All args must be of equal length.                                         
 
    Args:                                                                                                               
        longitudes: pandas series of longitudes                                                                         
        latitudes:  pandas series of latitudes                               
        latVal:     latitude value of single position                                           
        lonVal:     longitude value of single position
 
    Returns:                                                                                                            
        Distance is returned an array in meters.                                                                             
 
    Example:                                                                                                            
        >>> df['gpsDist'] = gps_distance(df.longitude, df.latitude, 39.400,141.998)
    """
 
    # lon1 = longitudes[:-1].reset_index(drop = True)                                                                                       
    # lat1 = latitudes[:-1].reset_index(drop = True)                                                                                 
    # lon2 = longitudes[1:].reset_index(drop = True)                                                                                       
    # lat2 = latitudes[1:].reset_index(drop = True)                                                                                 
 
    # Vectorized haversine calculation                                                                                  
    lon, lat, lon1, lat1 = map(np.radians, [longitudes, latitudes, lonVal, latVal])                                                  
    a = np.sin((lat - lat1) / 2.0)**2 + (np.cos(lat) * np.cos(lat1) * np.sin((lon1 - lon) / 2.0)**2)                 
    dist = np.array(6371 * 2 * np.arcsin(np.sqrt(a)) * 1000)
    
    # Make the array as long as the input arrays                                                                        
    dist = np.insert(dist, 0, np.nan, axis=0)                                                               
    return dist


def distSpeed(lat,lon,DT):

    dist,speed = gps_speed(lat,lon,DT)
    while np.nanmax(speed) > threshold:

        # remove erroneous GPS values
        lon[speed > threshold] = np.nan
        lat[speed > threshold] = np.nan

        # recalculate speed
        dist,speed = gps_speed(lat,lon,DT)
    
    return dist,speed

# to be placed elsewhere
import re

def dtFormat(x):
    """
    Format incoming datetimes from BiP system. Typically datetimes are brought in the format YYYY-mm-dd HH:MM:SS+00:00, however, SS can contain decimal values or not. This function returns the same datetime in string format with a decimal place added if none is originally present and removes '+00:' from the string so that datetimes can be converted to datetime format in Pandas.

    Args:
    
        x:  datetime in string format

    Returns:
        String of x in correct datetime format %Y-%m-%d %H:%M:%S.%f
    """

    # extract all before '+'
    out = re.findall('^(.*)\+',x)[0]
    # remove all non-datetime characters
    out = re.sub('[^0-9 .:-]','',out)
    if '.' not in out: # add milliseconds if not present (3 d.p.)
        out = out + '.000'
    if out.count('.') > 1:
        out = re.findall('[^.]*.[^.]*',out)[0] # extract all before second period
    # ensure 3 d.p.
    msLength = len(re.findall('[^.]*.',out)[1])
    if msLength != 3:
        if msLength < 3:
            out = out + ('0' * (3-msLength))
        else:
            out = out[:-(msLength - 3)]

    return out

def gps_speed(longitudes, latitudes, timestamps):                                                                       
    # taken from https://www.tjansson.dk/2021/03/vectorized-gps-distance-speed-calculation-for-pandas/, thanks to Thomas Jansson for use of this function
    """                                                                                                                 
    Calculates the instantaneous speed from the GPS positions and timestamps. The distances between the points          
    are calculated using a vectorized haversine calculation the great circle distance between two arrays of points on   
    the earth (specified in decimal degrees). All args must be of equal length.                                         
 
    Args:                                                                                                               
        longitudes: pandas series of longitudes                                                                         
        latitudes:  pandas series of latitudes                                                                          
        timestamps: pandas series of timestamps                                                                         
 
    Returns:                                                                                                            
        Speed is returned an array in m/s.                                                                             
 
    Example:                                                                                                            
        >>> df['gpsSpeed'] = gps_speed(df.longitude, df.latitude, df.recordedAt)
    """
 
    lon1 = longitudes[:-1].reset_index(drop = True)                                                                                       
    lat1 = latitudes[:-1].reset_index(drop = True)                                                                                 
    lon2 = longitudes[1:].reset_index(drop = True)                                                                                       
    lat2 = latitudes[1:].reset_index(drop = True)                                                                                 
 
    # Vectorized haversine calculation                                                                                  
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])                                                  
    a = np.sin((lat2 - lat1) / 2.0)**2 + (np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2.0)**2)                 
    dist = np.array(6371 * 2 * np.arcsin(np.sqrt(a)) * 1000)
    time_array = (timestamps.diff().dt.seconds ).values[1:]                                                       
 
    # Calculate the speed                                                                                               
    time_array[time_array == 0] = np.nan  # To avoid division by zero                                                   
    speed = np.array(dist / time_array)

    # Make the arrays as long as the input arrays                                                                        
    speed = np.insert(speed, 0, np.nan, axis=0)
    dist = np.insert(dist, 0, np.nan, axis=0)                                                               
    return dist,speed