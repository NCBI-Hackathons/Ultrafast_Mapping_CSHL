#! /bin/bash

set -e -o pipefail

bash call_variants.sh 
	/usr/lib/jvm/jdk-8-oracle-x64/jre/bin/java \
	/opt/gatk/GenomeAnalysisTK.jar \
	16G  \
	/home/data/GCF_000001405.35_GRCh38.p9_genomic.fna \
	${BAM} \
	/home/data/dbsnp \
	/home/data/intervals \
	/home/data/vcf	\
	/home/data/indels


