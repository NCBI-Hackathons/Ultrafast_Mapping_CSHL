#! /bin/env python
import sys
bam=sys.argv[1]
cores=sys.argv[2]
samtools="samtools"
import re
import subprocess

proc=subprocess.Popen([samtools, "view", "-H", bam],stdout=subprocess.PIPE)
header=""
contigs=[]

contig_count=0
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

parallelize=(contig_count/int(cores))+1
print " ".join(["splitting into chunks of", str(parallelize), "contigs"])

from os import path

outname=path.basename(bam)

incount=1
while len(contigs)>0:
  with open(outname+str(incount)+".intervals", 'w') as i:
    i.write(header)
    for x in range(0,parallelize):
      line=contigs.pop()
      i.write(line+"\n")
      if len(contigs)==0:
        break
  incount+=1



