'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Dashing Growth Curves. If not, see <https://www.gnu.org/licenses/>.
'''

import ast
from os import lstat
from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import uncertainties as uc
from uncertainties import unumpy as ucn
from scipy.optimize import curve_fit
import dash
from string import ascii_uppercase
import auto_fitting


import math_functions as mf
import auxilliary_functions as ax
import default_settings as ds



def format_growth_rate_values(growth_rate_data_sp):
    # nan values can't be stored in serialized dicts in Dash stores, that's why they are stored as strings and upon retrieval are converted into np.nan
    growth_rate_data_sp_formatted = {}
    for key in growth_rate_data_sp:
        if growth_rate_data_sp[key] == 'NaN':
            growth_rate_data_sp_formatted[key] = np.nan
        else:
            growth_rate_data_sp_formatted[key] = growth_rate_data_sp[key]
    return growth_rate_data_sp_formatted



def format_output_strings(mu, mu_std, dt, dt_std, t0, t0_std, doublings, doublings_log, doublings_log_std, maxOD, error, fitting_mode, pop_size_measure):
    # format growth rate values for display in UI
    out_growth_rate = dcc.Markdown('growth rate \[h<sup>-1</sup>\] = {0:.2f} &plusmn; {1:.2f}'.format(mu, mu_std), dangerously_allow_html=True,)
    out_doubling_time = dcc.Markdown('doubling time \[h\] = {0:.2f} &plusmn; {1:.2f}'.format(dt, dt_std))
    out_lag_time = dcc.Markdown('lag time \[h\] = {0:.2f} &plusmn; {1:.2f}'.format(t0, t0_std))
    out_doublings = dcc.Markdown('doublings = {0:.2f}'.format(doublings))
    out_doublings_log = dcc.Markdown('doublings in log-phase = {0:.2f} &plusmn; {1:.2f}'.format(doublings_log, doublings_log_std))
    out_yield = dcc.Markdown('yield \[{0}\] = {1:.2f}'.format(pop_size_measure, maxOD), dangerously_allow_html=True)
    
    if (fitting_mode == 'Manual') or (fitting_mode == 'Manual-like') or (fitting_mode == 'Easy Linear'):
        out_error = dcc.Markdown('R<sup>2</sup> = {0:.3f}'.format(error), dangerously_allow_html=True)
    else:
        out_error = dcc.Markdown('RMSE = {0:.3f}'.format(error))
    return out_growth_rate, out_doubling_time, out_lag_time, out_doublings, out_doublings_log, out_yield, out_error




def add_to_growth_data_dict(growth_data_data_sp, 
                            t0='NaN', t0_std='NaN', t0_idx='NaN',
                            t1='NaN', t1_std='NaN', t1_idx='NaN',
                            # lambda='NaN', lambda_std='NaN',
                            mumax='NaN', mumax_std='NaN',
                            doublingslog='NaN', doublingslog_std='NaN',
                            dt='NaN', dt_std='NaN',
                            A='NaN', A_std='NaN',
                            n0='NaN',
                            doublings='NaN', 
                            Yield='NaN',
                            error='NaN',
                            fitting_mode='NaN',
                            smoothing_window='NaN'
                            ):

    # lag time, i.e. beginning of logistic growth phase (if growth curve was fitted manually, no error associated with lag time)
    growth_data_data_sp['t0'] = t0
    growth_data_data_sp['t0_std'] = t0_std
    growth_data_data_sp['t0_idx'] = t0_idx

    # end of logistic growth phase
    growth_data_data_sp['t1'] = t1
    growth_data_data_sp['t1_std'] = t1_std
    growth_data_data_sp['t1_idx'] = t1_idx

    # max growth rate
    growth_data_data_sp['mumax'] = mumax
    growth_data_data_sp['mumax_std'] = mumax_std

    # doubling time
    growth_data_data_sp['dt'] = dt
    growth_data_data_sp['dt_std'] = dt_std

    # doublings in logarithmic growth phase
    growth_data_data_sp['doublings_log'] = doublingslog
    growth_data_data_sp['doublings_log_std'] = doublingslog_std

    # carrying capacity
    growth_data_data_sp['carrying_capacity'] = A
    growth_data_data_sp['carrying_capacity_std'] = A_std

    # minimum non-negative measured OD
    growth_data_data_sp['n0'] = n0

    # doublings between lowest and highest measured OD
    growth_data_data_sp['doublings'] = doublings

    # max. measures OD
    growth_data_data_sp['yield'] = Yield

    # error measure: R2 or RMSE
    growth_data_data_sp['error'] = error

    # fitting mode used to gather data
    growth_data_data_sp['fitting_mode'] = fitting_mode

    # data smoothing window size
    growth_data_data_sp['smoothing_window'] = smoothing_window

    return growth_data_data_sp



def register_gd_callbacks(app):
    # callbacks in a file separate from main app need to be registered separately
    @app.callback(
                    Output('growth_rate', 'children'),
                    Output('doubling_time', 'children'),
                    Output('lag_time', 'children'),
                    Output('doublings', 'children'),
                    Output('doublings_log', 'children'),
                    Output('yield', 'children'),
                    Output('error', 'children'),
                    Output('store_growth_data', 'data'),
                    Output('message_area_fits', 'children'),
                    Input('fig_log', 'selectedData'),
                    Input('store_upload_flag', 'data'),
                    Input('store_sample_idx', 'data'),
                    Input('store_sample_names', 'data'),
                    Input('fig_log', 'clickData'),
                    Input('store_growth_data_auto', 'data'),
                    Input('store_default_popsizemeasure', 'data'),
                    State('store_growth_data', 'data'),
                    State('store_data_df', 'data'),
                    State('store_data_df_smoothed', 'data'),
                    State('store_smoother_flag', 'data'),
                    State('store_blank_locs', 'data'),
                    State('store_sample_locations', 'data'),
                    State('store_smoother_value', 'data'),
                    # background = True,

                    prevent_initial_call = True
    )
    def growth_data(selected_data, upload_flag, sample_idx, sample_names, click_data, growth_data_auto, pop_size_measure, growth_rate_data, df, df_smoothed, smoother_flag, blank_locs, sample_locations, smoother_ws):
        if df is None:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, ''

        # load data
        if smoother_flag == False:
            df = pd.DataFrame.from_dict(df, orient='tight')
        else:
            df = pd.DataFrame.from_dict(df_smoothed, orient='tight')


        # initialize growth data store
        if dash.callback_context.triggered[0]['prop_id'] == 'store_upload_flag.data':
            sample_locations = ax.set_sample_locations(df)
            sample_names = df.index
            growth_rate_data = {}
            for idx, s in enumerate(sample_locations):
                growth_rate_data[s] = {'sample_name': df.index[idx], 
                                        'excluded_flag': False, 
                                        'fitting_mode': 'NaN',
                                        't0': 'NaN', 't1': 'NaN', 
                                        't0_std': 'NaN', 't1_std': 'NaN',
                                        't0_idx': 'NaN', 't1_idx': 'NaN', 'n0': 'NaN', 
                                        # 'lambda': 'NaN', 'lambda_std': 'NaN',
                                        'mumax': 'NaN', 'mumax_std': 'NaN', 
                                        'dt': 'NaN', 'dt_std': 'NaN', 
                                        'doublings': 'NaN', 
                                        'doublings_log': 'NaN', 'doublings_log_std': 'NaN',
                                        'yield': 'NaN',
                                        'v': 'NaN', 'v_std': 'NaN',
                                        'carrying_capacity': 'NaN', 
                                        'error': 'NaN', # R2 if manual or manual-like fit, else RMSE as error measures
                                        'smoothing_window': 'NaN',
                                        }
            
         
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, growth_rate_data, ''

        # change sample name
        elif dash.callback_context.triggered[0]['prop_id'] == 'store_sample_names.data':
            for idx, s in enumerate(sample_locations):
                growth_rate_data[s]['sample_name'] = sample_names[idx]
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, growth_rate_data, ''

        # exclude or include sample in analysis
        elif dash.callback_context.triggered[0]['prop_id'] == 'fig_log.clickData':
            sp = list(growth_rate_data)[sample_idx]
            growth_rate_data[sp]['excluded_flag'] = not growth_rate_data[sp]['excluded_flag']
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, growth_rate_data, ''


        # compute growth data (manual data selection)
        elif (dash.callback_context.triggered[0]['prop_id'] == 'fig_log.selectedData') and (len(selected_data) > 1):
            df.index = sample_names
            sp = sample_locations[sample_idx]
            

            blanks = blank_locs[sp]
            blanks_mean = df.loc[blanks].mean(axis=0)

            sample_trace_0 = df.iloc[sample_idx]
            sample_trace = sample_trace_0.values

            nan_mask = ~np.isnan(sample_trace)
            nan_mask_blanks = ~np.isnan(blanks_mean)
                
            t_blanked = sample_trace_0.index.values[nan_mask & nan_mask_blanks]
            sample_trace_blanked = sample_trace[nan_mask & nan_mask_blanks] - blanks_mean[nan_mask & nan_mask_blanks] 


            # time points
            t = df.columns.tolist()

            # # blanks
            # blanks = blank_locs[sp]
            # blanks_mean = df.loc[blanks].mean(axis=0)

            # sample trace
            # sample_trace = df.iloc[sample_idx]
            # sample_trace_blanked = sample_trace - blanks_mean

            # selection idx
            t0 = selected_data['range']['x'][0]
            y0 = selected_data['range']['y'][0]
            t1 = selected_data['range']['x'][1]
            y1 = selected_data['range']['y'][1]

            sample_trace_blanked_temp = sample_trace_blanked.copy().reset_index()
            t0_idx = sample_trace_blanked_temp[(sample_trace_blanked_temp['index'] >= t0) & (sample_trace_blanked_temp[0] >= y0)].index[0]
            t1_idx = sample_trace_blanked_temp[(sample_trace_blanked_temp['index'] <= t1) & (sample_trace_blanked_temp[0] <= y1)].index[-1]


            # fit exponential curve
            x = t_blanked[t0_idx: t1_idx + 1]
            y = sample_trace_blanked.iloc[t0_idx: t1_idx + 1]
            popt_exp, pcov_exp = curve_fit(mf.exp_function, x, y, bounds=([0, 0], [5, np.inf]))

            # compute r2 value
            r2 = mf.comp_R2(np.array(x), np.log(y).values, [popt_exp[1], np.log(popt_exp[0])])

            # save growth parameters
            mu_u = uc.ufloat(popt_exp[1], np.sqrt(pcov_exp[1,1]))
            dt_u = ucn.log(2) / mu_u
            doublings = np.log2(sample_trace_blanked.max() / sample_trace_blanked[sample_trace_blanked > 0].min())
            doublings_log = np.log2(sample_trace_blanked.iloc[t1_idx] / sample_trace_blanked.iloc[t0_idx])
            doublings_log_std = 0
            n0 = popt_exp[0]
            Yield = sample_trace_blanked.max()
            fitting_mode = 'Manual'

            growth_rate_data[sp] = add_to_growth_data_dict(growth_rate_data[sp], 
                                                            t_blanked[t0_idx], 0, t0_idx, 
                                                            t_blanked[t1_idx], 0, t1_idx,
                                                            mu_u.n, mu_u.std_dev,
                                                            doublings_log, doublings_log_std,
                                                            dt_u.n, dt_u.std_dev,
                                                            n0=n0, 
                                                            doublings=doublings,
                                                            Yield=Yield,
                                                            error=r2,
                                                            fitting_mode=fitting_mode,
                                                            smoothing_window=smoother_ws
                                                            )

            # format values for display in UI
            out_growth_rate, out_doubling_time, out_lag_time, out_doublings, out_doublings_log, out_yield, out_error = format_output_strings(growth_rate_data[sp]['mumax'],
                                                                                                                                    growth_rate_data[sp]['mumax_std'],
                                                                                                                                    growth_rate_data[sp]['dt'],
                                                                                                                                    growth_rate_data[sp]['dt_std'],
                                                                                                                                    growth_rate_data[sp]['t0'],
                                                                                                                                    growth_rate_data[sp]['t0_std'],
                                                                                                                                    growth_rate_data[sp]['doublings'],
                                                                                                                                    growth_rate_data[sp]['doublings_log'],
                                                                                                                                    growth_rate_data[sp]['doublings_log_std'],
                                                                                                                                    growth_rate_data[sp]['yield'],
                                                                                                                                    growth_rate_data[sp]['error'],
                                                                                                                                    growth_rate_data[sp]['fitting_mode'],
                                                                                                                                    pop_size_measure
                                                                                                                                        )
            return out_growth_rate, out_doubling_time, out_lag_time, out_doublings, out_doublings_log, out_yield, out_error, growth_rate_data, ''

        # update growth rate message area on page turn
        elif dash.callback_context.triggered[0]['prop_id'] == 'store_sample_idx.data':
            current_sample_position = sample_locations[sample_idx]
            growth_rate_data_sp = growth_rate_data[current_sample_position]
            growth_rate_data_sp_formatted = format_growth_rate_values(growth_rate_data_sp)
          

            out_growth_rate, out_doubling_time, out_lag_time, out_doublings, out_doublings_log, out_yield, out_error = \
                format_output_strings(growth_rate_data_sp_formatted['mumax'],
                                      growth_rate_data_sp_formatted['mumax_std'],
                                      growth_rate_data_sp_formatted['dt'],
                                      growth_rate_data_sp_formatted['dt_std'],
                                      growth_rate_data_sp_formatted['t0'],
                                      growth_rate_data_sp_formatted['t0_std'],
                                      growth_rate_data_sp_formatted['doublings'],
                                      growth_rate_data_sp_formatted['doublings_log'],
                                      growth_rate_data_sp_formatted['doublings_log_std'],
                                      growth_rate_data_sp_formatted['yield'],
                                      growth_rate_data_sp_formatted['error'],
                                      growth_rate_data_sp_formatted['fitting_mode'],
                                      pop_size_measure,
                                        )
                                     
            return out_growth_rate, out_doubling_time, out_lag_time, out_doublings, out_doublings_log, out_yield, out_error, dash.no_update, ''
        
        # get autofit data
        elif dash.callback_context.triggered[0]['prop_id'] == 'store_growth_data_auto.data':
            growth_rate_data = growth_data_auto
            current_sample_position = sample_locations[sample_idx]
            growth_rate_data_sp = growth_rate_data[current_sample_position]
            growth_rate_data_sp_formatted = format_growth_rate_values(growth_rate_data_sp)
           
            out_growth_rate, out_doubling_time, out_lag_time, out_doublings, out_doublings_log, out_yield, out_error = format_output_strings(growth_rate_data_sp_formatted['mumax'],
                                                                                                                                  growth_rate_data_sp_formatted['mumax_std'],
                                                                                                                                  growth_rate_data_sp_formatted['dt'],
                                                                                                                                  growth_rate_data_sp_formatted['dt_std'],
                                                                                                                                  growth_rate_data_sp_formatted['t0'],
                                                                                                                                  growth_rate_data_sp_formatted['t0_std'],
                                                                                                                                  growth_rate_data_sp_formatted['doublings'],
                                                                                                                                  growth_rate_data_sp_formatted['doublings_log'],
                                                                                                                                  growth_rate_data_sp_formatted['doublings_log_std'],
                                                                                                                                  growth_rate_data_sp_formatted['yield'],
                                                                                                                                  growth_rate_data_sp_formatted['error'],
                                                                                                                                  growth_rate_data_sp_formatted['fitting_mode'],
                                                                                                                                  pop_size_measure
                                                                                                                                )
                                                                                                                                    
            return out_growth_rate, out_doubling_time, out_lag_time, out_doublings, out_doublings_log, out_yield, out_error, growth_rate_data, ''

        
        
        else:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update





    ###################
    # autofitting
    ###################
    style_auto_fit_div = {'visibility': 'visible',
                          'height': '100vh', 'width': '100vw', 
                          'position': 'absolute', 'left': '0', 'top': '0',
                          'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 
                          'background-color': 'rgb(245, 245, 245)', 
                          'z-index': '100'
                                }

    style_progress_bar = {'visibility': 'visible',
                          'height': '2em', 'width': '100%'
                            }

    style_cancel_button = {
                            'visibility': 'visible', 
                            'height':'25px', 'width': '110px', 
                            'display': 'flex', 'justify-content': 'center', 'align-items': 'center'
                            }
    @app.callback(
                    output = Output('store_growth_data_auto', 'data'),
                    inputs = Input('button_auto_fit', 'n_clicks'),
                    state = [State('store_data_df', 'data'),
                              State('store_data_df_smoothed', 'data'),
                              State('store_smoother_flag', 'data'),
                              State('store_growth_data', 'data'),
                              State('store_blank_locs', 'data'),
                              State('store_auto_fit_ws', 'data'),
                              State('store_auto_fit_slope_range', 'data'),
                              State('store_auto_fit_r2_var_weight', 'data'),
                              State('dropdown_fitting_algorithms', 'value'),
                              State('easy_linear_window_size', 'value'),
                              State('store_smoother_value', 'data'),
                              ],
                    background = True,
                    running = [
                                (Output('auto_fit_div', 'style'),
                                        style_auto_fit_div,
                                        {'visibility': 'hidden'}
                                ),
                                (Output('progress_count', 'style'),
                                        {'visibility': 'visible', 'justify-content': 'center'},
                                        {'visibility': 'hidden'},
                                ),
                                (Output("progress_bar", "style"),
                                        style_progress_bar,
                                        {"visibility": "hidden"},
                                ),
                                (Output('button_cancel_autofit', 'style'),
                                        style_cancel_button,
                                        {'visibility': 'hidden'}
                                ),
                                (Output('body_layout', 'style'),
                                        {'overflow': 'hidden', 'position': 'fixed'},
                                        {'overflow': 'visible'}
                                ),
                                
                                ],
                    progress = [Output('progress_bar', 'value'), Output('progress_bar', 'max'), Output('progress_count', 'children')],
                    cancel = [Input('button_cancel_autofit', 'n_clicks')],
                    prevent_initial_call = True
    )
    def auto_fit(set_progress, button_clicks, df, df_smoothed, smoother_flag, growth_rate_data, blank_locs, auto_fit_ws, auto_fit_sr, auto_fit_weight, fitting_algorithm, window_size, smoother_ws):
        # autofit on button press
        if growth_rate_data is None:
            return dash.no_update

        # load data
        if smoother_flag == False:
            df = pd.DataFrame.from_dict(df, orient='tight')
        else:
            df = pd.DataFrame.from_dict(df_smoothed, orient='tight')

        skip_list = ds.accepted_blank_names
        n_samples_total = len(growth_rate_data)
        for i, sp in enumerate(growth_rate_data):
            set_progress((str(i + 1), str(n_samples_total), '{} / {}'.format(i + 1, n_samples_total)))

            if any([x in growth_rate_data[sp]['sample_name'] for x in skip_list]) or (growth_rate_data[sp]['sample_name'] == '-'):
                continue

            else:
                blanks = blank_locs[sp]
                blanks_mean = df.loc[blanks].mean(axis=0)

                sample_trace_0 = df.iloc[i]
                sample_trace = sample_trace_0.values

                nan_mask = ~np.isnan(sample_trace)
                nan_mask_blanks = ~np.isnan(blanks_mean)
                
                t_blanked = sample_trace_0.index.values[nan_mask & nan_mask_blanks]
                sample_trace_blanked = sample_trace[nan_mask & nan_mask_blanks] - blanks_mean[nan_mask & nan_mask_blanks] 

                
        
                
                # remove negative and zero value (taking the log negative values become NaN, fitting algorithms can't handle NaNs and infinities)
                sample_trace_blanked_log = np.log(sample_trace_blanked)
                nan_inf_mask = (~np.isnan(sample_trace_blanked_log)) & (sample_trace_blanked_log != - np.inf)
                sample_trace_blanked = sample_trace_blanked[nan_inf_mask]
                t_blanked = t_blanked[nan_inf_mask]
                
                if sample_trace_blanked.shape[0] <= 0.1 * sample_trace_blanked_log.shape[0]:
                    # don't analyzed samples that contain majority negative values after blanking
                    continue

                # fitting
                if fitting_algorithm == 'Manual-like':
                    t0_idx, t1_idx = auto_fitting.autofit_manual_like(t_blanked, sample_trace_blanked, ws=auto_fit_ws, slope_range=auto_fit_sr, b=auto_fit_weight)

                    if t0_idx is None:
                        continue

                    try:
                        x = t_blanked[t0_idx: t1_idx]
                        y = sample_trace_blanked.iloc[t0_idx: t1_idx]
                        popt_exp, pcov_exp = curve_fit(mf.exp_function, x, y, bounds=([0, 0.001], [5, 2]))
                        
                    except:
                        continue
                    
                    # compute r2 value
                    r2 = mf.comp_R2(np.array(x), np.log(y), [popt_exp[1], np.log(popt_exp[0])])


                    mu_u = uc.ufloat(popt_exp[1], np.sqrt(pcov_exp[1,1]))
                    dt_u = ucn.log(2) / mu_u

                    doublings_log = np.log2(sample_trace_blanked.iloc[t1_idx] / sample_trace_blanked.iloc[t0_idx])
                    doublings_log_std = 0

                    Yield = sample_trace_blanked.max()

                    fitting_mode = 'Manual-like'

                    growth_rate_data[sp] = add_to_growth_data_dict(growth_rate_data[sp], 
                                                t_blanked[t0_idx], 0, t0_idx, 
                                                t_blanked[t1_idx], 0, t1_idx,
                                                mu_u.n, mu_u.std_dev,
                                                doublings_log, doublings_log_std,
                                                dt_u.n, dt_u.std_dev,
                                                n0=n0, 
                                                doublings=doublings,
                                                Yield=Yield,
                                                error=r2,
                                                fitting_mode=fitting_mode,

                                                )
                
                else:
                    if 'Gompertz' in fitting_algorithm:
                        # A: carrying capacity
                        # mu: max growth rate
                        # l: lag time (i.e. beginning of exponential phase)
                        # t1: beginning of stationary phase (i.e. end of exponential phase)
                        A, A_std, mu, mu_std, l, l_std, n0 = auto_fitting.autofit_gompertz(t_blanked, sample_trace_blanked)


                        if (np.isnan(A)) or (np.isnan(mu_std)) or (mu_std == np.inf):
                            continue
                        
                        A_u = uc.ufloat(A, A_std)
                        mu_u = uc.ufloat(mu, mu_std)
                        l_u = uc.ufloat(l, l_std)

                        if fitting_algorithm == 'Gompertz - tight':
                            t0_u = l_u + 0.014 * A_u / mu_u
                            t1_u = l_u + 0.72 * A_u / mu_u
                            ratio = ucn.exp(mf.modified_gompertz(t1_u, A_u, mu_u, l_u)) / ucn.exp(mf.modified_gompertz(l_u, A_u, mu_u, l_u))
                        elif fitting_algorithm == 'Gompertz - conventional':
                            t0_u = l_u
                            t1_u = (A_u + mu_u * l_u) / mu_u # end of exponential phase
                            ratio = ucn.exp(mf.modified_gompertz(t1_u, A_u, mu_u, l_u)) / ucn.exp(mf.modified_gompertz(l_u, A_u, mu_u, l_u))
                        doublings_log_u = ucn.log(ratio) / ucn.log(2) 
                    
                    elif 'Logistic' in fitting_algorithm:
                        # A: carrying capacity
                        # mu: max growth rate
                        # l: lag time (i.e. beginning of exponential phase)
                        # t1: beginning of stationary phase (i.e. end of exponential phase)
                        A, A_std, mu, mu_std, l, l_std, n0 = auto_fitting.autofit_logistic(t_blanked, sample_trace_blanked)

                        if (np.isnan(A)) or (np.isnan(mu_std)) or (mu_std == np.inf):
                            continue  
                        A_u = uc.ufloat(A, A_std)
                        mu_u = uc.ufloat(mu, mu_std)
                        l_u = uc.ufloat(l, l_std)
                        if fitting_algorithm == 'Logistic - tight':
                            t0_u = l_u + 0.17 * A_u / mu_u
                            t1_u = l_u + 0.83 * A_u / mu_u
                            ratio = ucn.exp(mf.modified_logistic(t1_u, A_u, mu_u, l_u)) / ucn.exp(mf.modified_logistic(l_u, A_u, mu_u, l_u))

                        elif fitting_algorithm == 'Logistic - conventional':
                            t0_u = l_u
                            t1_u = (A_u + mu_u * l_u) / mu_u # end of exponential phase
                            ratio = ucn.exp(mf.modified_logistic(t1_u, A_u, mu_u, l_u)) / ucn.exp(mf.modified_logistic(l_u, A_u, mu_u, l_u)) 
                        doublings_log_u = ucn.log(ratio) / ucn.log(2) 
                    
                    elif 'Easy Linear' in fitting_algorithm:
                        # mu: max growth rate
                        # l: lag time (i.e. beginning of exponential phase)
                        # t1: beginning of stationary phase (i.e. end of exponential phase)
                        t0, t1, mu, mu_std, y_intercept, y_intercept_std, R2_error = auto_fitting.autofit_easylinear(t_blanked, sample_trace_blanked, window_size)
                        
                        A_u = uc.ufloat(np.nan, np.nan)
                        # n0 = mf.lin_function(t0, mu, y_intercept) / np.exp(mf.lin_function(t0, mu, y_intercept))
                        n0 = np.exp(y_intercept)
                        t0_u = uc.ufloat(t0, 0)
                        t1_u = uc.ufloat(t1, 0)
                        mu_u = uc.ufloat(mu, mu_std)
                        y_intercept_u = uc.ufloat(y_intercept, y_intercept_std)

                        ratio = ucn.exp(mf.lin_function(t1, mu_u, y_intercept_u)) / ucn.exp(mf.lin_function(t0, mu_u, y_intercept_u))
                        doublings_log_u = ucn.log(ratio) / ucn.log(2)

                

                    # compute doubling time
                    dt_u = ucn.log(2) / mu_u

                    # compute yield (i.e. max OD measurement)
                    maxOD600 = sample_trace_blanked.max()

                    # compute doublings in measured data (take the smallest non-negative value as reference point)
                    doublings = np.log2(sample_trace_blanked.max() / sample_trace_blanked[sample_trace_blanked > 0].min())
                   
                    # fill in data
                    growth_rate_data[sp] = add_to_growth_data_dict(
                                                growth_rate_data[sp], 
                                                ax.format_value_for_store(t0_u.n), ax.format_value_for_store(t0_u.std_dev), 'NaN', 
                                                ax.format_value_for_store(t1_u.n), ax.format_value_for_store(t1_u.std_dev), 'NaN',
                                                ax.format_value_for_store(mu_u.n), ax.format_value_for_store(mu_u.std_dev),
                                                ax.format_value_for_store(doublings_log_u.n), ax.format_value_for_store(doublings_log_u.std_dev),
                                                ax.format_value_for_store(dt_u.n), ax.format_value_for_store(dt_u.std_dev),
                                                ax.format_value_for_store(A_u.n), ax.format_value_for_store(A_u.std_dev),
                                                n0=ax.format_value_for_store(n0), 
                                                doublings=ax.format_value_for_store(doublings),
                                                Yield=ax.format_value_for_store(maxOD600) ,
                                                fitting_mode=fitting_algorithm,
                                                smoothing_window=smoother_ws
                                                )
                    t_fit, y_fit = ax.generate_fitted_curve(t_blanked, fitting_algorithm, growth_rate_data[sp], t_blanked.shape[0])
                    
                    if 'Easy Linear' in fitting_algorithm:
                        growth_rate_data[sp]['error'] = R2_error
                    else:
                        rmse = mf.rmse(np.array(sample_trace_blanked), y_fit)
                        growth_rate_data[sp]['error'] = rmse
                   
        return growth_rate_data