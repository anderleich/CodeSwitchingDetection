#!/usr/bin/env python
# encoding: utf-8

import csv
import string
import Process
import hunspell as hunspellES
import hunspell as hunspellEU
import random

#returns the accuracy score for sequence items
def seqItemAccuracyScore(y_true, y_pred):
	right = 0
	total = 0
	for i in range(0,len(y_true)):
		if len(y_true[i]) == len(y_pred[i]):
			for j in range(0,len(y_true[i])):
				if y_true[i][j] == y_pred[i][j]:
					right += 1
				total += 1
	return (float)(right)/(float)(total)

#returns the accuracy score for sequences
def seqAccuracyScore(y_true, y_pred):
	right = 0
	total = 0
	for i in range(0,len(y_true)):
		if len(y_true[i]) == len(y_pred[i]):
			same = True
			for j in range(0,len(y_true[i])):
				if y_true[i][j] != y_pred[i][j]:
					same = False
			if same: right += 1
		total += 1
	return (float)(right)/(float)(total)

#returns the accuracy score for sequence global tags
def globalTagAccuracyScore(y_true, y_pred):
	right = 0
	total = 0
	for i in range(0,len(y_true)):
		if len(y_true[i]) == len(y_pred[i]):
			tag_true = globalTag(y_true[i])
			tag_pred = globalTag(y_pred[i])
			if tag_true == tag_pred: right += 1
		total += 1
	return (float)(right)/(float)(total)

#computes the baseline for the given corpus
def baseline(corpus_file_name):
	dic_es = hunspellES.HunSpell("es.dic", "es.aff") #Get Hunspell spanish dictionary
	dic_eu = hunspellEU.HunSpell('eu.dic', 'eu.aff') #Get Hunspell basque dictionary

	CS_Corpus = open(corpus_file_name, 'rb')
	CS_Reader = csv.reader(CS_Corpus, delimiter=',', quotechar='"')
	CS_Reader.next() #Skip first line

	count = 0
	right = 0
	total = 0

	y_true = []
	y_pred = []
	
	for row in CS_Reader:
		row_processed = getTweetTokensTags(row) 
		hand_tagged_tags = []
		for token, tag in row_processed:
			hand_tagged_tags.append(tag)

		tokens = Process.tokenize(row[2].decode('UTF-8')) # Tweet text tokenized
		predicted_tags = []
		for i in range(0,len(tokens)):
			t0 = tokens[i]
			if i > 0 and tokens[i-1] not in [".", "!", "?"] and t0.istitle():
				predicted_tags.append("IE")
			elif t0.isupper():
				predicted_tags.append("IE")
			elif dic_es.spell(t0):
				predicted_tags.append("ES")
			elif dic_eu.spell(t0):
				predicted_tags.append("EUS")
			elif Process.isURL(t0):
				predicted_tags.append("URL")
			elif Process.isID(t0):
				predicted_tags.append("ID")
			else:
				predicted_tags.append("EG")
		
		y_true.append(hand_tagged_tags)
		y_pred.append(predicted_tags)

	print ""
	print "Sequence item accuracy score: %.5f" % seqItemAccuracyScore(y_true,y_pred)
	print "Sequence accuracy score: %.5f" % seqAccuracyScore(y_true,y_pred)
	print "Global tag accuracy score: %.5f" % globalTagAccuracyScore(y_true, y_pred)

#returns a list of tuples (token,tag) for a given corpus row
def getTweetTokensTags(row):	
	tokens_num = int(float(row[3])) #Number of tokens
	
	row_processed = []	
	for i in xrange(4,(int(tokens_num)*2)+4,2):
		token = row[i].decode('UTF-8')
		tag = row[i+1].decode('UTF-8')
		row_processed.append((token,tag))

	return row_processed

#Shuffles the corpus
def shuffle(corpus_file_name, result_corpus_file_name):
	corpus_file = open(corpus_file_name,'rb')
	corpus_reader = csv.reader(corpus_file, delimiter=',', quotechar='"')
	corpus_reader.next() #Skip first line

	result_file = open(result_corpus_file_name, 'w')
	writer = csv.writer(result_file)
	writer.writerow(["tweetId","userId","text","tokens","(token,tag)"]) #Write first line
	
	rows = []
	for row in corpus_reader:
		rows.append(row)
	corpus_file.close()
	
	print "Tweets read: %d" % len(rows)
	random.shuffle(rows)
	for row in rows:
		writer.writerow(row)
	result_file.close()
	print "Corpus shuffled"
	print "Result file: %s" % result_corpus_file_name

#prints corpus information
def corpusInfo(corpus_file_name):
	CS_Corpus = open(corpus_file_name, 'rb')
	CS_Reader = csv.reader(CS_Corpus, delimiter=',', quotechar='"')
	CS_Reader.next() #Skip first line

	num_tweets = 0
	es_tags = 0
	eus_tags = 0
	id_tags = 0
	url_tags = 0
	eg_tags = 0
	anb_tags = 0
	nh_tags = 0
	ie_tags = 0
	es_tweets = 0
	eus_tweets = 0
	cs_tweets = 0
	none_tweets = 0
	num_tokens = 0

	for row in CS_Reader:
		num_tweets += 1
		row_processed = getTweetTokensTags(row) 
		for token, tag in row_processed:
			num_tokens += 1
			if tag == "ES": es_tags += 1
			if tag == "EUS": eus_tags += 1
			if tag == "ID": id_tags += 1
			if tag == "URL": url_tags += 1
			if tag == "EG": eg_tags += 1
			if tag == "ANB": anb_tags += 1
			if tag == "NH": nh_tags += 1
			if tag == "IE": ie_tags += 1
		tag = globalTag([tag for token,tag in row_processed])
		if tag == "ES": es_tweets += 1
		elif tag == "EUS": eus_tweets += 1
		elif tag == "CS": cs_tweets += 1
		elif tag == "NONE": none_tweets += 1

	print ""
	print "Corpus information"
	print "------------------"
	print "Number of tweets: %d" % num_tweets
	print "Number of spanish tweets: %d" % es_tweets
	print "Number of basque tweets: %d" % eus_tweets
	print "Number of code-switching tweets: %d" % cs_tweets
	print "Number of none tagged tweets: %d" % none_tweets
	print ""
	print "Number of tokens: %d" % num_tokens
	print "Number of ES tags: %d" % es_tags
	print "Number of EUS tags: %d" % eus_tags
	print "Number of ID tags: %d" % id_tags
	print "Number of URL tags: %d" % url_tags
	print "Number of EG tags: %d" % eg_tags
	print "Number of ANB tags: %d" % anb_tags
	print "Number of NH tags: %d" % nh_tags
	print "Number of IE tags: %d" % ie_tags

#returns tweet's global tag given sequence tags
def globalTag(tags):
	eu = 0
	es = 0
	for tag in tags:
		if tag == "ES": es += 1
		if tag == "EUS": eu += 1
	if eu==0 and es>0: return "ES"
	elif eu>0 and es==0: return "EUS"
	elif eu>0 and es>0: return "CS"
	else: return "NONE"