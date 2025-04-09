from golab.golabchart import GOLabChart
from qtpy.QtWidgets import QApplication#, QMessageBox


def main():
    app = QApplication()
    window = GOLabChart()
    window.show()

    # # MacOS Magnet warning
    # import platform
    # if platform.system() == 'Darwin':
    #     QMessageBox.warning(window, 'Magnet Warning', 'If you are using the window management software Magnet, please disable it for this app to work properly.')

    # # load example data?
    # answer = QMessageBox.question(window, 'Example?', 'Load example data?')
    # if answer == QMessageBox.StandardButton.Yes:
    #     try:
    #         load_example(ui)
    #     except Exception as err:
    #         QMessageBox.critical(ui, 'Failed to load example', str(err))
    
    app.exec()


# def load_example(ui: XarrayGraph):
#     from datatree import DataTree, open_datatree
#     import requests
#     import io

#     url = 'https://raw.githubusercontent.com/marcel-goldschen-ohm/xarray-graph/main/examples/ERPdata.nc'
#     req = requests.get(url, stream=True)
#     if req.status_code != 200:
#         raise ValueError(f'Failed to download example data: request status code = {req.status_code}')
#     dt: DataTree = open_datatree(io.BytesIO(req.content), 'h5netcdf')

#     ui.data = dt

#     ui._show_control_panel_at(0)
#     ui._data_treeview.expandAll()


if __name__ == '__main__':
    main()
