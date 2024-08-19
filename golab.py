import numpy as np
import scipy as sp
import matplotlib.pyplot as plt


# Set non-numeric values to NaN in DataFrame columns.
# This allows marking outliers with an asterix as in GraphPad Prism
def remove_outliers(df, columns=None):
    if columns is None:
        columns = df.columns
    for col in columns:
        if df[col].dtypes == 'object':
            values = df[col].values
            for i in range(len(values)):
                if type(values[i]) is str:
                    values[i] = np.nan
            df[col] = np.array(values, dtype=float)


# Hill equation for fitting concentration-response curves
def hill_equation(x, *params):
    if len(params) == 2:
        EC50, slope = params
        y = (x**slope) / (EC50**slope + x**slope)
    elif len(params) == 3:
        ymax, EC50, slope = params
        y = ymax * (x**slope) / (EC50**slope + x**slope)
    return y


# Optimize Hill fit parameters for concentration-response curve (CRC)
def fit_CRC(x, y, params=None, bounds=None):
    if params is None:
        params = (max(y), np.median(x), 1)  # ymax, EC50, slope
    if bounds is None:
        if len(params) == 2:
            bounds = [(min(x), 0), (max(x), np.inf)]
        elif len(params) == 3:
            bounds = [(0, min(x), 0), (np.inf, max(x), np.inf)]
    params, _ = sp.optimize.curve_fit(hill_equation, x, y, p0=params, bounds=bounds)
    return params


# Plot concentration-response curve (CRC) data with Hill curve
def plot_CRC(x, y, params=None, normalize=False, show_params_text=False, show_fit=True, xfit=None, xpad_factor=3, marker='o', ax=None, **kwargs):
    # params
    if params is not None:
        if len(params) == 2:
            ymax = 1
            EC50, slope = params
        elif len(params) == 3:
            ymax, EC50, slope = params
    else:
        ymax = max(y)
    
    # plot axes
    if ax is None:
        ax = plt.gca()
    
    # plot data points
    if normalize:
        y = y / ymax
    xy = ax.plot(x, y, marker, **kwargs)
    ax.set_xscale('log')

    # plot fitted curve
    if show_fit and (params is not None):
        if xfit is None:
            x_fit = np.logspace(np.log10(min(x) / xpad_factor), np.log10(max(x) * xpad_factor), 100)
        y_fit = hill_equation(x_fit, *params)
        if normalize:
            y_fit = y_fit / ymax
        ax.plot(x_fit, y_fit, color=ax.lines[-1].get_color())

    # print params on the plot
    if show_params_text and (params is not None):
        if len(params) == 2 or normalize:
            ax.text(0.02, 0.98, f'EC50: {EC50:.2e}\nslope: {slope:.2f}', transform=plt.gca().transAxes, ha='left', va='top')
        elif len(params) == 3:
            ax.text(0.02, 0.98, f'ymax: {ymax:.2f}\nEC50: {EC50:.2e}\nslope: {slope:.2f}', transform=plt.gca().transAxes, ha='left', va='top')

    # default axis labels
    ax.set_xlabel('[Ligand] (M)')
    ax.set_ylabel(r'Response ($\mu$A)')