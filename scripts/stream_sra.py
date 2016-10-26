#!/usr/bin/env python
from argparse import ArgumentParser
from evac.sra import *
from evac.writers import *

def stream_sra_reads(args):
    bufsize = args.batch_size * 1024
    writer = FastqWriter(
        FileWriter(args.fastq1, args.fastq2, bufsize),
        args.batch_size)
    with writer:
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
    parser.add_argument('fastq1', help="Output file for fastq1")
    parser.add_argument('fastq2', help="Output file for fastq2")
    args = parser.parse_args()
    stream_sra_reads(args)

if __name__ == "__main__":
    main()
