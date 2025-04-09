# GOLab
Goldschen-Ohm lab software.

## Setup Python
1. Install [miniforge](https://github.com/conda-forge/miniforge).
2. Install [Visual Studio Code (VSCode)](https://code.visualstudio.com).
3. In VSCode install the Python and Jupyter extensions.
4. Open a command line interface (e.g., Terminal, shell, etc.).
5. Create a python environment named "golab" to work in:
```shell
conda create -n golab python
```
6. Activate your golab environment:
```shell
conda activate golab
```
7. Install the latest golab python package into your active environment:
```shell
pip install -U golab@git+https://github.com/marcel-goldschen-ohm/GOLab
```
*To install an earlier version of the golab package associated with a git tag (e.g., v2025.4.9):*
```shell
pip install -U golab@git+https://github.com/marcel-goldschen-ohm/GOLab@v2025.4.9
```

## Work with a Jupyter Notebook python script
Open or create a `*.ipynb` file in VSCode and select the python interpreter associated with your golab environment.

## Run GoLabChart
1. Open a command line interface (e.g., Terminal, shell, etc.).
2. Activate your golab environment:
```shell
conda activate golab
```
3. Run GoLabChart (assumes you installed the golab package as indicated above):
```shell
golabchart
```
