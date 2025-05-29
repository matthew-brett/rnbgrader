# Install requirements for book build
# Force user install.
# This code adapted from install.packages function.
userdir <- unlist(strsplit(Sys.getenv("R_LIBS_USER"), .Platform$path.sep))[1L]
if (!file.exists(userdir)) {
    if (!dir.create(userdir, recursive = TRUE))
        stop(gettextf("unable to create %s", sQuote(userdir)),
             domain = NA)
    .libPaths(c(userdir, .libPaths()))
}

# Set default repo, if not set.
if (getOption('repos')["CRAN"] == "@CRAN@") {
   options(repos = c(CRAN = "http://cloud.r-project.org"))
}

# R kernel instructions from:
# https://irkernel.github.io/docs/IRkernel/0.7/

# https://stackoverflow.com/questions/4090169/elegant-way-to-check-for-missing-packages-and-install-them
# Install devtools with `apt install r-cran-devtools`
to_install <- c('repr', 'IRdisplay', 'crayon', 'pbdZMQ')
to_install <- to_install[!(to_install %in% installed.packages()[,"Package"])]
if (length(to_install)) {
    install.packages(to_install)
}

# https://www.r-project.org/nosvn/pandoc/devtools.html
# "In this mode, R will install packages to ~/R-dev. This is useful to avoid
# clobbering the existing versions of CRAN packages that you need for other
# tasks."
fs::dir_create('~/R-dev')  # ?also correct for Windows

# IRKernel
devtools::install_github('IRkernel/IRkernel')

# We will finally need to to register IRKernel in the current R
# installation, but only after we have installed jupyter-client.
# RScript -e "IRkernel::installspec()"
