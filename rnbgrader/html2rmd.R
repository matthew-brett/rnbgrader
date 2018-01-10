# R script converts rendered HTML to Rmd
args <- commandArgs(trailingOnly=TRUE)
library(rmarkdown)
library(stringr)
if (length(args) == 0) {
    cat('Give at least .nb.html filename as argument')
    quit(1)
}
if (length(args) > 2) {
    cat('Give only .nb.html and output filename')
    quit(1)
}
fname <- args[1]
root = str_match(fname, regex("(.*).nb.html", ignore_case=TRUE))[2]
if (is.na(root)) {
    cat(sprintf("Filename '%s' should end in '.nb.html'\n", fname))
    quit(1)
}
if (length(args) == 2) {
    out_fname = args[2]
} else {
    out_fname = paste(root, '.Rmd', sep='')
}

# http://rmarkdown.rstudio.com/r_notebook_format.html
parsed <- rmarkdown::parse_html_notebook(fname)
cat(sprintf("Writing '%s' to '%s'\n", fname, out_fname))
f = file(out_fname)
write(parsed$rmd, f)
close(f)
