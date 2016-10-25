#! /bin/bash

set -e -o pipefail

BAM=$1

CMD="/usr/bin/python3 /home/devsci2/Ultrafast_Mapping_CSHL/pipeline/src/call_variants_GATKHC.py /usr/lib/jvm/jdk-8-oracle-x64/jre/bin/java /opt/gatk/GenomeAnalysisTK.jar 16G /home/data/GCF_000001405.35_GRCh38.p9_genomic.fna ${BAM} /home/data/hg38bundle/Homo_sapiens_assembly38.dbsnp.vcf.gz /home/data/bed/Hsapiens_UCSC_hg38_knownGene.bed /home/data/vcf /home/data/hg38bundle/Mills_and_1000G_gold_standard.indels.hg38.vcf.gz 12 /opt/samtools/1.3.1/bin/samtools"

echo $CMD
eval $CMD

