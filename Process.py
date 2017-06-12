# -*- coding: utf-8 -*-
import re
import string

#Regular expression that matches different tokens
regex_str = [
	r'(?:@\w+)', # @-mentions
    r"(?:\#\w+)", # hash-tags
    r'(?:https?\S*)', # URLs
    r'(?:\d+(?:[.,]\d+)?)', #Emojis
    r'(?:\w+)', # numbers
	r'(?:[?¿.,;:!¡()/\-"]+)', # numbers
	r'(?:\S)'
]

tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE | re.UNICODE )

#tokenizes the given string
def tokenize(text):
	return tokens_re.findall(text)

#evaluates whether the given string is a URL
def isURL(text):
	return re.search(r'https?\S*',text) is not None

#evaluates whether the given string is an ID
def isID(text):
	return re.search(r'@\w+',text) is not None