#!/bin/env python3
import sys
from evac.utils import TempDir
import os.path
import subprocess
import re
import logging

log = logging.getLogger()

def proccall(cmd_seq):
        log.info("Running command: {}".format(' '.join(cmd_seq)))
        with subprocess.Popen(cmd_seq,stdout=sys.stdout,bufsize=1) as proc:
            proc.wait()

def gatk_pipeline(args, script_dir):
    JAVA=args.java          #sys.argv[1]
    GATK_JAR=args.gatk      #sys.argv[2]
    GATK_MEM=args.mem       #sys.argv[3]
    REF=args.index          #sys.argv[4]
    BAM=args.bam            #sys.argv[5]
    DBSNP_VCF=args.dbsnp    #sys.argv[6]
    INTERVALS=args.regions  #sys.argv[7]
    OUTDIR=args.output      #sys.argv[8]
    GOLD_INDELS=args.indels #sys.argv[9]
    THREADS=args.threads    #sys.argv[10]
    samtools=args.samtools  #sys.argv[11]
    caller_args=args.caller_args

    OUTNAME=os.path.splitext(BAM)[0]
    interval_files=[]

    #get the header of the bam file

    CMD=[samtools, "view", "-H", BAM]
    log.info("Running command: {}".format(' '.join(CMD)))
    proc=subprocess.Popen(CMD,stdout=subprocess.PIPE,universal_newlines=True)
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
    log.info("splitting into chunks of {} contigs".format(str(parallelize)))
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

    from multiprocessing import Pool
    p = Pool(int(THREADS))
    p.map(proccall,cmds)
 
    final_gvcf=os.path.join(OUTDIR,OUTNAME+".g.vcf")
    #Combine the separate GVCFs together
    #if necessary
    CMD=[ JAVA, "-jar", "-Xmx"+GATK_MEM, GATK_JAR,
        "-R", REF,
        "-T", "CombineGVCFs",
        "-o", final_gvcf ]
    for f in gvcf_files:
        CMD.append("--variant")
        CMD.append(f)
    proccall(CMD)

    final_vcf=os.path.join(OUTDIR,OUTNAME+".vcf")
    CMD=[ JAVA, "-jar", "-Xmx"+GATK_MEM, GATK_JAR,
        "-R", REF,
        "-T", "GenotypeGVCFs",
        "-V", final_gvcf,
        "-o", final_vcf ]
    proccall(CMD)


###### Running code, largely copied from pipeline.py

callers = dict(
    gatk=gatk_pipeline
    )

def list_callers():
    """Returns the currently supported pipelines.
    
    Returns:
        A list of caller names
    """
    return list(callers.keys())

def run_caller(args, script_dir):
    """Run a caller using a set of command-line args.
    
    Args:
        args: a Namespace object
    """
    setup_logging(args)
    caller = callers[args.caller]
    import time
    start_time = time.time()
    caller(args, script_dir)
    log.info("{} caller -- {} seconds ---".format(args.caller, str(time.time() - start_time))

def setup_logging(args):
    if not logging.root.handlers:
        level = 'ERROR' if args.quiet else getattr(logging, args.log_level)
        if args.log_file:
            handler = logging.FileHandler(args.log_file)
        else:
            handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'))
        handler.setLevel(level)
        logging.getLogger().setLevel(level)
        logging.getLogger().addHandler(handler)