FROM python:3.11-slim-bullseye

WORKDIR /

# Install the necessary dependencies
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y libopenblas-dev gcc gfortran graphviz git make g++ build-essential cmake pandoc texlive-latex-extra dvipng sudo swig
RUN rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash pybamm && echo "pybamm:pybamm" | chpasswd && adduser pybamm sudo
RUN usermod -ou 1000 -g 0 pybamm
USER pybamm

WORKDIR /home/pybamm/

# Install casadi from source
RUN git clone https://github.com/casadi/casadi.git -b main casadi
RUN mkdir casadi/build && cd casadi/build
RUN cmake -DWITH_PYTHON=ON -DPYTHON_PREFIX=/home/pybamm/.local -DCMAKE_INSTALL_PREFIX=/home/pybamm/.local /home/pybamm/casadi/
RUN make -j$(nproc) install

WORKDIR /home/pybamm

# Clone project files from Git repository
RUN git clone https://github.com/santacodes/PyBaMM.git -b casadibug

WORKDIR /home/pybamm/PyBaMM

ENV CMAKE_C_COMPILER=/usr/bin/gcc
ENV CMAKE_CXX_COMPILER=/usr/bin/g++
ENV CMAKE_MAKE_PROGRAM=/usr/bin/make
ENV SUNDIALS_INST=/home/pybamm/.local
ENV LD_LIBRARY_PATH=/home/pybamm/.local/lib
ENV casadi_DIR=/home/pybamm/.local

# Migrating to venv and create a virtual environment for python 3.11
ENV VIRTUAL_ENV=/home/pybamm/venv
RUN python3.11 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade setuptools wheel wget && \
pip install cmake
RUN #!/bin/bash && \
source /home/pybamm/venv/bin/activate;

RUN python scripts/install_KLU_Sundials.py && \
rm -rf pybind11 && \
git clone https://github.com/pybind/pybind11.git && \
pip install -e ".[all,dev,docs,jax]";

ENTRYPOINT ["/bin/bash"]
