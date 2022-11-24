ARG BASE_IMAGE=jupyter/base-notebook:latest
FROM $BASE_IMAGE as base

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV TZ=Europe/Rome
ENV DEBIAN_FRONTEND='noninteractive'

MAINTAINER "Giacomo Nodjoumi <giacomo.nodjoumi@hyranet.info>"

USER root

RUN apt-get update				&& \
    apt-get upgrade -y 			&& \
    apt-get install --no-install-recommends -y	\
				build-essential					\
				curl 							\
				git-core 						\
				python3-pip 					\
				sudo 							\
				tzdata							\
				vim							 && \	
    rm -rf /var/lib/apt/lists/* 	 		 && \
    apt-get clean

USER jovyan

RUN set -x 																				 && \    
	mamba install -c conda-forge		 		 	 									    \
				fiona																		\
				geopandas 																	\
				geoplot 																	\
				geoviews 																	\
				holoviews 																	\
				hvplot 																		\
				ipywidgets 																	\
				owslib 																		\
				opencv 																		\
				pillow 																		\
				plotly 																		\
				pscript 																	\
				psutil 																		\
				pyproj																		\
				rasterio 																	\
				rioxarray 																	\
				scikit-image																\
				scipy 																		\
				shapely 					 	 		 								 && \
	conda clean -a



RUN 			pip --no-cache-dir install 											   \
				ipykernel \
				https://github.com/chbrandt/gpt/archive/refs/tags/v0.3dev.zip  \
				pds4-tools 		&& \
				python -m ipykernel install --user --name 'MORDOR'											

ADD $PWD/Notebooks $HOME/MORDOR
WORKDIR $HOME/MORDOR

ENV JUPYTER_ENABLE_LAB='yes'

