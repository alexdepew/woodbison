# Clear Environment
rm(list = ls())

# Load RLDNe
library(RLDNe)

library(adegenet)
library(graph4lg)

bison.data <- read.csv("./datafiles/Cleaned_locus_data_20.02.2026.csv",
                       check.names = F)

# Make genind object
bison.genind <- df2genind(X=bison.data[,c(19:ncol(bison.data))],
                          sep = "/",
                          ind.names = bison.data$Spreadsheet_ID,
                          loc.names = NULL,
                          pop = bison.data$HERD,
                          NA.char = "NA",
                          ploidy = 2,
                          type = "codom",
                          strata = NULL,
                          hierarchy = NULL)

# Attach collection year metadata
idx <- match(indNames(bison.genind), bison.data$Spreadsheet_ID)
stopifnot(!any(is.na(idx)))
bison.genind@other$YEAR.ASSIGN <- bison.data$YEAR.ASSIGN[idx]


# Subset
temp1 <- bison.genind[bison.genind@other$YEAR.ASSIGN <=1999]
temp2 <- bison.genind[bison.genind@other$YEAR.ASSIGN %in% 2000:2015]
temp3 <- bison.genind[bison.genind@other$YEAR.ASSIGN >= 2016]
genind_to_genepop(temp2,
                  output = "./temp2.genepop.txt")
