#!/bin/bash

JAVA=$1
GATK_JAR=$2
GATK_MEM=$3
REF=$4
BAM=$5
DBSNP_VCF=$6
INTERVALS=$7
OUTDIR=$8
GOLD_INDELS=$9
THREADS=${10}

OUTNAME=`basename ${BAM} .bam`

CMD="${JAVA} -jar -Xmx${GATK_MEM} ${GATK_JAR} \
     -R ${REF} \
     -T HaplotypeCaller \
     -I ${BAM} \
     --emitRefConfidence GVCF \
     --dbsnp ${DBSNP_VCF} \
     -o ${OUTDIR}/${OUTNAME}.vcf \
     -variant_index_type LINEAR -variant_index_parameter 128000  -U ALLOW_N_CIGAR_READS -nct ${THREADS}"
#    -L ${INTERVALS} \

echo "${CMD}"
eval "${CMD}"




