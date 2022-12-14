'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Dashing Growth Curves. If not, see <https://www.gnu.org/licenses/>.
'''



import default_settings as ds
import dash_bootstrap_components as dbc
from dash import dcc



### tooltips
tooltip_sample_name = 'Enter a sample name that\'s unique and different from the location identifier. For replicates add a replicate identifier to the sample name (e.g. \'_1\' or \' 1\')'
tooltip_blanks = 'Enter a comma-separated list of sample names which will be used as blanks for the current sample.'
tooltip_popsizemeasure = 'Provide name of method used to measure population size. For formatting use markdown.'
tooltip_data_smoothing = 'Smooth data to remove noise using a sliding window of size {}'.format(ds.default_smoothing_window_size)
tooltip_autofitting_button = 'Automatically detect exponential growth phases in data and extract growth parameters (individual samples can be adjusted afterwards) - computation may take a few minutes depending on the size of your dataset', 
tooltip_autofitting_docs = 'Documentation of fitting algorithms'

tooltip_auto_ws = 'Set the rolling window size for curve smoothing, larger values smooth out more noise in the data (important, else the fitting algorithm detects the exponential growth phase in the noise)'
tooltip_auto_sr = 'Delineate window around maximum slope that is considered for exponential growth'
tooltip_auto_weight = 'Higher values favor improved fit over size of the fitted area'

tooltip_set_blanks = 'Set the default blanks for all samples (Note: overrides previously set blanks for individual samples)'

tooltip_csv_download = dcc.Markdown('t0: start of log phase<br>t1: end of log-phase<br>t0_idx: datapoint at which log-phase starts', dangerously_allow_html=True)
# settings div


### error messages
error_upload_file = 'Could not read file. File needs to be either Excel file or semicolon-separated .csv file'

error_blank_name = 'Invalid blank name. All blank names need to be existing sample names.'
error_blank_location = 'Invalid blank locations. All blank names need to be existing sample names.'
error_duplicate_sample = 'Duplicate sample name. Sample names need to be unique. For replicates append number to sample name (e.g. test 5)'

error_smoother_ws = 'window size needs to be an integer > 0'

error_manual_like_fit_ws = 'Window size needs to be an integer value'
error_manual_like_fit_sr = 'Slope range needs to be a float value'
error_manual_like_fit_w = 'Weight needs to be an float value'


# landing page
intro_text = dcc.Markdown('''
                Use {} to quickly extract growth parameters (e.g. max. growth rate, lag time, etc.)\
                    from growth curves for hundreds of samples.<br>
                Growth curves can be fit by conventional manual selection of the linear growth phase in a\
                    log plot or automatically by different statistical growth models.
             '''.format(ds.app_name),
             dangerously_allow_html=True)

upload_area = dcc.Markdown(
                '<b>Drag and Drop or Select File (semicolon-separated .csv or Excel)</b>',
                 dangerously_allow_html=True
                 )
                                                                    

data_privacy_text = dcc.Markdown('''
    No data is stored on the server. {0} is open source. For sensitive data {0} can be installed [locally](https://github.com/Dahlai/growthdash)
                    '''.format(ds.app_name)
                    )
