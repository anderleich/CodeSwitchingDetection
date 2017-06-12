# -*- coding: utf-8 -*-
import tweepy
import csv
import sys
import json
import Process
import CRFSuite
import argparse

#Twitter API credentials
consumer_key = "U5UvXxXqvTaqy6aIHCR0Jjfgc"
consumer_secret = "tWxBT4VsOCyM6DN9Ge0zqRbwaC758ve8FBqzoqLICx8Mcd28pf"

access_token = "2225564845-hV2lFTCkQhS6ylCvcgd9TCmjT0jQ78VFSZ5YzZy"
access_token_secret = "hVUxB3uMbrEahRpwLBN5DmwHS3smxMhHLVAw8Cuirpa0q"

FILE = ""
FETCHED = 0
json_data = ""

#override tweepy.StreamListener to add logic to on_status and on_error
class MyStreamListener(tweepy.StreamListener):

	def on_status(self, status):
		global FETCHED
		FETCHED += 1
		getTweetInfo(status)
		print "Tweets fetched: " + str(FETCHED) + "\n"

	def on_error(self, status_code):
		if status_code == 420:
			print "Disconnected"
			return False

def getTweetInfo(tweet):
	tweet_id = str(tweet.id)
	user_id = str(tweet.user.id)
	user_image = str(tweet.user.profile_image_url)
	text = str(tweet.text.encode('UTF-8'))
	user_name = str(tweet.user.name.encode('UTF-8'))
	user_screenname = str(tweet.user.screen_name.encode('UTF-8'))
	print text

	tokens = Process.tokenize(text.decode('UTF-8'))
	preprocess = []
	for t in tokens:
		preprocess.append((t,""))

	global crf
	(features, y) = CRFSuite.TrainTweetToCRF(tweet= preprocess)
	if features:
		predicted = crf.predict(features)
	else:
		print "Too short!"
		return


	global json_data
	data = json.loads(json_data)
	json_tweet_temp = { "tweet" : {
			"text": text,
			"tweet_id": tweet_id,
			"user_id": user_id,
			"user_image" : user_image,
			"user_name" : user_name,
			"user_screenname" : user_screenname,
			"tags" : [],
			"language" : ""
			}}
	json_tweet = json.loads(json.dumps(json_tweet_temp))
	es = 0
	eus = 0
	for i in range(0,len(tokens)):
		token = tokens[i];
		tag = predicted[0][i];
		if tag == "ES":
			es += 1
		elif tag == "EUS":
			eus += 1
		json_tweet["tweet"]["tags"].append({"token":tokens[i], "tag":predicted[0][i]})
	if es > 0 and eus > 0:
		json_tweet["tweet"]["language"] = "CS"
	elif es > 0 and eus == 0:
		json_tweet["tweet"]["language"] = "ES"
	elif es == 0 and eus > 0:
		json_tweet["tweet"]["language"] = "EUS"
	else:
		json_tweet["tweet"]["language"] = "NULL"

	data["tweets"].append(json_tweet)
	json_data = json.dumps(data)

	global FILE
	file = open(FILE,"w") 
	file.write(json_data)
	file.close()


if __name__ == '__main__':

	#Check arguments
	parser = argparse.ArgumentParser(description="Performs code switching analysis in Twitter streaming")
	parser.add_argument('corpus', action="store", help="Name of the corpus file, with extension")
	parser.add_argument('output', action="store", help="Name of the JSON output file, no extension")
	parser.add_argument('type', action='store', choices=["word","user"], help="Search by word or by user")
	parser.add_argument('query', nargs="+", help="List of queries (words or users)")
	args = parser.parse_args()

	print ""
	print "=========== Twitter streaming ============"
	print "\tCorpus file:\t"+args.corpus
	print "\tOutput file:\t"+args.output+".json"
	print "\tSearch type:\tBy "+args.type
	print "\tQueries:\t"+', '.join(args.query)
	print ""

	#Twitter API authentication
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)

	#Train CRF
	crf = CRFSuite.trainCRF(args.corpus)

	#Create output file
	FILE = args.output + ".json"
	json_data = json.dumps({ "tweets" : [] })
	file = open(FILE,"w") 
	file.write(json_data)
	file.close()
	
	#Start stream
	myStreamListener = MyStreamListener()
	#Start tweepy
	api = tweepy.API(auth)
		
	print ""
	print "Fetching tweets...."
	
	while True:
		try:
			stream = tweepy.Stream(auth, myStreamListener)
			if args.type == "word": #By words
				stream.filter(track=args.query, stall_warnings=True)
			elif args.type == "user": #Bu users
				users = []
				for user in args.query:
					users.append(api.get_user(user).id_str)
				stream.filter(follow=users, stall_warnings=True)
			else:
				print "There was a problem with the stream"
				exit()
		except KeyboardInterrupt:
			stream.disconnect()
			break
		'''
		except:
			print "Trying to reconnect..."
			continue
		'''