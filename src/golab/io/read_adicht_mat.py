
from pathlib import Path
import numpy as np
import scipy as sp
import xarray as xr
# from datetime import datetime, date, time

def read_adicht_mat(filepath: Path | str) -> xr.Dataset:
    """Read data from a LabChart .adicht file that has been converted to a MATLAB .mat file into an xarray.Dataset.
    """
    
    matdict = sp.io.loadmat(str(filepath), simplify_cells=True)
    # print(matdict)
    current = matdict['current']
    if current.ndim == 1:
        current = current.reshape((1, -1))  # (sweep, time)
    current_units = matdict['current_units']
    # if len(current_units) > 1:
    #     prefix = current_units[0]
    #     if prefix in metric_scale_factors:
    #         current *= metric_scale_factors[prefix]
    #         current_units = current_units[1:]
    time = np.arange(current.shape[-1]) * matdict['time_interval_sec']
    time_units = 's'

    ds = xr.Dataset(
        data_vars={
            'current': xr.DataArray(data=current, dims=['sweep', 'time'], attrs={'units': current_units}),
        },
        coords={
            'time': xr.DataArray(data=time, dims=['time'], attrs={'units': time_units}),
        },
    )

    if 'events' in matdict and matdict['events']:
        ds.attrs['regions'] = []
        for event in matdict['events']:
            time = event['time_sec']
            text = event['text']
            ds.attrs['regions'].append({
                'region': {'time': [time, time]},
                'text': text,
            })
    
    if 'notes' in matdict:
        ds.attrs['notes'] = matdict['notes']
    
    return ds


if __name__ == '__main__':
    filepath = 'your/path/to/file.mat'  # change this
    filepath = "/Users/marcel/Documents/GitHub/GOLab/2023_06_29 _GABAa a1L9'Tb2g2L.mat"
    filepath = "/Users/marcel/Documents/GitHub/GOLab/2024-09-10_IL_1.mat"
    data = read_adicht_mat(filepath)
    print(data)

    import matplotlib.pyplot as plt
    for i, name in enumerate(data.data_vars):
        plt.subplot(len(data.data_vars), 1, i + 1)
        plt.plot(data['time'].values, data[name].mean(dim='sweep').values)
        if i == len(data.data_vars) - 1:
            plt.xlabel(f'Time ({data['time'].attrs['units']})')
        plt.ylabel(f'{name} ({data[name].attrs['units']})')
    plt.tight_layout()
    plt.show()