#!/bin/bash
set -e

# Copy ECW SDK from mounted volume to /opt/ecw
echo "Setting up ECW SDK..."
mkdir -p /opt/ecw
cp -r /ecw/* /opt/ecw/

ECW_LIB="/opt/ecw/lib/x64/release/libNCSEcw.so"
ECW_LIB_DIR="/opt/ecw/lib/x64/release"

# Check if ECW library exists
if [ ! -f "$ECW_LIB" ]; then
    echo "ERROR: ECW library not found!"
    exit 1
fi

# Download and build GDAL with ECW support
echo "Building GDAL with ECW support..."
curl -L https://github.com/OSGeo/gdal/releases/download/v3.10.2/gdal-3.10.2.tar.gz > gdal.tar.gz
tar -xf gdal.tar.gz
cd gdal-3.10.2
mkdir -p build
cd build

# Configure and build GDAL
cmake .. \
  -DBUILD_SHARED_LIBS=ON \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/opt/gdal-custom \
  -DECW_ROOT=/opt/ecw \
  -DECW_INCLUDE_DIR=/opt/ecw/include \
  -DECW_LIBRARY=$ECW_LIB \
  -DGDAL_USE_ECW=ON \
  -DGDAL_ENABLE_DRIVER_ECW=ON \
  -DPython_EXECUTABLE="${PYBIN}/python"

cmake --build . -j$(nproc)
cmake --build . --target install
cd /work

# Set environment variables
export PATH=/opt/gdal-custom/bin:$PATH
export LD_LIBRARY_PATH=/opt/gdal-custom/lib:/opt/gdal-custom/lib64:/opt/proj/lib:/opt/proj/lib64:$ECW_LIB_DIR:$LD_LIBRARY_PATH
export GDAL_CONFIG=/opt/gdal-custom/bin/gdal-config

# Clone and build rasterio
echo "Building rasterio wheel..."
git clone https://github.com/rasterio/rasterio.git
cd rasterio

# Create configuration for build
cat > setup.cfg << EOF
[build_ext]
include_dirs = /opt/gdal-custom/include
library_dirs = /opt/gdal-custom/lib:/opt/gdal-custom/lib64
libraries = gdal
EOF

# Build and repair wheel
"${PYBIN}/python" -m build --wheel
"${PYBIN}/auditwheel" repair dist/*.whl --plat manylinux2014_x86_64 -w dist/bundled/

# Copy artifacts to output
mkdir -p /output
cp dist/bundled/*.whl /output/
mkdir -p /output/gdal_share
cp -r /opt/gdal-custom/share/gdal/* /output/gdal_share/

echo "Build complete! Wheel and GDAL share data are available in the /output directory."