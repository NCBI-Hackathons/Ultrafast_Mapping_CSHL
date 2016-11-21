# UltraFast Expressed Variant Calling

The current tools for identification of expressed variants are either slow or involve several software dependencies which are difficult to install. In addition, they either generate several intermediate files or use significant amounts of RAM which is not highthroughput if you are trying to analyze large datasets.

Our pipeline identifies expressed variants from public databases such as NCBI SRA as well as user’s own RNA-Seq data using one of several RNA aligners and quantification tools.

Presentation: [Hackathon end presentation](https://docs.google.com/presentation/d/1dUL5vSF2vqZljXa7FQJ6D-1eldAw0Gb-YeKrk9Gun8Q/pub?start=false&loop=false&delayms=3000)

## Alignment/quantification from SRA

### Dependencies

Older or newer versions may be used but may not be fully compatible.

Pull from SRA:

* [NGS Software Development Kit 1.3.0+](https://github.com/ncbi/ngs)
* [NCBI VDB Software Development Kit 2.8.0+](https://github.com/ncbi/ncbi-vdb)
* [pv](https://linux.die.net/man/1/pv) (or any pipe-able buffering tool)

RNA Aligners

* [HISAT2 2.0.4+](http://ccb.jhu.edu/software/hisat2/index.shtml)
* [STAR 2.5.2b](https://github.com/alexdobin/STAR)

Transcript quantification

* [kallisto v0.43.0+](https://pachterlab.github.io/kallisto/)
* [SALMON 0.7.2+](https://combine-lab.github.io/salmon/)

Transcript counting

* [Subread (for featureCounts) 1.5.1+](http://bioinf.wehi.edu.au/featureCounts/)

Variant callers

* [Samtools 1.3.1+](http://www.htslib.org/)
* [The Genome Analysis Toolkit (GATK)
* 3.6+](https://software.broadinstitute.org/gatk/)
* [Bedops](https://bedops.readthedocs.io/en/latest/content/reference/file-management/conversion/vcf2bed.html)
* - to convert VCFs into BED

Reference data : note that the chromosome/contig identifiers need to match for
all of these

* [GRCh38 human genome reference fasta]()
  * Create reference indexes for almost all of the above tools
* [ClinVar vcf]()
* [GTF file with exome regions]()


Other tools

* [Sambamba v0.6.5+](http://lomereiter.github.io/sambamba/)

### Installation

```
pip install git+https://github.com/NCBI-Hackathons/Ultrafast_Mapping_CSHL.git
```

### Usage

There are two main python scripts: stream_sra.py and align.py. The first streams a set of reads for a given accession to a file (or stdout by default). The second uses the first and pipes the reads to the aligner of your choice (via a FIFO, or pair of FIFOs for paired-end reads).

Save the first 10 reads of SRR1616919 to a pair of fastq files:

```
stream_sra.py -a SRR1616919 -M 10 head.1.fq head.2.fq
```

Append the next 10 reads to the same files:

```
stream_sra.py -a SRR1616919 -f 11 -l 20 -o a head.1.fq head.2.fq
```

Print the first 10 reads of SRR1616919 to stdout:

```
align.py -a SRR1616919 -M 10 -p head
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

Call variants with mpileup...:

```
varcallers.py 	--caller mpileup \
		--samtools PATH_TO/samtools \
		--bam mybam.bam \
		--out OUTFILE.vcf \
                --index hg38.fa \
		--regions clinvar.chr.bed 
		```

...or with GATK:

```
varcallers.py 	--caller gatk \
		--gatk PATH_TO/GenomeAnalysisTK.jar \
		--bam mybam.bam \
		--out OUTDIR \
		--index hg38.fa \
		--regions clinvar.chr.bed \
		--indels Mills_and_1000G_gold_standard.indels.hg38.vcf.gz \
		--dbsnp Homo_sapiens_assembly38.dbsnp.vcf.gz \
		--mem 16 --threads 12
```

## Expressed variant calling

#### Usage

Install the alignment tools as above, and the run the 'run_pipeline.sh' script in the 'scripts' directory.
