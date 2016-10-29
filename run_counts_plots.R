#!/usr/local/bin Rscript

# Example of run: Rscript run_counts_plots.R -i ~/Downloads/hisat_tags_output_SRR1616919_hg38.mpileup.mod.counts_both_mapped_no_chimera_gene.gff.mod3.intersect.mod.bed -o test.pdf

# Install dependencies
library(ggplot2)
library(getopt)

args<-commandArgs(TRUE)

#############################################################
## Command-line preparations and getopt parsing ##
#############################################################

options<-matrix(c('intfile',	'i',	1,	"character",
		  		  'outfile',	'o',	1,	"character",
		  		  'help',		'h', 	0,  "logical"),
		  		   	ncol=4,byrow=TRUE)

ret.opts<-getopt(options,args)

if ( !is.null(ret.opts$help) ) {
  cat(getopt(options, usage=TRUE));
  q(status=1);
}

# Input file
data <- read.csv(ret.opts$intfile, sep="\t", h = F)

data.1 <- data[order(data$V4),c(1,2,3,4,5)]

t <- as.data.frame(as.numeric(seq(1:nrow(data.1))))
names(t) <- "index"

data.2 <- cbind(t,data.1)

# Generate plot
p <- ggplot(data.2, aes(index,V4)) + geom_point() + theme_bw() + xlab("SNP's") + ylab("Counts")

ggsave(p, file = ret.opts$outfile)

