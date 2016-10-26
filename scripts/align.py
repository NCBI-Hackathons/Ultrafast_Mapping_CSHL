from argparse import ArgumentParser
from evac.pipeline import run_pipeline, list_pipelines

# Main

def main():
    parser = ArgumentParser()
    parser.add_argument(
        '-a', '--sra-accession',
        default=None, metavar="SRRXXXXXXX",
        help="Accession number of SRA run to align")
    parser.add_argument(
        '-l', '--library-type',
        default="SF", metavar="LIBTYPE",
        help="Library type, as specified by Salmon ( "
            "http://salmon.readthedocs.io/en/latest/salmon.html). "
            "Currently, this argument is only used for Kallisto and Salmon.")
    parser.add_argument(
        '-M', '--max-reads',
        type=int, default=None, metavar="N",
        help="Maximum reads to align")
    parser.add_argument(
        '-o', '--output',
        default="-", metavar="PATH",
        help="Path to output. For 'star' and 'histat' pipelines, this must be "
            "a file (including '-' for stdout). For 'kallisto', this must be a "
            "directory.")
    parser.add_argument(
        '-p', '--pipeline',
        choices=list_pipelines(), default='star',
        help="The alignment pipeline to use")
    parser.add_argument(
        '-r', '--index',
        default=None, metavar="PATH",
        help="Genome idex to use for alignment")
    parser.add_argument(
        '-t', '--threads',
        type=int, default=1, metavar="N",
        help="Number of threads to use for alignment")
    parser.add_argument(
        '--aligner-args',
        default="", metavar="ARGS",
        help="String of additional arguments to pass to the aligner")
    parser.add_argument(
        '--batch-size',
        type=int, default=5000, metavar="N",
        help="Number of reads to process in each batch.")
    args = parser.parse_args()
    run_pipeline(args)

if __name__ == "__main__":
    main()
