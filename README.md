# UltraFast Expressed Variant Calling

The current tools for identification of expressed variants are either slow or involve several software dependencies which are difficult to install. In addition, they either generate several intermediate files or use significant amounts of RAM which is not highthroughput if you are trying to analyze large datasets.

Our pipeline identifies expressed variants from public databases such as NCBI SRA as well as user’s own RNA-Seq data using one of several RNA aligners and quantification tools.

## Installation

```
pip install -e \
  "git+https://github.com/NCBI-Hackathons/Ultrafast_Mapping_CSHL.git#egg=pipeline&subdirectory=pipeline"
```

## Usage

Output the first 10 reads of SRR1616919 to standard output:

```
align.py -a SRR1616919 -M 10 -p mock
```

Align all reads of SRR1616919 using STAR and generate a sorted BAM using 16 threads...:

```
align.py -a SRR1616919 -p star -r /path/to/star/index -o aligned.bam -t 16
```

...or with Hisat2:

```
align.py -a SRR1616919 -p hisat -r /path/to/hisat/index -o aligned.bam -t 16
```

Generate counts of SRR1616919 using Kallisto...:

```
align.py -a SRR1616919 -p kallisto -r /path/to/kallisto/index -o kallisto_output -t 16
```

...or with Salmon:

```
align.py -a SRR1616919 -p salmon -r /path/to/salmon/index -o salmon_output -t 16
```
