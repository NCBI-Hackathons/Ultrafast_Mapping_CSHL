#!/usr/bin/python

import tabix as tb
import sys, subprocess, os
import multiprocessing as mp
import collections, itertools
import ConfigParser
import argparse
import time

parser = argparse.ArgumentParser(description="Annotate VCF with RefSeq Genes Example: ./VarRefSeqAnnotation.py -feature gene -gff test_RefSeq.gff -vcf dbSNP_147_GRCh38.vcf.gz -asm GCF_000001405.35.assembly.txt")
parser.add_argument("-gff", help="input RefSeq gff file")
parser.add_argument("-vcf", help="input VCF file")
parser.add_argument("-feature", help="feature name to Annotate, must be in gff file",type=str,default=None)
parser.add_argument("-np", help="number of processes",type=int,default=2)
parser.add_argument("-asm", help="input assembly info text file (ie. /home/data/GCF_000001405.35.assembly.txt", type=str,default=None)

args = parser.parse_args()

def splitline(l):
  data = None
  if not(len(l.strip()) == 0):
    data = l.strip().split("\t")
  return data

def getAsmInfo():
  asm = open(args.asm, 'r')
  asminfo = {}
  for line in asm:
    if line[0] == "#" or len(line.strip()) == 0:
      continue
    d = splitline(line)
    asminfo[d[6]] = d[0] 
  return asminfo

class gffChunk:
  def __init__(self, gff, vcf, feature):
    self.vcf = vcf
    self.gff = open(gff, 'r')
    self.feature = feature

  def __iter__(self):
    return self

  def next(self):
    line = self.gff.readline()
    while line:
      if line[0] == "#" or len(line.strip()) == 0:
        line = self.gff.readline()
        continue
      data = line.strip().split("\t")
      if data[2] == self.feature:
        lines = []
        if data[0] in chrAcc:
          chrnum = chrAcc[data[0] ]
          res = tb.open(self.vcf).query(chrnum,int(data[3])-1,int(data[4])+1)
          for r in res:
            r[7] = r[7] + ';' + data[8]
            lines.append(r)
          return (lines)
      line = self.gff.readline()
    raise StopIteration


def process_chunk(chunk):
    return chunk
  
 
results = None
start = time.time()
print ("loading and annotating variants..." + str(args.np) + ' processes' )

chrAcc = getAsmInfo()

if (args.gff and not args.feature) or (args.feature and not args.gff):
  print ("Must specify both gff and feature if either argument is used")
  print ("Use -feature and -gff arguments")
  sys.exit(0)


outfile = open(args.vcf + '.out', 'w')
p = mp.Pool(processes = args.np)
if args.feature:
  for r in p.map(process_chunk, gffChunk(args.gff, args.vcf, args.feature), 100):
      for l in r:
        outfile.write("\t".join(l) + "\n")
 
        
print "time to finish: " + str(time.time() - start)