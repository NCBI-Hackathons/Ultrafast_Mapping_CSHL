align.py -p star -a SRR1616919 -t 8 -r /home/data/star_ncbi_indices_overhang100 --star /opt/star/bin/STAR --temp-dir '.' --batch-size 100 | \
/opt/samtools/1.3.1/bin/samtools view -h - | \
/opt/samtools/1.3.1/bin/samtools mpileup -f /home/data/hg38.fa -l /home/data/clinvar.chr.bed -v -u -t DP,AD - > foo.vcf
