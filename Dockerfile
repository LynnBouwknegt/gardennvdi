FROM quay.io/pypa/manylinux2014_x86_64

# Set python to use
ENV PYBIN="/opt/python/cp39-cp39/bin"

# Set working directory
WORKDIR /work

# Install build dependencies
RUN yum install -y \
    libtiff-devel \
    libcurl-devel \
    git

# Install Python dependencies (Python 3.9 only)
RUN ${PYBIN}/pip install --upgrade pip && \
    ${PYBIN}/pip install numpy setuptools build wheel auditwheel

# Build and install PROJ
RUN curl -LO https://download.osgeo.org/proj/proj-9.2.1.tar.gz && \
    tar xf proj-9.2.1.tar.gz && \
    cd proj-9.2.1 && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/opt/proj && \
    make -j$(nproc) && \
    make install

# Build and install SQLite with spatial capabilities
RUN curl -O https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz && \
    tar xzf sqlite-autoconf-3420000.tar.gz && \
    cd sqlite-autoconf-3420000 && \
    export CFLAGS="-DSQLITE_ENABLE_RTREE=1 -DSQLITE_ENABLE_COLUMN_METADATA=1 -DSQLITE_ENABLE_JSON1=1 -DSQLITE_ENABLE_FTS5=1" && \
    ./configure --prefix=/usr/local && \
    make -j$(nproc) && \
    make install

# Copy build script
COPY build.sh /work/build.sh
RUN chmod +x /work/build.sh

# Set volumes for ECW SDK input and wheel output
VOLUME /ecw
VOLUME /output

ENTRYPOINT ["/work/build.sh"]