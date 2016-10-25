# Ultrafast_Mapping_CSHL

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
align.py -a SRR1616919 -p star -i /path/to/star/index -o aligned.bam -t 16
```

...or with Hisat2:

```
align.py -a SRR1616919 -p hisat -i /path/to/hisat/index -o aligned.bam -t 16
```

Generate counts of SRR1616919 using Kallisto:

```
align.py -a SRR1616919 -p kallisto -i /path/to/kallisto/index \
  -o kallisto_output -t 16
```
