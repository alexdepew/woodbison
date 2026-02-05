rm(list = ls())
library(tidyverse)

# Load data
gold_genotypes <- read.csv("ball_samples/goldgenotypes_greg_Parks.csv")
einp <- read.csv("ball_samples/plains bison einp.csv")
gold_genotypes_list <- read.table("GWilson_goldgenotypes_AB sample info list.txt",
                                                  sep = "\t", header = T)
einp <- einp %>%
  mutate(across(bm2830:bovfsh, ~ gsub("\035", "", .x)))

# Consistent formatting
einp <- einp %>% 
  select(-4) %>% 
  select(-subspecies) %>% 
  select(-bm4513)

# Split columns
loc_names <- colnames(einp)[3:ncol(einp)]

einp <- einp %>% 
  separate("bm2830", into = c("bm2830", "bm2830.1"), sep = 3) %>% 
  separate("bm143", into = c("bm143", "bm143.1"), sep = 3) %>% 
  separate("rt9", into = c("rt9", "rt9.1"), sep = 3) %>% 
  separate("rt24", into = c("rt24", "rt24.1"), sep = 3) %>% 
  separate("rt27", into = c("rt27", "rt27.1"), sep = 3) %>% 
  separate("rt29", into = c("rt29", "rt29.1"), sep = 3) %>% 
  separate("bmc1222", into = c("bmc1222", "bmc1222.1"), sep = 3) %>% 
  separate("bm1225", into = c("bm1225", "bm1225.1"), sep = 3) %>% 
  separate("eth121", into = c("eth121", "eth121.1"), sep = 3) %>% 
  separate("bovfsh", into = c("bovfsh", "bovfsh.1"), sep = 3) %>% 
  mutate(across(bm2830:bovfsh.1, as.integer))
  
# Merge by colnames 
ball_2016 <- bind_rows(gold_genotypes, einp, gold_genotypes_list) %>% 
  select(-Region)
# Shorten cols
# Need to import dataframe as a gtypes object. For this, columns need to be merged.
locus_cols <- names(ball_2016)[3:ncol(ball_2016)]

# Get base locus names without ".1"
base_loci <- unique(gsub("\\.1$", "", locus_cols))

# Loop through each locus and combine alleles
for (locus in base_loci) {
  
  col1 <- locus
  col2 <- paste0(locus, ".1")
  
  if (col1 %in% names(ball_2016) && col2 %in% names(ball_2016)) {
    ball_2016[[col1]] <- paste(ball_2016[[col1]], ball_2016[[col2]], sep = "/")
  }
}

# Remove all the _2 columns
ball_2016 <- ball_2016[, !grepl("\\.1$", names(ball_2016))]

# Fix popnames

ball_2016 <- ball_2016 %>% 
  mutate(Population = case_match(Population,
                                 "WBNPSR" ~ "WBNPPAD",
                                 "WBNPSG" ~ "WBNPPAD",
                                 "WBNPPL" ~ "WBNPHC",
                                 "WBNPLB" ~ "WBNPLB",
                                 "WBNPGR" ~ "WBNPGR",
                                 "WBNPNL" ~ "WBNPNY",
                                 "Wood Buffalo NP" ~ "WBNPNY",
                                 "ELKISL" ~ "EINPW",
                                 "Elk Island NP" ~ "EINPP",
                                 "RonaldLake" ~ "RL",
                                 "RBL" ~ "RL",
                                 "Wentzel" ~ "WENT",
                                 "Harpercreek" ~ "WAB",
                                 "Hay zama" ~ "HZ",
                                 "Rainbow Lake" ~ "HZ",
                                 "NWT" ~ "MBS",
                                 .default = Population 
  ))

# Herd Count
table(ball_2016$Population)

ball_2016 <- ball_2016 %>%
  mutate(across(3:ncol(.), ~ if_else(str_detect(.x, "NA"), NA_character_, .x)))

# Make genind object
library(adegenet)
ball.genind <- df2genind(X=ball_2016[,c(3:ncol(ball_2016))],
                          sep = "/",
                          ind.names = ball_2016$ID,
                          loc.names = NULL,
                          pop = ball_2016$Population,
                          NA.char = "NA",
                          ploidy = 2,
                          type = "codom",
                          strata = NULL,
                          hierarchy = NULL)

