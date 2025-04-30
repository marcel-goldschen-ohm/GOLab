
from pathlib import Path
import numpy as np
import scipy as sp
import xarray as xr

def read_adicht_mat(filepath: Path | str) -> xr.Dataset:
    """Read data from a LabChart .adicht file that has been converted to a MATLAB .mat file into an xarray.Dataset.
    """
    
    matdict = sp.io.loadmat(str(filepath), simplify_cells=True)
    # print(matdict)

    current = matdict['current']
    if current.ndim == 1:
        current = current.reshape((1, -1))  # (sweep, time)
    current_units = matdict['current_units']

    voltage = matdict['voltage']
    if voltage.ndim == 1:
        voltage = voltage.reshape((1, -1))  # (sweep, time)
    voltage_units = matdict['voltage_units']

    sweeps = np.arange(1, current.shape[0] + 1)
    
    time = np.arange(current.shape[-1]) * matdict['time_interval_sec']
    time_units = 's'

    ds = xr.Dataset(
        data_vars={
            'Im': xr.DataArray(data=current, dims=['sweep', 'time'], attrs={'units': current_units}),
            'Vm': xr.DataArray(data=voltage, dims=['sweep', 'time'], attrs={'units': voltage_units}),
        },
        coords={
            'sweep': xr.DataArray(data=sweeps, dims=['sweep']),
            'time': xr.DataArray(data=time, dims=['time'], attrs={'units': time_units}),
            'sweep_status': xr.DataArray(data=np.array(['ACCEPTED'] * len(sweeps), dtype=object),  dims=['sweep']),
        },
    )

    if 'events' in matdict and matdict['events']:
        ds.attrs['regions'] = []
        for event in matdict['events']:
            time = event['time_sec']
            text = event['text']
            ds.attrs['regions'].append({
                'region': [time, time],
                'text': text,
            })
    
    if 'notes' in matdict:
        ds.attrs['notes'] = matdict['notes']
    
    return ds


if __name__ == '__main__':
    filepath = 'your/path/to/file.mat'  # change this
    filepath = '/Users/marcel/Documents/GitHub/GOLab/2025_04_29 GABA-A a1b2g2 repeated GABA & PPF applications_L_1_H a1b2g2_1.mat'
    dt = read_adicht_mat(filepath)
    print(dt)

    import matplotlib.pyplot as plt
    for i, name in enumerate(dt.data_vars):
        plt.subplot(len(dt.data_vars), 1, i + 1)
        dt[name].mean(dim='sweep').plot()
    plt.tight_layout()
    plt.show()