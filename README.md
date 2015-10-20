# Introduction
The script extracts hard coded texts from jsp files. 
# Usage
`./textExtractor.py <path of jsp folder/file> <output filename with extension>`

The script returns exit codes. `0` means failure and `1` means success. Exit code is stored in special variable `$?`. Example usage is:

`./textExtractor.py <path of jsp folder/file> <output filename with extension>; echo $?`
# Requirements
Python 2.7+