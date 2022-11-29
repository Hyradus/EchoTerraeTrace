# MORDOR
**M**ars **O**rbital **R**adar **D**ata **O**pen-**R**eader

This repository contains the first pre-release of MORDOR, a toolset dedicated to Mars Orbital Radar Data downloading, reading and processing using interactive Jupyter notebooks.

This first pre-relase contains:

* a dockerfile to build the docker image.
* Notebooks for SHARAD (including SCS) and MARSIS data downloading.

## Prerequisites

* Docker
or 
* Conda

## How-to
### Using Docker (suggested)

#### Pull the image from dockerhub
```
docker pull hyradus/mordor:latest
```
**OR**
#### Build the image from scratch

  * Clone [this](https://github.com/Hyradus/MORDOR) repository
  * Build the docker image:
  ```
  docker build -t mordor -f mordord.dockerfile .
  ```
**THEN**
#### Run the container
```
docker run -it --rm -e NB_UID=$UID -e NB_GID=$UID -e CHOWN_HOME=yes -e CHOWN_HOME_OPTS='-R' --user root -v path-to-data-folder:/home/jovyan/MORDOR/Data -p 8888:8888 mordor:latest
```
**Remember to change path-to-data-folder with a folder where the data will be downloaded or where are stored the data in the local machine (e.g. if downloaded previously)**

### Using conda environment

* Clone [this](https://github.com/Hyradus/MORDOR) repository.
* Create the conda environment:

```
cd MORDOR
conda env create -name mordor -f env.yml
```

**Run it:**
```
conda activate mordor
jupyter lab
```

## To-DO

* [ ] Add a guide for the downloaders
* [ ] Add the Data processing notebooks
* [ ] Write a better tutorial

_____________________
This study is within the Europlanet 2024 RI and EXPLORE project, and it has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 871149 and No 101004214.

