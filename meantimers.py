import numpy as np
import pandas as pd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as ptc
import matplotlib.colors as mc
import math
from scipy import stats
# load the dataset containing the events
#source_file = '/home/lab/dat/262_000_definitive.txt'
#events = pd.read_csv(source_file, sep=",")
#events['LAYERS'] = events['LAYERS'].astype(str)
#events
# define the function that computes the crossing angle
#         ti : time recorded by the i-th layer's cell
#         tj : time recorded by the (i+2)-th layer's cell
#    v_drift : drift velocity
#          h : height of each cell
# angle_sign : sign of the crossing angle (deduced by applying the mean-timer technique)
def crossing_angle(ti, tj, v_drift, h, angle_sign):
    dx = np.abs(v_drift * (ti-tj))   # projection of the distance between the two hits along the direction of the layers
    angle_tan = dx / (2*h)   # tangent of the crossing angle
    angle = angle_sign * np.rad2deg(np.arctan(angle_tan))
    return angle

# define the functions that apply the mean-timer technique to the single event
#       t : list of times recorded by the cells hit by the particle
#       c : list of indices of the cells hit by the particle
#    tmax : maximum drift time
# v_drift : drift velocity
#       h : height of each cell
def meantimer_123(t, c, tmax, v_drift, h):   # case layers 1-2-3
    t1, t2, t3, t4 = t
    c1, c2, c3, c4 = c
    t0 = (t1 + 2*t2 + t3 - 2*tmax) / 4   # time pedestal
    if c2 == c1:
        pattern = 'LRL_'
        angle_sign = np.sign(t1-t3)   
    else:
        pattern = 'RLR_'
        angle_sign = np.sign(t3-t1)
    angle = crossing_angle(t1, t3, v_drift, h, angle_sign)
    return t0, pattern, angle

def meantimer_124(t, c, tmax, v_drift, h):   # case layers 1-2-4
    t1, t2, t3, t4 = t
    c1, c2, c3, c4 = c
    t0 = (2*t1 + 3*t2 - t4 -2*tmax) / 4   # time pedestal
    if c2 == c1:
        pattern = 'LR_R'
        angle_sign = np.sign(t4-t2)   
    else:
        pattern = 'RL_L'
        angle_sign = np.sign(t2-t4)  
    angle = crossing_angle(t2, t4, v_drift, h, angle_sign)
    return t0, pattern, angle

def meantimer_134(t, c, tmax, v_drift, h):   # case layers 1-3-4
    t1, t2, t3, t4 = t
    c1, c2, c3, c4 = c
    t0 = (-t1 + 3*t3 + 2*t4 -2*tmax) / 4   # time pedestal
    if c4 == c1:
        pattern = 'L_LR'
        angle_sign = np.sign(t1-t3)
    else:
        pattern = 'R_RL'
        angle_sign = np.sign(t3-t1)
    angle = crossing_angle(t1, t3, v_drift, h, angle_sign)
    return t0, pattern, angle

def meantimer_234(t, c, tmax, v_drift, h):   # case layers 2-3-4
    t1, t2, t3, t4 = t
    c1, c2, c3, c4 = c
    t0 = (t2 + 2*t3 + t4 -2*tmax) / 4   # time pedestal
    if c3 == c2:
        pattern = '_RLR'
        angle_sign = np.sign(t4-t2)
    else:
        pattern = '_LRL'
        angle_sign = np.sign(t2-t4)
    angle = crossing_angle(t2, t4, v_drift, h, angle_sign)
    return t0, pattern, angle
    
def meantimer_1234(t, c, tmax, v_drift, h):   # case layers 1-2-3-4
    t0_123, pattern_123, angle_123 = meantimer_123(t, c, tmax, v_drift, h)
    t0_124, pattern_124, angle_124 = meantimer_124(t, c, tmax, v_drift, h)
    t0_134, pattern_134, angle_134 = meantimer_134(t, c, tmax, v_drift, h)
    t0_234, pattern_234, angle_234 = meantimer_234(t, c, tmax, v_drift, h)
    
    pedestals, angles = [], []   # lists of plausible time pedestals and crossing angles
    pattern = ''
    sampling = 25   # sampling period of the acquisition system (ns)
    
    if np.abs(t0_123-t0_124) < sampling:
        pedestals += [t0_123, t0_124]
        angles += [angle_123, angle_124]
        if pattern == '':
            pattern = pattern_123[:-1] + pattern_124[-1]
    
    if np.abs(t0_123-t0_134) < sampling:
        pedestals += [t0_123, t0_134]
        angles += [angle_123, angle_134]
        if pattern == '':
            pattern = pattern_123[:-1] + pattern_134[-1]
    
    if np.abs(t0_123-t0_234) < sampling:
        pedestals += [t0_123, t0_234]
        angles += [angle_123, angle_234]
        if pattern == '':
            pattern = pattern_123[:-1] + pattern_234[-1]
    
    if np.abs(t0_124-t0_134) < sampling:
        pedestals += [t0_124, t0_134]
        angles += [angle_124, angle_134]
        if pattern == '':
            pattern = pattern_124[:2] + pattern_134[2:]
    
    if np.abs(t0_124-t0_234) < sampling:
        pedestals += [t0_124, t0_234]
        angles += [angle_124, angle_234]
        if pattern == '':
            pattern = pattern_124[:2] + pattern_234[2:]
    
    if np.abs(t0_134-t0_234) < sampling:
        pedestals += [t0_134, t0_234]
        angles += [angle_134, angle_234]
        if pattern == '':
            pattern = pattern_134[0] + pattern_234[1:]
    
    if len(pedestals) == 0:
        return 0, 'FAIL', 0
    else:
        t0, angle = np.mean(pedestals), np.mean(angles)
        return t0, pattern, angle
                                                                              
### end test

# define the function that applies the mean-timer technique to the dataset containing the events
def meantimer(dataframe):
    df = dataframe.copy()
    
    # dictionary used to select the appropriate function
    meantimers = {'123'  : meantimer_123,
                  '124'  : meantimer_124,
                  '134'  : meantimer_134,
                  '234'  : meantimer_234,
                  '1234' : meantimer_1234}

    # dictionary used to convert the pattern of the trajectory into signs of the positions in the cells
    LR_to_sign = {'L' : -1,
                  'R' : +1,
                  '_' : 0}
    
    # detector parameters
    tmax = 390   # maximum drift time (ns)
    L = 42   # length of each cell (mm)
    h = 13   # height of each cell (mm)
    v_drift = L / (2*tmax)   # drift velocity (mm/ns)
    
    # apply the mean-timer functions to the dataset
    df[['PEDESTAL', 'PATTERN', 'ANGLE']] = df.apply(lambda row: meantimers[row['LAYERS']](row[['L1_TIME', 'L2_TIME', 'L3_TIME', 'L4_TIME']],
                                                                                          row[['L1_CELL', 'L2_CELL', 'L3_CELL', 'L4_CELL']],
                                                                                          tmax, v_drift, h), axis=1, result_type="expand")
    
    df = df[df['PATTERN'] != 'FAIL']
    
    for i in range(1, 5):
        df['L'+str(i)+'_DRIFT'] = np.abs(df['L'+str(i)+'_TIME'] - df['PEDESTAL'])
        df = df[(df['L'+str(i)+'_DRIFT'] < tmax) | (np.isnan(df['L'+str(i)+'_DRIFT']))]   # reject events with drift times >= 'tmax'
        df['L'+str(i)+'_X'] = v_drift * df['L'+str(i)+'_DRIFT'] * (df['PATTERN'].str[i-1]).replace(LR_to_sign)
    
    df = df.reset_index(drop=True)
    return df

events = meantimer(events)
events