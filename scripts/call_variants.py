#!/usr/bin/env python
from argparse import ArgumentParser
import os
from evac.varcallers import run_caller, list_callers

# Main

def main(script_dir):
    parser = ArgumentParser()
    parser.add_argument(
        '-b', '--bam',
        default='-', metavar="PATH",
        help="Location of the BAM file")
    parser.add_argument(
        '-o', '--output',
        default="-", metavar="PATH",
        help="Directory to output.")
    parser.add_argument(
        '-c', '--caller',
        choices=list_callers(), default='mpileup',
        help="The caller pipeline to use")
    parser.add_argument(
        '-r', '--index',
        default=None, metavar="PATH",
        help="Genome index to use for alignment")
    parser.add_argument(
        '-t', '--threads',
        type=int, default=10, metavar="N",
        help="Number of threads to use for 'gatk'")
    parser.add_argument(
        '-m', '--mem',
        type=int, default=1, metavar="N",
        help="Memory in GB to use for 'gatk'")
    parser.add_argument(
        '-L', '--regions',
        default=None, metavar="PATH",
        help="A BED file to limit the calling space")
    parser.add_argument(
        '--dbsnp',
        default=None, metavar="PATH",
        help="Path to the dbsnp VCF file for 'gatk'")
    parser.add_argument(
        '--indels',
        default=None, metavar="PATH",
        help="Path to the golden indels VCF file for 'gatk'")
    parser.add_argument(
        '--java',
        default="java", metavar="PATH",
        help="Absolute path to the 'java' JRE executable ")
    parser.add_argument(
        '--gatkpath',
        default="GenomeAnalysisTK.jar", metavar="PATH",
        help="Absolute path to the GATK jar")
    parser.add_argument(
        '--samtools',
        default="samtools", metavar="PATH",
        help="Absolute path to the samtools executable")
    parser.add_argument(
        '--caller-args',
        default="", metavar="ARGS",
        help="String of additional arguments to pass to the caller")
    parser.add_argument(
        '--temp-dir',
        default=None, metavar="DIR",
        help="The root directory to use for temporary files/directories")
    parser.add_argument(
        '--log-file',
        default=None, metavar="FILE",
        help="File for log messages (defaults to stdout)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--log-level',
        default="ERROR", metavar="LEVEL",
        help="Logging level")
    group.add_argument(
        '-q', '--quiet',
        action='store_true', default=False,
        help="Only write error messages (equivalent to "
            "--log-level ERROR --no-progress)")
    
    # Paths to callers
    # TODO: move this into a config file
    parser.add_argument('--gatk')
    parser.add_argument('--mpileup')
    
    run_pipeline(parser.parse_args(), script_dir)

if __name__ == "__main__":
    main(os.path.dirname(__file__))
