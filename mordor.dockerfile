ARG BASE_IMAGE=jupyter/base-notebook:python-3.9.5
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



RUN set -x 																				 && \    
	mamba install -c conda-forge		 		 	 									    \
				bs4																			\							
				fiona																		\
				geopandas 																	\
				geoplot 																	\
				geoviews=1.9.4 																\				
				hvplot 																		\
				ipywidgets=8.0.0															\
				ipykernel=6.17 																\				
				opencv 																		\
				owslib																		\
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



RUN 			pip --no-cache-dir install 											   		\
				ipykernel 																	\
				https://github.com/chbrandt/gpt/archive/refs/tags/v0.3dev.zip  				\
				cartopy==0.21 \
				pds4-tools 																 && \
				python -m ipykernel install --user --name 'MORDOR'											



ADD $PWD/Notebooks $HOME/MORDOR

WORKDIR $HOME/MORDOR

ENV JUPYTER_ENABLE_LAB='yes'

USER ${NB_UID}

