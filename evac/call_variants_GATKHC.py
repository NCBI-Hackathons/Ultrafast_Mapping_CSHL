#!/bin/env python
import sys
from evac.utils import TempDir

JAVA=sys.argv[1]
GATK_JAR=sys.argv[2]
GATK_MEM=sys.argv[3]
REF=sys.argv[4]
BAM=sys.argv[5]
DBSNP_VCF=sys.argv[6]
INTERVALS=sys.argv[7]
OUTDIR=sys.argv[8]
GOLD_INDELS=sys.argv[9]
THREADS=sys.argv[10]
samtools=sys.argv[11]

import os.path
import subprocess
import re


OUTNAME=os.path.splitext(BAM)[0]
interval_files=[]

#get the header of the bam file
print([samtools, "view", "-H", BAM])

proc=subprocess.Popen([samtools, "view", "-H", BAM],stdout=subprocess.PIPE,universal_newlines=True)
header=""
contigs=[]
contig_count=0
#pull the header from the bam with the contigs and their length
while True:
  line = proc.stdout.readline()
  if line != '':
    header+=line
    m = re.match('^@SQ.*SN:(.*)\s+LN:(.*)\s*.*', line)
    if m:
      contig_count+=1
      contigs.append("\t".join([m.group(1), "1", m.group(2), "+", m.group(1)]))
  else:
    break

#create interval files for GATK parallelizing
#we create Picard-format files instead of providing on the command line because
#GRCh38 has contigs with colons : in them, which GATK will choke on

from math import ceil

parallelize=ceil(contig_count/int(THREADS))
print(" ".join(["splitting into chunks of", str(parallelize), "contigs"]))
with TempDir() as workdir:
    incount=1
    while len(contigs)>0:
        outfile=workdir.make_path(OUTNAME+str(incount)+".list")
        interval_files.append(outfile)
        with open(outfile, 'w') as i:
          i.write(header)
          for x in range(0,parallelize):
            line=contigs.pop()
            i.write(line+"\n")
            if len(contigs)==0:
                break
        incount+=1

    CMD=[JAVA, "-jar", "-Xmx"+GATK_MEM, GATK_JAR,
        "-R", REF,
        "-T", "HaplotypeCaller",
        "-I", BAM,
        "--emitRefConfidence", "GVCF",
        "--dbsnp", DBSNP_VCF,
        "-L",INTERVALS,
        "-U","ALLOW_N_CIGAR_READS","-nct", THREADS]
    #Call variants by splitting using those interval files
    gvcf_files=[]
    cmds=[]
    for f in interval_files:
        gvcf=workdir.make_path(OUTNAME+str(len(gvcf_files))+".g.vcf")
        gvcf_files.append(gvcf)
        hc_cmd=list(CMD)
        hc_cmd.append("-o")
        hc_cmd.append(gvcf)
        hc_cmd.append("-L")
        hc_cmd.append(f)
        cmds.append(hc_cmd)
    def hapcall(cmd_seq):
        with subprocess.Popen(cmd_seq,stdout=sys.stdout,bufsize=1) as proc:
            proc.wait()

    from multiprocessing import Pool
    p = Pool(int(THREADS))
    p.map(hapcall,cmds)
 
#Combine the separate GVCFs together
#if necessary
CMD=[ JAVA, "-jar", "-Xmx"+GATK_MEM, GATK_JAR,
     "-R", REF,
   "-T", "CombineGVCFs",
   "-o",os.path.join(OUTDIR,OUTNAME+".g.vcf") ]

for f in gvcf_files:
  CMD.append("--variant")
  CMD.append(f)
with subprocess.Popen(CMD,stdout=sys.stdout,bufsize=1) as proc:
    proc.wait()
