This function uses 3rd party libraries.
For this to work with AWS Lambda, the libs must be installed in this directory and zipped up with the code.

`pip install -r reqs.txt -t .`

Then zip it all up without the `utterances.txt` or `schema.json` files.

`zip -r fivethirtyeight.zip *`
