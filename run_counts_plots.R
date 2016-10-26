#!/usr/local/bin Rscript

library(ggplot2)

data <- read.csv("~/Downloads/hisat_tags_output_SRR1616919_hg38.mpileup.mod.counts_both_mapped_no_chimera_gene.gff.mod3.intersect.mod.bed", sep="\t", h = F)
head(data)

data.1 <- data[order(data$V4),c(1,2,3,4,5)]
head(data.1)

t <- as.data.frame(as.numeric(seq(1:nrow(data.1))))
names(t) <- "index"
head(t)

data.2 <- cbind(t,data.1)
head(data.2)

p <- ggplot(data.2, aes(index,V4)) + geom_point() + theme_bw() + xlab("SNP's") + ylab("Counts")
setwd("~/Downloads/")
ggsave(p, file = "hisat_tags_output_SRR1616919_hg38.mpileup.mod.counts_both_mapped_no_chimera_gene.gff.mod3.intersect.mod.bed.pdf")

