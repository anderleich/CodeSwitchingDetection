#!/usr/bin/env python
# encoding: utf-8

import csv
import string
import sklearn_crfsuite
from sklearn_crfsuite import metrics
from sklearn.model_selection import KFold
import numpy as np
import Corpus

token_prev_next = 1
options = {	"prefix1" : True,
			"prefix2" : True,
			"prefix3" : True,
			"prefix4" : False,
			"suffix4" : True,
			"suffix3" : True,
			"suffix2" : True,
			"suffix1" : True,
			"istitle" : True,
			"ispunctuation" : False,
			"isaccented" : False,
			"isupper" : False }

def trainCRF(corpus_file_name):
	X_set = []
	Y_set = []
	global options

	#Read the corpus
	CS_Corpus = open(corpus_file_name, 'rb')
	CS_Reader = csv.reader(CS_Corpus, delimiter=',', quotechar='"')
	CS_Reader.next() #Skip first line

	lines = 0
	for row in CS_Reader:
		(X_set_part, Y_set_part) = TrainTweetToCRF(
					tweet= Corpus.getTweetTokensTags(row),
					token_prev_next = token_prev_next,
					options = options,
					y_set = True)
		if X_set_part and Y_set_part:
			X_set.extend(X_set_part)
			Y_set.extend(Y_set_part)
		lines += 1

	CS_Corpus.close()
	print "Tweets read: %d" % lines
	print "Train amount: %d" % lines

	crf = sklearn_crfsuite.CRF(
		algorithm='lbfgs',
		c1=0.1,
		c2=0.1,
		max_iterations=100,
		all_possible_transitions=True
	)
	crf.fit(X_set, Y_set) #Train CRF

	return crf	

def testCRF(corpus_file_name, testtype):
	test_types = ['test', 'evaluate']
	if testtype not in test_types:
		raise ValueError("Invalid test type. Expected one of: %s" % test_types)

	X_set = []
	Y_set = []

	#Read the corpus
	CS_Corpus = open(corpus_file_name, 'rb')
	CS_Reader = csv.reader(CS_Corpus, delimiter=',', quotechar='"')
	CS_Reader.next() #Skip first line

	lines = 0
	for row in CS_Reader:
		(X_set_part, Y_set_part) = TrainTweetToCRF(
					tweet= Corpus.getTweetTokensTags(row),
					token_prev_next = token_prev_next,
					options = options,
					y_set = True)
		if X_set_part and Y_set_part:
			X_set.extend(X_set_part)
			Y_set.extend(Y_set_part)
		lines += 1

	CS_Corpus.close()
	print "Tweets read: %d" % lines
	print "X set: %d" % len(X_set)
	print "Y set: %d" % len(Y_set)

	if testtype == "evaluate":
		train_amount = (len(X_set)*80/100) #80% tweets for the train set
		test_amount = (len(X_set)*10/100) #10% tweets for the evaluation set
		print "Amount of tweets for training set: %d" % train_amount
		print "Amount of tweets for evaluation set: %d" % test_amount
	elif testtype == "test":
		train_amount = (len(X_set)*90/100) #90% tweets for the train set
		test_amount = (len(X_set)*10/100) #10% tweets for the test set
		print "Amount of tweets for training set: %d" % train_amount
		print "Amount of tweets for testing set: %d" % test_amount

	crf = sklearn_crfsuite.CRF(
		algorithm='lbfgs',
		c1=0.1,
		c2=0.1,
		max_iterations=100,
		all_possible_transitions=True
	)

	crf.fit(X_set[:train_amount], Y_set[:train_amount]) #Train CRF

	labels = list(crf.classes_)
	labels.remove('-')
	print labels

	y_pred = crf.predict(X_set[train_amount:train_amount+test_amount])

	sorted_labels = sorted(labels, key=lambda name: (name[1:], name[0]))
	print(metrics.flat_classification_report(
			Y_set[train_amount:train_amount+test_amount], y_pred, labels=sorted_labels, digits=3
	))
		
	print "Sequence item accuracy: %.5f" % crf.score(X_set[train_amount:train_amount+test_amount],Y_set[train_amount:train_amount+test_amount])
	print "Sequence accuracy : %.5f" % metrics.sequence_accuracy_score(Y_set[train_amount:train_amount+test_amount],y_pred)
	print "Global tag accuracy: %.5f" % globalTagAccuracy(Y_set[train_amount:train_amount+test_amount],y_pred)
	F1scores(Y_set[train_amount:train_amount+test_amount],y_pred)

def crossValidation(corpus_file_name, k):
	k_fold = KFold(n_splits=k, shuffle=False, random_state=None)
	print "Number of iterations in the cross validator: %d" % k

	X_set = []
	Y_set = []
	global options

	#Read the corpus
	CS_Corpus = open(corpus_file_name, 'rb')
	CS_Reader = csv.reader(CS_Corpus, delimiter=',', quotechar='"')
	CS_Reader.next() #Skip first line

	lines = 0
	for row in CS_Reader:
		(X_set_part, Y_set_part) = TrainTweetToCRF(
					tweet=Corpus.getTweetTokensTags(row),
					token_prev_next = token_prev_next,
					options = options,
					y_set = True)
		if X_set_part and Y_set_part:
			X_set.extend(X_set_part)
			Y_set.extend(Y_set_part)
		lines += 1

	CS_Corpus.close()
	print "Tweets read: %d" % lines
	print "X set: %d" % len(X_set)
	print "Y set: %d" % len(Y_set)

	X = np.array(X_set)
	Y = np.array(Y_set)

	crf = sklearn_crfsuite.CRF(
		algorithm='lbfgs',
		c1=0.1,
		c2=0.1,
		max_iterations=100,
		all_possible_transitions=True
	)
	item_scores = []
	seq_scores = []
	global_scores = []
	for train_index, test_index in k_fold.split(X):
		print "Test set: [" + str(test_index[0]) + " - " + str(test_index[len(test_index)-1]) +"]"
		x_train, x_test = X[train_index], X[test_index]
		y_train, y_test = Y[train_index], Y[test_index]
		crf.fit(x_train,y_train)

		item_score = crf.score(x_test,y_test)
		item_scores.append(item_score)
		print "Sequence item score: %f" % item_score

		y_pred = crf.predict(x_test)
		seq_score = metrics.sequence_accuracy_score(y_test,y_pred)
		seq_scores.append(seq_score)
		print "Sequence score: %f" % seq_score

		global_score = globalTagAccuracy(y_test,y_pred)
		global_scores.append(global_score)
		print "Global tag score: %f" % global_score
		
		
		print ""

	#Mean
	print "Cross validation results"
	print "------------------------"
	print "Sequence item mean score: %.5f" % np.mean(item_scores)
	print "Sequence mean score: %.5f" % np.mean(seq_scores)
	print "Global tag mean score: %.5f" % np.mean(global_scores)
	#Standard deviation
	print "Sequence item standard deviation: %.5f" % np.std(item_scores)
	print "Sequence standard deviation: %.5f" % np.std(seq_scores)
	print "Global tag standard deviation: %.5f" % np.std(global_scores)


def TrainTweetToCRF(tweet, token_prev_next=token_prev_next, options=options, y_set=False):
	if len(tweet) < (token_prev_next*2 + 1): # 3:
		return ([],[])

	X_set = []
	Y_set = []

	tweet_features = []
	tweet_tags = []
	 
	for j in range(0,len(tweet)):
		features = {}

		features['token[0]'] = tweet[j][0]
		if options["prefix1"]: features['prefix1[0]'] = tweet[j][0][:1].lower()
		if options["prefix2"]: features['prefix2[0]'] = tweet[j][0][:2].lower()
		if options["prefix3"]: features['prefix3[0]'] = tweet[j][0][:3].lower()
		if options["prefix4"]: features['prefix4[0]'] = tweet[j][0][:4].lower()
		if options["suffix4"]: features['suffix4[0]'] = tweet[j][0][-4:].lower()
		if options["suffix3"]: features['suffix3[0]'] = tweet[j][0][-3:].lower()
		if options["suffix2"]: features['suffix2[0]'] = tweet[j][0][-2:].lower()
		if options["suffix1"]: features['suffix1[0]'] = tweet[j][0][-1:].lower()
		if options["istitle"]: features['isTitle[0]'] = tweet[j][0].istitle()
		if options["ispunctuation"]: features['isPunctuation[0]'] = True if tweet[j][0] in string.punctuation else False
		if options["isaccented"]: features['isAccented[0]'] = True if u'á' or u'é' or u'í' or u'ó' or u'ú' in tweet[j][0].lower() else False
		if options["isupper"]: features['isUpper[0]'] = tweet[j][0].isupper()

		for x in range(1,token_prev_next+1):
			if j>=0 and j<len(tweet)-x: #1:
				features['token['+str(x)+']'] = tweet[j+x][0]
				if options["prefix1"]: features['prefix1['+str(x)+']'] = tweet[j+x][0][:1].lower()
				if options["prefix2"]: features['prefix2['+str(x)+']'] = tweet[j+x][0][:2].lower()
				if options["prefix3"]: features['prefix3['+str(x)+']'] = tweet[j+x][0][:3].lower()
				if options["prefix4"]: features['prefix4['+str(x)+']'] = tweet[j+x][0][:4].lower()
				if options["suffix4"]: features['suffix4['+str(x)+']'] = tweet[j+x][0][-4:].lower()
				if options["suffix3"]: features['suffix3['+str(x)+']'] = tweet[j+x][0][-3:].lower()
				if options["suffix2"]: features['suffix2['+str(x)+']'] = tweet[j+x][0][-2:].lower()
				if options["suffix1"]: features['suffix1['+str(x)+']'] = tweet[j+x][0][-1:].lower()
				if options["istitle"]: features['isTitle['+str(x)+']'] = tweet[j+x][0].istitle()
				if options["ispunctuation"]: features['isPunctuation['+str(x)+']'] = True if tweet[j+x][0] in string.punctuation else False
				if options["isaccented"]: features['isAccented['+str(x)+']'] = True if u'á' or u'é' or u'í' or u'ó' or u'ú'  in tweet[j+x][0].lower() else False
				if options["isupper"]: features['isUpper['+str(x)+']'] = tweet[j+x][0].isupper()

			if j>x-1 and j<len(tweet):
				features['token[-'+str(x)+']'] = tweet[j-x][0]
				if options["prefix1"]: features['prefix1[-'+str(x)+']'] = tweet[j-x][0][:1].lower()
				if options["prefix2"]: features['prefix2[-'+str(x)+']'] = tweet[j-x][0][:2].lower()
				if options["prefix3"]: features['prefix3[-'+str(x)+']'] = tweet[j-x][0][:3].lower()
				if options["prefix4"]: features['prefix4[-'+str(x)+']'] = tweet[j-x][0][:4].lower()
				if options["suffix4"]: features['suffix4[-'+str(x)+']'] = tweet[j-x][0][-4:].lower()
				if options["suffix3"]: features['suffix3[-'+str(x)+']'] = tweet[j-x][0][-3:].lower()
				if options["suffix2"]: features['suffix2[-'+str(x)+']'] = tweet[j-x][0][-2:].lower()
				if options["suffix1"]: features['suffix1[-'+str(x)+']'] = tweet[j-x][0][-1:].lower()
				if options["istitle"]: features['isTitle[-'+str(x)+']'] = tweet[j-x][0].istitle()
				if options["ispunctuation"]: features['isPunctuation[-'+str(x)+']'] = True if tweet[j-x][0] in string.punctuation else False
				if options["isaccented"]: features['isAccented[-'+str(x)+']'] = True if u'á' or u'é' or u'í' or u'ó' or u'ú'  in tweet[j-x][0].lower() else False
				if options["isupper"]: features['isUpper[-'+str(x)+']'] = tweet[j-x][0].isupper()

		tweet_features.append(features)
		if y_set:
			tweet_tags.append(tweet[j][1])

	X_set.append(tweet_features)
	if y_set:
		Y_set.append(tweet_tags)		

	return (X_set,Y_set)

def globalTagAccuracy(y_true, y_pred):
	count = 0
	for i in range(0,len(y_pred)):
		if Corpus.globalTag(y_pred[i]) == Corpus.globalTag(y_true[i]):
			count += 1
	return (float)(count)/(float)(len(y_pred))

def F1scores(y_true, y_pred):
	cs_positive_correct = 0.0
	cs_positive_total = 0.0
	cs_positive_true = 0.0

	mono_positive_correct = 0.0
	mono_positive_total = 0.0
	mono_positive_true = 0.0

	for i in range(0,len(y_pred)):
		tag_true = Corpus.globalTag(y_true[i])
		tag_pred = Corpus.globalTag(y_pred[i])

		if tag_pred == "CS": 
			cs_positive_total += 1.0
		elif tag_pred == "ES" or tag_pred == "EUS": 
			mono_positive_total += 1.0
		
		if tag_pred == "CS" and tag_true == "CS": 
			cs_positive_correct += 1.0
		elif tag_pred == "ES" and tag_true == "ES": 
			mono_positive_correct += 1.0
		elif tag_pred == "EUS" and tag_true == "EUS": 
			mono_positive_correct += 1.0
		
		if tag_true == "CS": 
			cs_positive_true += 1.0
		elif tag_true == "ES" or tag_true == "EUS": 
			mono_positive_true += 1.0

	cs_precision = float(cs_positive_correct / cs_positive_total)
	cs_recall = float(cs_positive_correct / cs_positive_true)
	if cs_precision + cs_recall > 0:
		cs_f1 = float(2.0 * ((cs_precision*cs_recall)/(cs_precision+cs_recall)))
	else:
		cs_f1 = 0.0

	mono_precision = float(mono_positive_correct / mono_positive_total)
	mono_recall = float(mono_positive_correct / mono_positive_true)
	if mono_precision + mono_recall > 0:
		mono_f1 = float(2.0 * ((mono_precision*mono_recall)/(mono_precision+mono_recall)))
	else:
		mono_f1 = 0.0

	print ""
	print "Precision for code-switched tweets: %.5f" % cs_precision
	print "Recall for code-switched tweets: %.5f" % cs_recall
	print "F1-score for code-switched tweets: %.5f" % cs_f1
	print "Code-switched tagged tweets: %d" % cs_positive_total
	print "Precision for monolingual tweets: %.5f" % mono_precision
	print "Recall for monolingual tweets: %.5f" % mono_recall
	print "F1-score for monolingual tweets: %.5f" % mono_f1
	print "Monolingual tagged tweets: %d" % mono_positive_total