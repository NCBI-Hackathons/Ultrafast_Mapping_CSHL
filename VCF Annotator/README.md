
Annotate VCF file with RefSeq genes and other features.  


Usage help: ./VarRefSeqAnnotation.py -h

./VarRefSeqAnnotation.py -feature gene -gff test_RefSeq.gff -vcf dbSNP_147_GRCh38.vcf.gz -asm GCF_000001405.35.assembly.txt

optional arguments:
  -h, --help        show this help message and exit
  -gff GFF          input RefSeq gff file
  -vcf VCF          input VCF file
  -feature FEATURE  feature name to Annotate, must be in gff file
  -np NP            number of processes
  -asm ASM          input assembly info text file (ie.
                    /home/data/GCF_000001405.35.assembly.txt

Available Features:
	antisense_RNA
	C_gene_segment
	cDNA_match
	CDS
	centromere
	D_gene_segment
	D_loop
	enhancer
	exon
	gene
	J_gene_segment
	lnc_RNA
	match
	miRNA
	mRNA
	ncRNA
	primary_transcript
	promoter
	region
	repeat_region
	RNase_MRP_RNA
	RNase_P_RNA
	rRNA
	sequence_feature
	snoRNA
	snRNA
	SRP_RNA
	telomerase_RNA
	transcript
	tRNA
	V_gene_segment
	vault_RNA
	Y_RNA

Data source:
VCF - user provided VCF.  Example use dbSNP VCF.
NCBI Assembly info files: ftp://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/All/GCF_000001405.28.assembly.txt
NCBI RefSeq info file: ftp://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/H_sapiens

Example: 
./VarRefSeqAnnotation.py -feature gene -gff test_RefSeq.gff -vcf test_SNV.vcf.gz -asm test_GCF_000001405.35.assembly.txt 

Input VCF:
1       12053   rs111341249     C       T       .       .       RS=111341249;RSPOS=12053;dbSNPBuildID=132;SSR=0;SAO=0;VP=0x050000000005000002000100;GENEINFO=DDX11L1:100287102;WGT=1;VC=SNV;ASP

Output VCF:

1       12053   rs111341249     C       T       .       .       RS=111341249;RSPOS=12053;dbSNPBuildID=132;SSR=0;SAO=0;VP=0x050000000005000002000100;GENEINFO=DDX11L1:10028
7102;WGT=1;VC=SNV;ASP;ID=gene0;Dbxref=GeneID:100287102,HGNC:HGNC:37102;Name=DDX11L1;description=DEAD/H-box helicase 11 like 1;gbkey=Gene;gene=DDX11L1;gene_biotype=misc_RN
A;pseudo=true
