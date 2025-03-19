import os
import numpy as np
import pandas as pd
import scipy as sp
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
import qtawesome as qta
import pyqtgraph_ext as pgx
from read_winwcp import read_winwcp


class WinWCP_CRC_Viewer(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('WinWCP CRC Viewer')

        self._trace_plot = pgx.Figure()
        self._stimulus_plot = pgx.Figure()
        self._crc_plot = pgx.Figure()

        self._stimulus_plot.setLogMode(False, True)
        self._crc_plot.setLogMode(True, False)
        self._stimulus_plot.setLabel('bottom', 'Time (s)')
        self._stimulus_plot.setLabel('left', '[Ligand] (M)')
        self._trace_plot.setLabel('left', 'Current (A)')
        self._crc_plot.setLabel('bottom', '[Ligand] (M)')
        self._crc_plot.setLabel('left', 'Current (A)')
        self._stimulus_plot.setXLink(self._trace_plot)

        vsplitter = QSplitter(Qt.Vertical)
        vsplitter.addWidget(self._trace_plot)
        vsplitter.addWidget(self._stimulus_plot)
        vsplitter.setSizes([200, 0])

        hsplitter = QSplitter(Qt.Horizontal)
        hsplitter.addWidget(vsplitter)
        hsplitter.addWidget(self._crc_plot)
        hsplitter.setSizes([200, 0])

        self._select_data_dir_button = QPushButton(qta.icon('mdi.folder-open-outline'), 'Select data directory')
        self._select_data_dir_button.pressed.connect(self.set_data_dir)

        self._select_metadata_file_button = QPushButton(qta.icon('mdi.file-document-outline'), 'Select metadata file')
        self._select_metadata_file_button.pressed.connect(self.set_metadata_file)

        self._data_dir_edit = QLineEdit()

        self._metadata_file_edit = QLineEdit('metadata.xlsx')

        self._median_filter_window_spinbox = QSpinBox()
        self._median_filter_window_spinbox.setRange(1, 101)
        self._median_filter_window_spinbox.setSingleStep(2)
        self._median_filter_window_spinbox.setValue(11)
        self._median_filter_window_spinbox.setSpecialValueText('None')

        self._baseline_range_edit = QLineEdit('0, 0.1')
        self._baseline_range_edit.setPlaceholderText('start, stop')

        self._display_range_edit = QLineEdit('0, 1.5')
        self._display_range_edit.setPlaceholderText('start, stop')

        self._refresh_button = QToolButton()
        self._refresh_button.setIcon(qta.icon('mdi.refresh'))
        self._refresh_button.setIconSize(QSize(32, 32))
        self._refresh_button.pressed.connect(self.refresh)

        self._epoch_index_spinbox = QSpinBox()
        self._epoch_index_spinbox.setRange(1, 99)
        self._epoch_index_spinbox.setSingleStep(1)
        self._epoch_index_spinbox.setValue(2)

        self._cell_id_edit = QLineEdit()
        self._cell_id_edit.setPlaceholderText('ID1, ID2, ...')
        self._cell_id_edit.setToolTip('Enter cell IDs separated by commas.\nUse "all" to select all cells.\nDefaults to the last cell.')

        self._settings_button = QToolButton()
        self._settings_button.setIcon(qta.icon('fa.gear'))
        self._settings_button.setIconSize(QSize(32, 32))
        self._settings_button.pressed.connect(self.edit_settings)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(5)
        grid.addWidget(self._select_data_dir_button, 0, 0)
        grid.addWidget(self._select_metadata_file_button, 1, 0)
        grid.addWidget(self._data_dir_edit, 0, 1)
        grid.addWidget(self._metadata_file_edit, 1, 1)
        grid.addWidget(self._settings_button, 0, 2, 2, 1)
        grid.addWidget(self._refresh_button, 0, 3, 2, 1)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.setSpacing(0)
        vbox.addLayout(grid)
        vbox.addWidget(hsplitter)

    def set_data_dir(self, dirpath: str = None):
        if dirpath is None:
            dirpath = QFileDialog.getExistingDirectory(self, 'Select data directory')
        if os.path.exists(dirpath):
            self._data_dir_edit.setText(dirpath)
    
    def set_metadata_file(self, filepath: str = None):
        if filepath is None:
            filepath, _ = QFileDialog.getOpenFileName(self, 'Select metadata file', '', 'Excel files (*.xlsx)')
        if os.path.exists(filepath):
            self._metadata_file_edit.setText(filepath)
    
    def edit_settings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Settings')

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)

        refresh_button = QPushButton('Refresh Main UI')
        refresh_button.setIcon(qta.icon('mdi.refresh'))
        refresh_button.pressed.connect(self.refresh)

        form = QFormLayout(dlg)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)
        form.setHorizontalSpacing(10)
        form.addRow('Cell ID', self._cell_id_edit)
        form.addRow('Median filter window', self._median_filter_window_spinbox)
        form.addRow('Baseline range (s)', self._baseline_range_edit)
        form.addRow('Display range (s)', self._display_range_edit)
        form.addRow('Epoch', self._epoch_index_spinbox)
        form.addRow(refresh_button)
        form.addRow(buttons)

        dlg.exec()

        self._cell_id_edit.setParent(None)
        self._median_filter_window_spinbox.setParent(None)
        self._baseline_range_edit.setParent(None)
        self._display_range_edit.setParent(None)
        self._epoch_index_spinbox.setParent(None)
    
    def refresh(self):
        # get list of WinWCP files in the data directory
        data_dirpath = self._data_dir_edit.text().strip()
        data_files = [file for file in os.listdir(data_dirpath) if file.endswith('.wcp')]

        # ensure metadata_filepath is an absolute path
        # if not, assume it is relative to the data_dirpath
        metadata_filepath = self._metadata_file_edit.text().strip()
        if not metadata_filepath.startswith(os.path.sep):
            metadata_filepath = os.path.join(data_dirpath, metadata_filepath)
        
        # read metadata from Excel file
        # (expects first row to be column titles)
        # (reads all columns as strings)
        metadata = pd.read_excel(metadata_filepath, dtype=str)
        n_rows, n_cols = metadata.shape

        # fill in missing metadata values with the previous value in each column
        nulls = metadata.isnull()
        for col in range(n_cols):
            value = metadata.iloc[0, col]
            for row in range(1, n_rows):
                if nulls.iloc[row, col]:
                    metadata.iloc[row, col] = value
                else:
                    value = metadata.iloc[row, col]
        
        # selected cell(s)
        unique_cell_ids = [cell_id.strip() for cell_id in metadata['Cell'].unique()]
        selected_cell_ids = [cell_id.strip() for cell_id in self._cell_id_edit.text().split(',') if cell_id.strip() != '']
        if (selected_cell_ids == []) and (len(unique_cell_ids) > 0):
            # default to last cell
            selected_cell_ids = unique_cell_ids[-1:]
        elif selected_cell_ids == ['all']:
            selected_cell_ids = unique_cell_ids
        if selected_cell_ids != unique_cell_ids:
            cell_ids = [cell_id.strip() for cell_id in metadata['Cell']]
            row_mask = [cell_id in selected_cell_ids for cell_id in cell_ids]
            metadata = metadata[row_mask]
            n_rows, n_cols = metadata.shape
            metadata.index = range(n_rows)
        
        # visualize CRC
        self._trace_plot.clear()
        time0 = 0
        for row in range(n_rows):
            filename = metadata.loc[row, 'File']
            filepath = os.path.join(data_dirpath, filename)
            if not os.path.exists(filepath):
                continue
            data = read_winwcp(filepath)
            n_sweeps, n_channels, n_samples = data['channel_data'].shape
            dt_sec = data['sample_interval_sec']
            time_sec = np.arange(n_samples) * dt_sec
            current = data['channel_data'][:, 0, :].mean(axis=0)

            # filter
            filter_window = self._median_filter_window_spinbox.value()
            current = sp.signal.medfilt(current, kernel_size=filter_window)

            # baseline
            baseline_range = [float(x) for x in self._baseline_range_edit.text().split(',')]
            baseline_mask = (time_sec >= baseline_range[0]) & (time_sec <= baseline_range[1])
            baseline = current[baseline_mask].mean()
            current -= baseline

            # trace
            display_range = [float(x) for x in self._display_range_edit.text().split(',')]
            display_mask = (time_sec >= display_range[0]) & (time_sec <= display_range[1])
            time_sec = time_sec[display_mask]
            current = current[display_mask]
            time_sec -= time_sec[0]
            current_trace = pgx.Graph(time0 + time_sec, current)
            self._trace_plot.addItem(current_trace)

            # stimulus
            protocol = metadata.loc[row, 'Protocol']
            try:
                epochs = protocol.split(',')
                epoch_index = self._epoch_index_spinbox.value() - 1
                epoch = epochs[epoch_index]
                duration_str, stimulus_str = epoch.split(':')
                if len(selected_cell_ids) > 1:
                    cell_id = metadata.loc[row, 'Cell']
                    stimulus_str = f'Cell {cell_id}: {stimulus_str}'
                stimulus_text = pg.TextItem(stimulus_str, color=(0,0,0), angle=90)
                stimulus_text.setPos(time0, 0)
                self._trace_plot.addItem(stimulus_text)
            except:
                pass

            time0 += time_sec[-1] * 1.1
        self._trace_plot.setLabel('left', f'Current ({data["channel_units"][0]})')


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication()
    widget = WinWCP_CRC_Viewer()
    widget.show()
    app.exec()
