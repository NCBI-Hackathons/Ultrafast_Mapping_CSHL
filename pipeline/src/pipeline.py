
from contextlib import contextmanager
import os
from subprocess import Popen, PIPE

from pipeline.utils import *

from ngs import NGS
from ngs.Read import Read
from ngs.ErrorMsg import ErrorMsg

# Readers

def sra_read_pair(read_pair):
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

def sra_reader(accn, batch_size=5000, max_reads=None):
    with NGS.openReadCollection(accn) as run:
        run_name = run.getName()
        read_count = run.getReadCount()
        if max_reads:
            max_reads = min(read_count, max_reads)
        else:
            max_reads = read_count
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

# Writers

def fastq(name, sequence, qualities):
    return "@{name}\n{sequence}\n+\n{qualities}\n".format(
        name, sequence, qualities)

class FifoWriter(object):
    def __init__(self, fifo1, fifo2, read_format, **kwargs):
        self.fifo1 = open(fifo1, 'wt', **kwargs)
        self.fifo2 = open(fifo2, 'wt', **kwargs)
        self.read_format = read_format
    
    def __call__(self, read1, read2):
        self.fifo1.write(self.read_format(*read1))
        self.fifo2.write(self.read_format(*read2))
    
    def __enter__(self):
        return self
    
    def __exit__(exception_type, exception_value, traceback):
        self.close()
    
    def close(self):
        for fifo in (self.fifo1, self.fifo2):
            try:
                fifo.flush()
                fifo.close()
            finally:
                os.remove(fifo)

# Pipelines

def star_pipeline(args):
    with TempDir() as workdir:
        fifo1, fifo2 = workdir.mkfifos('Read1', 'Read2')
        with open_(args.output_bam, 'wb') as bam:
            cmd = normalize_whitespace("""
                STAR --runThreadN {threads} --genomeDir {index}
                    --readFilesIn {Read1} {Read2}
                    --outSAMtype BAM SortedByCoordinate
                    --outStd BAM SortedByCoordinate
                    --outMultimapperOrder Random
                    {extra}
            """.format(
                threads=args.threads,
                index=args.index,
                Read1=fifo1,
                Read2=fifo2,
                extra=args.aligner_args
            ))
            with Popen(cmd, stdout=bam) as proc:
                with FifoWriter(fifo1, fifo2, fastq) as writer:
                    for read_pair in sra_reader(
                            args.sra_accession,
                            batch_size=args.batch_size,
                            max_reads=args.max_reads):
                        writer(*read_pair)
                proc.wait()

def hisat_pipeline(args):
    with open_(args.output_bam, 'wb') as bam:
        cmd = normalize_whitespace("""
            hisat2 -p {threads} -x {index} --sra-acc {accn} {extra}
                | sambamba view -S -t {threads} -f bam /dev/stdin
                | sambamba sort -t {threads} /dev/stdin
        """.format(
            accn=args.sra_accession,
            threads=args.threads,
            index=args.index,
            extra=args.aligner_args
        ))
        with Popen(cmd, stdout=bam) as proc:
            proc.wait()

def mock_pipeline(args):
    for read1, read2 in sra_reader(
            args.sra_accession,
            batch_size=args.batch_size,
            max_reads=args.max_reads):
        print(read1[0] + ':')
        print('  ' + '\t'.join(read1[1:]))
        print('  ' + '\t'.join(read2[1:]))

pipelines = dict(
    star=star_pipeline,
    hisat=hisat_pipeline,
    mock=mock_pipeline)

# Main interface

def list_pipelines():
    return list(pipelines.keys())

def run_pipeline(args):
    pipeline = pipelines.get(args.pipeline)
    pipeline(args)
