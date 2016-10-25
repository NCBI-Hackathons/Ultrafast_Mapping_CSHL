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

OUT1="${OUTDIR}/${OUTNAME}.split.bam"
CMD="${JAVA} -Xms${GATK_MEM} -jar ${GATK_JAR} \
	-T SplitNCigarReads \
	-R ${REF} \
	-I ${BAM} \
	-o ${OUT1} \
	-rf ReassignOneMappingQuality \
	-RMQF 255 -RMQT 60 -U ALLOW_N_CIGAR_READS"

echo "${CMD}"
eval "${CMD}"

OUT2="${OUTDIR}/${OUTNAME}.rnaseq.vcf"
CMD="${JAVA} -jar -Xmx${GATK_MEM} ${GATK_JAR} \
     -R ${REF} \
     -T HaplotypeCaller \
     -I ${OUT1} \
     --emitRefConfidence GVCF \
     --dbsnp ${DBSNP_VCF} \
     -o ${OUT2} \
     -dontUseSoftClippedBases \
     -stand_call_conf 20.0 -stand_emit_conf 20.0 \
     -variant_index_type LINEAR -variant_index_parameter 128000  -U ALLOW_N_CIGAR_READS -nct ${THREADS}"

#    -L ${INTERVALS} \


echo "${CMD}"
eval "${CMD}"



