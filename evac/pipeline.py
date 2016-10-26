# -*- coding: utf-8 -*-
"""Aligner-agnostic alignment pipeline that reads from SRA.
"""
from inspect import inclass
import logging
import shlex
from subprocess import Popen, PIPE
from evac.utils import *

log = logging.getLogger()

# Pipelines

# TODO: [JD] These have lots of redundant code right now. I will be adding
# alternate readers for local FASTQ and SAM/BAM/CRAM files and refactoring the
# Pipelines to accept an arbitrary reader.

# TODO: [JD] Pipe stderr of pipelines to logger

def stream_sra_reads(script_dir, args, progress, fifo1, fifo2):
    script = os.path.join(script_dir, "stream_sra.py")
    cmd = shlex.split("""
        {exe} {script} -a {accn} --batch-size {batch_size}
            {max_reads} {progress} {fifo1} {fifo2}
    """.format(
        exe=sys.executable,
        script=script,
        accn=args.sra_accession,
        max_reads='--max-reads {}'.format(args.max_reads) if args.max_reads else '',
        batch_size=args.batch_size,
        progress='--progress' if progress else '',
        fifo1=fifo1,
        fifo2=fifo2))
    return Popen(cmd)

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
    def __init__(self, script_dir):
        self.script_dir = script_dir
    
    def __call__(self, args):
        with TempDir(dir=args.temp_dir) as workdir:
            fifo1, fifo2 = workdir.mkfifos('Read1', 'Read2')
            progress = args.progress and (
                not args.quiet or args.log_level == 'ERROR' or args.log_file)
            sra_proc = stream_sra_reads(
                self.script_dir, args, progress, fifo1, fifo2)
            with self.align(args) as align_proc:
                for proc in (sra_proc, align_proc):
                    proc.wait()

class StarPipeline(SraPipeline):
    def align(self, args):
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
    def align(self, args):
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
    def align(self, args):
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
    fq1_path = args.output + '.1.fq'
    fq2_path = args.output + '.2.fq'
    with open(fq1_path, 'wt') as fq1, open(fq2_path, 'wt') as fq2:
        for read1, read2 in sra_reader(
                args.sra_accession,
                batch_size=args.batch_size,
                max_reads=args.max_reads):
            fq1.write("@{}\n{}\n+\n{}\n".format(*read1))
            fq2.write("@{}\n{}\n+\n{}\n".format(*read2))

def head_pipeline(args):
    for read1, read2 in sra_reader(
            args.sra_accession,
            batch_size=args.batch_size,
            max_reads=args.max_reads or 10,
            progress=False):
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

def run_pipeline(args, script_dir):
    """Run a pipeline using a set of command-line args.
    
    Args:
        args: a Namespace object
    """
    setup_logging(args)
    pipeline = pipelines[args.pipeline]
    if isclass(pipeline):
        pipeline = pipeline(script_dir)
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
