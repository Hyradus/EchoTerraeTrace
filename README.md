# EchoTerraeTrace (prev. MORDOR)

**M**ars **O**rbital **R**adar **D**ata **O**pen-**R**eader

First Release of EchoTerraeTrace!

## With this first release:

Former app names where changed:

EchoTerraeTrace-Draw -> ett_*instrument*.py
EchoTerraeTrace-Profiler -> ett_*instrument*_profiler.py
EchoTerraeTrace-3D -> dash_app.py (experimental)

### SHARAD
* **ett_sharad.py**
* **ett_sharad_profiler.py**

### MARSIS
* **ett_marsis.py**
* **ett_marsis_profiler.py**

### 3D Visualization and analysis

* **dash_app.py**

## Data Prerequisites

* Mars MOLA basemap with filename *Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2-cog.tiff* in folder data-folder-path/Basemaps
* SHARAD Coverage shapefile, from ODE-PDS, in folder data-folder-path/Instrument/Coverage (e.g. data/SHARAD/Coverage)
* A polygon gpkg named *LavaFieldGroups_buffer_01.gpkg* in data/Products/ - This will be used to crop on the fly the radar footprint 

## Software Prerequisites

* Docker + docker-buildx
or 
* Conda

## How-to
### Using Docker (suggested)

#### Pull the image from dockerhub
```
docker pull hyradus/echoterraetrace:latest
```
**OR**
#### Build the image from scratch

  * Clone [this](https://github.com/Hyradus/MORDOR) repository
  * Build the docker image:
  ```
  docker buildx -t ett -f Dockerfile .
  ```
**THEN**
#### Run the container
```
docker run -it --rm --name ett -p 8881:8888 -p 5006:5006 -p 5007:5007 -p 5008:5008 -p 5009:5009 -p 8050:8050 --name ett -v path-to-data:/Data/SHARAD/ ett:latest 
```
**Remember to change path-to-data-folder with a folder where the data will be downloaded or where are stored the data in the local machine (e.g. if downloaded previously)**

### Using conda environment

* Clone [this](https://github.com/Hyradus/MORDOR) repository.
* Create the conda environment:

```
cd EchoTerraeTrace
conda env create -name ett -f environment.yml
```

**Run it:**
```
conda activate ett
```
then run one of the app, remember first to edit the absolute folder in each python file before execution.

```
bokeh serve ett_sharad.py --port 5006
```

## To-DO

* [ ] Add a guide for the downloaders
* [ ] Add the Data processing notebooks
* [ ] Write a better tutorial

_____________________
This study is within the Europlanet 2024 RI and EXPLORE project, and it has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 871149 and No 101004214.

