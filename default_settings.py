'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>.
'''

################################################
# app name
################################################
# app_name = 'GrowthRat0r'
app_name = 'Dashing Growth Curves'

################################################
# default population density measure
################################################
default_pop_size_measure = 'OD<sub>600</sub>'


################################################
# manual-like fitting algorithm
################################################
auto_fit_default_ws = 10        # default rolling window size for auto fitting algorithm
auto_fit_default_sr = 0.6       # default slope range for auto fitting algrorithm
auto_fit_default_weight = 25    # default weight of optimiation algorithm
default_smoothing_window_size = 10


################################################
# available automatic fitting algorithms
################################################
fittings_algorithms = ['Gompertz - tight', 'Gompertz - conventional', 'Logistic - tight', 'Logistic - conventional', ]  #'Manual-like', 'Schnute', 'Richards'
default_fitting_algorithm = 'Gompertz - tight'


################################################
# outgoing links
################################################
tutorial_link = 'https://www.youtube.com/watch?v=lhvgZyPlHzA'
models_links =  'https://github.com/mretier/growthdash/blob/master/docs_growth_curve_fitting.md'