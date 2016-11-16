FROM ubuntu:14.04.3
MAINTAINER Upendra Devisetty <upendra@cyverse.org>
LABEL Description "This Dockerfile for Ultrafast_Mapping_CSHL pipeline"

# Install dependencies
RUN apt-get update && apt-get install -y \
			wget \
			g++ \
			openjdk-7-jre \
			make \
			git \
			pv \
			libz-dev \
			unzip \
			python-pip

# ncbi-sra and ncbi-vdb tool kit
WORKDIR /ncbi
RUN git clone https://github.com/ncbi/ngs.git
RUN git clone https://github.com/ncbi/ncbi-vdb.git
RUN git clone https://github.com/ncbi/sra-tools.git
RUN ngs/ngs-sdk/configure --prefix=~/software/apps/sratoolkit/gcc/64/2.5.8
RUN make default install -C ngs/ngs-sdk
RUN ncbi-vdb/configure --prefix=~/software/apps/sratoolkit/gcc/64/2.5.8
RUN make default install -C ncbi-vdb
RUN sra-tools/configure --prefix=~/software/apps/sratoolkit/gcc/64/2.5.8
RUN make default install -C sra-tools
WORKDIR /

# Hisat2
RUN ftp://ftp.ccb.jhu.edu/pub/infphilo/hisat2/downloads/hisat2-2.0.5-Linux_x86_64.zip
RUN unzip hisat2-2.0.5-Linux_x86_64.zip

# STAR
RUN wget https://github.com/alexdobin/STAR/archive/2.5.2b.tar.gz
RUN tar xvf 2.5.2b.tar.gz

# Kallisto
RUN https://github.com/pachterlab/kallisto/releases/download/v0.43.0/kallisto_linux-v0.43.0.tar.gz
RUN tar xvf kallisto_linux-v0.43.0.tar.gz

# Salmon
RUN https://github.com/COMBINE-lab/salmon/releases/download/v0.7.2/Salmon-0.7.2_linux_x86_64.tar.gz
RUN tar xvf Salmon-0.7.2_linux_x86_64.tar.gz

# Sambamba
WORKDIR /sambamba
RUN https://github.com/lomereiter/sambamba/releases/download/v0.6.5/sambamba_v0.6.5_linux.tar.bz2
RUN tar xvf sambamba_v0.6.5_linux.tar.bz2
RUN alias python=python3.4

# Samtools
RUN wget https://github.com/samtools/samtools/releases/download/1.3.1/samtools-1.3.1.tar.bz2
RUN tar xvf samtools-1.3.1.tar.bz2
WORKDIR /samtools-1.3.1
RUN ./configure --without-curses && make
WORKDIR /

# Bedops
WORKDIR /bedops
RUN wget https://github.com/bedops/bedops/releases/download/v2.4.20/bedops_linux_i386-v2.4.20.tar.bz2
RUN tar xvf bedops_linux_i386-v2.4.20.tar.bz2
WORKDIR /

# Subread
RUN wget https://sourceforge.net/projects/subread/files/subread-1.5.1/subread-1.5.1-Linux-x86_64.tar.gz/download
RUN tar xvf download

# Clone Ultrafast repo
RUN git clone https://github.com/NCBI-Hackathons/Ultrafast_Mapping_CSHL.git
RUN wget https://bootstrap.pypa.io/ez_setup.py
RUN python ez_setup.py
#RUN python setup.py build

# Environmental variables
ENV PATH /STAR-2.5.2b/bin/Linux_x86_64/:$PATH
ENV PATH /kallisto_linux-v0.43.0/:$PATH
ENV PATH /Salmon-0.7.2_linux_x86_64/bin:$PATH
ENV PATH /sambamba/:$PATH
ENV PATH /bedops/bin/:$PATH
ENV PATH /subread-1.5.1-Linux-x86_64/bin/:$PATH



