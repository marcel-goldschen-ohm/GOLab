
import struct
import numpy as np
from datetime import datetime, date, time

def read_winwcp(filepath: str):
    """Read data from a WinWCP file."""

    # read file contents as binary byte array
    with open(filepath, mode='rb') as file:
        file_bytes = file.read()

    # search for the number of channels in the header
    start = file_bytes.find(b'NC=') + 3
    stop = start + file_bytes[start:].find(b'\r\n')
    n_channels = int(file_bytes[start:stop])

    # read header
    n_header_bytes = (int((n_channels - 1) / 8) + 1) * 1024
    header_bytes = file_bytes[:n_header_bytes]
    header_lines = header_bytes.decode('utf-8').split('\r\n')
    header = {}
    for line in header_lines:
        try:
            k, v = line.split('=')
            header[k] = v
        except:
            pass

    # read records (i.e., sweeps)
    # Each record consists of an analysis block followed by a data block.
    n_sweeps = int(header['NR'])
    try:
        n_analysis_bytes = int(header['NBA']) * 512
    except:
        n_analysis_bytes = (int((n_channels - 1) / 8) + 1) * 1024
    n_data_bytes = int(header['NBD']) * 512
    try:
        n_samples = int(header['NP'])
    except:
        n_samples = int(n_data_bytes / 2 / n_channels)

    # store everything in a dict
    data = {}
    data['winwcp_header'] = header
    data['sample_interval_sec'] = float(header['DT'])
    data['channel_names'] = np.array([header[f'YN{i}'] for i in range(n_channels)], dtype=object)
    data['channel_units'] = np.array([header[f'YU{i}'] for i in range(n_channels)], dtype=object)
    data['digitized_signal'] = np.zeros((n_sweeps, n_channels, n_samples), dtype=np.int16)
    data['channel_physical_signal_conversion_factors'] = np.ones(n_channels)
    data['sweep_status'] = np.array([''] * n_sweeps, dtype=object)
    data['sweep_type'] = np.array([''] * n_sweeps, dtype=object)
    data['sweep_group'] = np.zeros(n_sweeps)
    data['sweep_start_time_sec'] = np.zeros(n_sweeps)
    data['sweep_sample_interval_sec'] = np.zeros(n_sweeps)
    
    # datetime
    date = header['CTIME'].split(' ')[0].strip()
    month, day, year = date.split('-')
    if len(year) == 2:
        year = f'20{year}'
    if len(month) == 1:
        month = f'0{month}'
    if len(day) == 1:
        day = f'0{day}'
    date = f'{year}-{month}-{day}'
    timestamp = header['RTIME'].split(' ')[-1].strip()
    data['date'] = date
    data['datetime'] = f'{date} {timestamp}'

    # needed for converting digitized signal to signal in physical units
    ADCmax = int(header['ADCMAX'])
    gain_per_channel = np.array([float(header[f'YG{i}']) for i in range(n_channels)])#.reshape(n_channels, 1)

    for i in range(n_sweeps):
        n_offset_bytes = n_header_bytes + i * (n_analysis_bytes + n_data_bytes)
        analysis_bytes = file_bytes[n_offset_bytes:n_offset_bytes+n_analysis_bytes]
        data_bytes = file_bytes[n_offset_bytes+n_analysis_bytes:n_offset_bytes+n_analysis_bytes+n_data_bytes]

        data['sweep_status'][i] = analysis_bytes[:8].decode('utf-8')
        data['sweep_type'][i] = analysis_bytes[8:12].decode('utf-8')
        data['sweep_group'][i] = struct.unpack('f', analysis_bytes[12:16])[0]
        data['sweep_start_time_sec'][i] = struct.unpack('f', analysis_bytes[16:20])[0]
        data['sweep_sample_interval_sec'][i] = struct.unpack('f', analysis_bytes[20:24])[0]
        Vmax_per_channel = np.array(struct.unpack('f'*n_channels, analysis_bytes[24:24+4*n_channels]))#.reshape(n_channels, 1)
        data['channel_physical_signal_conversion_factors'][i] = Vmax_per_channel

        # digitized data as 16-bit signed integers -> (channel, sample)
        n_pts = int(n_samples * n_channels)
        digitized_sweep = np.array(struct.unpack('h'*n_pts, data_bytes[:2*n_pts])).reshape(n_samples, n_channels).T
        data['digitized_signal'][i] = digitized_sweep
        
        # calibrated signal in physical units
        data['channel_data'][i] = (Vmax_per_channel / (ADCmax * gain_per_channel)) * digitized_signal
    
    return data


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    filepath = 'your/path/to/file.wcp'  # change this
    data = read_winwcp(filepath)
    n_sweeps, n_channels, n_samples = data['channel_data'].shape
    time_sec = np.arange(n_samples) * data['sample_interval_sec']

    # plot the sweep average
    fig, ax = plt.subplots(nrows=n_channels, ncols=1)
    for i in range(n_channels):
        ax[i].plot(time_sec, data['channel_data'][:,i].mean(axis=0), lw=1)
        ax[i].set_ylabel(f'{data["channel_names"][i]} ({data["channel_units"][i]})')
    ax[-1].set_xlabel('Time (s)')
    ax[0].set_title(data["datetime"])
    plt.tight_layout()
    plt.show()
