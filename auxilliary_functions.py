'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Dashing Growth Curves. If not, see <https://www.gnu.org/licenses/>.
'''


import dash_bootstrap_components as dbc
from dash import html
from string import ascii_uppercase
import numpy as np

import math_functions as mf

################################################
# graph configs
################################################
def graph_config(f_name):
    config = {
                'toImageButtonOptions': {
                    'format': 'svg', # one of png, svg, jpeg, webp
                    'filename': f_name,
                    'height': 500,
                    'width': 1000,
                    'scale': 0.5 # Multiply title/legend/axis/canvas sizes by this factor
                },
                'displaylogo': False,
                
                'modeBarButtonsToRemove': ['pan', 'zoomin', 'zoomout', 'zoom', 'select2D', 'autoscale', 'lasso']
            }
    return config

################################################
# download buttons
################################################
def create_download_button(name):
    button_out = dbc.Button(html.B(name), 
                            color='secondary',
                            style={
                                    'height':'60px', 
                                    'width': '100px'
                                    }
                                    )
    return button_out


################################################
# link buttons
################################################
def create_link_button(name, target):
    button_out = dbc.Button(html.B(name), 
                            color='secondary',
                            target=target,
                            href=target,
                            style={
                                    'height':'55px', 
                                    'width': '150px',
                                    'display': 'flex',
                                    'align-items': 'center',
                                    'justify-content': 'center',
                                    }
                                    )
    return button_out


################################################
# set sample locations
################################################
def set_sample_locations(df):
    # generate sample locations to fit 12, 24, 96 or 384 well format
    # if data wasn't collected from any of the type, just generate numerical IDs
    sample_locations = []
    if df.shape[0] == 384:
        for x in ascii_uppercase[:16]:
            for y in np.arange(1,25):
                sample_locations.append('{}{}'.format(x, y))
    elif df.shape[0] == 96:
        for x in ascii_uppercase[:8]:
            for y in np.arange(1,13):
                sample_locations.append('{}{}'.format(x, y))
    elif df.shape[0] == 24:
        for x in ascii_uppercase[:4]:
            for y in np.arange(1,7):
                sample_locations.append('{}{}'.format(x, y))
    elif df.shape[0] == 12:
        for x in ascii_uppercase[:3]:
            for y in np.arange(1,5):
                sample_locations.append('{}{}'.format(x, y))
    else:
        for i in np.arange(1, df.shape[0] + 1):
            sample_locations.append('{}'.format(i))
    return sample_locations


################################################
# generate alert
################################################
def generate_alert(alert_message):
    alert = dbc.Alert(alert_message,
                        duration = 10000,
                        color = 'danger',
                    )
    return alert



################################################
# generate fitted curve
################################################
def generate_fitted_curve(t, fitting_algorithm, growth_data_sp, n_iter=1000):
    t0_idx = growth_data_sp['t0_idx']
    t1_idx = growth_data_sp['t1_idx']
    mu = growth_data_sp['mumax']
    n0 = growth_data_sp['n0']
    l = growth_data_sp['t0']
    A = growth_data_sp['carrying_capacity']
    v = growth_data_sp['v']

    # for tight fits, need to convert lag time value to lambda parameter
    if fitting_algorithm == 'Logistic - tight':
        l = l - 0.17 * A / mu
    elif fitting_algorithm == 'Gompertz - tight':
        l = l - 0.014 * A / mu

    # create timepoints
    if fitting_algorithm in ['Manual', 'Manual-like']:
        t_fit_start = t[t0_idx]
        t_fit_end = t[t1_idx]
    else:
        t_fit_start = t[0]
        t_fit_end = t[-1]

    t_fit = np.linspace(t_fit_start, t_fit_end, n_iter)

    # create fit values (i.e. associated y-values)
    if fitting_algorithm in ['Manual', 'Manual-like']:
        
        y_fit = mf.exp_function(t_fit, n0, mu)

    elif 'Gompertz' in fitting_algorithm:
        y_gompertz_fit = mf.modified_gompertz(t_fit, A, mu, l)
        y_fit = np.exp(y_gompertz_fit) * n0

    elif 'Logistic' in fitting_algorithm:
        y_logistic_fit = mf.modified_logistic(t_fit, A, mu, l)
        y_fit = np.exp(y_logistic_fit) * n0

    elif fitting_algorithm == 'Richards':
        y_richards_fit = mf.modified_richards(t_fit, A, mu, l, v)
        y_fit = np.exp(y_richards_fit) * n0
    
    elif fitting_algorithm == 'Schnute':
        y_schnute_fit = mf.modified_schnute(t_fit, A, mu, l, v)
        y_fit = np.exp(y_schnute_fit) * n0
    return t_fit, y_fit



def generate_start_end_logphase_indicator_lines(fitting_algorithm, growth_data_sp, sample_trace_blanked, n_iter=1000):

    t0 = growth_data_sp['t0']
    t0_std = growth_data_sp['t0_std']

    t1 = growth_data_sp['t1']
    t1_std = growth_data_sp['t1_std']
        
    A = growth_data_sp['carrying_capacity']
    mu = growth_data_sp['mumax']
    l = growth_data_sp['t0']
    n0 = growth_data_sp['n0']
    v = growth_data_sp['v']

    # for tight fits, need to convert lag time value to lambda parameter
    if fitting_algorithm == 'Logistic - tight':
        l = l - 0.17 * A / mu
    elif fitting_algorithm == 'Gompertz - tight':
        l = l - 0.014 * A / mu

    x_0 = np.ones(n_iter) * t0
    x_1 = np.ones(n_iter) * t1
    


    if fitting_algorithm in ['Manual', 'Manual-like']:
        t0_idx = growth_data_sp['t0_idx']
        y0 = sample_trace_blanked.iloc[t0_idx]
        t1_idx = growth_data_sp['t1_idx']
        y1 = sample_trace_blanked.iloc[t1_idx]

        hovertext_start = ['start log-phase: {0:.2f} h'.format(t0) for x in range(n_iter)]
        hovertext_end = ['end log-phase: {0:.2f} h'.format(t1) for x in range(n_iter)]

    else:
        if 'Gompertz' in fitting_algorithm:
            y0 = np.exp(mf.modified_gompertz(t0, A, mu, l)) * n0
            y1 = np.exp(mf.modified_gompertz(t1, A, mu, l)) * n0
        elif 'Logistic' in fitting_algorithm:
            y0 = np.exp(mf.modified_logistic(t0, A, mu, l)) * n0
            y1 = np.exp(mf.modified_logistic(t1, A, mu, l)) * n0
        elif fitting_algorithm == 'Richards':
            y0 = np.exp(mf.modified_richards(t0, A, mu, l, v)) * n0
            y1 = np.exp(mf.modified_richards(t1, A, mu, l, v)) * n0
        elif fitting_algorithm == 'Schnute':
            y0 = np.exp(mf.modified_schnute(t0, A, mu, l, v)) * n0
            y1 = np.exp(mf.modified_schnute(t1, A, mu, l, v)) * n0
        hovertext_start = ['start log-phase: {0:.2f} &plusmn; {1:.2f} h'.format(t0, t0_std) for x in range(n_iter)]
        hovertext_end = ['end log-phase: {0:.2f} h &plusmn; {1:.2f}'.format(t1, t1_std) for x in range(n_iter)]
    y_0 = np.linspace(0, y0, n_iter)
    y_1 = np.linspace(0, y1, n_iter)    

    return x_0, y_0, x_1, y_1, hovertext_start, hovertext_end


################################################
# format nan for store
################################################
# np.nan value cannot be stored in serialized dict (get turned to None value), need to convert them to 'NaN' (a string)
def format_value_for_store(x):
    if ~np.isnan(x):
        return x
    else:
        return 'NaN'