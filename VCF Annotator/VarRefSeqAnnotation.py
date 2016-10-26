import tabix as tb
import sys, subprocess, os
import multiprocessing as mp
import collections, itertools
import ConfigParser
import argparse
import time

parser = argparse.ArgumentParser(description="Annotate VCF with RefSeq Genes")
parser.add_argument("-gff3", help="input RefSeq GFF3 file")
parser.add_argument("-vcf", help="input VCF file")
parser.add_argument("-feature", help="feature name to Annotate, must be in gff3 file",type=str,default=None)
args = parser.parse_args()

chrAcc = {
  'NC_000001.11': '1',
  'NC_000002.12': '2',
  'NC_000003.12':'3',
  'NC_000004.12':'4',
  'NC_000005.10':'5',
  'NC_000006.12':'6',
  'NC_000007.14':'7',
  'NC_000008.11':'8',
  'NC_000009.12':'9',
  'NC_000010.11':'10',
  'NC_000011.10':'11',
  'NC_000012.12':'12',
  'NC_000013.11':'13',
  'NC_000014.9':'14',
  'NC_000015.10':'15',
  'NC_000016.10':'16',
  'NC_000017.11':'17',
  'NC_000018.10':'18',
  'NC_000019.10':'19',
  'NC_000020.11':'20',
  'NC_000021.9':'21',
  'NC_000022.11':'22',
  'NC_000023.11':'X',
  'NC_000024.10':'Y'} 


class gffChunk:
  def __init__(self, gff3, vcf, feature):
    self.vcf = vcf
    self.gff3 = open(gff3, 'r')
    self.feature = feature

  def __iter__(self):
    return self

  def next(self):
    line = self.gff3.readline()

    while line:
      if line[0] == "#" or len(line.strip()) == 0:
        line = self.gff3.readline()
        continue
      #print(line)
      data = line.strip().split("\t")
      if data[2] == self.feature:
        #print line
        lines = []
        if data[0] in chrAcc:
          chrnum = chrAcc[data[0] ]
          #print(line)
          #print (chrnum,int(data[3])-1,int(data[4])+1)
          res = tb.open(self.vcf).query(chrnum,int(data[3])-1,int(data[4])+1)
          for r in res:
            
            r[7] = r[7] + ';' + data[8]
            lines.append(r)
            #print (r)
          return (lines)
      line = self.gff3.readline()
    raise StopIteration


def process_chunk(chunk):
    #print(chunk)
    return chunk
  
 
results = None
start = time.time()
print ("loading and annotating variants...")
if (args.gff3 and not args.feature) or (args.feature and not args.gff3):
  print ("Must specify both gff3 and feature if either argument is used")
  print ("Use -feature and -gff3 arguments")
  sys.exit(0)


outfile = open(args.vcf + '.' + args.feature, 'w')
p = mp.Pool(processes = 2)
if args.feature:
  #FeatureChunk(args.gff3, args.vcf, args.feature)
  for r in p.map(process_chunk, gffChunk(args.gff3, args.vcf, args.feature), 5):
      for l in r:
        outfile.write("\t".join(l))

           # f.write(l+"\n")
 
        
print "time to finish: " + str(time.time() - start)
