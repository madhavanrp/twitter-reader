from collections import Counter
from guess_language import guess_language
import os
from pprint  import pprint

fname = "/Users/madhavan/Downloads/twitter-dataset/WordTable.txt"
output_folder = "/Users/madhavan/Downloads/twitter-dataset/output"
tweets_root = "/Users/madhavan/Downloads/twitter-dataset/Tweets-withoutwords/"
twitter_network_root = "/Users/madhavan/Downloads/twitter-dataset/twitter_network"

def language_counts():
	counts = dict()
	for line in open(fname):
	    triple = line.strip().split('\t')
	    if len(triple)<3:
	    	continue
	    word = triple[2]
	    lang = guess_language(word)
	    counts[lang] = counts.get(lang,0)+1
	return counts

def word_counts():
	counts = dict()
	for line in open(fname):
	    triple = line.strip().split('\t')
	    if len(triple)<3:
	    	continue
	    word = triple[2]
	    num_times = int(triple[1])
	    counts[word] = num_times
	return counts
# counts = word_counts()
# c = Counter(counts)
# print(c.most_common(40))

topic_words = ["israel", "gaza", "hamas", "fatah", "flotilla","hezbollah","intifada","knesset","nakba","zionism"]
pair_words = ["geneva accord", "palestinian authority", "west bank", "green line", "balfour declaration","golan heights","haram esh-sharif","oslo accords","temple mount","wye accord"]
topic_pair_words = []
for pair_w in pair_words:
	topic_pair_words.append(pair_w.split())


def get_word_mappings():
	word_to_id = dict()
	id_to_word = dict()
	for line in open(fname):
	    triple = line.strip().split('\t')
	    if len(triple)<3:
	    	continue
	    word_id = int(triple[0])
	    word = triple[2]
	    word_to_id[word] = word_id
	    id_to_word[word_id] = word
	return id_to_word, word_to_id

id_to_word, word_to_id = get_word_mappings()
print("Finished reading Word Mappings")

twitter_graph_file = os.path.join(twitter_network_root,"graph_cb.txt")
twitter_user_id_map = os.path.join(twitter_network_root, "user_list.txt")
twitter_username_map = os.path.join(twitter_network_root, "user_map.txt")
user_forward_map = []
user_reverse_map = dict()
def get_user_mappings():
	with open(twitter_user_id_map) as f:
		for line in f:
			line = line.strip()
			user_forward_map.append(int(line))
		i = 0
		for u in user_forward_map:
			user_reverse_map[u] = i
			i+=1
get_user_mappings()
print("Finished reading user mappings")

username_to_id = dict()
id_to_username = [None]*len(user_forward_map)
def get_username_mappings():
	with open(twitter_username_map) as f:
		for line in f:
			line = line.strip()
			user, username = line.split()
			# pprint(user_reverse_map)
			if int(user) not in user_reverse_map:
				continue
			user_id = user_reverse_map[int(user)]
			id_to_username[user_id] = username
			username_to_id[username] = user_id

get_username_mappings()
# prints number of users for which , we don't know the user name (6)
# number_of_unmapped = [x for x in id_to_username if x==None]
# print("Number of unmapped = {}".format(len(number_of_unmapped)))
# print("Total = {}".format(len(id_to_username)))

print("Finished reading username mappings")

topic_words_ids = set([word_to_id[w] for w in topic_words if w in word_to_id])
topic_pair_words_joined = set(["{} {}".format(word_to_id[w1],word_to_id[w2]) for w1,w2 in topic_pair_words if w1 and w2 in word_to_id])

language_counts = dict()
def get_tweet_files(tweets_root):
	tweet_files = []
	for root, subdirs, files in os.walk(tweets_root):
		for f in files:
			if f.endswith(".txt"):
				f = os.path.join(tweets_root,root, f)
				tweet_files.append(f)
	return tweet_files

all_tweet_files = get_tweet_files(tweets_root)

def process_tweet(tweet_numbers):
	i = 0
	num_words = len(tweet_numbers)
	interesting_tweet = False
	for x in tweet_numbers:
		if int(x) in topic_words_ids:
			interesting_tweet = True
			break
		if (i+1)<num_words:
			pair = "{} {}".format(x, tweet_numbers[i+1])
			if pair in topic_pair_words_joined:
				interesting_tweet = True
				break
		i+=1
	return interesting_tweet

original_counts = [0]*len(id_to_username)
retweet_counts = [0]*len(original_counts)
def read_tweet_file(tweet_file):
	c = 0
	f = open(tweet_file, encoding="utf8", errors='ignore')
	eof = False
	tot=0
	interesting_tweets=0
	username = None
	retweet = False
	original_user = None
	while True:
		line = f.readline()
		if len(line)==0:
			break

		line = line.strip()
		if c==0:
			username = line
		if c==4 and line!="-1":
			retweet = True
			original_user = line
		if c==6 and username in username_to_id:
			# This line contains the tweet content as numbers
			numbers = line.split()
			interesting = process_tweet(numbers)
			interesting_tweets+=1 if interesting else 0
			original_counts[username_to_id[username]]+=1 if interesting and not retweet else 0
			retweet_counts[username_to_id[username]]+=1 if interesting and retweet else 0
			# if interesting and retweet:
			# 	print("Original user:{}".format(original_user))
			# 	print("Retweeting user:{}".format(username))

		if c==7:
			retweet = False
			username = None
			lines_to_skip = int(line)
			for x in range(0,lines_to_skip+1):
				f.readline()
				tot+=1
			c=-1
		c+=1
		# if tot>100000:
		# 	break
	f.close()
	print("Interesting tweets : {}".format(interesting_tweets))
	print("Original sum = {}".format(sum(original_counts)))
	print("retweet sum = {}".format(sum(retweet_counts)))

def read_all_tweets():
	for t in all_tweet_files:
		print("Starting file {}".format(t))
		read_tweet_file(t)
		print("Done with file {}".format(t))
read_all_tweets()

def write_output_file():
	belief_file = os.path.join(output_folder,"belief.txt")
	with open(belief_file,'a') as f:
		for u in range(len(original_counts)):
			f.write("{} {} {}\n".format(u,original_counts[u],retweet_counts[u]))
write_output_file()
