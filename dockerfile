FROM debian:stretch
ARG DEBIAN_FRONTEND="noninteractive"

ENV LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    ND_ENTRYPOINT="/neurodocker/startup.sh"
RUN export ND_ENTRYPOINT="/neurodocker/startup.sh" \
    && apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
           curl \
           locales \
           unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG="en_US.UTF-8" \
    && chmod 777 /opt && chmod a+s /opt \
    && mkdir -p /neurodocker \
    && if [ ! -f "$ND_ENTRYPOINT" ]; then \
         echo '#!/usr/bin/env bash' >> "$ND_ENTRYPOINT" \
    &&   echo 'set -e' >> "$ND_ENTRYPOINT" \
    &&   echo 'export USER="${USER:=`whoami`}"' >> "$ND_ENTRYPOINT" \
    &&   echo 'if [ -n "$1" ]; then "$@"; else /usr/bin/env bash; fi' >> "$ND_ENTRYPOINT"; \
    fi \
    && chmod -R 777 /neurodocker && chmod a+s /neurodocker

ENTRYPOINT ["/neurodocker/startup.sh"]

ENV FREESURFER_HOME="/opt/freesurfer-6.0.0-min" \
    PATH="/opt/freesurfer-6.0.0-min/bin:$PATH"
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           libgomp1 \
           libxmu6 \
           libxt6 \
           perl \
           tcsh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Downloading FreeSurfer ..." \
    && mkdir -p /opt/freesurfer-6.0.0-min \
    && curl -fsSL --retry 5 https://dl.dropbox.com/s/nnzcfttc41qvt31/recon-all-freesurfer6-3.min.tgz \
    | tar -xz -C /opt/freesurfer-6.0.0-min --strip-components 1 \
    && sed -i '$isource "/opt/freesurfer-6.0.0-min/SetUpFreeSurfer.sh"' "$ND_ENTRYPOINT"\
    && cd /opt/freesurfer-6.0.0-min\
    && echo "Downloading Matlab compiler ..." \
    && curl "http://surfer.nmr.mgh.harvard.edu/fswiki/MatlabRuntime?action=AttachFile&do=get&target=runtime2012bLinux.tar.gz" -o "runtime2012b.tar.gz"\
    && tar xvf runtime2012b.tar.gz

ENV CONDA_DIR="/opt/miniconda-latest" \
    PATH="/opt/miniconda-latest/bin:$PATH"
RUN export PATH="/opt/miniconda-latest/bin:$PATH" \
    && echo "Downloading Miniconda installer ..." \
    && conda_installer="/tmp/miniconda.sh" \
    && curl -fsSL --retry 5 -o "$conda_installer" https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash "$conda_installer" -b -p /opt/miniconda-latest \
    && rm -f "$conda_installer" \
    && conda update -yq -nbase conda \
    && conda config --system --prepend channels conda-forge \
    && conda config --system --set auto_update_conda false \
    && conda config --system --set show_channel_urls true \
    && sync && conda clean --all && sync \
    && conda create -y -q --name neuro \
    && conda install -y -q --name neuro \
           'python=3.6' \
           'numpy' \
           'traits' \
    && sync && conda clean --all && sync \
    && bash -c "source activate neuro \
    &&   pip install --no-cache-dir  \
             'nipype' \
             'fire'" \
    && rm -rf ~/.cache/pip/* \
    && sync

RUN sed -i '$isource activate neuro' $ND_ENTRYPOINT

RUN echo "source activate neuro" > ~/.bashrc
ENV PATH /opt/miniconda-latest/envs/neuro/bin:$PATH

RUN mkdir  /mnt/subjects_dir
RUN mkdir  /mnt/output
RUN mkdir  /working_dir
RUN mkdir  /app

RUN chmod 777 /mnt/subjects_dir
RUN chmod 777 /mnt/output
RUN chmod 777 /working_dir
RUN chmod 777 /app

COPY ["license.txt", "/opt/freesurfer-6.0.0-min/license.txt"]
COPY ["./labelling", "/app/"]
