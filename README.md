# MORDOR
**M**ars **O**rbital **R**adar **D**ata **O**pen-**R**eader

This repository contains the first pre-release of MORDOR, a toolset dedicated to Mars Orbital Radar Data downloading, reading and processing using interactive Jupyter notebooks.

This first pre-relase contains:

* a dockerfile to build the docker image.
* Notebooks for SHARAD (including SCS) and MARSIS data downloading.

## Prerequisites

* Docker

## How-to
### Get the Image

* From dockerhub
```
docker pull hyradus/mordor:latest
```

* Building from scratch

  * Clone this repository
  * Build the docker image by executing:
  ```
  docker build -t mordor -f mordord.dockerfile .
  ```

### Run the image

* Run it by executing:
```
docker run -it --rm -e NB_UID=$UID -e NB_GID=$UID -e CHOWN_HOME=yes -e CHOWN_EXTRA_OPTS='-R' -v path-to-data-folder:/home/jovyan/MORDOR/Data -p 8888:8888 mordor:latest
```
**Remember to change path-to-data-folder with a folder where the data will be downloaded or where are stored the data in the local machine (e.g. if downloaded previously)**

## To-DO

* [ ] Add a guide for the downloaders
* [ ] Add the Data processing notebooks
* [ ] Write a better tutorial

_____________________
This study is within the Europlanet 2024 RI and EXPLORE project, and it has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 871149 and No 101004214.

