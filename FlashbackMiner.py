#!/usr/bin/python

'''
FlashbackMiner.py
The script mines a given Flashback.org forum thread and extracts all posts and their metadata as raw data.
Use this tool if you need clean JSON formatted data from any Flashback thread.

Version 0.4
Created: 2014-01-18
By: Joar Svensson
Company: Notiio.se

External dependencies: BeautifulSoup4, tablib

Usage: ./FlashbackMiner.py [-h] -l LINK -o OUTPUT -f FORMAT
Example: ./FlashbackMiner.py -l https://www.flashback.org/t2299507 -o dump.json -f json
Example: ./FlashbackMiner.py -l https://www.flashback.org/t2299507 -o dump.xls -f xls
'''

try:
	from bs4 import BeautifulSoup
	import tablib
	import sys, argparse, time, urllib2, re, json, os.path, csv
except ImportError as e:
	print '{message}: {error}'.format(message='Terminating due to errors. Please install dependencies', error=e)
	sys.exit(1)

# Forum thread class for processing and exporting data
class FlashBThread():
	def __init__(self, url, fileName, format):
		self.url = url
		self.title = ''
		self.pages = 0
		self.posts_count = 0
		self.posts = []
		self.fileName = fileName
		self.format = format
	
	# Add forum posts to object
	def addPost(self, dictionary):
		self.posts.append(dictionary)
	
	# Process HTML
	def process(self):
		try:
			startTime = time.time()
			# Get HTML from url and start parsing
			html = urllib2.urlopen(self.url).read()
			soup = BeautifulSoup(html)
			
			# Assign title to object
			self.title = soup.title.string.encode('utf-8')
			print '{heading}: {data}'.format(heading='Flashback thread', data=self.title)
			print '{heading}: {data}'.format(heading='URL', data=self.url)
			
			# Check if multiply pages exist and assign number of pages (int) to object
			if soup.find("td", { "class" : "vbmenu_control smallfont2 delim" }):
				pages = soup.find("td", { "class" : "vbmenu_control smallfont2 delim" }).text
				self.pages = int(re.findall(r'\d+', str(pages))[1])
			else:
				self.pages = 1
				
			print '{heading}: {data}{newline}'.format(heading='#Pages', data=self.pages, newline='\n')
			
			# Begin page iterations
			for i in range(self.pages):
			
				# Construct page url
				pageNumber = str(i+1)
				currentPage = str(self.url+'p'+pageNumber)
				print '{heading}: {data}'.format(heading='Processing', data=currentPage)
				
				# Read HTML
				html = urllib2.urlopen(currentPage).read()
				soup = BeautifulSoup(html)
				
				# Find user post tables by CSS class
				tables = soup.findAll("table", { "class" : "alignc p4 post" })
			
				for table in tables:
					# instantiate new post
					newPost = FlashBPost()
				
					# Start processing post html
					tmp_table = BeautifulSoup(str(table))
				
					# Find post date and number
					post_meta = tmp_table.find("td", {"class" : "thead post-date"}).text.strip().replace('\n', '')
					# Find post body
					post_body = tmp_table.find("div", {"class" : "post_message"}).text.strip().replace('\n', '')
					# Find username
					post_username = tmp_table.find("a", {"class" : "bigusername"}).text.strip().replace('\n', '')
					# Find users registration date and number of posts
					post_userInfo = tmp_table.find("div", {"class" : "post-user-info smallfont"}).text.strip().replace('\n', '')
					#.decode('utf-8')
					
					# Add post data to object
					newPost.add("post_id",int(re.findall(r'(?:#)(.*)', post_meta)[0]))
					newPost.add("post_date",post_meta[0:17])
					newPost.add("post_body",post_body)
					newPost.add("user_name",post_username)
					newPost.add("user_reg_date",post_userInfo[5:13])
					newPost.add("user_total_posts",int("".join(post_userInfo[21:].split())))
				
					# Add post to thread object
					self.addPost(newPost.post)
					time.sleep(0.6)
				
			# Dump data to file
			self.dump()
			
			self.posts_count = len(self.posts)
			processingTime = time.time() - startTime
			print '{heading} {time} {timeHeading} {data} {endText}'.format(heading='Completed in',timeHeading='seconds, with',time=processingTime, data=self.posts_count, endText='processed posts.')
		except Exception as e:
			print e
	
	# Dump all data to either JSON, XLS or CSV format
	def dump(self,self.fileName,self.format):
		try:
			data = {"title":self.title,"url":self.url,"pages":self.pages,"posts_count":self.posts_count,"posts":self.posts}
			if format == 'json':
				with open(fileName, 'w') as tmpFile:
					JSON_data = json.dumps(data)
					tmpFile.write(JSON_data)
				print '{heading}: {data}'.format(heading='File saved as', data=fileName)
			elif format == 'xls':
				with open(fileName, 'wb') as tmpFile:
					xlsData = tablib.Dataset()
					xlsData.headers = ['post_id', 'post_date', 'post_body', 'user_name', 'user_reg_date', 'user_total_posts']
					for post in self.posts:
						xlsData.append([post['post_id'], post['post_date'], post['post_body'], post['user_name'], post['user_reg_date'], post['user_total_posts']])
					tmpFile.write(xlsData.xls)
				print '{heading}: {data}'.format(heading='File saved as', data=fileName)
			elif format == 'csv':
				with codecs.open(fileName, 'a','utf-8') as csvFile:
					csvFile.write('post_id, post_date, post_body, user_name, user_reg_date, user_total_posts\n')
					for post in self.posts:
						csvFile.write(str(post['post_id']) + ',' + post['post_date'] +','+ post['post_body'] +','+ post['user_name']+','+ post['user_reg_date']+','+ str(post['user_total_posts'])+'\n')
				
				print '{heading}: {data}'.format(heading='File saved as', data=fileName)
			else:
				print 'Encoding format missing, please specifiy one, e.g json/xls/csv'
		except Exception as e:
			print e

# Forum post class
class FlashBPost:
	def __init__(self):
		self.post = {}
	def add(self, key, value):
		self.post[key] = value

# Main method for running script
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Flashback.org forum miner')
	parser.add_argument('-l','--link', help='Link to forum thread',required=True)
	parser.add_argument('-o','--output',help='Output file', required=True)
	parser.add_argument('-f','--format',help='Output format <json> <xls> <csv>', required=True)
	args = parser.parse_args()
	
	# Start processing forum thread and dump to file
	newThread = FlashBThread(str(args.link),str(args.output),str(args.format))
	newThread.process()
	
	sys.exit(0)
