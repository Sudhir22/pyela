# ela

**Python package for Exploratory Lithology Analysis**

![status](https://img.shields.io/badge/status-alpha-orange.svg)
[![license](http://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/jmp75/pyela/blob/devel/LICENSE.txt)
[![build](https://img.shields.io/travis/jmp75/pyela.svg?branch=master)](https://travis-ci.org/jmp75/pyela)
[![coverage](https://coveralls.io/repos/github/jmp75/pyela/badge.svg?branch=master)](https://coveralls.io/github/jmp75/pyela?branch=master)

<!-- [![Docker Build](https://img.shields.io/docker/build/kinverarity/ela.svg)](https://hub.docker.com/r/kinverarity/ela/)
[![Build status](https://ci.appveyor.com/api/projects/status/csr7bg8urkbtbq4n?svg=true)](https://ci.appveyor.com/project/kinverarity1/ela)
[![Python versions](https://img.shields.io/pypi/pyversions/ela.svg)](https://www.python.org/downloads/) -->
<!-- [![Version](http://img.shields.io/pypi/v/ela.svg)](https://pypi.python.org/pypi/ela/) -->

<!-- .. image:: https://img.shields.io/codacy/ad9af103cba14d33abd5b327727ff644.svg 
    :target: https://www.codacy.com/app/matt/striplog/dashboard
    :alt: Codacy code review -->

Analysing driller’s logs is a tedious and repetitive task in many groundwater modelling projects. Automating the process of extracting useful information from driller's logs allows spending less time on manual data wrangling, more time on its interpretation, and enhances the reproducibility of the analysis.

This packages combines features to:

* perform natural language processing lithology descriptions in the logs, to detect primary and secondary lithologies
* apply supervised machine learning to interpolate lithologies across a 3D grid
* visualise interactively the 3D data

## License

MIT (see [License.txt](./LICENSE.txt))

## Documentation

Get a [quick tour of the visualisation part of 'ela'](./docs/visual_tour.md)

_Placeholder section for other introductory material such as tutorials_

<!-- See here for the [complete ela package documentation](https://ela.readthedocs.io/en/latest/). -->

## Installation

Note that 'ela' relies on several external packages, and some can be fiddly to install depending on the version of Python and packages. Below are fairly prescriptive instructions, given in the hope of limiting the risk of issues.

### Debian packages for spatial projections

`cartopy` and possibly other python packages require `proj4` version 4.9+ to be installed (libproj-dev). If your debian/ubuntu repo does not suffice (older versions) you may try:

```sh
sudo apt-get install -y libc6  
wget http://en.archive.ubuntu.com/ubuntu/pool/universe/p/proj/proj-data_4.9.3-2_all.deb
sudo dpkg -i proj-data_4.9.3-2_all.deb
wget http://en.archive.ubuntu.com/ubuntu/pool/universe/p/proj/libproj12_4.9.3-2_amd64.deb
sudo dpkg -i libproj12_4.9.3-2_amd64.deb
wget http://en.archive.ubuntu.com/ubuntu/pool/universe/p/proj/proj-bin_4.9.3-2_amd64.deb
sudo dpkg -i proj-bin_4.9.3-2_amd64.deb
wget http://en.archive.ubuntu.com/ubuntu/pool/universe/p/proj/libproj9_4.9.2-2_amd64.deb 
sudo dpkg -i libproj9_4.9.2-2_amd64.deb
wget http://en.archive.ubuntu.com/ubuntu/pool/universe/p/proj/libproj-dev_4.9.3-2_amd64.deb
sudo dpkg -i libproj-dev_4.9.3-2_amd64.deb
```

### Installation of python dependencies with conda

You may want to install [Anaconda](http://docs.continuum.io/anaconda/install) to install dependencies. Note that I recommend to **not** let anaconda change your startup file and change the `PATH` environment. To activate Anaconda you first need: `source ~/anaconda3/bin/activate`. Then choose a conda environment name.

Optionally you may want to do `conda update -n base conda` and `conda update -n base anaconda-navigator`

```sh
my_env_name=ELA
```

```sh
conda create --name ${my_env_name} python=3.6
conda activate  ${my_env_name}
conda install --name ${my_env_name} rasterio cartopy geopandas pandas nltk scikit-learn scikit-image matplotlib vtk
```

As of writing (2018-08) conda does not have pyqt5, and a suitable version of mayavi for python3. We use `pip`

```sh
pip install --upgrade pip
```

```sh
pip search pyqt5
pip search mayavi
```

```sh
pip install pyqt5
pip install mayavi
```

### Windows

Placeholder section. As of Sept 2018 it may be possible to install upon Python 3.6+ with Anaconda 3, and then including mayavi from pip.

### Installation of pyela

```sh
pip install -r requirements.txt
python setup.py install
```

For Python 2.7.x pyqt5 is not available:

```sh
# Note: not sure if conda-forge needed: conda config --add channels conda-forge
conda create --name  ${my_env_name} python=2.7 mayavi rasterio cartopy geopandas pandas nltk scikit-learn scikit-image matplotlib vtk
```

## Related Geoscience packages

'ela' aims to complement other Python packages for geoscience, in particular for handling bore data . It depends on the package ['striplog'](https://github.com/agile-geoscience/striplog) and is likely to depend on ['lasio'](https://github.com/kinverarity1/lasio) in the future.

<!-- Draft Notes-----------
``conda install coveralls`` then ``conda install pytest-cov pytest-mpl``: this downgrades numpy a tad. Why? Trying ``conda update numpy`` but even odder outcome -->

## Known issues

As of 2018-08, using mayavi 4.6 on python 3.6 is [buggy, a VTK issue it seems](https://github.com/enthought/mayavi/issues/656). Python 2.7 with mayavi 4.5 via Anaconda2 is known to work.

## Troubleshooting

If in a conda environment trying to use `pip` you get:

```txt
ModuleNotFoundError: No module named 'pip._internal'
```

consider:

```sh
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --force-reinstall
```