#!/bin/bash

#1 /usr/lib/jvm/jdk-8-oracle-x64/jre/bin/java
#2 /opt/gatk/GenomeAnalysisTK.jar
#3 16G
#4 /home/data/GCF_000001405.35_GRCh38.p9_genomic.fna
#5 
#6 
#7
#8 /home/data/vcf
#9 

JAVA=$1
GATK_JAR=$2
GATK_MEM=$3
REF=$4
BAM=$5
DBSNP_VCF=$6
INTERVALS=$7
OUTDIR=$8
GOLD_INDELS=$9

OUTNAME=`basename ${BAM} .bam`

if ( $DO_BQRS ) 
then
    #BASE QUALITY SCORE RECALIBRATION
    BQ1="${OUTNAME}.recal.table"

    CMD="${JAVA} -Xmx${GATK_MEM}-jar ${GATK_JAR} \ 
	-T BaseRecalibrator \ 
    	-R ${REF} \ 
    	-I ${BAM} \ 
    	-L 20 \ 
    	-knownSites ${DBSNP_VCF} \ 
    	-knownSites ${GOLD_INDELS} \ 
    	-o ${BQ1} "

    echo "${CMD}"

    BAM2="${OUTNAME}.recal.bam"

    CMD="${JAVA} -Xmx${GATK_MEM} -jar ${GATK_JAR} \ 
	-T PrintReads \ 
	-R ${REF} \ 
	-I ${BAM} \ 
	-L 20 \ 
	-BQSR ${BQ1} \ 
	-o ${BAM2} "

    echo "${CMD}"
    BAM=$BAM2
fi

CMD="${JAVA} -jar -Xmx${GATK_MEM} ${GATK_JAR} \
     -R ${REF} \
     -T HaplotypeCaller \
     -I ${BAM} \
     --emitRefConfidence GVCF \
     --dbsnp ${DBSNP_VCF} \
     -L ${INTERVALS} \
     -o ${OUTDIR}/${OUTNAME}"

echo "${CMD}"




