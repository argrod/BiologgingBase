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
