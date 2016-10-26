#! /bin/bash

SAM=$1
OUT=$2

CMD="hisat2 -p 8 -x /home/data/hg38/genome --sra-acc SRR2056440 --rg-id test1 --rg PU:99.9.Z --rg SM:SAMN03120904 --rg PL:ILLUMINA --rg LB:M407 -S ${SAM}"
CMD="sambamba_v0.6.5 view -S -t 8 -f bam ${SAM} | sambamba_v0.6.5 sort -t 8 -o ${OUT} /dev/stdin"

echo $CMD
eval $CMD
