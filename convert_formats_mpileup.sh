#! /bin/bash

VCF=$1
COU=$2
INT=$3

CMD="grep -v "#" ${COU} | grep -v "Geneid" > ${COU}.bed"
CMD="awk '{printf("%s\t%s\t%s\t%s\t%s\t%s\t%s\n",$2,$3,$4,$5,$6,$7,$1)}' ${COU}.bed > ${COU}.mod.bed"
CMD="grep -v "chrX;chrY" ${COU}.mod.bed > ${COU}.mod2.bed"
CMD="vcf2bed < ${VCF} > ${VCF}.bed"
CMD="grep -v "<*>" ${VCF}.bed > temp && mv temp ${VCF}.bed"
CMD="intersectBed -a ${VCF}.bed -b ${COU}.mod2.bed -wa -wb > intersect.bed"
CMD="cut -f 1,2,3,17,18 intersect.bed > ${INT}"

echo $CMD
eval $CMD
