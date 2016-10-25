#!/bin/env python
import sys

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

import os.path
import subprocess
import re
import tempfile

tmpdir = tempfile.mkdtemp()

OUTNAME=os.path.splitext(BAM)[0]
interval_files=[]

#get the header of the bam file
proc=subprocess.Popen([samtools, "view", "-H", bam],stdout=subprocess.PIPE)
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
parallelize=(contig_count/int(cores))+1
print " ".join(["splitting into chunks of", str(parallelize), "contigs"])
incount=1
while len(contigs)>0:
  outfile=os.path.join(tmpdir,outname+str(incount)+".intervals")
  interval_files.append(outfile)
  with open(outfile, 'w') as i:
    i.write(header)
    for x in range(0,parallelize):
      line=contigs.pop()
      i.write(line+"\n")
      if len(contigs)==0:
        break
  incount+=1


#Call variants by splitting using those interval files
gvcf_files=[]
for f in interval_files:
  gvcf=os.path.join(tmpdir,OUTNAME+len(gvcf_files)+".g.vcf")
  gvcf_files.append(gvcf)
  CMD=[JAVA, "-jar", "-Xmx"+GATK_MEM, "GATK_JAR",
     "-R", REF,
     "-T", "HaplotypeCaller",
     "-I", BAM,
     "--emitRefConfidence", "GVCF",
     "--dbsnp", DBSNP_VCF,
     "-o", gvcf,
     "-L",f,
     "-U","ALLOW_N_CIGAR_READS","-nct", THREADS]
  print CMD
  proc=subprocess.Popen(CMD,stdout=subprocess.PIPE)
  while True:
    line = proc.stdout.readline()
    if line != '':
      print line.rstrip()
    else:
      break


#Combine the separate GVCFs together 
#if necessary
CMD=[ JAVA, "-jar", "-Xmx"+GATK_MEM, "GATK_JAR",
     "-R", REF,
   "-T", "CombineGVCFs",
   "-o",os.path.join(OUTDIR,OUTNAME+".g.vcf") ]

for f in gvcf_files:
  CMD.append("--variant")
  CMD.append(f)
proc=subprocess.Popen(CMD,stdout=subprocess.PIPE)
while True:
  line = proc.stdout.readline()
  if line != '':
    print line.rstrip()
  else:   
    break

