#!/usr/bin/env python
from argparse import ArgumentParser
import os
import stat
from evac.sra import *
from evac.writers import *

def is_fifo(path):
    return os.path.exists(path) and stat.S_ISFIFO(os.stat(path).st_mode)

def stream_sra_reads(args):
    if is_fifo(args.fastq1) and is_fifo(args.fastq2):
        string_writer = FifoWriter(args.fastq1, args.fastq2, args.buffer)
    else:
        string_writer = FileWriter(args.fastq1, args.fastq2)
    with FastqWriter(string_writer, args.batch_size) as writer:
        for read_pair in sra_reader(
                args.sra_accession,
                batch_size=args.batch_size,
                max_reads=args.max_reads,
                progress=args.progress):
            writer(*read_pair)

def main():
    parser = ArgumentParser()
    parser.add_argument(
        '-a', '--sra-accession',
        default=None, metavar="SRRXXXXXXX",
        help="Accession number of SRA run to align")
    parser.add_argument(
        '-M', '--max-reads',
        type=int, default=None, metavar="N",
        help="Maximum reads to align")
    parser.add_argument(
        '--batch-size',
        type=int, default=1000, metavar="N",
        help="Number of reads to process in each batch.")
    parser.add_argument(
        '--progress',
        action='store_true', default=False,
        help="Show a progress bar.")
    parser.add_argument('--buffer', default='pv -q -B 1M')
    parser.add_argument('fastq1', help="Output file for fastq1")
    parser.add_argument('fastq2', help="Output file for fastq2")
    args = parser.parse_args()
    stream_sra_reads(args)

if __name__ == "__main__":
    main()
