#! /bin/bash

ANNO=$1
OUT=$2
BAM=$3

CMD="featureCounts -T 8 -B -C -p -t exon -g gene_id -a ${ANNO} -o ${OUT} ${BAM}"

echo $CMD
eval $CMD
