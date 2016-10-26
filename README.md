# UltraFast Expressed Variant Calling

The current tools for identification of expressed variants are either slow or involve several software dependencies which are difficult to install. In addition, they either generate several intermediate files or use significant amounts of RAM which is not highthroughput if you are trying to analyze large datasets.

Our pipeline identifies expressed variants from public databases such as NCBI SRA as well as user’s own RNA-Seq data using one of several RNA aligners and quantification tools.

Presentation: [Hackathon end presentation](https://docs.google.com/presentation/d/1dUL5vSF2vqZljXa7FQJ6D-1eldAw0Gb-YeKrk9Gun8Q/pub?start=false&loop=false&delayms=3000)


## Installation

```
pip install -e \
  "git+https://github.com/NCBI-Hackathons/Ultrafast_Mapping_CSHL.git#egg=pipeline&subdirectory=pipeline"
```

## Dependencies for the RNA flotilla

Older or newer versions may be used but may not be fully compatible.

Pull from SRA:

* [SRA Toolkit 2.8.0+](https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?cmd=show&f=software&m=software&s=software): set [use vdb-config -i to DISABLE local file caching](https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?view=toolkit_doc&f=std)
* [NGS Software Development Kit 1.3.0+](https://github.com/ncbi/ngs)
* [NCBI VDB Software Development Kit 2.8.0+](https://github.com/ncbi/ncbi-vdb)

RNA Aligners

* [HISAT2 2.0.4+](http://ccb.jhu.edu/software/hisat2/index.shtml)
* [STAR 2.5.2b](https://github.com/alexdobin/STAR)
* [Sambamba v0.6.5+](http://lomereiter.github.io/sambamba/)

Transcript counting

* [kallisto v0.43.0+](https://pachterlab.github.io/kallisto/)
* [SALMON 0.7.2+](https://combine-lab.github.io/salmon/)
* [Subread (for featureCounts) 1.5.1+](http://bioinf.wehi.edu.au/featureCounts/)

Variant callers

* [Samtools 1.3.1+](http://www.htslib.org/)
* [The Genome Analysis Toolkit (GATK) 3.6+](https://software.broadinstitute.org/gatk/)
* [Bedops](https://bedops.readthedocs.io/en/latest/content/reference/file-management/conversion/vcf2bed.html) - to convert VCFs into BED

Reference data : note that the chromosome/contig identifiers need to match for all of these
* [GRCh38 human genome reference fasta]()
  * Create reference indexes for almost all of the above tools
* [ClinVar vcf]()
* [GTF file with exome regions]()



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
