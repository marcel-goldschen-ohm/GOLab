from __future__ import annotations
import os
import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import scipy as sp
import xarray as xr
import zarr
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import qtawesome as qta
import pyqtgraph as pg
import pyqtgraph_ext as pgx
from pyqt_ext.widgets import *
from xarray_treeview import *

from pint import UnitRegistry
UREG = UnitRegistry()

from importlib.metadata import version
VERSION = version('golab')

TODO = """
- apply scaling
"""


# class GOLabChart(QObject):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self._init_menubar()
#         self.new_window()
    
#     def _init_menubar(self) -> None:
#         self._menubar = QMenuBar()

#         self._file_menu = self._menubar.addMenu("File")
#         self._file_menu.addAction('New Window', QKeySequence.StandardKey.New, self.new_window)
#         self._file_menu.addSeparator()
#         self._file_menu.addAction(qta.icon('fa5.folder-open'), 'Open', QKeySequence.StandardKey.Open, lambda: (self.active_window() or self.new_window()).load())
#         # self._import_menu = self._file_menu.addMenu('Import')
#         self._file_menu.addSeparator()
#         self._file_menu.addAction(qta.icon('fa5.save'), 'Save', QKeySequence.StandardKey.Save, lambda: self.active_window().save(self.active_window()._filepath.with_suffix('.zarr.zip')))
#         self._file_menu.addAction(qta.icon('fa5.save'), 'Save As', QKeySequence.StandardKey.SaveAs, lambda: self.active_window().save())
#         self._file_menu.addSeparator()
#         self._file_menu.addAction('Close Window', QKeySequence.StandardKey.Close, lambda: self.active_window().close())
#         self._file_menu.addSeparator()
#         self._file_menu.addAction('Quit', QKeySequence.StandardKey.Quit, qApp.quit)

#         # self._import_menu.addAction('Zarr zip store (.zip)')
#         # self._import_menu.addSeparator()
#         # self._import_menu.addAction('WinWCP (.wcp)')
#         # self._import_menu.addSeparator()
#         # self._import_menu.addAction('LabChart GOLab conversion (.mat)')
#         # self._import_menu.addSeparator()
#         # self._import_menu.addAction('HEKA (.dat)')
#         # self._import_menu.addSeparator()
#         # self._import_menu.addAction('Axon (.abf)')

#         self._channels_menu = self._menubar.addMenu("Channels")
#         self._channels_menu.addAction('Rename Channels', lambda: self.active_window().rename_channels())

#         self._sweeps_menu = self._menubar.addMenu("Sweeps")
#         action = self._sweeps_menu.addAction('Mask Selected Sweeps', QKeySequence("M"), lambda: self.active_window().mask_selected_sweeps())
#         action.setShortcutContext(Qt.ApplicationShortcut)
#         self._sweeps_menu.addAction('Unmask Selected Sweeps', QKeySequence("U"), lambda: self.active_window().unmask_selected_sweeps())

#         self._regions_menu = self._menubar.addMenu("Regions")
#         self._regions_menu.addAction('Draw New Region', QKeySequence("R"), lambda: self.active_window().start_drawing_regions())
#         self._regions_menu.addSeparator()
#         self._regions_menu.addAction('Show All Regions', lambda: self.active_window().show_all_regions())
#         self._regions_menu.addAction('Hide All Regions', lambda: self.active_window().hide_all_regions())
#         self._regions_menu.addAction('Toggle Region Visibility', QKeySequence("T"), lambda: self.active_window().toggle_active_regions())
#         self._regions_menu.addSeparator()
#         self._regions_menu.addAction('Group Active Regions', QKeySequence("G"), lambda: self.active_window().group_active_regions())
#         self._regions_menu.addAction('Format Active Regions', lambda: self.active_window().format_active_regions())
#         self._regions_menu.addAction('Delete Active Regions', lambda: self.active_window().delete_active_regions())

#         self._detrend_menu = self._menubar.addMenu("Detrend")
#         self._detrend_menu.addAction('Linear Two Peaks Rundown')
#         self._detrend_menu.addAction('Baseline Rundown')
    
#     def windows(self) -> list[GOLabChartWindow]:
#         windows = []
#         for widget in qApp.topLevelWidgets():
#             if isinstance(widget, GOLabChartWindow):
#                 windows.append(widget)
#         return windows
    
#     def active_window(self) -> GOLabChartWindow | None:
#         window = qApp.activeWindow()
#         if isinstance(window, GOLabChartWindow):
#             return window
    
#     def new_window(self) -> GOLabChartWindow:
#         window = GOLabChartWindow()
#         window.show()
#         return window


class GOLabChart(QMainWindow):

    MASKED = 'REJECTED'
    UNMASKED = 'ACCEPTED'

    UNGROUPED = 'Ungrouped'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(self.__class__.__name__)

        self._datatree = xr.DataTree()

        self._init_ui()

        if False:
            n_sweeps = 5
            n_samples = 1000
            ds = xr.Dataset(
                data_vars={
                    'Im': xr.DataArray(
                        data=np.random.randn(n_sweeps, n_samples) * 100, 
                        dims=['sweep', 'time'], 
                        attrs={'units': 'pA'}),
                    'Vm': xr.DataArray(
                        data=np.random.randn(n_sweeps, n_samples), 
                        dims=['sweep', 'time'], 
                        attrs={'units': 'mV'}),
                },
                coords={
                    'sweep': np.arange(1, n_sweeps + 1),
                    'time': xr.DataArray(
                        data=np.arange(n_samples) * 0.0001,
                        dims=['time'],
                        attrs={'units': 's'}),
                    'sweep_status': xr.DataArray(
                        data=np.array([self.UNMASKED]*n_sweeps), 
                        dims=['sweep']),
                },
            )
            ds['sweep_status'][:2] = self.MASKED
            self._root['Data'] = ds
            self._root['Data/Baselined'] = ds[['Im']].reset_coords(drop=True)
            self._root['Data/Baselined']['Im'] += 100
            self.notes = 'This is a test note.'
            self.xregions = [
                {'group': 'GABA', 'region': [0.1, 0.2]},
                {'group': self.UNGROUPED, 'region': [0.3, 0.4]},
            ]
        
        # self.refresh()
    
    def __del__(self):
        self._shutdown_console()
    
    @property
    def datatree(self) -> xr.DataTree:
        return self._datatree
    
    @datatree.setter
    def datatree(self, dt: xr.DataTree) -> None:
        self._datatree = dt
        self.refresh()
    
    @property
    def metadata(self) -> dict:
        return self.datatree['Data'].attrs
    
    @metadata.setter
    def metadata(self, metadata: dict):
        self.datatree['Data'].attrs = metadata
    
    # @property
    # def date(self) -> datetime.date:
    #     return datetime.strptime(self.metadata['date'], "%Y-%m-%d")
    
    # @date.setter
    # def date(self, date: datetime.date | str):
    #     if isinstance(date, datetime.date):
    #         self.metadata['date'] = date.strftime("%Y-%m-%d")
    #     elif isinstance(date, str):
    #         self.metadata['date'] = date.strip()
    
    @property
    def regions(self) -> list[dict]:
        if 'regions' not in self.metadata:
            self.metadata['regions'] = []
        return self.metadata['regions']
    
    @regions.setter
    def regions(self, regions: list[dict]):
        self.metadata['regions'] = regions
        self._update_active_regions()
        self._update_region_groups_menu()
    
    # datatree paths
    
    def datatree_paths(self) -> list[str]:
        # all paths except the root
        return [path for path, node in self.datatree.subtree_with_keys if node.parent is not None]
    
    def selected_datatree_paths(self) -> list[str]:
        return [path for path in self._datatree_view.selectedPaths()]
    
    def set_selected_datatree_paths(self, paths: list[str]) -> None:
        self._datatree_view.setSelectedPaths(paths)
    
    # channels

    def channels(self) -> list[str]:
        try:
            return list(self.datatree['Data'].data_vars)
        except KeyError:
            return []
    
    def selected_channels(self) -> list[str]:
        return [
            action.defaultWidget().text() 
            for action in self._channel_actions() 
            if action.defaultWidget().isChecked()
        ]
    
    def set_selected_channels(self, channels: list[str]) -> None:
        for action in self._channel_actions():
            action.defaultWidget().setChecked(action.defaultWidget().text() in channels)
        self.replot()
    
    def _channel_actions(self) -> list[QWidgetAction]:
        try:
            actions = self._channels_button_menu.actions()
            before = actions.index(self._before_channel_actions)
            after = actions.index(self._after_channel_actions)
            return actions[before+1:after]
        except IndexError:
            return []
    
    def _update_channels_menu(self) -> None:
        channels = self.channels()
        old_actions = self._channel_actions()
        old_selection = {action.defaultWidget().text(): action.defaultWidget().isChecked() for action in old_actions}
        if (len(channels) > 1) and (channels == list(old_selection)):
            # keep current selection
            return
        
        # remove old actions
        for action in old_actions:
            self._channels_button_menu.removeAction(action)
        
        # insert new actions
        new_actions = []
        for channel in channels:
            checked = old_selection.get(channel, True) if len(channels) > 1 else True
            checkbox = QCheckBox(channel, checked=checked)
            checkbox.stateChanged.connect(lambda state: self.replot())
            action = QWidgetAction(self)
            action.setDefaultWidget(checkbox)
            new_actions.append(action)
        self._channels_button_menu.insertActions(self._after_channel_actions, new_actions)
        
        self._channels_menu.setEnabled(len(channels) > 0)
    
    def rename_channels(self) -> None:
        channels = self.channels()
        if len(channels) == 0:
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle('Rename Channels')
        vbox = QVBoxLayout(dlg)
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.setSpacing(10)

        edits = {channel: QLineEdit() for channel in channels}
        for channel, edit in edits.items():
            edit.setPlaceholderText(channel)
            vbox.addWidget(edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        vbox.addWidget(buttons)
        
        if dlg.exec() != QDialog.Accepted:
            return
        
        rename_map = {}
        for channel in channels:
            new_channel = edits[channel].text().strip()
            if new_channel != '':
                rename_map[channel] = new_channel
        
        if rename_map:
            for node in self.datatree['Data'].subtree:
                node.dataset = node.to_dataset().rename_vars(rename_map)
            self.refresh()
    
    # sweeps
    
    def sweeps(self, include_masked = True) -> np.ndarray:
        try:
            sweeps = self.datatree['Data/sweep'].values
        except KeyError:
            return np.array([], dtype=int)
        if include_masked:
            return sweeps
        try:
            mask = self.datatree['Data/sweep_status'].values != self.MASKED
            return sweeps[mask]
        except KeyError:
            return sweeps
    
    def selected_sweeps(self) -> np.ndarray:
        return self._sweeps_spinner.selectedValues()
    
    def set_selected_sweeps(self, sweeps: np.ndarray) -> None:
        self._sweeps_spinner.setSelectedValues(sweeps)
    
    def _selectable_sweeps(self) -> np.ndarray:
        return self._sweeps_spinner.indexedValues()
    
    def _set_selectable_sweeps(self, sweeps: np.ndarray) -> None:
        sweeps = np.intersect1d(sweeps, self.sweeps())
        
        if self._sweeps_spinner.selectedValues().size == self._sweeps_spinner.indexedValues().size:
            # all sweeps were selected, so keep all selected
            selected_sweeps = sweeps
        else:
            selected_sweep_indices = np.intersect1d(np.arange(sweeps.size), self._sweeps_spinner.indices())
            selected_sweeps = sweeps[selected_sweep_indices]
            if selected_sweeps.size == 0 and sweeps.size > 0:
                selected_sweeps = sweeps[:1]
        
        self._sweeps_spinner.blockSignals(True)
        self._sweeps_spinner.setIndexedValues(sweeps)
        self._sweeps_spinner.setSelectedValues(selected_sweeps)
        self._sweeps_spinner.blockSignals(False)

        n_sweeps = len(sweeps)
        self._sweeps_label_action.setVisible(n_sweeps > 1)
        self._sweeps_spinner_action.setVisible(n_sweeps > 1)
        # self._sweeps_menu.setEnabled(n_sweeps > 0)
        # self._tile_sweeps_action_group.setEnabled(n_sweeps > 1)
    
    def _update_sweeps_spinbox(self) -> None:
        sweeps = self.sweeps(include_masked=self._include_masked_sweeps_checkbox.isChecked())
        self._set_selectable_sweeps(sweeps)
    
    def sweep_status(self, sweep: int) -> str:
        return self.datatree['Data/sweep_status'].sel(sweep=sweep).item()
    
    def set_sweep_status(self, sweep: int, status: str) -> None:
        self.datatree['Data/sweep_status'].loc[sweep] = status
    
    def mask_sweeps(self, sweeps: np.ndarray | list[int] | int) -> None:
        if isinstance(sweeps, int) or np.isscalar(sweeps):
            sweeps = [sweeps]
        for sweep in sweeps:
            self.set_sweep_status(sweep, self.MASKED)
        self.refresh()
    
    def unmask_sweeps(self, sweeps: np.ndarray | list[int] | int) -> None:
        if isinstance(sweeps, int) or np.isscalar(sweeps):
            sweeps = [sweeps]
        for sweep in sweeps:
            self.set_sweep_status(sweep, self.UNMASKED)
        self.refresh()
    
    def mask_selected_sweeps(self) -> None:
        sweeps = self.selected_sweeps()
        if len(sweeps) > 0:
            self.mask_sweeps(sweeps)
    
    def unmask_selected_sweeps(self) -> None:
        sweeps = self.selected_sweeps()
        if len(sweeps) > 0:
            self.unmask_sweeps(sweeps)
    
    # regions

    def add_region(self, region: dict) -> None:
        if ('group' not in region) or (region['group'] == ''):
            region['group'] = self.UNGROUPED
        self.regions.append(region)

        self._add_region_to_plots(region)
        self._update_region_groups_menu()
        self._on_region_plot_item_drag_finished() # updates previews
    
    def _add_region_to_plots(self, region: dict, plots: list[pgx.Plot] = None) -> None:
        if plots is None:
            plots = self._plots()
        for plot in plots:
            item = pgx.XAxisRegion()
            item.setState(region)
            item._region_ref = region  # ref to data
            item.sigRegionChanged.connect(self._on_region_plot_item_changed)
            item.sigRegionDragFinished.connect(self._on_region_plot_item_drag_finished)
            item.sigEditingFinished.connect(self._on_region_plot_item_changed)
            item.sigRequestDeletion.connect(self._on_region_plot_item_deleted)
            plot.vb.addItem(item)
            item.setZValue(0)
    
    def active_regions(self) -> list[dict]:
        plots = self._plots()
        if len(plots) == 0:
            return []
        plot = plots[0]
        items = [item for item in plot.vb.allChildren() if isinstance(item, pgx.XAxisRegion) and item.isVisible()]
        regions = []
        for item in items:
            if item._region_ref not in regions:
                regions.append(item._region_ref)
        return regions

    def set_active_regions(self, regions: list[dict]) -> None:
        self._clear_region_plot_items()
        for region in regions:
            self._add_region_to_plots(region)
        self._update_region_groups_menu()
        self._on_region_plot_item_drag_finished() # updates previews
    
    def _regions_mask(self, x: xr.DataArray = None, regions: list[dict] = None) -> np.ndarray:
        if x is None:
            x = self.datatree['Data/time']
        
        if regions is None:
            regions = self.active_regions()
        
        if len(regions) == 0:
            mask = np.full(x.values.shape, True, dtype=bool)
            return mask
        
        mask = np.full(x.values.shape, False, dtype=bool)
        for region in regions:
            xmin, xmax = region['region']
            mask[(x.values >= xmin) & (x.values <= xmax)] = True
        return mask
    
    def _region_plot_items(self, plots: list[pgx.Plot] = None) -> list[pgx.XAxisRegion]:
        if plots is None:
            plots = self._plots()
        items = []
        for plot in self._plots():
            items.extend([item for item in plot.vb.allChildren() if isinstance(item, pgx.XAxisRegion)])
        return items
    
    def _clear_region_plot_items(self, plots: list[pgx.Plot] = None) -> None:
        if plots is None:
            plots = self._plots()
        for plot in plots:
            items = [item for item in plot.vb.allChildren() if isinstance(item, pgx.XAxisRegion)]
            for item in items:
                # likely a bug in pyqtgraph, removing parent does not appropriately remove child items?
                plot.vb.removeItem(item._textLabelItem)
                # now we can safely remove the parent region item
                plot.vb.removeItem(item)
                item.deleteLater()
    
    def _update_active_regions(self) -> None:
        regions = self.active_regions()

        # add/remove regions based on group selections
        region_group_checkboxes = [action.defaultWidget() for action in self._region_group_actions()]
        for checkbox in region_group_checkboxes:
            group = checkbox.text()
            if checkbox.checkState() == Qt.CheckState.Checked:
                # add all regions in this group
                for region in self.regions:
                    if (region.get('group', self.UNGROUPED) == group) and (region not in regions):
                        regions.append(region)
            elif checkbox.checkState() == Qt.CheckState.Unchecked:
                # remove all regions in this group
                regions = [region for region in regions if region.get('group', self.UNGROUPED) != group]
            elif checkbox.checkState() == Qt.CheckState.PartiallyChecked:
                pass
        
        # reset plot regions to new active regions
        self._clear_region_plot_items()
        for region in regions:
            self._add_region_to_plots(region)
        
        # update check state of region groups to reflect active regions
        # self._update_regions_menu()

    def region_groups(self) -> list[str]:
        try:
            return np.unique([
                region.get('group', self.UNGROUPED)
                for region in self.regions
            ]).tolist()
        except KeyError:
            return []
    
    def selected_region_groups(self) -> list[str]:
        return [
            action.defaultWidget().text() 
            for action in self._region_group_actions() 
            if action.defaultWidget().isChecked()
        ]
    
    def set_selected_region_groups(self, groups: list[str]) -> None:
        for action in self._region_group_actions():
            action.defaultWidget().setChecked(action.defaultWidget().text() in groups)
        self._update_active_regions()

    def _region_group_actions(self) -> list[QWidgetAction]:
        try:
            actions = self._regions_button_menu.actions()
            before = actions.index(self._before_region_group_actions)
            after = actions.index(self._after_region_group_actions)
            return actions[before+1:after]
        except IndexError:
            return []

    def _update_region_groups_menu(self) -> None:
        region_groups = self.region_groups()
        old_actions = self._region_group_actions()
        
        # remove old actions
        for action in old_actions:
            self._regions_button_menu.removeAction(action)
        
        # insert new actions
        active_regions = self.active_regions()
        new_actions = []
        for group in region_groups:
            checkbox = QCheckBox(group)
            checkbox.setTristate(False)
            regions_in_group = [region for region in self.regions if region.get('group', self.UNGROUPED) == group]
            active_regions_in_group = [region for region in active_regions if region.get('group', self.UNGROUPED) == group]
            has_region = [region in active_regions_in_group for region in regions_in_group]
            if np.all(has_region):
                checkbox.setChecked(True)
            elif np.any(has_region):
                checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
                # this converts checkbox to on/off (no tristate) when clicked
                checkbox.stateChanged.connect(lambda state, cbox=checkbox: cbox.setChecked(cbox.isChecked()))
            else:
                checkbox.setChecked(False)
            checkbox.stateChanged.connect(lambda state: self.replot())
            action = QWidgetAction(self)
            action.setDefaultWidget(checkbox)
            new_actions.append(action)
        self._regions_button_menu.insertActions(self._after_region_group_actions, new_actions)

        self._regions_button.setEnabled(len(region_groups) > 0)
    
    def start_drawing_regions(self) -> None:
        # self._draw_region_action.setChecked(True)
        for plot in self._plots():
            plot.vb.sigItemAdded.connect(self._on_item_added_to_axes)
            plot.vb.startDrawingItemsOfType(pgx.XAxisRegion)
    
    def stop_drawing_regions(self) -> None:
        # self._draw_region_action.setChecked(False)
        for plot in self._plots():
            plot.vb.stopDrawingItems()
            plot.vb.sigItemAdded.disconnect(self._on_item_added_to_axes)
    
    def toggle_drawing_regions(self) -> None:
        if self._draw_region_action.isChecked():
            self.start_drawing_regions()
        else:
            self.stop_drawing_regions()
    
    @Slot(pgx.XAxisRegion)
    def _on_region_plot_item_changed(self, item: pgx.XAxisRegion) -> None:
        view: pgx.View = item.getViewBox()
        # plot: pgx.Plot = view.parentItem()
        region = item.getState()
        group_changed = region.get('group', self.UNGROUPED) != item._region_ref.get('group', self.UNGROUPED)
        
        # update ref dict from plot item
        for key in region:
            item._region_ref[key] = region[key]
        
        # update associated regions in other plots
        for plot in self._plots():
            if plot.vb is view:
                continue
            other_items = [item for item in plot.vb.allChildren() if isinstance(item, pgx.XAxisRegion)]
            for other_item in other_items:
                if other_item._region_ref is item._region_ref:
                    other_item.setState(other_item._region_ref)
                    break
        
        if group_changed:
            self._update_region_groups_menu()
    
    def _on_region_plot_item_drag_finished(self) -> None:
        if self._baseline_action.isChecked():
            # update baseline preview
            self.replot()
    
    @Slot(pgx.XAxisRegion)
    def _on_region_plot_item_deleted(self, item: pgx.XAxisRegion) -> None:
        self.regions.remove(item._region_ref)
        active_regions = self.active_regions()
        active_regions.remove(item._region_ref)
        self.set_active_regions(active_regions)
    
    @Slot(QGraphicsObject)
    def _on_item_added_to_axes(self, item: QGraphicsObject) -> None:
        view: pgx.View = self.sender()
        # plot: pgx.Plot = view.parentItem()
        if isinstance(item, pgx.XAxisRegion):
            # remove item and add to all plots
            region = item.getState()
            view.removeItem(item)
            item.deleteLater()
            self.add_region(region)
            # draw one region at a time
            self.stop_drawing_regions()
            # edit newly added region
            items = self._region_plot_items()
            for item in items:
                if item._region_ref == region:
                    state = pgx.editAxisRegion(item, parent=self)
                    if state is not None:
                        for key, value in state.items():
                            item._region_ref[key] = value
                        self._update_region_groups_menu()
                    break
    
    def show_all_regions(self) -> None:
        regions = self.regions
        for region in self.active_regions():
            if region not in regions:
                regions.append(region)
        self.set_active_regions(regions)
    
    def hide_all_regions(self) -> None:
        self.set_active_regions([])
    
    def toggle_active_regions(self) -> None:
        active_regions = self.active_regions()
        if len(active_regions) == 0:
            # restore previously toggled active regions
            regions = getattr(self, '_active_regions', [])
            self.set_active_regions(regions)
        else:
            # store and hide current active regions
            self._active_regions = active_regions
            self.set_active_regions([])
    
    def group_active_regions(self) -> None:
        active_regions = self.active_regions()
        if len(active_regions) == 0:
            return
        group, ok = QInputDialog.getText(self, 'Group Active Regions', 'Group Name:', text=self.UNGROUPED)
        if not ok:
            return
        for region in active_regions:
            region['group'] = group
        self._update_region_groups_menu()

    def format_active_regions(self) -> None:
        active_regions = self.active_regions()
        if len(active_regions) == 0:
            return
        item = pgx.XAxisRegion()
        found = False
        for plot in self._plots():
            other_items = [item for item in plot.vb.allChildren() if isinstance(item, pgx.XAxisRegion) and item.isVisible()]
            for other_item in other_items:
                if other_item._region_ref in active_regions:
                    item.setFormat(other_item.getFormat())
                    found = True
                    break
            if found:
                break
        fmt = pgx.formatAxisRegion(region=item, parent=self)
        if fmt is None:
            return
        for region in active_regions:
            region['format'] = fmt
        self._update_active_regions()

    def delete_active_regions(self) -> None:
        active_regions = self.active_regions()
        if len(active_regions) == 0:
            return
        ok = QMessageBox.question(
            self, 'Delete Active Regions',
            f'Delete {len(active_regions)} active regions?', 
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        if ok != QMessageBox.StandardButton.Ok:
            return
        self.set_active_regions([])
        self.regions = [region for region in self.regions if region not in active_regions]
    
    # window management
    
    def windows(self) -> list[GOLabChart]:
        windows = []
        for widget in qApp.topLevelWidgets():
            if isinstance(widget, GOLabChart):
                windows.append(widget)
        return windows
    
    def new_window(self) -> GOLabChart:
        window = GOLabChart()
        window.show()
        return window
    
    # i/o
    
    def load(self, filepath: Path | str = None) -> None:
        if filepath is None:
            filepath, _ = QFileDialog.getOpenFileName(self, 'Open File')
            if not filepath:
                return
        if isinstance(filepath, str):
            filepath = Path(filepath)
        if not filepath.exists():
            QMessageBox.warning(self, 'File Not Found', f'File not found: {filepath}')
            return
        
        # read data from file
        if filepath.suffix == '.wcp':
            from golab.io import read_winwcp
            ds: xr.Dataset = read_winwcp(str(filepath))
            dt = xr.DataTree()
            dt['Data'] = ds
        elif filepath.suffix == '.zip':
            # assume file is a zarr zip store
            with zarr.storage.ZipStore(filepath, mode='r') as store:
                dt = xr.open_datatree(store, engine='zarr')
        else:
            dt = xr.open_datatree(filepath)
            # QMessageBox.warning(self, 'Unsupported File', f'Unsupported file extension: {ext}')
            # return
        
        # inherit references to any missing data_vars present in parent nodes
        dt = inherit_missing_data_vars(dt)

        # restore designated order of data_vars
        order_data_vars(dt)

        # update datatree
        self._datatree = dt

        # update UI
        self._datatree_view.selectionWasChanged.disconnect(self.replot)
        self._datatree_view.setDataTree(self.datatree)
        self._datatree_view.expandAll()
        self._datatree_view.setSelectedPaths([node.path for node in self.datatree['Data'].leaves])
        self._datatree_view.selectionWasChanged.connect(self.replot)
        
        self._filepath: Path = filepath
        self.setWindowTitle(filepath.name)

        self.set_active_regions([])
        self._update_sweeps_spinbox()
        self._sweeps_spinner.setIndices([0])
        self.refresh()
    
    def save(self, filepath: Path | str = None) -> None:
        if filepath is None:
            filepath, _ = QFileDialog.getSaveFileName(self, 'Save File')
            if not filepath:
                return
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        # default to zarr zip store
        if filepath.suffix == '':
            filepath = filepath.with_suffix('.zarr.zip')
        elif filepath.suffix == '.zarr':
            filepath = filepath.with_suffix('.zarr.zip')
        
        # uneeded: system already handles this
        # if filepath.exists():
        #     answer = QMessageBox.question(self, 'Overwrite File', f'Overwrite file at {filepath}?')
        #     if answer != QMessageBox.StandardButton.Yes:
        #         return
        
        # remove inherited data referencing parent data
        dt = remove_inherited_data_vars(self.datatree)
        
        # store data_var order
        if 'Data' in dt:
            dt['Data'].attrs['ordered_data_vars'] = list(dt['Data'].data_vars)
        
        # save to file
        if filepath.suffix == '.zip':
            # assume file is a zarr zip store
            with zarr.storage.ZipStore(filepath, mode='w') as store:
                dt.to_zarr(store)
        # elif filepath.suffix == '.h5':
        #     dt.to_netcdf(filepath, engine='h5netcdf')
        # elif filepath.suffix == '.nc':
        #     dt.to_netcdf(filepath, engine='netcdf4')
        else:
            QMessageBox.warning(self, 'Unsupported File Type', f'Unsupported file extension: {filepath.suffix}')
            return
        
        # update UI
        self._filepath: Path = filepath
        self.setWindowTitle(filepath.name)
    
    # data
    
    def _get_sweep_data(self, path: str, channel: str, sweep: int, raw: bool = False) -> tuple[xr.DataArray, xr.DataArray]:
        ds = self.datatree[path].dataset
        x = ds['time']
        y = ds[channel].sel(sweep=sweep)

        if raw:
            return x, y
                    
        if self._live_filter_checkbox.isChecked():
            y = self._apply_filter(x, y)
        
        return x, y
    
    def _apply_filter(self, x: xr.DataArray, y: xr.DataArray) -> xr.DataArray:
        y = y.copy(deep=False) # do NOT copy y.values
        if self._filter_type_combobox.currentText() == 'Gaussian':
            lowpass_cutoff = self._gaussian_filter_lowpass_edit.text().strip()
            if lowpass_cutoff != '':
                lowpass_cutoff = float(lowpass_cutoff) * UREG.Hz
                xunits = x.attrs.get('units', 'second')
                dx = (x.values[1] - x.values[0]) * UREG(xunits)
                lowpass_cycles_per_sample = (lowpass_cutoff * dx).magnitude
                sigma = 1 / (2 * np.pi * lowpass_cycles_per_sample)
                y.values = sp.ndimage.gaussian_filter1d(y.values, sigma)
        return y
    
    def _get_baseline_prediction(self, x: xr.DataArray, y: xr.DataArray, regions: list[dict] = None) -> xr.DataArray:
        mask = self._regions_mask(x, regions)
        result = self._baseline_panel.fit(x.values[mask], y.values[mask])
        if result is None:
            return None
        
        ybaseline = y.copy(deep=False)
        ybaseline.values = self._baseline_panel.predict(x.values, result)
        return ybaseline
    
    def _apply_operation(self, op_name: str, result_name: str):
        paths = self.selected_datatree_paths()
        channels = self.selected_channels()
        sweeps = self.selected_sweeps()

        for path in paths:
            parent: xr.DataTree = self.datatree[path]
            if path.endswith(result_name):
                parent = parent.parent
            if result_name not in parent:
                parent[result_name] = parent.to_dataset().reset_coords(drop=True)
            
            result: xr.DataTree = parent[result_name]
            
            # x = result['time']
            # regions = self.active_regions()
            # mask = self._regions_mask(x, regions)
            
            for channel in channels:
                if result[channel].values is parent[channel].values:
                    result[channel].values = parent[channel].values.copy()
                
                for sweep in sweeps:
                    x, y = self._get_sweep_data(path, channel, sweep)

                    if op_name == 'subtract baseline':
                        ybaseline = self._get_baseline_prediction(x, y)
                        if ybaseline is not None:
                            result[channel].loc[{'sweep': sweep}] -= ybaseline.values
                    
                    elif op_name == 'filter':
                        if not self._live_filter_checkbox.isChecked():
                            y.values = self._apply_filter(x, y).values
                        result[channel].loc[{'sweep': sweep}] = y.values
        
        # stop live filter if filter was applied
        if op_name == 'filter':
            self._live_filter_checkbox.setChecked(False)
        
        # select result nodes
        for i, path in enumerate(paths):
            if not path.endswith(result_name):
                paths[i] += f'/{result_name}'
        
        self.refresh()
        self._datatree_view.expandAll()
        self.set_selected_datatree_paths(paths)
        self._datatree_action.setChecked(True) # popup datatree panel
        self.refresh()

    # UI
    
    def refresh(self) -> None:
        self._datatree_view.setDataTree(self.datatree)
        self._update_control_panel()
        self._console.setVisible(self._console_action.isChecked())
        self._update_channels_menu()
        self._update_sweeps_spinbox()
        self._update_region_groups_menu()
        self.replot()

        # ensure grid layout is applied after plots are drawn
        QTimer.singleShot(30, self._apply_regular_layout_to_plot_grids)
    
    def replot(self) -> None:
        self._update_plot_grids()
        self._update_sweeps_label()

        # clear plots
        for plot in self._plots():
            traces = [item for item in plot.listDataItems() if isinstance(item, pgx.Graph)]
            for trace in traces:
                plot.removeItem(trace)
                trace.deleteLater()

        paths = self.selected_datatree_paths()
        channels = self.selected_channels()
        sweeps = self.selected_sweeps()
        channel_plot_grids = [self._channel_splitter.widget(i) for i in range(self._channel_splitter.count())]
        tile_sweeps = \
            'vertical' if self._tile_sweeps_vertically_action.isChecked() \
            else 'horizontal' if self._tile_sweeps_horizontally_action.isChecked() \
            else None
        n_total_sweeps = len(self.sweeps())
        xoffset = float(self._sweep_xoffset_edit.text())
        yoffset = float(self._sweep_yoffset_edit.text())
        for i, path in enumerate(paths):
            ds = self.datatree[path].dataset
            for channel, grid in zip(channels, channel_plot_grids):
                if channel not in ds:
                    continue
                for j, sweep in enumerate(sweeps):
                    if tile_sweeps == 'vertical':
                        plot = grid.getItem(j, 0)
                    elif tile_sweeps == 'horizontal':
                        plot = grid.getItem(0, j)
                    else:
                        plot = grid.getItem(0, 0)
                    
                    # sweep
                    x, y = self._get_sweep_data(path, channel, sweep)
                    
                    # preview operation?
                    ypreview: xr.DataArray = None
                    if self._baseline_action.isChecked():
                        ypreview = self._get_baseline_prediction(x, y)
                        if ypreview is not None:
                            if self._preview_baseline_correction_checkbox.isChecked():
                                y.values = y.values - ypreview.values
                                ypreview.values[:] = 0
                    
                    if tile_sweeps is None:
                        if xoffset:
                            x.values = x.values + j * xoffset
                        if yoffset:
                            y.values = y.values + j * yoffset
                            if ypreview is not None:
                                ypreview.values = ypreview.values + j * yoffset
                    
                    trace = pgx.Graph(x.values, y.values)
                    trace._info = {
                        'path': path,
                        'channel': channel,
                        'sweep': sweep,
                    }

                    if tile_sweeps is None:
                        if xoffset:
                            trace._info['xoffset'] = j * xoffset
                        if yoffset:
                            trace._info['yoffset'] = j * yoffset
                    
                    trace.setZValue(1)
                    
                    name = f'{channel}'
                    if len(paths) > 1:
                        name = f'{path} {name}'
                    if n_total_sweeps > 1:
                        name = f'{name}[{sweep}]'
                    trace.setName(name)

                    status = self.sweep_status(sweep)
                    is_masked = status == self.MASKED
                    if is_masked:
                        trace.setPen(pg.mkPen((200, 200, 200)))
                    else:
                        trace.setPen(pg.mkPen(plot.vb.colormap()[i % len(plot.vb.colormap())]))
                    
                    trace.contextMenu.addSeparator()
                    action = QAction(parent=self, text=f'Mask Sweep', checkable=True, checked=is_masked)
                    if is_masked:
                        action.triggered.connect(lambda checked, sweep=sweep: self.unmask_sweeps(sweep))
                    else:
                        action.triggered.connect(lambda checked, sweep=sweep: self.mask_sweeps(sweep))
                    trace.contextMenu.addAction(action)

                    plot.addItem(trace)

                    if ypreview is not None:
                        preview_trace = pgx.Graph(x.values, ypreview.values)
                        preview_trace.setZValue(2)
                        preview_trace.setPen(pg.mkPen((255, 0, 0), width=2))
                        plot.addItem(preview_trace)
        
        self._update_active_regions()
    
    def _update_plot_grids(self) -> None:
        # one plot grid per channel
        channels = self.selected_channels()
        n_channels = len(channels)
        while self._channel_splitter.count() < n_channels:
            grid = pgx.PlotGrid()
            grid.setHasRegularLayout(True)
            self._channel_splitter.addWidget(grid)
        while self._channel_splitter.count() > n_channels:
            widget = self._channel_splitter.widget(self._channel_splitter.count()-1)
            widget.setParent(None)
            widget.deleteLater()
        if n_channels == 0:
            return
        
        # plot grids (for tiling sweeps)
        sweeps = self.selected_sweeps()
        n_sweeps = len(sweeps)
        tile_sweeps = \
            'vertical' if self._tile_sweeps_vertically_action.isChecked() \
            else 'horizontal' if self._tile_sweeps_horizontally_action.isChecked() \
            else None
        channel_plot_grids = [self._channel_splitter.widget(i) for i in range(n_channels)]
        for channel, grid in zip(channels, channel_plot_grids):
            # grid size
            if tile_sweeps == 'vertical':
                grid.setGrid(n_sweeps, 1)
                last_row = n_sweeps - 1
                grid.setAxisLabelAndTickVisibility(xlabel_rows=[last_row], xtick_rows=[last_row])
            elif tile_sweeps == 'horizontal':
                grid.setGrid(1, n_sweeps)
                grid.setAxisLabelAndTickVisibility(ylabel_columns=[0], ytick_columns=[0])
            else:
                grid.setGrid(1, 1)
                grid.setAxisLabelAndTickVisibility()
            
            # axis labels and linking
            try:
                xunits = self.datatree['Data/time'].attrs['units']
            except KeyError:
                xunits = None
            try:
                yunits = self.datatree[f'Data/{channel}'].attrs['units']
            except KeyError:
                yunits = None
            for row in range(grid.rowCount()):
                for col in range(grid.columnCount()):
                    plot = grid.getItem(row, col)
                    if row == grid.rowCount() - 1:
                        plot.setLabel('bottom', 'time', units=xunits)
                    if col == 0:
                        if (tile_sweeps == 'vertical') or ((n_sweeps == 1) and len(self.sweeps()) > 1):
                            sweep = sweeps[row]
                            plot.setLabel('left', f'{channel}[{sweep}]', units=yunits)
                        else:
                            plot.setLabel('left', channel, units=yunits)
                    if row == col == 0:
                        if channel != channels[0]:
                            plot.setXLink(channel_plot_grids[0].getItem(0, 0))
                    else:
                        plot.setXLink(grid.getItem(0, 0))
                        if tile_sweeps == 'vertical':
                            # TODO: allow setting ylink for vertical tiles too (based on setting)
                            pass
                        elif tile_sweeps == 'horizontal':
                            plot.setYLink(grid.getItem(0, 0))
    
    def _update_sweeps_label(self, sweeps: np.ndarray = None) -> None:
        if sweeps is None:
            sweeps = self.selected_sweeps()
        n_sweeps = len(sweeps)
        n_total_sweeps = len(self.sweeps())
        n_selectable_sweeps = len(self._selectable_sweeps())
        label = f'({n_sweeps}/{n_selectable_sweeps})'
        if n_total_sweeps > n_selectable_sweeps:
            label += f' of {n_total_sweeps}'
        self._sweeps_label.setText(label + ':')
    
    def _apply_regular_layout_to_plot_grids(self) -> None:
        for i in range(self._channel_splitter.count()):
            grid = self._channel_splitter.widget(i)
            if grid.hasRegularLayout():
                grid.applyRegularLayout()
    
    def _plots(self) -> list[pgx.Plot]:
        plots = []
        for i in range(self._channel_splitter.count()):
            grid = self._channel_splitter.widget(i)
            for row in range(grid.rowCount()):
                for col in range(grid.columnCount()):
                    plot = grid.getItem(row, col)
                    plots.append(plot)
        return plots
    
    def pile_sweeps(self):
        self._default_select_multiple_sweeps()
        self.tile_sweeps(None)
    
    def tile_sweeps(self, orientation: Qt.Orientation | None):
        if orientation is None:
            self._pile_sweeps_action.setChecked(True)
            self._tile_sweeps_button.setIcon(self._pile_sweeps_action.icon())
        elif orientation == Qt.Orientation.Vertical:
            self._default_select_multiple_sweeps()
            self._tile_sweeps_vertically_action.setChecked(True)
            self._tile_sweeps_button.setIcon(self._tile_sweeps_vertically_action.icon())
        elif orientation == Qt.Orientation.Horizontal:
            self._default_select_multiple_sweeps()
            self._tile_sweeps_horizontally_action.setChecked(True)
            self._tile_sweeps_button.setIcon(self._tile_sweeps_horizontally_action.icon())
        self.replot()

        # ensure grid layout is applied after plots are drawn
        QTimer.singleShot(30, self._apply_regular_layout_to_plot_grids)
    
    def _default_select_multiple_sweeps(self, max_sweeps=10):
        selected_sweeps = self.selected_sweeps()
        if len(selected_sweeps) > 1:
            # keep current multiple selection
            return
        # select up to max_sweeps
        selectable_sweeps = self._selectable_sweeps()
        if len(selectable_sweeps) <= max_sweeps:
            selected_sweeps = selectable_sweeps
        elif len(selected_sweeps) == 0:
            selected_sweeps = selectable_sweeps[:max_sweeps]
        else:
            i = np.where(selectable_sweeps == selected_sweeps[0])[0][0]
            stop = min(i + max_sweeps, len(selectable_sweeps))
            start = max(0, stop - max_sweeps)
            selected_sweeps = selectable_sweeps[start:stop]
        self.set_selected_sweeps(selected_sweeps)
    
    def autoscale(self, plots: list[pgx.Plot] = None) -> None:
        if plots is None:
            plots = self._plots()
        
        xlinked_views = []
        ylinked_views = []
        xlinked_range = []
        ylinked_range = []
        for plot in plots:
            view = plot.getViewBox()
            xlinked_view = view.linkedView(view.XAxis)
            ylinked_view = view.linkedView(view.YAxis)
            if (xlinked_view is None) and (ylinked_view is None):
                view.enableAutoRange()
            if xlinked_view is not None:
                view.enableAutoRange(axis=view.YAxis)
                xlim, ylim = view.childrenBounds()
                xlinked_range.append(xlim)
                if xlinked_view not in xlinked_views:
                    xlinked_views.append(xlinked_view)
                    xlim, ylim = xlinked_view.childrenBounds()
                    xlinked_range.append(xlim)
            if ylinked_view is not None:
                view.enableAutoRange(axis=view.XAxis)
                xlim, ylim = view.childrenBounds()
                ylinked_range.append(ylim)
                if ylinked_view not in ylinked_views:
                    ylinked_views.append(ylinked_view)
                    xlim, ylim = ylinked_view.childrenBounds()
                    ylinked_range.append(ylim)
            view.updateAutoRange()
        
        if xlinked_views:
            xmin = np.min(xlinked_range)
            xmax = np.max(xlinked_range)
            for view in xlinked_views:
                view.setXRange(xmin, xmax)
        if ylinked_views:
            ymin = np.min(ylinked_range)
            ymax = np.max(ylinked_range)
            for view in ylinked_views:
                view.setYRange(ymin, ymax)
    
    def sizeHint(self) -> QSize:
        return QSize(1000, 800)
    
    def _init_ui(self) -> None:
        self._init_console()
        self._init_menubar()
        self._init_top_toolbar()
        self._init_left_toolbar()
        self._init_control_panels()
        self._channel_splitter = QSplitter(Qt.Orientation.Vertical)

        w, h = self.sizeHint().width(), self.sizeHint().height()
        self._main_vsplitter = QSplitter(Qt.Orientation.Vertical)
        self._main_vsplitter.addWidget(self._channel_splitter)
        self._main_vsplitter.addWidget(self._console)
        self._main_vsplitter.setSizes([h-250, 250])

        self._main_hsplitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_hsplitter.addWidget(self._control_panels_stack)
        self._main_hsplitter.addWidget(self._main_vsplitter)
        self._main_hsplitter.setSizes([250, w-250])

        self.setCentralWidget(self._main_hsplitter)

        self.refresh()

        # self._key_press_event_filter = IgnoreLettersKeyPressFilter()
        # self.installEventFilter(self._key_press_event_filter)
    
    def _init_console(self) -> None:
        from qtconsole.rich_jupyter_widget import RichJupyterWidget
        from qtconsole.inprocess import QtInProcessKernelManager

        self._console_kernel_manager = QtInProcessKernelManager()
        self._console_kernel_manager.start_kernel(show_banner=False)

        self._console_kernel_client = self._console_kernel_manager.client()
        self._console_kernel_client.start_channels()

        self._console = RichJupyterWidget()
        self._console.kernel_manager = self._console_kernel_manager
        self._console.kernel_client = self._console_kernel_client

        self._console_kernel_manager.kernel.shell.push({'self': self})

        self._console.execute('import numpy as np', hidden=True)
        self._console.execute('import pandas as pd', hidden=True)
        self._console.execute('import scipy as sp', hidden=True)
        self._console.execute('import xarray as xr', hidden=True)
        self._console.execute('self', hidden=False)
        self._console.execute('dt = self.datatree', hidden=False)
        self._console.execute('dt', hidden=False)
        self._console._set_input_buffer('') # seems silly to have to call this?

        self._console.executed.connect(self.refresh)
    
    def _shutdown_console(self) -> None:
        self._console_kernel_client.stop_channels()
        self._console_kernel_manager.shutdown_kernel()
        self._console.deleteLater()
    
    def _init_menubar(self) -> None:
        menubar = self.menuBar()

        self._file_menu = menubar.addMenu("File")
        self._file_menu.addAction('New Window', QKeySequence.StandardKey.New, self.new_window)
        self._file_menu.addSeparator()
        self._file_menu.addAction(qta.icon('fa5.folder-open'), 'Open', QKeySequence.StandardKey.Open, self.load)
        # self._import_menu = self._file_menu.addMenu('Import')
        self._file_menu.addSeparator()
        self._file_menu.addAction(qta.icon('fa5.save'), 'Save', QKeySequence.StandardKey.Save, lambda self = self: self.save(self._filepath.with_suffix('.zarr.zip')))
        self._file_menu.addAction(qta.icon('fa5.save'), 'Save As', QKeySequence.StandardKey.SaveAs, self.save)
        self._file_menu.addSeparator()
        self._file_menu.addAction('Close Window', QKeySequence.StandardKey.Close, self.close)
        self._file_menu.addSeparator()
        self._file_menu.addAction('Quit', QKeySequence.StandardKey.Quit, qApp.quit)

        # self._import_menu.addAction('Zarr zip store (.zip)')
        # self._import_menu.addSeparator()
        # self._import_menu.addAction('WinWCP (.wcp)')
        # self._import_menu.addSeparator()
        # self._import_menu.addAction('LabChart GOLab conversion (.mat)')
        # self._import_menu.addSeparator()
        # self._import_menu.addAction('HEKA (.dat)')
        # self._import_menu.addSeparator()
        # self._import_menu.addAction('Axon (.abf)')

        self._channels_menu = menubar.addMenu("Channels")
        self._channels_menu.addAction('Rename Channels', self.rename_channels)

        self._sweeps_menu = menubar.addMenu("Sweeps")
        self._sweeps_menu.addAction('Mask Selected Sweeps', QKeySequence("M"), self.mask_selected_sweeps)
        self._sweeps_menu.addAction('Unmask Selected Sweeps', QKeySequence("U"), self.unmask_selected_sweeps)

        self._regions_menu = menubar.addMenu("Regions")
        self._regions_menu.addAction('Draw New Region', QKeySequence("R"), self.start_drawing_regions)
        self._regions_menu.addSeparator()
        self._regions_menu.addAction('Show All Regions', self.show_all_regions)
        self._regions_menu.addAction('Hide All Regions', self.hide_all_regions)
        self._regions_menu.addAction('Toggle Region Visibility', QKeySequence("T"), self.toggle_active_regions)
        self._regions_menu.addSeparator()
        self._regions_menu.addAction('Group Active Regions', QKeySequence("G"), self.group_active_regions)
        self._regions_menu.addAction('Format Active Regions', self.format_active_regions)
        self._regions_menu.addAction('Delete Active Regions', self.delete_active_regions)

        self._detrend_menu = menubar.addMenu("Detrend")
        self._detrend_menu.addAction('Linear Two Peaks Rundown')
        self._detrend_menu.addAction('Baseline Rundown')
    
    def _init_top_toolbar(self) -> None:
        self._top_toolbar = QToolBar()
        self._top_toolbar.setOrientation(Qt.Orientation.Horizontal)
        self._top_toolbar.setStyleSheet("QToolBar{spacing:2px;}")
        self._top_toolbar.setIconSize(QSize(24, 24))
        self._top_toolbar.setMovable(False)
        self._top_toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._top_toolbar)

        # channels
        self._channels_button = QToolButton(
            icon=qta.icon('fa6s.sliders'),
            text='Channels',
            toolTip='Channels',
            popupMode=QToolButton.ToolButtonPopupMode.InstantPopup)
        self._channels_button_menu = QMenu()
        self._channels_button.setMenu(self._channels_button_menu)

        self._before_channel_actions = self._channels_button_menu.addSeparator()
        self._after_channel_actions = self._channels_button_menu.addSeparator()

        # sweeps
        self._pile_sweeps_action = QAction(
            parent = self, 
            icon = qta.icon('ph.stack'), 
            text = 'Pile Sweeps', 
            iconVisibleInMenu = True, 
            checkable = True, 
            checked = True,
            triggered = self.pile_sweeps,
        )
        self._tile_sweeps_vertically_action = QAction(
            parent = self, 
            icon = qta.icon('mdi.reorder-horizontal'), 
            text = 'Tile Sweeps Vertically', 
            iconVisibleInMenu = True, 
            checkable = True, 
            checked = False,
            triggered = lambda: self.tile_sweeps(Qt.Orientation.Vertical),
        )
        self._tile_sweeps_horizontally_action = QAction(
            parent = self, 
            icon = qta.icon('mdi.reorder-vertical'), 
            text = 'Tile Sweeps Horizontally', 
            iconVisibleInMenu = True, 
            checkable = True, 
            checked = False,
            triggered = lambda: self.tile_sweeps(Qt.Orientation.Horizontal),
        )

        self._tile_sweeps_button = QToolButton(
            icon=self._pile_sweeps_action.icon(),
            text='Tile Sweeps',
            toolTip='Tile Sweeps',
            popupMode=QToolButton.ToolButtonPopupMode.InstantPopup)
        self._tile_sweeps_button_menu = QMenu()
        self._tile_sweeps_button.setMenu(self._tile_sweeps_button_menu)

        self._tile_sweeps_button_menu.addAction(self._pile_sweeps_action)
        self._tile_sweeps_button_menu.addAction(self._tile_sweeps_vertically_action)
        self._tile_sweeps_button_menu.addAction(self._tile_sweeps_horizontally_action)

        self._tile_sweeps_action_group = QActionGroup(self._tile_sweeps_button_menu)
        self._tile_sweeps_action_group.addAction(self._pile_sweeps_action)
        self._tile_sweeps_action_group.addAction(self._tile_sweeps_vertically_action)
        self._tile_sweeps_action_group.addAction(self._tile_sweeps_horizontally_action)
        self._tile_sweeps_action_group.setExclusive(True)

        self._sweeps_label = QLabel('(0/0) Sweeps:')
        self._sweeps_label.setToolTip('(# Selected / # Unmasked) of # Sweeps')
        self._sweeps_label.setContentsMargins(5, 0, 5, 0)
        
        self._sweeps_spinner = MultiValueSpinBox()
        self._sweeps_spinner.setToolTip('Sweeps: 1, 2:5, ...')
        self._sweeps_spinner.indicesChanged.connect(lambda: self.replot())
        self._sweeps_spinner_event_filter = IgnoreLettersKeyPressFilter()
        self._sweeps_spinner.installEventFilter(self._sweeps_spinner_event_filter)

        # regions
        self._regions_button = QToolButton(
            icon=qta.icon('mdi.arrow-expand-horizontal'),
            text='Regions',
            toolTip='Regions',
            popupMode=QToolButton.ToolButtonPopupMode.InstantPopup)
        self._regions_button_menu = QMenu()
        self._regions_button.setMenu(self._regions_button_menu)

        self._before_region_group_actions = self._regions_button_menu.addSeparator()
        self._after_region_group_actions = self._regions_button_menu.addSeparator()

        # far right
        hspacer = QWidget()
        hspacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._home_action = QAction(
            parent = self, 
            icon = qta.icon('mdi.home'), 
            iconVisibleInMenu = True,
            text = 'Autoscale', 
            toolTip = 'Autoscale',
            triggered = lambda: self.autoscale())

        self._top_toolbar.addWidget(self._channels_button)
        self._top_toolbar.addSeparator()
        self._top_toolbar.addWidget(self._tile_sweeps_button)
        self._sweeps_label_action = self._top_toolbar.addWidget(self._sweeps_label)
        self._sweeps_spinner_action = self._top_toolbar.addWidget(self._sweeps_spinner)
        self._top_toolbar.addSeparator()
        self._top_toolbar.addWidget(self._regions_button)
        self._top_toolbar.addSeparator()
        self._top_toolbar.addWidget(hspacer)
        self._top_toolbar.addAction(self._home_action)

        # self._top_toolbar_key_press_event_filter = IgnoreLettersKeyPressFilter()
        # self._top_toolbar.installEventFilter(self._top_toolbar_key_press_event_filter)

    def _init_left_toolbar(self) -> None:
        self._left_toolbar = QToolBar()
        self._left_toolbar.setOrientation(Qt.Orientation.Vertical)
        self._left_toolbar.setStyleSheet("QToolBar{spacing:2px;}")
        self._left_toolbar.setIconSize(QSize(24, 24))
        self._left_toolbar.setMovable(False)
        self._left_toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self._left_toolbar)

        self._datatree_action = QAction(
            parent=self, 
            icon=qta.icon('mdi.file-tree'), 
            iconVisibleInMenu=True,
            text='Data Tree',
            toolTip='Data Tree',
            checkable=True, 
            checked=True)
        self._datatree_action.triggered.connect(lambda checked: self.refresh())

        self._baseline_action = QAction(
            parent=self, 
            icon=qta.icon('ri.align-bottom'), 
            iconVisibleInMenu=True,
            text='Baseline Correction', 
            toolTip='Baseline Correction', 
            checkable=True, 
            checked=False)
        self._baseline_action.triggered.connect(lambda checked: self.refresh())

        self._filter_action = QAction(
            parent=self, 
            icon=qta.icon('mdi.waveform'), 
            iconVisibleInMenu=True,
            text='Filter', 
            toolTip='Filter', 
            checkable=True, 
            checked=False)
        self._filter_action.triggered.connect(lambda checked: self.refresh())

        self._metadata_action = QAction(
            parent=self, 
            icon=qta.icon('mdi6.text-box-edit-outline'), 
            iconVisibleInMenu=True,
            text='Metadata & Notes', 
            toolTip='Metadata & Notes', 
            checkable=True, 
            checked=False)
        self._metadata_action.triggered.connect(lambda checked: self.refresh())

        self._settings_action = QAction(
            parent=self, 
            icon=qta.icon('mdi.cog-outline'), 
            iconVisibleInMenu=True,
            text='Settings', 
            toolTip='Settings', 
            checkable=True, 
            checked=False)
        self._settings_action.triggered.connect(lambda checked: self.refresh())

        self._console_action = QAction(
            parent=self, 
            icon=qta.icon('mdi.console'), 
            iconVisibleInMenu=True,
            text='Console', 
            toolTip='Console', 
            checkable=True, 
            checked=False)
        self._console_action.triggered.connect(lambda checked: self._console.setVisible(checked))

        vspacer = QWidget()
        vspacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self._left_toolbar.addAction(self._datatree_action)
        self._left_toolbar.addAction(self._baseline_action)
        self._left_toolbar.addAction(self._filter_action)
        self._left_toolbar.addAction(self._metadata_action)
        self._left_toolbar.addAction(self._settings_action)
        self._left_toolbar.addWidget(vspacer)
        self._left_toolbar.addAction(self._console_action)

        self._control_panel_action_group = QActionGroup(self._left_toolbar)
        self._control_panel_action_group.addAction(self._datatree_action)
        self._control_panel_action_group.addAction(self._baseline_action)
        self._control_panel_action_group.addAction(self._filter_action)
        self._control_panel_action_group.addAction(self._metadata_action)
        self._control_panel_action_group.addAction(self._settings_action)
        self._control_panel_action_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
    
    def _init_control_panels(self) -> None:
        self._control_panels_stack = QStackedWidget()

        self._init_datatree_panel()
        self._init_baseline_panel()
        self._init_filter_panel()
        self._init_metadata_panel()
        self._init_settings_panel()
    
    def _init_datatree_panel(self) -> None:
        self._datatree_viewer = XarrayTreeViewer()
        self._datatree_view = self._datatree_viewer.view()
        self._datatree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._datatree_view.setAlternatingRowColors(False)
        self._datatree_view.setVariablesVisible(False)
        self._datatree_view.setCoordinatesVisible(False)
        self._datatree_model: XarrayTreeModel = XarrayTreeModel(dt=self.datatree)
        self._datatree_model.setDetailsColumnVisible(False)
        self._datatree_view.setModel(self._datatree_model)
        self._datatree_view.expandAll()
        self._datatree_view.selectionWasChanged.connect(self.replot)
        self._datatree_viewer.setSizes([400, 200])

        # on attr changes
        self._datatree_view.sigFinishedEditingAttrs.connect(self.replot)
        attrs_model: KeyValueTreeModel = self._datatree_viewer._attrs_view.model()
        attrs_model.sigValueChanged.connect(self.replot)

        self._control_panels_stack.addWidget(self._datatree_viewer)
    
    def _init_baseline_panel(self) -> None:
        self._baseline_panel = pgx.CurveFitControlPanel()
        self._baseline_panel._fitTypeComboBox.setCurrentIndex(0)
        self._baseline_panel.paramsChanged.connect(self.replot)

        self._preview_baseline_correction_checkbox = QCheckBox('Preview Baseline Correction', checked=False)
        self._preview_baseline_correction_checkbox.setToolTip('Preview baseline correction without applying it.')
        self._preview_baseline_correction_checkbox.stateChanged.connect(lambda state: self.replot())

        self._apply_baseline_correction_button = QPushButton('Apply Baseline Correction')
        self._apply_baseline_correction_button.pressed.connect(lambda: self._apply_operation('subtract baseline', 'Baselined'))
        
        vbox: QVBoxLayout = self._baseline_panel.layout()
        vbox.setSpacing(10)
        vbox.insertWidget(0, QLabel('Baseline model:'))
        vbox.insertWidget(vbox.count() - 1, self._preview_baseline_correction_checkbox)
        vbox.insertWidget(vbox.count() - 1, self._apply_baseline_correction_button)

        self._control_panels_stack.addWidget(self._baseline_panel)
    
    def _init_filter_panel(self) -> None:
        self._filter_type_combobox = QComboBox()
        self._filter_type_combobox.addItems(['Gaussian'])
        self._filter_type_combobox.setCurrentText('Gaussian')
        self._filter_type_combobox.currentIndexChanged.connect(lambda index: self.replot())

        self._gaussian_filter_lowpass_edit = QLineEdit('1000')
        self._gaussian_filter_lowpass_edit.editingFinished.connect(self.replot)

        self._gaussian_filter_groupbox = QGroupBox()
        form = QFormLayout(self._gaussian_filter_groupbox)
        form.setContentsMargins(3, 3, 3, 3)
        form.setSpacing(3)
        form.setHorizontalSpacing(5)
        form.addRow('Lowpass (Hz)', self._gaussian_filter_lowpass_edit)

        self._live_filter_checkbox = QCheckBox('Live Filter', checked=False)
        self._live_filter_checkbox.setToolTip('Apply filter without altering underlying data.')
        self._live_filter_checkbox.stateChanged.connect(lambda state: self.replot())

        self._apply_filter_button = QPushButton('Apply Filter')
        self._apply_filter_button.pressed.connect(lambda: self._apply_operation('filter', 'Filtered'))
        
        self._filter_panel = QWidget()
        self._filter_panel.setWindowTitle('Filter')
        vbox = QVBoxLayout(self._filter_panel)
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.setSpacing(10)
        vbox.addWidget(QLabel('Filter:'))
        vbox.addWidget(self._filter_type_combobox)
        vbox.addWidget(self._gaussian_filter_groupbox)
        vbox.addWidget(self._live_filter_checkbox)
        vbox.addWidget(self._apply_filter_button)
        vbox.addStretch()

        self._control_panels_stack.addWidget(self._filter_panel)

        # self._filter_panel_scroll_area = QScrollArea()
        # self._settings_panel_filter_panel_scroll_area_scroll_area.setWidgetResizable(True)
        # self._filter_panel_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # self._filter_panel_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # self._filter_panel_scroll_area.setWidget(self._filter_panel)

        # self._control_panels_stack.addWidget(self._filter_panel_scroll_area)
    
    def _init_metadata_panel(self) -> None:
        self._date_edit = QLineEdit(datetime.date.today().strftime("%Y-%m-%d"))
        self._date_edit.setPlaceholderText('YYYY-MM-DD')
        self._date_edit.editingFinished.connect(lambda: self.metadata.update({'date', self._date_edit.text()}))

        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText('Jane Doe')
        self._user_edit.editingFinished.connect(lambda: self.metadata.update({'user', self._user_edit.text()}))

        self._construct_edit = QLineEdit()
        self._construct_edit.setPlaceholderText('human GABA-A a1(L264T) b2S g2')
        self._construct_edit.editingFinished.connect(lambda: self.metadata.update({'construct', self._construct_edit.text()}))
        
        self._notes_edit = QTextEdit()
        self._notes_edit.setToolTip('Notes')
        self._notes_edit.textChanged.connect(lambda: self.metadata.update({'notes', self._notes_edit.toPlainText()}))

        self._metadata_panel = QWidget()
        self._metadata_panel.setWindowTitle('Metadata')
        form = QFormLayout(self._metadata_panel)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)
        form.setHorizontalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.addRow('Date', self._date_edit)
        form.addRow('User', self._user_edit)
        form.addRow('Construct', self._construct_edit)
        form.addRow(self._notes_edit)

        self._control_panels_stack.addWidget(self._metadata_panel)
    
    def _init_settings_panel(self) -> None:
        self._include_masked_sweeps_checkbox = QCheckBox('Include Masked Sweeps', checked=False)
        self._include_masked_sweeps_checkbox.stateChanged.connect(lambda state: self.refresh())

        self._sweep_xoffset_edit = QLineEdit()
        self._sweep_xoffset_edit.setToolTip('Sweep X Offset\n!!! In data units, not necessarily displayed units')
        self._sweep_xoffset_edit.setText('0')
        self._sweep_xoffset_edit.editingFinished.connect(lambda: self.replot())
        sweep_xoffset_label = QLabel('Sweep X Offset')
        sweep_xoffset_label.setToolTip(self._sweep_xoffset_edit.toolTip())

        self._sweep_yoffset_edit = QLineEdit()
        self._sweep_yoffset_edit.setToolTip('Sweep Y Offset\n!!! In data units, not necessarily displayed units')
        self._sweep_yoffset_edit.setText('0')
        self._sweep_yoffset_edit.editingFinished.connect(lambda: self.replot())
        sweep_yoffset_label = QLabel('Sweep Y Offset')
        sweep_yoffset_label.setToolTip(self._sweep_yoffset_edit.toolTip())
        
        self._settings_panel = QWidget()
        self._settings_panel.setWindowTitle('Settings')
        form = QFormLayout(self._settings_panel)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)
        form.setHorizontalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        # separator = QFrame()
        # separator.setFrameShape(QFrame.HLine)
        # separator.setFrameShadow(QFrame.Sunken)
        # form.addRow(separator)
        form.addRow(self._include_masked_sweeps_checkbox)
        form.addRow(sweep_xoffset_label, self._sweep_xoffset_edit)
        form.addRow(sweep_yoffset_label, self._sweep_yoffset_edit)

        self._control_panels_stack.addWidget(self._settings_panel)

        # self._settings_panel_scroll_area = QScrollArea()
        # self._settings_panel_scroll_area.setWidgetResizable(True)
        # self._settings_panel_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # self._settings_panel_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # self._settings_panel_scroll_area.setWidget(self._settings_panel)

        # self._control_panels_stack.addWidget(self._settings_panel_scroll_area)
    
    def _update_control_panel(self) -> None:
        objs = [
            (self._datatree_action, self._datatree_viewer),
            (self._baseline_action, self._baseline_panel),
            (self._filter_action, self._filter_panel),
            (self._metadata_action, self._metadata_panel),
            (self._settings_action, self._settings_panel),
        ]
        for obj in objs:
            action, widget = obj
            if action.isChecked():
                self._control_panels_stack.setCurrentWidget(widget)
                self._control_panels_stack.setVisible(True)
                return
        self._control_panels_stack.setVisible(False)


class IgnoreLettersKeyPressFilter(QObject):

    def eventFilter(self, object, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.text().isalpha():
                # Do not handle letters A-Z
                return True
        return False


def remove_inherited_data_vars(dt: xr.DataTree) -> xr.DataTree:
    dt = dt.copy()  # copy tree but not underlying data
    for node in reversed(list(dt.subtree)):
        if not node.parent:
            continue
        for key in list(node.parent.data_vars):
            if key in node.data_vars:
                if node.data_vars[key].values is node.parent.data_vars[key].values:
                    node.dataset = node.to_dataset().drop_vars(key)
    return dt


def inherit_missing_data_vars(dt: xr.DataTree) -> xr.DataTree:
    dt = dt.copy()  # copy tree but not underlying data
    for node in dt.subtree:
        if not node.parent:
            continue
        for key in list(node.parent.data_vars):
            if key not in node.data_vars:
                node.dataset = node.to_dataset().assign({key: node.parent.data_vars[key]})
    return dt


def order_data_vars(dt: xr.DataTree) -> None:
    for child in dt.children.values():
        ordered_data_vars = child.attrs.get('ordered_data_vars', None)
        if ordered_data_vars is not None:
            for node in child.subtree:
                ds = node.to_dataset()
                node.dataset = xr.Dataset(
                    data_vars={key: ds[key] for key in ordered_data_vars},
                    coords=ds.coords,
                    attrs=ds.attrs,
                )


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication()
    app.setQuitOnLastWindowClosed(False)
    window = GOLabChart()
    window.show()
    app.exec()
