# This folder was created to overcome the error:

OSError: No wkhtmltopdf executable found: "b''"
If this file exists please check that this process can read it. Otherwise please install wkhtmltopdf - https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf


## Got the pdf maker to work by manually getting this binary for the X server
# wget https://github.com/wkhtmltopdf/obsolete-downloads/releases/download/linux/wkhtmltopdf-0.10.0_beta2-static-amd64.tar.bz2
# tar xvjf wkhtmltopdf-0.10.0_beta2-static-amd64.tar.bz2
# sudo mv bin/wkhtmltopdf-amd64 /usr/local/bin/wkhtmltopdf
# sudo chmod +x /usr/local/bin/wkhtmltopdf