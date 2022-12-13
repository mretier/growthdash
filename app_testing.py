# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import plotly.express as px
import plotly
import plotly.graph_objects as go
import pandas as pd
import base64
import io
import numpy as np

from scipy.ndimage import uniform_filter1d
from scipy.optimize import curve_fit




def lin_function(x, m, t):
    return m * x + t

def comp_R2(xdata, ydata, popt):
    residuals = ydata - lin_function(xdata, *popt)

    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((ydata - np.mean(ydata))**2)

    r2 = 1 - (ss_res / ss_tot)
    return r2


def modified_gompertz(x, A, mu, l):
    # modified Gompertz function from "Modeling of the Bacterial Growth Curve", Zwittering et al, 1990
    return A * np.exp(- np.exp(mu * np.exp(1) / A * (l - x) + 1))

def modified_richards(x, A, mu, l, v):
    # modified Richards function from "Modeling of the Bacterial Growth Curve", Zwittering et al, 1990
    return A * (1 + v * np.exp(1 + v) * np.exp(mu / A * (1 + 1 / v) * (1 + v) * (l - x)))**(-1/v)


df = pd.read_excel('./../20220909_r41_to_r44_growthcurves_mineraloil_test_1.xlsx')

mu


y = df.iloc[18, 1:]
blank = df.iloc[0, 1:]

y_b = y - blank
# y_b = np.log(y_b.values.astype(float))

n0 = np.min([y_i for y_i in y_b if y_i > 0])


r = np.log(y_b.astype(float) / n0)


r
nan_inf_mask = ~np.isnan(r) & (r != -np.inf) & (r > 0)
r
x = r.index

y_log_clean = r.values[nan_inf_mask]

x_clean = x[nan_inf_mask]


popt, pcov = curve_fit(modified_richards, x_clean, y_log_clean, p0=[2, 0.5, 0.5, 2], bounds=[[0, 0, -np.inf, 0], [np.inf, np.inf, np.inf, np.inf]], maxfev=100000)
popt[1]
popt[3]
popt_log, pcov_log = curve_fit(modified_gompertz, x_clean, y_log_clean, p0=[2, 0.5, 0.5], bounds=[[0, 0, -np.inf], [np.inf, np.inf, np.inf]], maxfev=100000)
popt_log[1]

popt
pcov.diagonal()

A = popt[0]
A_std = np.sqrt(pcov[0, 0])
mu = popt[1]
mu_std = np.sqrt(pcov[1, 1])
l = popt[2]
l_std = np.sqrt(pcov[2, 2])
v = popt[3]
v_std = np.sqrt(pcov[3, 3])
x_clean
y_fit = modified_richards(x_clean, A, mu, l, v)

np.gradient(y_fit).max()
A
mu
l
v
data = [
        go.Scatter(x = x_clean, y = y_log_clean),
        go.Scatter(x = x_clean, y = y_fit)
]

figure = go.Figure(data=data)
figure.show()


fig2 = figure
fig2.show()
