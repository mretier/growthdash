'''
author: Michael A. Reiter


This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>.
'''

from dash import Dash, html, dcc, Output, Input, State
import dash
import dash_bootstrap_components as dbc
from dash import DiskcacheManager, CeleryManager, Input, Output, html

import os

import pandas as pd
import numpy as np

import base64
from base64 import b64encode
import io

from PIL import Image
import re

import plotly.graph_objects as go
import plotting as pl

import math_functions as mf
import growth_data as gd
import default_settings as ds
import messages as ms
import auxilliary_functions as ax

################################################
# initialize app
################################################
if 'REDIS_URL' in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery
    celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'], include=['growth_data'], CELERY_REDIS_MAX_CONNECTIONS=18, BROKER_POOL_LIMIT=0)
    background_callback_manager = CeleryManager(celery_app)

else:
    # Diskcache for non-production apps when developing locally
    import diskcache
    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)


external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME, dbc.icons.BOOTSTRAP]
app = Dash(__name__,
            external_stylesheets=external_stylesheets,
            background_callback_manager=background_callback_manager,
            )

server = app.server

################################################
# app layout
################################################
# register external callbacks
gd.register_gd_callbacks(app)


############
# stores
############
stores = html.Div([
    dcc.Store(id = 'store_sample_idx', data=0),         # store idx of currently selectec sample
    dcc.Store(id = 'store_data_df'),                    # store uploaded data as dictionary (operation on it as dataframe)
    dcc.Store(id = 'store_data_df_smoothed'),           # store smoothed data
    dcc.Store(id = 'store_smoother_value', data=0),     # store used smoothing window size
    dcc.Store(id = 'store_smoother_flag', data=False),  # store indicator if raw or smoothed data is used for analysis
    dcc.Store(id = 'store_blank_locs'),                 # store locations in dataframe which are blanks
    dcc.Store(id = 'store_sample_names'),               # store the names associated to samples
    dcc.Store(id = 'store_sample_names_old'),           # temporary store of old sample names to facilitate renaming
    dcc.Store(id = 'store_sample_locations'),
    dcc.Store(id = 'store_upload_flag', data=False),    # store indicator if data has been uploaded, yet
    dcc.Store(id = 'analysis_flag', data=False),        # TODO: redundant, change code and remove
    dcc.Store(id = 'store_growth_data'),                # store growth parameters as dictionary (operation on it as dataframe)
    dcc.Store(id = 'store_growth_data_auto'),           # temporary store of growth parameters found by automatic growth curve analysis (as dictionary, operation on it as dataframe)
    dcc.Store(id = 'store_gd_by_replicates'),           # store summarizing replicate growth data
    dcc.Store(id = 'store_default_blanks'),             # store of set of default blanks
    dcc.Store(id = 'store_default_popsizemeasure', data=ds.default_pop_size_measure),   # string to format axes of plots with the correct population size measured used in data
    dcc.Store(id = 'store_auto_fit_ws', data=ds.auto_fit_default_ws),
    dcc.Store(id = 'store_auto_fit_slope_range', data=ds.auto_fit_default_sr),
    dcc.Store(id = 'store_auto_fit_r2_var_weight', data=ds.auto_fit_default_weight)
    ])

############
# upload div
############
# first page that user sees
# shows tutorial and exposes data upload interface
# after data upload div collapses and remains hidden
upload_div = dbc.Collapse([
                            html.H1(dcc.Markdown('<b>{}</b>'.format(ds.app_name), dangerously_allow_html=True),
                                    style={
                                            'text-align': 'center',
                                            'margin-top': '1em',
                                            'margin-bottom': '1em',
                                            'font-size': '80px',
                                            }
                                    ),
                                    
                            
                            dbc.Row(
                                    dcc.Upload(id='upload', max_size=3e7,
                                                children=html.Div([                                                                    
                                                                    ms.upload_area
                                                                    ],
                                                                    style={
                                                                            'line-height': '8em',   # vertically align text
                                                                            
                                                                            }
                                                                    ),
                                                style={
                                                        'width': '100%',
                                                        'borderWidth': '1px',
                                                        'borderStyle': 'dashed',
                                                        'borderRadius': '5px',
                                                        'textAlign': 'center',
                                                        'display': 'inline-block',
                                                        'height': '8em',
                                                        },
                                                ),
                                    style = {
                                            'margin-right': '20em',
                                            'margin-left': '20em',
                                            'margin-bottom': '2em',
                                            }
                                    ),
                            
                            dbc.Row([
                                    ax.create_link_button('Info', 'https://github.com/Dahlai/growthdash'),
                                    ax.create_link_button('Ask a question', 'https://github.com/Dahlai/growthdash/issues'),
                                    ax.create_link_button('How to cite?', 'https://github.com/Dahlai/growthdash'),
                                    dbc.Button(html.B('Download a sample file'), 
                                                color='secondary', 
                                                style={
                                                        'height':'55px', 
                                                        'width': '150px',
                                                        'display': 'flex',
                                                        'align-items': 'center',
                                                        'justify-content': 'center',
                                                        }, 
                                                id = 'button_download_sample_file'),
                                    dcc.Download(id = 'download_sample_file'),
                                    # ax.create_link_button('Download a sample file', 'https://github.com/Dahlai/growthdash'),
                                    ax.create_link_button('Watch the tutorial', ds.tutorial_link),
                                    ],
                                    style = {
                                            'margin-left': '10em',
                                            'margin-right': '10em',
                                            'justify-content': 'space-evenly',
                                            'margin-bottom': '1.5em'
                                            }
                                    ),
                            
                            dbc.Row(
                                    ms.intro_text,
                                    style = {
                                            'margin-bottom': '1em',
                                            'margin-left': '5em',
                                            'margin-right': '5em',
                                            'text-align': 'center',
                                        }
                                    ),
                            
                            dbc.Row(
                                    ms.data_privacy_text,
                                    style = {
                                            'text-align': 'center',
                                            }
                                    ),
                            html.Div(id='upload_alert_area'),   # error messages during upload are sent to this div

                            
                            dbc.Collapse([
                                            html.H1('Data structure:', 
                                                    style={'margin-top': '80px', 'margin-bottom': '30px'}
                                                    ),
                                            html.Img(src='./assets/help page_small.png', 
                                                     style={'width':'80%'}
                                                     )

                                            ], 
                                            id='info_section', 
                                            is_open=False
                                        )
                            ],
                            id = 'div_upload_collapsible',
                            is_open = True,
                            )



############
# main app div
############
# components to set sample name, blanks and additional functionalities (currently only automatic exponential phase determination)
sample_name_input = html.Div([
                            dcc.Markdown('<b>Sample name:</b>',
                                         style={'color':'black', 
                                                'font-size': 24,
                                                }, 
                                         dangerously_allow_html=True),
                            dcc.Input(id = 'input_sample_name', 
                                        type='text', 
                                        debounce=True, 
                                        style={'width':'85%'}
                                     ),
                            
                            html.I(id='sample_name_info', 
                                    className='bi bi-info-circle-fill', 
                                    style={'color': 'darkslategray', 
                                            'margin-left':'10px'}
                                    ),
                            dbc.Tooltip(dcc.Markdown(ms.tooltip_sample_name), 
                                        target='sample_name_info', 
                                        placement='top'
                                        )
                            ])

blanks_input = html.Div([
                            dcc.Markdown('<b>Sample blanks:</b>', 
                                        style={'color':'black', 
                                               'font-size': 24
                                               }, 
                                        dangerously_allow_html=True
                                        ),
                            dcc.Input(id = 'blanks_input', 
                                      type='text', 
                                      debounce=True, 
                                      style={'width': '85%'}
                                      ),
                            html.I(id='blanks_info', 
                                   className='bi bi-info-circle-fill', 
                                   style={'color': 'darkslategray', 
                                          'margin-left':'10px'}
                                  ),
                            dbc.Tooltip(ms.tooltip_blanks, 
                                        target='blanks_info', 
                                        placement='top'
                                        )
                            ])

additional_input = html.Div([
                            # data smoothing
                            dbc.Row([
                                    html.I(id='button_smoother', 
                                           className='bi bi-circle', 
                                           style={
                                                    'color': 'darkslategray', 
                                                    'font-size':'11pt', 
                                                    'display': 'inline-block', 
                                                    'width': '8%','padding': '0', 
                                                    'margin-top': '5px', 
                                                    'text-align':'center'}
                                           ),
                                    dbc.Tooltip(ms.tooltip_data_smoothing, 
                                                target='button_smoother',
                                                placement='top', 
                                                id='tooltip_button_smoother'
                                                ),
                                    html.Div(dcc.Input(id='input_smoother_ws', 
                                                       value=ds.default_smoothing_window_size, 
                                                       debounce=False, 
                                                       style={'padding': '0', 
                                                              'margin-top': '1px', 
                                                              'height': '30px', 
                                                              'width': '100%', 
                                                              'text-align': 'center'
                                                              }
                                                        ),
                                                style={'width': '13%', 
                                                        'padding-right':0}
                                            ),
                                    

                                    ], 
                                    style={'margin-bottom': '10px'}
                                    ),

                            # data auto fitting
                            dbc.Row([
                                     html.I(
                                            id='button_auto_fit', 
                                            className='bi bi-cpu-fill', 
                                            style={
                                                    'color': 'darkslategray',
                                                    'font-size':'15pt', 
                                                    'display': 'inline-block', 
                                                    'width': '8%','padding': '0', 
                                                    'margin-top': '5px', 
                                                    'text-align':'center'}
                                            ),
                                     dbc.Tooltip(
                                                ms.tooltip_autofitting_button,
                                                target='button_auto_fit', 
                                                placement='bottom'
                                                ),
                                     html.Div(
                                                dcc.Dropdown(ds.fittings_algorithms, 
                                                value=ds.default_fitting_algorithm, 
                                                id='dropdown_fitting_algorithms', 
                                                clearable=False, 
                                                style={
                                                        'padding': '0', 
                                                        'margin-top': '1px'}
                                                ), 
                                                style={
                                                        'width': '48%', 
                                                        'padding-right': 0
                                                        }
                                        ),
                                        
                                     html.Div(
                                                html.A(href=ds.models_links, 
                                                       target='_blank', 
                                                       id='button_go_to_algorithm_doc', 
                                                       className='bi bi-box-arrow-up-right', 
                                                       style={
                                                                'color': 'darkslategray', 
                                                                'background-color': 'transparent', 
                                                                'border-color':'transparent'
                                                             }
                                                      ),
                                                style={
                                                        'width': '10%', 
                                                        'display': 'inline-block', 
                                                        'margin-top': '8px'}
                                            ),
                                    
                                     dbc.Tooltip(
                                                ms.tooltip_autofitting_docs, 
                                                target='button_go_to_algorithm_doc', 
                                                placement='bottom'
                                                )
                                    ]),
                            
                            # hidden div that can be turned full screen to show progress of auto-fitting algorithm
                            html.Div([
                                        dbc.Row([
                                                 dbc.Row(id='progress_count'), 
                                                 dbc.Row(html.Progress(id='progress_bar', value='0')),
                                                 dbc.Row(
                                                        dbc.Button(html.B("cancel"), 
                                                        color='secondary', 
                                                        id='button_cancel_autofit'), 
                                                        style={'justify-content': 'center'}
                                                        )
                                                ],
                                                style={'width': '35em'}
                                                ),
                                        
                                     ], 
                                     id='auto_fit_div', 
                                     style={'visibility': 'hidden'}, 
                                    ),
                        ])



# settings div
settings_div = [
                html.Hr(style={'margin-bottom':'20'}),

                dbc.Row([
                        dbc.Col([
                                ], 
                                width=4
                                ),
                        dbc.Col([
                                dcc.Markdown('<b>Fitting parameters</b>', 
                                            style={'font-size': '14pt'}, 
                                            dangerously_allow_html=True
                                            )
                                ], 
                                width=4)
                        ]),

                dbc.Row([
                        dbc.Col([
                                html.B('Default blanks:'),
                                dcc.Input(id='default_blanks_input', 
                                          debounce=True, 
                                          style={
                                                  'margin-left': '38px', 
                                                  'width':'52%'
                                                  }),
                                html.I(id='default_blanks_info', 
                                       className='bi bi-info-circle-fill', 
                                       style={
                                            'color': 'darkslategray', 
                                            'margin-left':'10px',
                                            },
                                        ),
                                dbc.Tooltip(ms.tooltip_set_blanks, 
                                            target='default_blanks_info',
                                            ),
                                ], 
                                width=4
                                ),
                        dbc.Col([
                                html.B('Window size: ', 
                                       style={
                                                'display': 'inline-block', 
                                                'width': '25%',
                                              },
                                        ),
                                dcc.Input(value=ds.auto_fit_default_ws, 
                                          id='input_auto_default_ws', 
                                          debounce=True, 
                                          style={
                                                'margin-left': '10px', 
                                                'width':'55%'
                                                }
                                        ),
                                html.I(id='auto_default_sw_info', 
                                        className='bi bi-info-circle-fill', 
                                        style={
                                                'color': 'darkslategray', 
                                                'margin-left':'10px'
                                                }
                                        ),
                                dbc.Tooltip(ms.tooltip_auto_ws, 
                                            target='auto_default_sw_info'
                                            )

                                ], 
                                width=4, 
                                style={'margin-bottom': '10px'}
                                )
                            ]),
                dbc.Row([
                        dbc.Col([
                                html.B('Pop. size measure:'),
                                dcc.Input(id='input_popsizemeasure', 
                                          debounce=True, 
                                          value = ds.default_pop_size_measure,
                                          style={
                                                  'margin-left': '10px', 
                                                  'width':'52%'
                                                  }),
                                html.I(id='info_popsizemeasure', 
                                       className='bi bi-info-circle-fill', 
                                       style={
                                            'color': 'darkslategray', 
                                            'margin-left':'10px',
                                            },
                                        ),
                                dbc.Tooltip(ms.tooltip_popsizemeasure, 
                                            target='info_popsizemeasure',
                                        )
                                ], 
                                width=4
                                ),
                        dbc.Col([
                                html.B('Slope range: ', 
                                        style={
                                                'display': 'inline-block', 
                                                'width': '25%'
                                                }
                                        ),
                                dcc.Input(value=ds.auto_fit_default_sr, 
                                          id='input_auto_default_sr', 
                                          debounce=True, 
                                          style={
                                                'margin-left': '10px', 
                                                'width': '55%'
                                                }
                                          ),
                                html.I(id='auto_default_sr_info', 
                                       className='bi bi-info-circle-fill', 
                                       style={
                                                'color': 'darkslategray', 
                                                'margin-left':'10px'
                                            }),
                                dbc.Tooltip(ds.auto_fit_default_weight, target='auto_default_sr_info')

                                ], 
                                width=4, 
                                style={'margin-bottom': '10px'}
                                )
                        ]),
                dbc.Row([
                        dbc.Col([
                                ], 
                                width=4
                                ),
                        dbc.Col([
                                html.B('Weight: ', 
                                        style={
                                                'display': 'inline-block', 
                                                'width': '25%'
                                               }),
                                dcc.Input(value=ds.auto_fit_default_weight, 
                                          id='input_auto_default_weight', 
                                          debounce=True, 
                                          style={
                                                'margin-left': '10px', 
                                                'width':'55%'
                                                }
                                        ),
                                html.I(id='auto_default_weight_info', 
                                       className='bi bi-info-circle-fill', 
                                       style={
                                                'color': 'darkslategray', 
                                                'margin-left':'10px'
                                             }
                                        ),
                                dbc.Tooltip(ms.tooltip_auto_sr, 
                                            target='auto_default_weight_info'
                                            )

                                ], 
                                width=4, 
                                style={'margin-bottom': '10px'},
                                )
                        ])               
                    ]


# div showing results for individual samples
results_growth = [
                    dbc.Row(id = 'growth_rate', children = dcc.Markdown('growth rate \[h<sup>-1</sup>\] =', dangerously_allow_html=True)),
                    dbc.Row(id = 'doubling_time', children = dcc.Markdown('doubling time \[h\] =')),
                    dbc.Row(id = 'lag_time', children = dcc.Markdown('lag time \[h\] =')),
                    dbc.Row(id = 'doublings', children = dcc.Markdown('doublings =')),
                    dbc.Row(id = 'doublings_log', children = dcc.Markdown('doublings in log-phase =')),
                    dbc.Row(id = 'yield', children = dcc.Markdown('yield \[{}\] ='.format(ds.default_pop_size_measure), dangerously_allow_html=True)),
                    dbc.Row(id = 'error', children= dcc.Markdown('RMSE = '))
                    ]


# sample graphs
blanks_graph = dcc.Graph(id='fig_blanks', config=ax.graph_config('blanks'), style={'height': '6em'})
sample_graph = dcc.Graph(id='fig_sample', config=ax.graph_config('sample'), style={'height': '6em'})
sample_blanked_graph = dcc.Graph(id='fig_blanked', config=ax.graph_config('sample_blanked'), style={'height': '11.25em'})
sample_log_graph = dcc.Graph(id='fig_log', config=ax.graph_config('sample_blanked_log'))


# analysis graphs
dt_graph = dcc.Graph(id='fig_dt', config=ax.graph_config('doubling time'))
mu_graph = dcc.Graph(id='fig_mu', config=ax.graph_config('growth rate'))
lag_time_graph = dcc.Graph(id='fig_lt', config=ax.graph_config('lag time'))
doublings_graph = dcc.Graph(id='fig_doublings', config=ax.graph_config('doublings'))
doublings_log_graph = dcc.Graph(id='fig_doublings_log', config=ax.graph_config('doublings_log'))
yield_graph = dcc.Graph(id='fig_yield', config=ax.graph_config('yield'))


# download buttons
download_buttons = [
                    html.Hr(style={'margin-top': '40px', 
                                    'margin-bottom': '40px'
                                    }
                            ),
                    html.H2('Download data:', 
                            style={'margin-bottom': '20px'}
                            ),
                    html.H6('Interactive .html plots '),
                    dbc.Row([
                            dbc.Col([dcc.Loading(html.A(
                                    id="dt_download",
                                    href="",
                                    children=[ax.create_download_button('doubling times')],
                                    target="_blank",
                                    download="dts.html"))], 
                                    width=1,
                                    ),

                            dbc.Col([dcc.Loading(html.A(
                                    id="mu_download",
                                    href="",
                                    children=[ax.create_download_button('growth rates')],
                                    target="_blank",
                                    download="mu_max.html"))], 
                                    width=1,
                                    ),
                            dbc.Col([dcc.Loading(html.A(
                                    id="lt_download",
                                    href="",
                                    children=[ax.create_download_button('lag time')],
                                    target="_blank",
                                    download="lag_times.html"))], 
                                    width=1,
                                    )
                                    ,
                            dbc.Col([dcc.Loading(html.A(
                                    id="doublings_download",
                                    href="",
                                    children=[ax.create_download_button('doublings')],
                                    target="_blank",
                                    download="doublings.html"))], 
                                    width=1,
                                    ),
                            dbc.Col([dcc.Loading(html.A(
                                    id="doublings_log_download",
                                    href="",
                                    children=[ax.create_download_button('doublings log-phase')],
                                    target="_blank",
                                    download="doublings_log.html"))],
                                    width=1,
                                    ),
                            dbc.Col([dcc.Loading(html.A(
                                    id="yields_download",
                                    href="",
                                    children=[ax.create_download_button('yields')],
                                    target="_blank",
                                    download="yields.html"))], 
                                    width=1,
                                    ),
                                   
                            ],
                            style={'margin-bottom': '20px'},
                            ),
                        html.H6('.csv file summarizing analyzed data'),
                        dbc.Row([
                                dbc.Col([
                                        dbc.Button(html.B('analysis'), color='secondary', style={'height':'60px', 'width': '110px'}, id = 'download_sample_data_button'),
                                        dcc.Download(id = 'download_sample_data')
                                        ], 
                                        width=1,
                                        ),
                                dbc.Tooltip(ms.tooltip_csv_download,
                                            target='download_sample_data_button', 
                                            delay={'show': 500}),
                        ])

  
                    ]

###########
# overall app layout structure 
###########
# data display layout
sample_data_div = dbc.Collapse([
        dbc.Row([
                # top row containing settings button and buttons to switch between samples
                dbc.Row([
                        dbc.Col(html.I(className='bi bi-gear-fill', 
                                       style={'font-size':25,}, 
                                       id='settings_button'), 
                                width=4
                                ),
                        dbc.Col(
                                dbc.Row([
                                        dbc.Col(html.I(id = 'backbutton', 
                                                       n_clicks=0, 
                                                       className='bi bi-arrow-left-square-fill', 
                                                       style={'font-size':25}
                                                       ), 
                                                width=1, 
                                                style={'padding': 0}
                                                ),
                                        dbc.Col(id='current_sample_position', 
                                                style={
                                                        'font-size':20, 
                                                        'text-align':'center'
                                                        }, 
                                                width=2),
                                        dbc.Col(html.I(id = 'forwardbutton', 
                                                       n_clicks=0, 
                                                       className='bi bi-arrow-right-square-fill', 
                                                       style={'font-size':25}
                                                       ), 
                                                width=1, 
                                                style={
                                                        'padding': 0, 
                                                        'text-align':'right'
                                                        }
                                                ),
                                        ], 
                                        justify='center', 
                                        align='center', 
                                        style={'margin-bottom':'20px'}
                                        ),
                                width=4),
                        dbc.Col(width=4),
                        ], 
                        id='top-row1'
                        ),

                # second row with drop down menu to choose sample
                dbc.Row([
                        dbc.Col(width=4),
                        dbc.Col(
                                dbc.Row([
                                        dbc.Col(width=1),
                                        dbc.Col(dcc.Dropdown(id='current_sample_name', clearable=False, optionHeight=50), width=8),
                                        dbc.Col(width=1)
                                        ], 
                                        justify='center', 
                                        align='center',
                                        ),
                                width=4
                                ),
                        dbc.Col(width=4),
                        ], 
                        align='center',
                        id = 'top-row2'
                        ),

                # collapsible settings div
                dbc.Row([
                        dbc.Collapse(settings_div, 
                                    id='settings_div', 
                                    is_open=False, 
                                    style={
                                            'margin-top': '15px', 
                                            'margin-bottom':'15px'
                                            }
                                    )
                        ]),
                        
                # message areas for sample analysis
                dbc.Row([
                        html.Div(id='message_area'),
                        html.Div(id='message_area_sample_names'),
                        html.Div(id='message_area_fits'),
                        html.Div(id='message_area_fits_parameters'),
                        html.Div(id='message_area_data_smoother'),
                        ]),

                html.Hr(style={'margin-top': '20px', 'margin-bottom': '30px', 'border': '1.5px solid'}),
                ],
                style = {'background-color': 'rgb(245, 245, 245)'},
                id = 'top-row',
                ),
        
        # input areas for sample name, associated blanks and additional features
        dbc.Row([
                dbc.Col([sample_name_input], 
                        id='sample_name', 
                        width=4
                        ),
                dbc.Col([blanks_input], 
                        id='blank_names', 
                        width=4
                        ),
                dbc.Col([additional_input], 
                        width=4
                        )
                ]),
        
        html.Hr(style={'margin-top': '30px', 'margin-bottom': '20px', 'border': '1.5px solid'}),
        
        dbc.Row([
                dbc.Col([
                        html.Div([blanks_graph]),
                        html.Div([sample_graph]),
                        html.Div([sample_blanked_graph]),
                        
                        ], 
                        width=3, 
                        style={'padding': 0, 'margin-top': '2.5em'}
                        ),
                dbc.Col([
                        html.Div([sample_log_graph])
                        ], 
                        width=6, 
                        style={'padding': 0}
                        ),
                dbc.Col(results_growth, 
                        width=3, 
                        style={'margin-top': '6em'}
                        )
                ]),
        # summary graphs of all analyzed samples
        dbc.Row([
                dbc.Collapse([
                            html.Hr(style={'margin-top': '40px'}),
                            dbc.Row([
                                    dbc.Col(dt_graph, width=4), 
                                    dbc.Col(mu_graph, width=4), 
                                    dbc.Col(lag_time_graph, width=4)
                                    ]),
                            dbc.Row([
                                    dbc.Col(doublings_graph, width=4), 
                                    dbc.Col(doublings_log_graph, width=4), 
                                    dbc.Col(yield_graph, width=4)
                                    ]),

                            ] + download_buttons,
                            is_open=False, 
                            id='analysis_div'
                            )
                ]),
        ],
        id = 'collapse_data',
        is_open = False,
        style={'margin-top': '30px'},
        )




# master layout
app.layout = html.Div(
    [
    stores,      # stores need to be inside html.Div
    upload_div,
    sample_data_div,

    ],
    style={'margin': '1%', 'margin-bot': '5em'},
    id = 'body_layout'
)


################################################
# callbacks
################################################
@app.callback(
    Output('store_data_df', 'data'),
    Output('div_upload_collapsible', 'is_open'),
    Output('store_upload_flag', 'data'),
    Output('upload_alert_area', 'children'),
    Input('upload', 'contents'),
    Input('upload', 'filename'),
    State('store_upload_flag', 'data'),
    prevent_initial_call=True
)
def load_data_page(contents, filename, upload_flag):
    # handle and format uploaded data
    if contents is None:
        return dash.no_update, dash.no_update, dash.no_update

    else:
        # load data
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        if filename.split('.')[-1] == 'csv':
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=';')
        elif (filename.split('.')[-1] == 'xlsx') or (filename.split('.')[-1] == '.xls'):
            df = pd.read_excel(decoded)
        else:
            upload_alert = ax.generate_alert(ms.error_upload_file)
            return dash.no_update, dash.no_update, dash.no_update, upload_alert

        # check if entries can be cast to float
        try:
            df.iloc[:, 1:].astype(float)
        except:
            upload_alert = dbc.Alert('Make sure all data entries are of numerical type (i.e. numbers or NaN)')
            return dash.no_update, dash.no_update, dash.no_update, upload_alert

        # format uploaded data
        df.set_index(df.iloc[:,0].values, inplace=True)
        df = df.iloc[:, 1:]
        df.columns = df.columns.astype(float)


        if len(set(df[[not x for x in df.index == '-']].index)) + df[df.index == '-'].shape[0] != df.shape[0]:
            # check for duplicate sample names
            upload_alert = dbc.Alert('Duplicate sample names are not allowed, please make sure that each sample is associated with a unique name and/or indicate replicates with digits (e.g.  \" test_sample 1\").', duration=10000, color='danger')
            return dash.no_update, dash.no_update, dash.no_update, upload_alert
    return df.to_dict('tight'), False, True, ''


@app.callback(
                Output('input_sample_name', 'value'),
                Output('store_sample_names', 'data'),
                Output('store_sample_names_old', 'data'),
                Output('message_area_sample_names', 'children'),
                Output('store_sample_locations', 'data'),
                Input('store_sample_idx', 'data'),
                Input('input_sample_name', 'value'),
                Input('store_upload_flag', 'data'),
                State('store_sample_names', 'data'),
                State('store_data_df', 'data'),
                prevent_initial_call=True
)
def update_sample_input_value(sample_idx, new_sample_name, upload_flag, sample_names, df):
    # update stored sample names from different inputs

    # update on data upload from names stored in uploaded data
    if dash.callback_context.triggered[0]['prop_id'] == 'store_upload_flag.data':
        df = pd.DataFrame.from_dict(df, orient='tight')

        # set default sample names as defined in uploaded data
        sample_names = []
        for loc in df.index:
            sample_names.append(loc)

        # set sample locations
        sample_locations = ax.set_sample_locations(df)
        return list(sample_names)[sample_idx], sample_names, sample_names, '', sample_locations

    # update on page turn
    elif dash.callback_context.triggered[0]['prop_id'] == 'store_sample_idx.data':
        current_sample_name = sample_names[sample_idx]
        return current_sample_name, dash.no_update, dash.no_update, '', dash.no_update

    # update on new name input
    elif dash.callback_context.triggered[0]['prop_id'] == 'input_sample_name.value':
        df = pd.DataFrame.from_dict(df, orient='tight')
        # check for duplicate sample names
        if new_sample_name in sample_names:
            alert_sn = ax.generate_alert(ms.error_duplicate_sample)
            return sample_names[sample_idx], dash.no_update, dash.no_update, alert_sn, dash.no_update
        else:
            sample_names_old = sample_names.copy()
            sample_names[sample_idx] = new_sample_name
            return new_sample_name, sample_names, sample_names_old, '', dash.no_update


@app.callback(
                Output('store_sample_idx', 'data'),
                Output('current_sample_name', 'options'),
                Output('current_sample_name', 'value'),
                Input('forwardbutton', 'n_clicks'),
                Input('backbutton', 'n_clicks'),
                Input('store_upload_flag', 'data'),
                Input('fig_dt', 'clickData'),
                Input('fig_mu', 'clickData'),
                Input('fig_lt', 'clickData'),
                Input('fig_doublings', 'clickData'),
                Input('fig_doublings_log', 'clickData'),
                Input('fig_yield', 'clickData'),
                Input('current_sample_name', 'value'),
                State('store_sample_names', 'data'),
                State('store_sample_idx', 'data'),
                State('store_data_df', 'data'),
                State('fig_dt', 'hoverData'),
                State('fig_mu', 'hoverData'),
                State('fig_lt', 'hoverData'),
                State('fig_doublings', 'hoverData'),
                State('fig_doublings_log', 'hoverData'),
                State('fig_yield', 'hoverData'),
                prevent_initial_call=True
)
def change_sample(f_clicks, b_clicks, upload_flag, 
                    fig_dt_click, fig_mu_click, fig_lt_click, fig_doublings_click, fig_doublings_log_click, fig_yield_click, 
                    selected_sample_name, sample_names, sample_idx, df, 
                    fig_dt_hover, fig_mu_hover, fig_lt_hover, fig_doublings_hover, fig_doublings_log_hover, fig_yield_hover,
                ):
    # change displayed sample with different inputs
    df = pd.DataFrame.from_dict(df, orient='tight')

    
    if dash.callback_context.triggered[0]['prop_id'] == 'store_upload_flag.data':
        # at data upload set sample_idx such that the first sample is displayed that's not been defined as 'to skip'
        sample_names = df.index.to_list()
        sample_idx = np.argmax(np.array(sample_names) != '-')
    elif dash.callback_context.triggered[0]['prop_id'] == 'backbutton.n_clicks':
        # go to the previous sample
        sample_idx_0 = sample_idx

        sample_idx -= 1

        while sample_names[sample_idx] == '-':
            sample_idx -= 1

        if sample_idx < 0:
            sample_idx = sample_idx_0

    elif dash.callback_context.triggered[0]['prop_id'] == 'forwardbutton.n_clicks':
        # go to the next sample
        sample_idx_0 = sample_idx
        sample_idx += 1

        while sample_names[sample_idx] == '-':
            sample_idx += 1

        if sample_idx >= df.shape[0]:
            sample_idx = sample_idx_0

    # when clicking on datapoint in summary plots, jump to sample in data display section
    elif dash.callback_context.triggered[0]['prop_id'] == 'fig_dt.clickData':
        clicked_sample_name = fig_dt_hover['points'][0]['hovertext']
        sample_idx = sample_names.index(clicked_sample_name)
    elif dash.callback_context.triggered[0]['prop_id'] == 'fig_mu.clickData':
        clicked_sample_name = fig_mu_hover['points'][0]['hovertext']
        sample_idx = sample_names.index(clicked_sample_name)
    elif dash.callback_context.triggered[0]['prop_id'] == 'fig_lt.clickData':
        clicked_sample_name = fig_lt_hover['points'][0]['hovertext']
        sample_idx = sample_names.index(clicked_sample_name)
    elif dash.callback_context.triggered[0]['prop_id'] == 'fig_doublings.clickData':
        clicked_sample_name = fig_doublings_hover['points'][0]['hovertext']
        sample_idx = sample_names.index(clicked_sample_name)
    elif dash.callback_context.triggered[0]['prop_id'] == 'fig_doublings_log.clickData':
        clicked_sample_name = fig_doublings_log_hover['points'][0]['hovertext']
        sample_idx = sample_names.index(clicked_sample_name)
    elif dash.callback_context.triggered[0]['prop_id'] == 'fig_yield.clickData':
        clicked_sample_name = fig_yield_hover['points'][0]['hovertext']
        sample_idx = sample_names.index(clicked_sample_name)


    # change sample on selection from drop down menu
    elif dash.callback_context.triggered[0]['prop_id'] == 'current_sample_name.value':
        sample_idx = sample_names.index(selected_sample_name)


    # format drop down menu with currently selected sample
    current_sample_name = sample_names[sample_idx]
    sample_names_out = [x for x in sample_names if x != '-']
    return sample_idx, sample_names_out, current_sample_name


@app.callback(
                Output('blanks_input', 'value'),
                Output('store_blank_locs', 'data'),
                Output('default_blanks_input', 'value'),
                Output('message_area', 'children'),
                Output('store_default_blanks', 'data'),
                Input('blanks_input', 'value'),
                Input('default_blanks_input', 'value'),
                Input('store_sample_idx', 'data'),
                Input('store_upload_flag', 'data'),
                Input('store_sample_names', 'data'),
                Input('store_sample_names_old', 'data'),
                State('store_blank_locs', 'data'),
                State('store_data_df', 'data'),
                State('store_data_df_smoothed', 'data'),
                State('store_smoother_flag', 'data'),
                State('store_default_blanks', 'data'),

                prevent_initial_call=True
)
def update_blanks(new_blanks, input_default_blanks, sample_idx, upload_flag, sample_names, sample_names_old, blank_locs, df, df_smoothed, smoother_flag, default_blanks):
    if dash.callback_context.triggered[0]['prop_id'] == 'store_upload_flag.data':
        # initialize blanks on data upload

        if smoother_flag == False:
            df = pd.DataFrame.from_dict(df, orient='tight')
        else:
            df = pd.DataFrame.from_dict(df_smoothed, orient='tight')
        
        sample_locations = ax.set_sample_locations(df)
        blank_locs = {}

        sample_names = df.index.to_list()
        for loc in sample_locations:
            blank_locs[loc] = np.array(sample_names)[np.array(sample_names) != '-'][:3]

        blanks_list = blank_locs[list(blank_locs)[sample_idx]]
        blanks_input_value = ', '.join(blanks_list)

        return blanks_input_value, blank_locs, blanks_input_value, '', blanks_input_value

    elif dash.callback_context.triggered[0]['prop_id'] == 'store_sample_idx.data':
        # update input value on page turn
        current_sample_loc = list(blank_locs.keys())[sample_idx]
        blanks_list = blank_locs[current_sample_loc]
        blanks_input_value = ', '.join(blanks_list)
        return blanks_input_value, blank_locs, input_default_blanks, '', dash.no_update


    elif dash.callback_context.triggered[0]['prop_id'] == 'default_blanks_input.value':
        # update all blank locations to new default
        blank_locs_new = {}
        new_default_blanks_list = [x.strip() for x in input_default_blanks.split(',')]

        # check if input is valid (i.e. if the input string contains sample names)
        inp_check = [x in sample_names for x in new_default_blanks_list]   
        if not all(inp_check):
            alert = ax.generate_alert(ms.error_blank_name)
            return dash.no_update, dash.no_update, default_blanks, alert, dash.no_update
        
        
        for b in blank_locs:
            blank_locs_new[b] = new_default_blanks_list

        sample_pos = list(blank_locs.keys())[sample_idx]
        blanks_input = blank_locs_new[sample_pos]
        blanks_input_str = ', '.join(blanks_input)
        return input_default_blanks, blank_locs_new, input_default_blanks, '', input_default_blanks

    elif dash.callback_context.triggered[0]['prop_id'] == 'store_sample_names.data':
        # update all blank locations on change of sample name (e.g. user might rename blanks from 'blank 1' to 'b 1')
        if len(list(set(sample_names) - set(sample_names_old))) == 0:
            return dash.no_update, dash.no_update, dash.no_update, ''
        blank_locs_new = {}
        old_sample_name = list(set(sample_names_old) - set(sample_names))[0]
        new_sample_name = list(set(sample_names) - set(sample_names_old))[0]

        # check if duplicate sample name
        for loc in blank_locs:
            blank_locs_new[loc] = [x if x != old_sample_name else new_sample_name for x in blank_locs[loc]]
        sample_pos = list(blank_locs.keys())[sample_idx]
        new_blanks_list = blank_locs_new[sample_pos]
        new_blanks = ', '.join(new_blanks_list)

        # update default blank names on change of sample name
        default_blanks_list = default_blanks.split(',')
        default_blanks_list = [x.strip() for x in default_blanks_list]
        default_blanks_list = [x if x != old_sample_name else new_sample_name for x in default_blanks_list]
        default_blanks_new = ', '.join(default_blanks_list)
        return new_blanks, blank_locs_new, default_blanks_new, '', default_blanks_new

    else:
        # update blanks on change of input
        new_blanks_list = new_blanks.split(',')
        new_blanks_list = [x.strip() for x in new_blanks_list]

        sample_pos = list(blank_locs.keys())[sample_idx]

        inp_check = [x in sample_names for x in new_blanks_list]     # check if input is valid (i.e. if the input string contains sample positions)
        if not all(inp_check):
            new_blanks_list = blank_locs[sample_pos]
            new_blanks = ', '.join(new_blanks_list)
            alert = ax.generate_alert(ms.error_blank_location)
            return new_blanks, blank_locs, input_default_blanks, alert, dash.no_update

        else:
            blank_locs[sample_pos] = new_blanks_list
            new_blank_input = dcc.Input(id = 'blanks_input', type='text', debounce=True, placeholder=new_blanks)
            return new_blanks, blank_locs, input_default_blanks, '', input_default_blanks


@app.callback(
                Output('fig_blanks', 'figure'),
                Output('fig_sample', 'figure'),
                Output('fig_blanked', 'figure'),
                Output('fig_log', 'figure'),
                Output('current_sample_position', 'children'),
                Output('collapse_data', 'is_open'),
                Input('store_sample_idx', 'data'),
                Input('store_blank_locs', 'data'),
                Input('store_upload_flag', 'data'),
                Input('store_sample_names', 'data'),
                Input('store_growth_data', 'data'),
                Input('store_smoother_flag', 'data'),
                Input('store_default_popsizemeasure', 'data'),
                State('store_data_df', 'data'),
                State('store_data_df_smoothed', 'data'),
                State('store_sample_locations', 'data'),
                
                prevent_initial_call=True,

)
def show_data(sample_idx, blank_locs, upload_flag, sample_names, growth_data, smoother_flag, pop_size_measure, df, df_smoothed, sample_locations):
    # plot data of the currently selected sample
    if df is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # reconstruct pandas df from store
    if smoother_flag == False:
        df = pd.DataFrame.from_dict(df, orient='tight')
    else:
        df = pd.DataFrame.from_dict(df_smoothed, orient='tight')

    if dash.callback_context.triggered[0]['prop_id'] != 'store_upload_flag.data':
        df.index = sample_names

    # time points
    t = df.columns.tolist()

    # sample position
    current_sample_position = sample_locations[sample_idx]

    # sample name
    current_sample_name = sample_names[sample_idx]



    ##########
    # blanks graph
    ##########
    # display the blanks associated with the current sample
    blanks = blank_locs[current_sample_position]
    data_blanks = []

    for b in blanks:
        data_blanks.append(go.Scatter(x=t, y=df.loc[b], name=b))

    # display mean of all selected blanks (mean of blanks is subtracted from sample trace)
    blanks_mean = df.loc[blanks].mean(axis=0)
    data_blanks.append(go.Scatter(x=t, y=blanks_mean, name='blanks averaged'))
    annotations_blank = [{'text': '<b>Blanks</b>', 'font_size': 22, 'textangle': -90, 'align':'center',
                          'showarrow': False,
                          'x': -0.4, 'xref': 'paper', 'xanchor': 'center', 
                          'y': 0.4, 'yref': 'paper', 'yanchor': 'middle', 
                          }]
    layout_blanks = go.Layout(
                            showlegend=False,
                            title_font_color='black',
                            xaxis_showticklabels=False,
                            xaxis_gridwidth = 2,
                            yaxis_gridwidth = 2,
                            yaxis_range = [blanks_mean.mean() - 0.1, blanks_mean.mean() + 0.1],
                            font={'size': 16},
                            paper_bgcolor='rgba(0,0,0,0)',
                            margin={'l': 120, 'r': 0, 't': 0, 'b': 20},
                            annotations=annotations_blank,
                            )

    fig_blanks = go.Figure(data=data_blanks, layout=layout_blanks)


    ##########
    # sample graph
    ##########
    # display the trace of the currently selected sample
    sample_trace = df.iloc[sample_idx]
    data_sample = [go.Scatter(x=t, y=df.iloc[sample_idx], line={'color':'rgb(44, 105, 154)', 'width':3})]
    annotations_sample = [{'text': '<b>Raw</b>', 'font_size': 22, 'textangle': -90, 'align':'center',
                          'showarrow': False,
                          'x': -0.4, 'xref': 'paper', 'xanchor': 'center', 
                          'y': 0.4, 'yref': 'paper', 'yanchor': 'middle', 
                          },
                          {'text': pop_size_measure, 'showarrow': False, 'textangle': -90,
                           'x': -0.3, 'xref': 'paper', 
                           'y': -0.2, 'yref': 'paper',
                          }
                          ]
    layout_sample = go.Layout(
                            showlegend=False,
                            title_font_color='black',
                            xaxis_showticklabels=False,
                            xaxis_gridwidth = 2,
                            yaxis_gridwidth = 2,
                            yaxis_range = [-0.01, sample_trace.max() * 1.1 + 0.05],
                            font={'size': 16},
                            paper_bgcolor='rgba(0,0,0,0)',
                            margin={'l': 120, 'r': 0, 't': 0, 'b': 20},
                            annotations=annotations_sample,
                            )
    fig_sample = go.Figure(data=data_sample, layout=layout_sample)
    

    ##########
    # sample blanked graph
    ##########
    # display the trace of the currently selected blanked sample
    sample_trace = df.iloc[sample_idx]
    sample_trace_blanked = sample_trace - blanks_mean
    sample_name = growth_data[current_sample_position]['sample_name']

    data_blanked = [go.Scatter(x=t, y=sample_trace_blanked, line={'color':'rgb(44, 105, 154)', 'width':3}, name=sample_name)]

    # add fitted trace, if computed
    fitting_algorithm = growth_data[current_sample_position]['fitting_mode']
    
    if (fitting_algorithm != 'NaN') and (growth_data[current_sample_position]['mumax'] != 'NaN'):
        # fitted trace
        t_fit, y_fit = ax.generate_fitted_curve(t, fitting_algorithm, growth_data[current_sample_position])

        # add start/end of log-phase overlay to plot
        x_0, y_0, x_1, y_1, hovertext_start, hovertext_end = ax.generate_start_end_logphase_indicator_lines(fitting_algorithm, growth_data[current_sample_position], sample_trace_blanked)


        scatter_fit = go.Scatter(x=t_fit, y=y_fit, line={'color': 'rgb(242, 158, 76)', 'width': 3}, name='fit')
        
        scatter_log_start = go.Scatter(x=x_0, y=y_0, 
                                        hoveron='points', hoverinfo='text', hovertext=hovertext_start,
                                        marker={'opacity': 0},
                                        line={'color': 'grey', 'width': 3}
                                        )
        
        scatter_log_end = go.Scatter(x=x_1, y=y_1, 
                                        hoveron='points', hoverinfo='text', hovertext=hovertext_end,
                                        marker={'opacity': 0},
                                        line={'color': 'grey', 'width': 3}
                                        )
        
        data_blanked.append(scatter_fit)
        data_blanked.append(scatter_log_start)
        data_blanked.append(scatter_log_end)
    
        
    # layout
    annotations_blanked = [{'text': '<b>Blanked</b>', 'font_size': 22, 'textangle': -90, 'align':'center',
                        'showarrow': False,
                        'x': -0.4, 'xref': 'paper', 'xanchor': 'center', 
                        'y': 0.4, 'yref': 'paper', 'yanchor': 'middle', 
                        }]

    layout_blanked = go.Layout(
                            showlegend=False,
                            title_font_color='black',
                            xaxis_gridwidth = 2,
                            yaxis_gridwidth = 2,
                            yaxis_range = [-0.01, sample_trace_blanked.max() * 1.1 + 0.1],
                            font={'size': 16},
                            paper_bgcolor='rgba(0,0,0,0)',
                            margin={'l': 120, 'r': 0, 't': 0, 'b': 20},
                            annotations=annotations_blanked

                            )
    fig_blanked = go.Figure(data=data_blanked, layout=layout_blanked)


    ##########
    # sample blanked log graph
    ##########
    # display the trace of the currently selected blanked sample on log-scale
    # in this view user can select the exponential growth phase from which all growth parameters are extracted

    sample_trace_blanked_log = sample_trace_blanked

    data_log = [
                go.Scatter(x=t, y=sample_trace_blanked_log,
                            yaxis='y1',
                            line={'color':'rgb(44, 105, 154)', 'width': 3}, 
                            name=sample_name),
                ]
    
    # button for exclusion of sample from analysis (can exclude indvidual samples from the summary)
    data_log.append(
                    go.Scatter(
                               x=[0.05, 0.10, 0.10, 0.05, 0.05], 
                               y=[0.95, 0.95, 0.90, 0.90, 0.95],
                               fill='toself',
                               fillcolor='white',
                               xaxis='x2',
                               yaxis='y2',
                               mode='lines',
                               marker={'color':'rgba(0,0,0,0)'},
                               hoveron='fills',
                               hoverinfo='text',
                               text='Exclude/include sample from analysis'
                               )
                    )


    # add exponential fit log growth, if already computed and beginning and end of log phase
    if (fitting_algorithm != 'NaN') and (growth_data[current_sample_position]['mumax'] != 'NaN'):
        data_log.append(go.Scatter(x=t_fit, y=y_fit, 
                                   line={'color': 'rgb(242, 158, 76)', 'width': 3}, 
                                   name='fit')
                        )
        data_log.append(scatter_log_start)
        data_log.append(scatter_log_end)
    
    # layout
    if sample_trace_blanked.max() > 0:
        y_log_lb = np.log10(sample_trace_blanked[sample_trace_blanked > 0].min() * 0.9)
        y_log_ub = np.log10(sample_trace_blanked.max() * 1.1)
    else:
        y_log_lb = -3
        y_log_ub = 1
    log_annotations = [{'showarrow':False, 
                        'xref':'paper', 'x':0, 
                        'yref':'paper', 'y':1.1, 
                        'text':'<i>Select exponential growth phase here</i>'
                        },
                        {'showarrow':False, 
                        'xref':'paper', 'x': -0.175, 
                        'yref':'paper', 'y': -0.175, 
                        'text':'time [h]'
                        }
                        ]
    layout_log = go.Layout(
                            showlegend=False,
                            title_font_color='black',
                            xaxis={
                                    'gridcolor': 'white', 'gridwidth': 2,
                                    },
                            xaxis2={'range':[0, 1], 'overlaying': 'x', 'showgrid':False, 'showticklabels':False},
                            yaxis1={
                                    'type': 'log',
                                    'dtick': 1,
                                    'gridcolor': 'white', 'gridwidth': 2, 
                                    'minor':{'showgrid': True, 'gridcolor': 'white', 'griddash':'dot', 'gridwidth': 1.5},
                                    'range':[y_log_lb, y_log_ub],
                            },
                            yaxis2={'side':'right', 'showticklabels':False, 'showgrid':False, 'range':[0,1], 'overlaying': 'y'},
                            paper_bgcolor='rgba(0,0,0,0)',
                            font={'size': 16, 'color': 'black'},
                            dragmode='select',
                            margin={'t':40, 'b': 60, 'l': 100},
                            annotations=log_annotations,
                            )
    fig_log = go.Figure(data=data_log, layout=layout_log)
    
    # add image to exclude sample button
    if growth_data[current_sample_position]['excluded_flag'] == False:
        img = Image.open('./assets/x-circle.png')
    else:
        img = Image.open('./assets/x-circle-fill.png')
    fig_log.add_layout_image({'source':img, 'x':0.075, 'y':0.925, 
                                    'xref': 'x2', 'yref':'y2',
                                    'xanchor': 'center', 'yanchor': 'middle',
                                    'sizex': 0.075, 'sizey': 0.075,
                                })
    return fig_blanks, fig_sample, fig_blanked, fig_log, current_sample_position, True


@app.callback(
    Output('fig_log', 'clickData'),
    Input('fig_log', 'clickData')
)
def reset_click(click):
    # reset click value, else multiple clicks in plot are not possible
    return None


def get_overlay_dp(growth_data, gd_by_replicates, voi):
    overlays = {sn: [] for sn in gd_by_replicates}
    for sn in gd_by_replicates:
        for sp in growth_data:
            sn_full = growth_data[sp]['sample_name']

            # discard excluded samples
            if growth_data[sp]['excluded_flag'] == True:
                continue

            if ' '.join(re.split('_| ', sn_full)[:-1]) == sn:
                if growth_data[sp][voi] == 'NaN':
                    overlays[sn].append({'name': sn_full, 'value': np.nan})
                else:
                    overlays[sn].append({'name': sn_full, 'value': growth_data[sp][voi]})
    return overlays


def generate_excluded_dict(growth_data):
    excluded = {}
    for i, sp in enumerate(growth_data):
        sn_full = growth_data[sp]['sample_name']
        sn = ' '.join(re.split('_| ', sn_full)[:-1])
        if sn in excluded:
            continue
        elif sn == '':
            # for '-' samples that are supposed to be skipped
            continue
        else:
            excluded[sn] = 0
    return excluded


@app.callback(
                Output('fig_mu', 'figure'),
                Output('fig_dt', 'figure'),
                Output('fig_lt', 'figure'),
                Output('fig_doublings', 'figure'),
                Output('fig_doublings_log', 'figure'),
                Output('fig_yield','figure'),
                Output('store_gd_by_replicates', 'data'),
                Input('store_growth_data', 'data'),
                Input('store_sample_names', 'data'),
                Input('store_default_popsizemeasure', 'data'),
                State('store_sample_locations', 'data'),
                
                prevent_initial_call = True
)
def show_analysis(growth_data, sample_names, pop_size_measure, sample_locations):
    # summarize data by group (usually groups are replicates of the same growth condition)
    # plot growth characteristics of the individual groups together so that different conditions can be easily compared

    # group data by sample name
    gd_by_replicates = {}
    excluded = generate_excluded_dict(growth_data)
    
    # summarize data by condition in dict
    for i, sn_full in enumerate(sample_names):
        if sn_full in sample_locations + ['-']:
            # check if sample name has been defined, if not, don't add to analysis
            continue

        sl = sample_locations[i]
        sn = ' '.join(re.split('_| ', sn_full)[:-1])
        if sn not in gd_by_replicates:
            # initialize dictionary
            gd_by_replicates[sn] = {}
            gd_by_replicates[sn]['sample_names'] = []
            gd_by_replicates[sn]['sample_locs'] = []
            gd_by_replicates[sn]['mus'] = []
            gd_by_replicates[sn]['dts'] = []
            gd_by_replicates[sn]['lts'] = []
            gd_by_replicates[sn]['doublings'] = []
            gd_by_replicates[sn]['doublings_log'] = []
            gd_by_replicates[sn]['yields'] = []

        # discard excluded samples:
        if growth_data[sl]['excluded_flag'] == True:
            excluded[sn] += 1
            continue

        # collect replicate samples
        gd_by_replicates[sn]['sample_names'].append(sn_full)
        gd_by_replicates[sn]['sample_locs'].append(sample_locations[i])
        gd_by_replicates[sn]['mus'].append(growth_data[sl]['mumax'])
        gd_by_replicates[sn]['dts'].append(growth_data[sl]['dt'])
        gd_by_replicates[sn]['lts'].append(growth_data[sl]['t0'])
        gd_by_replicates[sn]['doublings'].append(growth_data[sl]['doublings'])
        gd_by_replicates[sn]['doublings_log'].append(growth_data[sl]['doublings_log'])
        gd_by_replicates[sn]['yields'].append(growth_data[sl]['yield'])

    # add data summary statistics
    for sn in gd_by_replicates:
        # Dash Stores can't hold np.nan values which is why they are stored as 'NaN' strings and converted here
        mus = [np.nan if x == 'NaN' else x for x in gd_by_replicates[sn]['mus']]
        gd_by_replicates[sn]['mu_mean'] = np.nanmean(mus)
        gd_by_replicates[sn]['mu_std'] = np.nanstd(mus)

        dts = [np.nan if x == 'NaN' else x for x in gd_by_replicates[sn]['dts']]
        gd_by_replicates[sn]['dt_mean'] = np.nanmean(dts)
        gd_by_replicates[sn]['dt_std'] = np.nanstd(dts)

        lts = [np.nan if x == 'NaN' else x for x in gd_by_replicates[sn]['lts']]
        gd_by_replicates[sn]['lt_mean'] = np.nanmean(lts)
        gd_by_replicates[sn]['lt_std'] = np.nanstd(lts)

        doublings = [np.nan if x == 'NaN' else x for x in gd_by_replicates[sn]['doublings']]
        gd_by_replicates[sn]['doublings_mean'] = np.nanmean(doublings)
        gd_by_replicates[sn]['doublings_std'] = np.nanstd(doublings)

        doublings_log = [np.nan if x == 'NaN' else x for x in gd_by_replicates[sn]['doublings_log']]
        gd_by_replicates[sn]['doublings_log_mean'] = np.nanmean(doublings_log)
        gd_by_replicates[sn]['doublings_log_std'] = np.nanstd(doublings_log)

        yields = [np.nan if x == 'NaN' else x for x in gd_by_replicates[sn]['yields']]
        gd_by_replicates[sn]['yields_mean'] = np.nanmean(yields)
        gd_by_replicates[sn]['yields_std'] = np.nanstd(yields)



    # plot graphs
    if len(gd_by_replicates) == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    else:
        n_ex = [excluded[sn] if excluded[sn] != 0 else '' for sn in excluded]

        
        samples = list(gd_by_replicates)
        mu_means = [gd_by_replicates[x]['mu_mean'] for x in gd_by_replicates]
        mu_stds = [gd_by_replicates[x]['mu_std'] for x in gd_by_replicates]
        dp_overlay_means = get_overlay_dp(growth_data, gd_by_replicates, 'mumax')
        fig_mus = pl.bar_chart(samples, mu_means, mu_stds, n_ex, y_axis='&#956;<sub>max</sub> [h<sup>-1</sup>]', dp_overlay=dp_overlay_means)

        dt_means = [gd_by_replicates[x]['dt_mean'] for x in gd_by_replicates]
        dt_stds = [gd_by_replicates[x]['dt_std'] for x in gd_by_replicates]
        dp_overlay_dts = get_overlay_dp(growth_data, gd_by_replicates, 'dt')
        fig_dts = pl.bar_chart(samples, dt_means, dt_stds, n_ex, y_axis='doubling time [h]', dp_overlay=dp_overlay_dts)

        lt_means = [gd_by_replicates[x]['lt_mean'] for x in gd_by_replicates]
        lt_stds = [gd_by_replicates[x]['lt_std'] for x in gd_by_replicates]
        dp_overlay_lt = get_overlay_dp(growth_data, gd_by_replicates, 't0')
        fig_lts = pl.bar_chart(samples, lt_means, lt_stds, n_ex, y_axis='lag time [h]', dp_overlay=dp_overlay_lt) 

        doublings_means = [gd_by_replicates[x]['doublings_mean'] for x in gd_by_replicates]
        doublings_stds = [gd_by_replicates[x]['doublings_std'] for x in gd_by_replicates]
        dp_overlay_doublings = get_overlay_dp(growth_data, gd_by_replicates, 'doublings')
        fig_doublings = pl.bar_chart(samples, doublings_means, doublings_stds, n_ex, y_axis='doublings', dp_overlay=dp_overlay_doublings)

        doublings_log_means = [gd_by_replicates[x]['doublings_log_mean'] for x in gd_by_replicates]
        doublings_log_stds = [gd_by_replicates[x]['doublings_log_std'] for x in gd_by_replicates]
        dp_overlay_doublings_log = get_overlay_dp(growth_data, gd_by_replicates, 'doublings_log')
        fig_doublings_log = pl.bar_chart(samples, doublings_log_means, doublings_log_stds, n_ex, y_axis='doublings log-phase', dp_overlay=dp_overlay_doublings_log)

        yields_means = [gd_by_replicates[x]['yields_mean'] for x in gd_by_replicates]
        yields_stds = [gd_by_replicates[x]['yields_std'] for x in gd_by_replicates]
        dp_overlay_yields = get_overlay_dp(growth_data, gd_by_replicates, 'yield')
        fig_yields = pl.bar_chart(samples, yields_means, yields_stds, n_ex, y_axis='yield [{}]'.format(pop_size_measure), dp_overlay=dp_overlay_yields)
        return fig_mus, fig_dts, fig_lts, fig_doublings, fig_doublings_log, fig_yields, gd_by_replicates


@app.callback(
                Output('tooltip_button_smoother', 'children'),
                Input('input_smoother_ws', 'value'),
                Input('store_smoother_flag', 'data'),
                prevent_initial_call = True,
            )
def update_smoother_ws_tooltip(smoothing_ws, smoother_flag):
    if smoother_flag == True:
        tooltip = 'Use raw data'
    else:
        tooltip = 'Smooth data to remove noise using a sliding window of size {}'.format(smoothing_ws)
    return tooltip


@app.callback(
                Output('store_smoother_flag', 'data'),
                Output('store_data_df_smoothed', 'data'),
                Output('button_smoother', 'className'),
                Output('message_area_data_smoother', 'children'),
                Output('store_smoother_value', 'data'),
                Input('button_smoother', 'n_clicks'),
                State('store_data_df', 'data'),
                State('store_smoother_flag', 'data'),
                State('input_smoother_ws', 'value'),
                prevent_initial_call = True,
)
def smooth_data(n_clicks, df, smoother_flag, input_smoother_ws):
    alert_ws = ax.generate_alert(ms.error_smoother_ws)
    try:
        input_smoother_ws = np.int(input_smoother_ws)
    except:
        
        return dash.no_update, dash.no_update, dash.no_update, alert_ws, dash.no_update
    
    if input_smoother_ws <= 0:
        return dash.no_update, dash.no_update, dash.no_update, alert_ws, dash.no_update
    
    if smoother_flag == False:
        smoother_flag = True
        df = pd.DataFrame.from_dict(df, orient='tight')
        df_smoothed = df.rolling(input_smoother_ws, axis=1, min_periods=1, center=True).mean()
        button_shape = 'bi bi-chevron-up'
        return smoother_flag, df_smoothed.to_dict('tight'), button_shape, dash.no_update, input_smoother_ws
    else:
        smoother_flag = False
        button_shape = 'bi bi-circle'
        return smoother_flag, dash.no_update, button_shape, dash.no_update, 0



@app.callback(
                Output('store_auto_fit_ws', 'data'),
                Output('input_auto_default_ws', 'value'),


                Output('store_auto_fit_slope_range', 'data'),
                Output('input_auto_default_sr', 'value'),

                Output('store_auto_fit_r2_var_weight', 'data'),
                Output('input_auto_default_weight', 'value'),

                Output('message_area_fits_parameters', 'children'),
                Input('input_auto_default_ws', 'value'),
                Input('input_auto_default_sr', 'value'),
                Input('input_auto_default_weight', 'value'),
                State('store_auto_fit_ws', 'data'),
                State('store_auto_fit_slope_range', 'data'),
                State('store_auto_fit_r2_var_weight', 'data'),
                prevent_initial_call = True
)
def set_auto_fit_ws_store(ws_value_in, sr_value_in, weight_value_in, ws_value_old, sr_value_old, weight_value_old):
    if dash.callback_context.triggered[0]['prop_id'] == 'input_auto_default_ws.value':
        try:
            v_int = int(ws_value_in)
            return v_int, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        except:
            alert = ax.generate_alert(ms.error_manual_like_fit_ws)
            return dash.no_update, ws_value_old, dash.no_update, dash.no_update, dash.no_update, dash.no_update, alert
    
    if dash.callback_context.triggered[0]['prop_id'] == 'input_auto_default_sr.value':
        try:
            v_float = float(sr_value_in)
            return dash.no_update, dash.no_update, v_float, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        except:
            alert = ax.generate_alert(ms.error_manual_like_fit_sr)
            return dash.no_update, dash.no_update, dash.no_update, sr_value_old, dash.no_update, dash.no_update, alert
     
    if dash.callback_context.triggered[0]['prop_id'] == 'input_auto_default_weight.value':
        try:
            v_float = float(weight_value_in)
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, v_float, dash.no_update, dash.no_update
        except:
            alert = ax.generate_alert(ms.error_manual_like_fit_w)
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, weight_value_old, alert
            




##################
# layout callbacks
##################
@app.callback(
                Output('settings_div', 'is_open'),
                Output('settings_button', 'style'),
                Input('settings_button', 'n_clicks'),
                State('settings_div', 'is_open'),
                State('settings_button', 'style'),
                prevent_initial_call = True
)
def settings_div(n_clicks, is_open_state, style):
    # open settings div on button click
    if is_open_state == True:
        return False, {'font-size': 25, 'color': 'dimgray'}
    else:
        return True, {'font-size': 25, 'color': 'darkslategray'}


@app.callback(
                Output('analysis_div', 'is_open'),
                Output('analysis_flag', 'data'),
                Input('store_gd_by_replicates', 'data'),
                State('analysis_flag', 'data'),
                prevent_initial_call = True
)
def show_analysis_div(selected_data, analysis_flag):
    return True, True


@app.callback(
                Output('store_default_popsizemeasure', 'data'),
                Output('input_popsizemeasure', 'value'),
                Input('input_popsizemeasure', 'value'),
                prevent_initial_call = True,
)
def update_popsizemeasure(input_val):
    return input_val, input_val
   

def encode_plot_for_download(fig):
    buffer = io.StringIO()
    go.Figure(fig).write_html(buffer)
    html_bytes = buffer.getvalue().encode()
    encoded = b64encode(html_bytes).decode()
    href = "data:text/html;base64," + encoded
    return href

@app.callback(
              Output('dt_download', 'href'),
              Output('mu_download', 'href'),
              Output('lt_download', 'href'),
              Output('doublings_download', 'href'),
              Output('doublings_log_download', 'href'),
              Output('yields_download', 'href'),
              Input('fig_dt', 'figure'),
              Input('fig_mu', 'figure'),
              Input('fig_lt', 'figure'),
              Input('fig_doublings' , 'figure'),
              Input('fig_doublings_log' , 'figure'),
              Input('fig_yield', 'figure'),
              prevent_initial_call = True
              )
def make_image(fig_dt, fig_mu, fig_lt, fig_doublings, fig_doublings_log, fig_yields):
    # summary plot download as .html files
    href_dt = encode_plot_for_download(fig_dt)
    href_mu = encode_plot_for_download(fig_mu)
    href_lt = encode_plot_for_download(fig_lt)
    href_doublings = encode_plot_for_download(fig_doublings)
    href_doublings_log = encode_plot_for_download(fig_doublings_log)
    href_yields = encode_plot_for_download(fig_yields)
    return href_dt, href_mu, href_lt, href_doublings, href_doublings_log, href_yields


@app.callback(
    Output("download_sample_data", "data"),
    Input("download_sample_data_button", "n_clicks"),
    State('store_growth_data', 'data'),
    prevent_initial_call=True,
)
def func(n_clicks, df):
    # download summaries of sample data
    df = pd.DataFrame.from_dict(df, orient='index')
    return dcc.send_data_frame(df.to_csv, "sample_data.csv", sep='\t')


@app.callback(
    Output("download_sample_file", "data"),
    Input("button_download_sample_file", "n_clicks"),
    prevent_initial_call=True,
)
def download_sample_file(n_clicks):
    # download sample file
    
    return dcc.send_file('./assets/sample_file.xlsx')


if __name__ == '__main__':
    # import warnings
    # warnings.filterwarnings("ignore")
    app.run_server(debug=True, host="0.0.0.0", port=8050)
    app.config.suppress_callback_exceptions = True
