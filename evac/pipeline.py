# -*- coding: utf-8 -*-
"""Aligner-agnostic alignment pipeline that reads from SRA.
"""
from contextlib import contextmanager
import copy
import logging
import os
import shlex
from subprocess import Popen, PIPE

from evac.utils import *

from ngs import NGS
from ngs.Read import Read
from ngs.ErrorMsg import ErrorMsg

log = logging.getLogger()

# Readers

def sra_read_pair(read_pair):
    """Creates a pair of tuples (name, sequence, qualities) from the current
    read of an ngs.ReadIterator.
    """
    read_name = read_pair.getReadName()
    if read_pair.getNumFragments() != 2:
        raise Exception("Read {} is not paired".format(read_name))
        
    read_group = read_pair.getReadGroup()
    
    read_pair.nextFragment()
    if not read_pair.isPaired():
        raise Exception("Read {} is not paired".format(read_name))
    read1 = (
        read_name,
        read_pair.getFragmentBases(),
        read_pair.getFragmentQualities())
    
    read_pair.nextFragment()
    if not read_pair.isPaired():
        raise Exception("Read {} is not paired".format(read_name))
    read2 = (
        read_name,
        read_pair.getFragmentBases(),
        read_pair.getFragmentQualities())
    
    return (read1, read2)

def sra_reader(accn, batch_size=1000, max_reads=None, progress=True):
    """Iterates through a read collection for a given accession number using
    the ngs-lib python bindings.
    
    Args:
        accn: The accession number
        batch_size: The maximum number of reads to request in each call to SRA
        max_reads: The total number of reads to process, or all reads in the
            SRA run if None
    
    Yields:
        Each pair of reads (see ``sra_read_pair``)
    """
    def run_iter(run, max_reads):
        run_name = run.getName()
        for batch_num, first_read in enumerate(
                range(1, max_reads, batch_size)):
            cur_batch_size = min(
                batch_size,
                max_reads - first_read + 1)
            with run.getReadRange(
                    first_read, cur_batch_size, Read.all) as read:
                for read_idx in range(cur_batch_size):
                    read.nextRead()
                    yield sra_read_pair(read)
    
    with NGS.openReadCollection(accn) as run:
        read_count = run.getReadCount()
        if max_reads:
            max_reads = min(read_count, max_reads)
        else:
            max_reads = read_count
        itr = run_iter(run, max_reads)
        for read_pair in wrap_progress(itr, disable=not progress, total=max_reads):
            yield read_pair

# Writers

class BatchWriter(object):
    """Wrapper for a string writer (e.g. FifoWriter) that improves performance
    by buffering a set number of reads and sending them as a single call to the
    string writer.
    
    Args:
        writer: The string writer to wrap. Must be callable with two arguments
            (read1 string, read2 string)
        batch_size: The size of the read buffer
        lines_per_row: The number of lines used by each read for the specific
            file format (should be passed by the subclass in a
            super().__init__ call)
        linesep: The separator to use between each line (defaults to os.linesep)
    """
    def __init__(self, writer, batch_size, lines_per_row, linesep=os.linesep):
        self.writer = writer
        self.batch_size = batch_size
        self.lines_per_row = lines_per_row
        self.bufsize = batch_size * lines_per_row
        self.linesep = linesep
        self.read1_batch = self._create_batch_list()
        self.read2_batch = copy.copy(self.read1_batch)
        self.index = 0
    
    def _create_batch_list(self):
        """Create the list to use for buffering reads. Can be overridden, but
        must return a list that is of size ``batch_size * lines_per_row``.
        """
        return [None] * self.bufsize
    
    def __call__(self, read1, read2):
        """Add a read pair to the buffer. Writes the batch to the underlying
        writer if the buffer is full.
        
        Args:
            read1: read1 tuple (name, sequence, qualities)
            read2: read2 tuple
        """
        print('add 1 {}'.format(read1[0]))
        self.add_to_batch(*read1, self.read1_batch, self.index)
        print('add 2 {}'.format(read2[0]))
        self.add_to_batch(*read2, self.read2_batch, self.index)
        self.index += self.lines_per_row
        if self.index >= self.bufsize:
            print('flush')
            self.flush()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        print(exception_type)
        print(exception_value)
        print(traceback)
        if self.index > 0:
            self.flush()
        self.close()
    
    def flush(self):
        """Flush the current read buffers to the underlying string writer.
        
        Args:
            last: Is this the last call to flush? If not, a trailing linesep
                is written.
        """
        if self.index < self.bufsize:
            self.writer(
                self.linesep.join(self.read1_batch[0:self.index]),
                self.linesep.join(self.read2_batch[0:self.index]))
        else:
            self.writer(
                self.linesep.join(self.read1_batch),
                self.linesep.join(self.read2_batch))
        self.writer(self.linesep, self.linesep)
        self.index = 0
    
    def close(self):
        """Clear the buffers and close the underlying string writer.
        """
        self.read1_batch = None
        self.read2_batch = None
        self.writer.close()

class FastqWriter(BatchWriter):
    """BatchWriter implementation for FASTQ format.
    """
    def __init__(self, writer, batch_size):
        super(FastqWriter, self).__init__(writer, batch_size, 4)
    
    def _create_batch_list(self):
        return [None, None, '+', None] * self.batch_size
    
    def add_to_batch(self, name, sequence, qualities, batch, index):
        batch[index] = '@' + name
        batch[index+1] = sequence
        batch[index+3] = qualities

class FifoWriter(object):
    """String writer that opens and writes to a pair of FIFOs.
    
    Args:
        fifo1: Path to the read1 FIFOs
        fifo2: Path to the read2 FIFOs
        kwargs: Additional arguments to pass to the ``open`` call.
    """
    def __init__(self, fifo1, fifo2, **kwargs):
        self.fifo1 = open(fifo1, 'wt', **kwargs)
        self.fifo2 = open(fifo2, 'wt', **kwargs)
    
    def __call__(self, read1_str, read2_str):
        self.fifo1.write(read1_str)
        self.fifo2.write(read2_str)
    
    def close(self):
        for fifo in (self.fifo1, self.fifo2):
            fifo.flush()
            fifo.close()

# Pipelines

# TODO: [JD] These have lots of redundant code right now. I will be adding
# alternate readers for local FASTQ and SAM/BAM/CRAM files and refactoring the
# Pipelines to accept an arbitrary reader.

# TODO: [JD] Pipe stderr of pipelines to logger

def star_pipeline(args):
    progress = args.progress and (
        not args.quiet or args.log_level == 'ERROR' or args.log_file)
    with TempDir(dir=args.temp_dir) as workdir:
        fifo1, fifo2 = workdir.mkfifos('Read1', 'Read2')
        with open_(args.output, 'wb') as bam:
            cmd = shlex.split("""
                {exe} --runThreadN {threads} --genomeDir {index}
                    --readFilesIn {fifo1} {fifo2}
                    --outSAMtype BAM SortedByCoordinate
                    --outStd BAM_SortedByCoordinate
                    --outMultimapperOrder Random
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
            with Popen(cmd, bufsize=1, stdout=bam, universal_newlines=True) as proc:
                with FastqWriter(FifoWriter(fifo1, fifo2), args.batch_size) as writer:
                    for read_pair in sra_reader(
                            args.sra_accession,
                            batch_size=args.batch_size,
                            max_reads=args.max_reads,
                            progress=progress):
                        writer(*read_pair)
                if progress:
                    print("\nWaiting for STAR to finish...")
                proc.communicate()

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

def kallisto_pipeline(args):
    with TempDir(dir=args.temp_dir) as workdir:
        fifo1, fifo2 = workdir.mkfifos('Read1', 'Read2')
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
        with Popen(cmd) as proc:
            with FastqWriter(FifoWriter(fifo1, fifo2), args.batch_size) as writer:
                for read_pair in sra_reader(
                        args.sra_accession,
                        batch_size=args.batch_size,
                        max_reads=args.max_reads):
                    writer(*read_pair)
            proc.wait()

def salmon_pipeline(args):
    with TempDir(dir=args.temp_dir) as workdir:
        fifo1, fifo2 = workdir.mkfifos('Read1', 'Read2')
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
        with Popen(cmd) as proc:
            with FastqWriter(FifoWriter(fifo1, fifo2), args.batch_size) as writer:
                for read_pair in sra_reader(
                        args.sra_accession,
                        batch_size=args.batch_size,
                        max_reads=args.max_reads):
                    writer(*read_pair)
            proc.wait()

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
    star=star_pipeline,
    hisat=hisat_pipeline,
    kallisto=kallisto_pipeline,
    salmon=salmon_pipeline,
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
    pipeline(args)

def setup_logging(args):
    if not logging.root.handlers:
        level = 'ERROR' if args.quiet else getattr(logging, args.log_level)
        if args.log_file:
            handler = logging.FileHandler(args.log_file)
        else:
            handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        handler.setLevel(level)
        logging.getLogger().setLevel(level)
        logging.getLogger().addHandler(handler)
