# GardenNDVI

A project to process aerial infrared images to calculate NDVI (Normalized Difference Vegetation Index) per private yard.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Set-up](#set-up)
- [Instructions for Rasterio with ECW](#instructions-for-rasterio-with-ecw-linux-optional)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [License](#license)
- [Contributors](#contributors)

## Overview

The Normalized Difference Vegetation Index (NDVI) is a standardized index used to measure vegetation health. It ranges from -1 to +1, where:
- Higher values (0.6-0.9) indicate dense, healthy vegetation
- Moderate values (0.2-0.5) indicate sparse vegetation
- Low or negative values indicate non-vegetated areas (water, buildings, etc.)

This tool processes infrared aerial imagery to calculate NDVI values for private yards, helping to:
- Assess vegetation health
- Identify areas of stress or potential die-off
- Monitor changes in vegetation over time
- Support urban greening initiatives

## Prerequisites

1. **Pixi** installed. See the [Pixi Installation](https://pixi.sh/latest/#installation) instructions.
2. **Git** (optional, but generally recommended if you are cloning this repository).
3. **Docker** (only needed for ECW support). See the [Docker Installation](https://docs.docker.com/get-docker/) instructions.

This project uses **Pixi** to manage Python virtual environments.
**Pixi** makes it easy to isolate project dependencies, ensuring reproducible installations and clean development environments.

## Set-up

1. **Pull Project from Github**
    Pull the project from Github:
    ```sh
    git clone https://github.com/LynnBouwknegt/gardennvdi.git
    ```
    Or download the project as a zip file and extract it.
2. **Initiate project with Pixi**
    Go to your project directory:
    ```sh
    cd path/to/your/project
    ```
    And run:
    ```sh
    pixi install
    ```
3. **Open Jupyter Lab**
    After the installation is complete, you can open Jupyter Lab:
    ```sh
    pixi run -e <env> jupyter lab
    ```
    where `<env>` is the name of the environment you wish to use.
    See the [Environment Information](#environment-information) section for more information on the environments.

### Environment Information

The project contains two environments:
- **conda**: The default environment packages installed from conda. See `pixi.toml` for the list of packages.
  
- **ecw**: Special environment for working with ECW files:
  - All **conda** environment packages except Rasterio
  - Custom-built GDAL library with ECW support
  - Custom-built Rasterio wheel with above GDAL library
  See the [Instructions for Rasterio with ECW](#instructions-for-rasterio-with-ecw-linux-optional) section for more information on how to set it up.

## Instructions for Rasterio with ECW (Linux, optional)

### Prerequisites

* ECW Read Only SDK. See the [ECW SDK Set-up](#ecw-sdk-set-up) instructions.
* Docker installed. See the [Docker Installation](https://docs.docker.com/get-docker/) instructions.

### ECW SDK Set-up

To read ECW files, we need to request the read-only ECW SDK from Hexagon Geospatial:

https://supportsi.hexagon.com/s/article/ERDAS-ECW-JP2-SDK-Read-Only-Redistributable-Request

Once you have requested the SDK, you will receive an email with a link to download the SDK.
Download the zip file, extract it and run the binary setup:

```sh
chmod +x *.zip && 
unzip *.zip && 
chmod +x ./ECWJP2SDKSetup*.bin && 
./ECWJP2SDKSetup*.bin
```

Type 1, read and accept the license agreement, and type `yes` to install the SDK. 
In the terminal output, note down the installation path, as we will need it later.
It will likely be something like `/home/<username>/hexagon/ERDAS-ECW_JPEG_2000_SDK-5.5.0/Desktop_Read-Only` where `<username>` is your username.

Make a folder called `ecw` in your project directory and copy the contents of the `Desktop_Read-Only` folder into it:
```sh
mkdir -p ecw && 
cp -r /home/<username>/hexagon/ERDAS-ECW_JPEG_2000_SDK-5.5.0/Desktop_Read-Only/* ecw
```

### Generating Rasterio Wheel

To install Rasterio with ECW support, we need to build it from source.
We do this by first building the GDAL library with ECW support, and then using that to build Rasterio.

All of these steps are done in a Docker container:

```sh
sudo docker build . --tag rasterio-build
```

And then run the docker container once it builds:
```sh
sudo docker run --rm \                  
  -v ./ecw:/ecw \
  -v ./:/output \
  rasterio-build
```

Once the docker container has finished running, you will find the `rasterio` wheel and `gdal_shared` folder in the root of your project directory.
To finish up setting up the `ecw` environment, we need to install the `rasterio` wheel and set the `GDAL_DATA` environment variable. 
```sh
pixi install && pixi run -e ecw setup-ecw
```

## Project Structure

The project is structured as follows:

* `src/` - Core source code for the project.
    * `ndvi.py` - Main script to calculate NDVI and process both data and images.
    * `api/` - All external API calls handled here.
        * `bgt_api.py` - API calls to BGT API.
        * `kadaaster_api.py` - API calls to Kadaster API.
* `analysis.ipynb` - Jupyter Notebook for data analysis.
* `process_to_csv.ipynb` - Notebook for processing data to CSV format.
* `pixi.toml` - Human-readable Pixi file which states the project's dependencies.
* `pixi.lock` - Lock file generated by Pixi to ensure reproducible installations.
* `Dockerfile` - Dockerfile to build the Rasterio wheel with ECW support.
* `build.sh` - Shell script to build GDAL and Rasterio with ECW support.
* `AUTHORS.md` - List of project contributors.

## Usage Guide

Refer to the `analysis.ipynb` for examples on how to run the code.

## License

No license is yet specified.

## Contributors

See [AUTHORS.md](AUTHORS.md) for a list of contributors.

For questions or support, please open an issue on the GitHub repository.