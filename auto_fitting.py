'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Dashing Growth Curves. If not, see <https://www.gnu.org/licenses/>.
'''

import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d
from scipy.optimize import curve_fit

import math_functions as mf


# Easy Linear method
def autofit_easylinear(x, y, ws):
    '''
        Determine start and end point of the exponential growth phase as well as its associated growth rate by computing
        the growth rates for every window of data points
        - ws: window size
        - x: time points
        - y: population size measurements (expect blanked data), data can be smoothed beforehand using the smooth_data() function
    '''

    # n0 = np.min([y_i for y_i in y if y_i > 0]) # center around minimum measured OD value
    y_log = np.log(np.array(y))
    ws = int(ws)

    # iterate over all subarrays of length ws
    # compute the growth rate for each subarray
    # return the subarray with the highest growth rate
    
    max_growth_rate = 0
    max_growth_rate_std = np.nan
    max_growth_rate_idx = np.nan
    y_intercept = np.nan
    R2_error = np.nan
    for i in range(len(y_log) - ws):
        ydata = y_log[i:i+ws]
        xdata = x[i:i+ws]
        popt, pcov = curve_fit(mf.lin_function, xdata, ydata)
        growth_rate = popt[0]
        if growth_rate > max_growth_rate:
            max_growth_rate = growth_rate
            max_growth_rate_std = np.sqrt(pcov[0, 0])
            y_intercept = popt[1]
            y_intercept_std = np.sqrt(pcov[1, 1])
            max_growth_rate_idx = i
            R2_error = mf.comp_R2(xdata, ydata, popt)

    idx_start = max_growth_rate_idx
    t_start = x[idx_start]
    idx_end = max_growth_rate_idx + ws
    t_end = x[idx_end]
    
    return t_start, t_end, max_growth_rate, max_growth_rate_std, y_intercept, y_intercept_std, R2_error

# deprecated
# def autofit_manual_like(x, y, ws=10, slope_range=0.6, min_window_length=3, b=25):
#     # determine start and end point of exponential growth phase by finding the stretch of linear growth after linearizing the data
#     # expect blanked y values

#     # ws: window size of running mean filter
#     # slope_range: consider all slope values smaller than the max_slope and larger than max_slope * slope_range for finding the exponential growth phase

#     # min_window_length: shortest stretch of datapoints considered for finding the stretch of linear growth

#     # b: weight of R2 value over explained variance
#     # print(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2)
#     y_l = np.log(y.values)

#     y_l_sm = uniform_filter1d(y_l, size=ws)
#     y_l_sm_d = np.diff(y_l_sm, n=1)
#     y_l_sm_d_sm = uniform_filter1d(y_l_sm_d, size=ws)


#     max_slope = np.max(y_l_sm_d_sm)
#     min_slope = max_slope * slope_range


#     where = np.where(y_l_sm_d_sm > min_slope)[0]
#     if where.shape[0] == 0:
#         return None, None
#     window_start_idx = where[0]
#     window_end_idx = where[-1]

#     max_window_length = window_end_idx - window_start_idx
#     fits = []
#     if max_window_length - min_window_length - 1 < 0:
#         return None, None
#     for wl in range(min_window_length, max_window_length + 1):
#         for wp in range(max_window_length - wl):
#             x_start = window_start_idx + wp
#             x_end = x_start + wl
#             xdata = x[x_start:x_end]
#             ydata = y_l[x_start:x_end]
#             try:
#                 popt, pcov = curve_fit(mf.lin_function, xdata, ydata)
#                 r2 = mf.comp_R2(xdata, ydata, popt)

#                 ve = (y_l[x_end] - y_l[x_start]) / (y_l.max() - y_l.min())

#                 ov = b * r2 + ve

#                 fits.append({'window_length': wl, 'window_position': wp, 'R2': r2, 'variance_explained': ve, 'objective_value': ov, 'm': popt[0], 't': popt[1]})
#             except:
#                 fits.append({'window_length': np.nan, 'window_position': np.nan, 'R2': np.nan, 'variance_explained': np.nan, 'objective_value': np.nan, 'm': np.nan, 't': np.nan})
            
    
#     df_fits = pd.DataFrame(fits)
#     df_fits_opt = df_fits.iloc[df_fits['objective_value'].idxmax()]

#     fit_opt_start_idx = int(window_start_idx + df_fits_opt['window_position'])
#     fit_opt_end_idx = int(fit_opt_start_idx + df_fits_opt['window_length'])

#     return fit_opt_start_idx, fit_opt_end_idx



def autofit_gompertz(x, y):
    # fit a Gompertz growth sigmoid curve to the whole dataset
  
    n0 = np.min([y_i for y_i in y if y_i > 0]) # center around minimum measured OD value
    y_log = np.log(np.array(y) / n0)
    
    try:
        popt, pcov = curve_fit(mf.modified_gompertz, x, y_log, p0=[0.1, 0.5, -5], bounds=[[0, 0, -np.inf], [np.inf, np.inf, np.inf]])
        A = popt[0]
        A_std = np.sqrt(pcov[0, 0])
        mu = popt[1]
        mu_std = np.sqrt(pcov[1, 1])
        l = popt[2]
        l_std = np.sqrt(pcov[2, 2])
        return A, A_std, mu, mu_std, l, l_std, n0
    except:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,


def autofit_logistic(x, y):
    # fit a logistic growth sigmoid curve to the whole dataset
    n0 = np.min([y_i for y_i in y if y_i > 0]) # center around minimum measured OD value
    y_log = np.log(np.array(y) / n0)
    
    try:
        popt, pcov = curve_fit(mf.modified_logistic, x, y_log, p0=[0.1, 0.1, 1], bounds=[[0, 0, -np.inf], [np.inf, np.inf, np.inf]])
        A = popt[0]
        A_std = np.sqrt(pcov[0, 0])
        mu = popt[1]
        mu_std = np.sqrt(pcov[1, 1])
        l = popt[2]
        l_std = np.sqrt(pcov[2, 2])
        return A, A_std, mu, mu_std, l, l_std, n0
    except:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,


def autofit_richards(x, y):
     # fit a logistic growth sigmoid curve to the whole dataset
    n0 = np.min([y_i for y_i in y if y_i > 0]) # center around minimum measured OD value
    
    # print(x.shape, y.values[17])
    y_log = np.log(y.values / n0)

    mask = y_log != 0
    y_log = y_log[mask]
    x = x[mask]

    try:
        popt, pcov = curve_fit(mf.modified_richards, x, y_log, maxfev=1000000, p0=[np.max(y_log), np.median(x), 1, 0.5], bounds=[[0, 0, -np.inf, 0.01], [np.inf, np.inf, np.inf, np.inf]]) #
        A = popt[0]
        A_std = np.sqrt(pcov[0, 0])
        mu = popt[1]
        mu_std = np.sqrt(pcov[1, 1])
        l = popt[2]
        l_std = np.sqrt(pcov[2, 2])
        v = popt[3]
        v_std = pcov[3, 3]
        return A, A_std, mu, mu_std, l, l_std, v, v_std, n0
    except:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan


def autofit_schnute(x, y):
     # fit a logistic growth sigmoid curve to the whole dataset
    n0 = np.min([y_i for y_i in y if y_i > 0]) # center around minimum measured OD value
    y_log = np.log(np.array(y) / n0)
    
    try:
        popt, pcov = curve_fit(mf.modified_schnute, x, y_log, p0=[2, 0.5, 3, -1], maxfev=10000, ) #bounds=[[0, 0.001, -np.inf, -np.inf], [np.inf, 10, np.inf, 0]]
        A = popt[0]
        A_std = np.sqrt(pcov[0, 0])
        mu = popt[1]
        mu_std = np.sqrt(pcov[1, 1])
        l = popt[2]
        l_std = np.sqrt(pcov[2, 2])
        v = popt[3]
        v_std = pcov[3, 3]
        return A, A_std, mu, mu_std, l, l_std, v, v_std, n0
    except:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan