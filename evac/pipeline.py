# -*- coding: utf-8 -*-
"""Aligner-agnostic alignment pipeline that reads from SRA.
"""
from contextlib import contextmanager
from inspect import isclass
import logging
import shlex
from multiprocessing import Process
from subprocess import Popen
from srastream import SraReader, sra_dump
from srastream.utils import Batcher
import sys
from xphyle import open_
from xphyle.paths import TempDir

log = logging.getLogger()

# Pipelines

# TODO: [JD] These are just default pipelines. Version 2 will enable pipelines
# to be built from CWL descriptions using toil.

# TODO: [JD] These have lots of redundant code right now. I will be adding
# alternate readers for local FASTQ and SAM/BAM/CRAM files and refactoring the
# pipelines to accept an arbitrary reader.

# TODO: [JD] Pipe stderr of pipelines to logger

# TODO: [JD] Incorporate compressive mapping code from CORA
# https://github.com/jdidion/cora/blob/master/manual.txt
# http://bioinformatics.oxfordjournals.org/content/32/20/3124.short

# TODO: [JD] Incorporate qtip MAPQ correction?
# https://github.com/BenLangmead/qtip

# TODO: [JD] Aligner "boosting"
# https://github.com/Grice-Lab/AlignerBoost

class SraDump(Process):
    """Process to dump SRA reads to FIFOs.
    """
    def __init__(self, args, prefix, progress):
        self.args = args
        self.prefix = prefix
        self.progress = progress
        
    def run(self):
        sra_dump(
            self.args.sra_accession, self.prefix, 
            compression=self.args.compression,
            progress=self.progress,
            batch_size=self.args.batch_size, 
            max_reads=self.args.max_reads)

# TODO: [JD] The use of pipes and shell=True is insecure and not the recommended
# way of doing things, but I want to benchmark the alternative (chained Popens)
# to make sure it's not any slower.

def hisat_pipeline(args):
    with open_(args.output, 'wb') as bam:
        cmd = shlex.split("""
            {exe} -p {threads} -x {index} --sra-acc {accn} {extra}
                | sambamba view -S -t {threads} -f bam /dev/stdin
                | sambamba sort -t {threads} /dev/stdin
        """.format(
            exe=args.hisat2 or "hisat2",
            accn=args.sra_accession,
            threads=args.threads,
            index=args.index,
            extra=args.aligner_args
        ))
        log.info("Running command: {}".format(' '.join(cmd)))
        with Popen(cmd, stdout=bam, shell=True) as proc:
            proc.wait()

class SraPipeline(object):
    def __call__(self, args):
        with TempDir(dir=args.temp_dir) as workdir:
            progress = args.progress and (
                not args.quiet or args.log_level == 'ERROR' or args.log_file)
            sra_proc = SraDump(args, "fifo", progress)
            with self.align(args, "fifo.1.fq", "fifo.2.fq") as align_proc:
                for proc in (sra_proc, align_proc):
                    proc.wait()
    
    def align(self, args, fifo1, fifo2):
        raise NotImplementedError()

class StarPipeline(SraPipeline):
    @contextmanager
    def align(self, args, fifo1, fifo2):
        with open_(args.output, 'wb') as bam:
            cmd = shlex.split("""
                {exe} --runThreadN {threads} --genomeDir {index}
                    --readFilesIn {fifo1} {fifo2}
                    --outSAMtype BAM SortedByCoordinate
                    --outStd BAM_SortedByCoordinate
                    --outMultimapperOrder Random
                    --outSAMunmapped Within KeepPairs
                    {extra}
            """.format(
                exe=args.star or "STAR",
                threads=args.threads,
                index=args.index,
                fifo1=fifo1,
                fifo2=fifo2,
                extra=args.aligner_args
            ))
            log.info("Running command: {}".format(' '.join(cmd)))
            yield Popen(cmd, stdout=bam)

class KallistoPipeline(SraPipeline):
    @contextmanager
    def align(self, args, fifo1, fifo2):
        libtype = ''
        if 'F' in args.libtype:
            libtype = '--fr-stranded'
        elif 'R' in args.libtype:
            libtype = '--rf-stranded'
        cmd = shlex.split("""
            {exe} quant -t {threads} -i {index} -o {output}
                {libtype} {extra} {fifo1} {fifo2}
        """.format(
            exe=args.kallisto or "kallisto",
            threads=args.threads,
            index=args.index,
            output=args.output,
            libtype=libtype,
            extra=args.aligner_args,
            fifo1=fifo1,
            fifo2=fifo2))
        log.info("Running command: {}".format(' '.join(cmd)))
        yield Popen(cmd)

class SalmonPipeline(SraPipeline):
    @contextmanager
    def align(self, args, fifo1, fifo2):
        cmd = shlex.split("""
            {exe} quant -p {threads} -i {index} -l {libtype}
                {extra} -1 {fifo1} -2 {fifo2} -o {output}
        """.format(
            exe=args.salmon or 'salmon',
            threads=args.threads,
            index=args.index,
            libtype=args.libtype,
            output=args.output,
            extra=args.aligner_args,
            fifo1=fifo1,
            fifo2=fifo2))
        log.info("Running command: {}".format(' '.join(cmd)))
        yield Popen(cmd)

def sra_to_fastq_pipeline(args):
    """Just dump reads from SRA to fastq files.
    """
    sra_dump(
        args.sra_accession, args.output, compression=args.compression, 
        batch_size=args.batch_size, max_reads=args.max_reads)

def head_pipeline(args):
    """Just print the first ``max_reads`` reads.
    """
    batcher = Batcher(
        item_limit=args.max_reads or 10,
        batch_size=args.batch_size,
        progress=False)
    for read1, read2 in SraReader(args.sra_accession, batcher):
        print(read1[0] + ':')
        print('  ' + '\t'.join(read1[1:]))
        print('  ' + '\t'.join(read2[1:]))

pipelines = dict(
    hisat=hisat_pipeline,
    star=StarPipeline,
    kallisto=KallistoPipeline,
    salmon=SalmonPipeline,
    fastq=sra_to_fastq_pipeline,
    head=head_pipeline)

# Main interface

def list_pipelines():
    """Returns the currently supported pipelines.
    
    Returns:
        A list of pipeline names
    """
    return list(pipelines.keys())

def run_pipeline(args):
    """Run a pipeline using a set of command-line args.
    
    Args:
        args: a Namespace object
    """
    setup_logging(args)
    pipeline = pipelines[args.pipeline]
    if isclass(pipeline):
        pipeline = pipeline()
    pipeline(args)

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
