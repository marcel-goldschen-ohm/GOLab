# GOLab
Goldschen-Ohm lab software.

# Setup Python
1. Install [miniforge](https://github.com/conda-forge/miniforge).
    
    **macOS**: You can first install [Homebrew](https://brew.sh/), then run `brew install miniforge`. Finally, copy the *conda initialize* portion added to your `.bash_profile` to your `.zshrc` if it is not already there.
2. Create a python environment named "golab" to work in: `mamba create -n golab python`
3. Activate your golab environment: `mamba activate golab`
4. Install some basic python packages: `pip install ipykernel numpy pandas scipy matplotlib seaborn`
5. Install [Visual Studio Code](https://code.visualstudio.com).
6. In VSCode install the Python and Jupyter extensions.
7. Open a `*.ipynb` file in VSCode and select the python interpreter associated with your golab environment.
