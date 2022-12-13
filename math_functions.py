'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Dashing Growth Curves. If not, see <https://www.gnu.org/licenses/>.
'''

import numpy as np


def lin_function(x, m, t):
    return m * x + t

def exp_function(t, n0, mu):
    return n0 * np.exp(1)**(mu * t)

def modified_gompertz(x, A, mu, l):
    # modified Gompertz function from "Modeling of the Bacterial Growth Curve", Zwittering et al, 1990
    return A * np.exp(1)**(- np.exp(1)**(mu * np.exp(1) / A * (l - x) + 1))

def modified_logistic(x, A, mu, l):
    # modified Logistic function from "Modeling of the Bacterial Growth Curve", Zwittering et al, 1990
    return A * 1 / (1 + np.exp(1)**(4 * mu / A * (l - x) + 2))

def modified_richards(x, A, mu, l, v):
    # modified Richards function from "Modeling of the Bacterial Growth Curve", Zwittering et al, 1990
    return A * (1 + v * np.exp(1)**(1 + v) * np.exp(1)**(mu / A * (1 + v) * (1 + 1/v) * (l -x)))**(-1/v)

def modified_schnute(x, A, mu, l, v):
    # modified Richards function from "Modeling of the Bacterial Growth Curve", Zwittering et al, 1990
    return (mu * (1 - v) / A) * ((1 - v * np.exp(1)**(A * l + 1 - v - A * x)) / (1 - v))**(1/v)

def comp_R2(xdata, ydata, popt):
    residuals = ydata - lin_function(xdata, *popt)

    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((ydata - np.mean(ydata))**2)

    r2 = 1 - (ss_res / ss_tot)
    return r2

def rmse(data, data_predicted):
    return np.sqrt(np.mean((data_predicted - data) ** 2))