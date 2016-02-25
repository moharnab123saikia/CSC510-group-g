import urllib2
from bs4 import BeautifulSoup
import requests
from os import listdir
from os import getcwd
import json
import csv
import re

def removeNonAscii(s): 
	return "".join(i for i in s if ord(i)<128)

def getReviewsForTripAdvisor(soup):
	reviewArr = []
	header = soup.find("div", id="REVIEWS")
	info = header.find_all("div", class_="reviewSelector")
	cnt = 0
	for review in info:
		print "id..",review['id']
		wrap = review.find("div", class_="wrap")
		if wrap is not None:
			scale = wrap.find("img")['alt'].split(' ')[0]
			text = wrap.find("p", class_="partial_entry").contents[0]
			text = re.sub('<span class="partnerRvw">.*</span>', '', removeNonAscii(text))
			text = re.sub('<img>.*</img>', '', text)
			reviewArr.append({"scale":scale, "review":text})
			cnt = cnt + 1
		if cnt == 5:
			break
	return reviewArr

def getReviewsForFourSquare(soup):
	reviewArr = []
	header = soup.find("ul", id="tipsList")
	info = header.find_all("li", class_="tip tipWithLogging")
	cnt = 0
	for review in info:
		wrap = review.find("div", class_="tipContents").find("p", class_="tipText")
		if wrap is not None:
			text = re.sub('<[^>]*>', '', str(wrap))
			reviewArr.append({"scale":"", "review":text})
			cnt = cnt + 1
		if cnt == 5:
			break
	return reviewArr

def getReviewsForYelp(soup):
	reviewArr = []
	header = soup.find("ul", class_="ylist-bordered")
	info = header.find_all("li", recursive=False)
	cnt = 0
	for review in info:
		wrap = review.find("div", class_="review-wrapper").find("p", {"itemprop":"description"})
		if wrap is not None: 
			text = removeNonAscii(wrap.contents[0])
			scale = review.find("div", class_="review-wrapper").find("meta", {"itemprop":"ratingValue"})['content']
			reviewArr.append({"scale":scale, "review":text})
			cnt = cnt + 1
		if cnt == 5:
			break
	print reviewArr
	return reviewArr

def crawlpage(restaurant_id, restaurant_name, url_list):
	count = 0
	finalJson = {}
	jsonData = {}
	data = {}
	yelp_obj = {}
	foursq_obj = {}
	trip_obj = {}
	for weburl in url_list:
		print weburl	
		page = requests.get(weburl)
		soup = BeautifulSoup(page.text,'html.parser')
		for e in soup.findAll('br'):
    			e.extract()	

		if count == 0:
			print "yelp"
			header = soup.find("div", class_="biz-page-header-left")
			info = header.find("div", class_="biz-rating")
			overall_rating = info.find("i", class_="star-img")['title'].split(' ')[0]
			total_reviews = info.find("span", class_="review-count").find("span").contents[0]
			print overall_rating
			print total_reviews
			yelp_obj['rating'] = overall_rating
			yelp_obj['count'] = total_reviews
			yelp_obj['reviews'] = getReviewsForYelp(soup)
			yelp_obj['url'] = weburl

		elif count == 1:
			print "tripadvisor"
			info = soup.find("div", class_="rs rating")
			overall_rating = info.find("img")['content']
			total_reviews = info.find("a")['content']
			print overall_rating
			print total_reviews
			trip_obj['rating'] = overall_rating
			trip_obj['count'] = total_reviews
			trip_obj['reviews'] = getReviewsForTripAdvisor(soup)
			trip_obj['url'] = weburl

		elif count == 2:
			print "foursquare"
			header = soup.find("div", class_="attrBar")
			info = header.find("div", class_="leftColumn")
			print info
			overall_rating = info.find("span", {"itemprop":"ratingValue"}).contents[0]
			total_reviews = info.find("span", {"itemprop":"ratingCount"}).contents[0]
			print overall_rating
			print total_reviews
			foursq_obj['rating'] = overall_rating
			foursq_obj['count'] = total_reviews
			foursq_obj['reviews'] = getReviewsForFourSquare(soup)
			foursq_obj['url'] = weburl

		count = count + 1

	data['yelp'] = yelp_obj
	data['foursquare'] = foursq_obj
	data['tripadvisor'] = trip_obj
	jsonData['name'] = restaurant_name
	jsonData['data'] = data
	finalJson[restaurant_id] = jsonData
	return finalJson

def fetchNameFromUrl(url):
	page = requests.get(url)
	soup = BeautifulSoup(page.text,'html.parser')
	name = soup.find("h1", class_="biz-page-title").contents[0]
	print name
	return name.strip()

def uploadJsonToServer():
	print 'in upload'
	
def crawlCsvAndCreateJsonFile(fileName, jsonfile):
	ifile  = open(fileName, "rb")
	jsonFile = open(jsonfile,"w")
	reader = csv.reader(ifile)
	rownum = 0
	mainJson = {}
	jsonArray = []
	for row in reader:
		if rownum == 0:
			header = row
		else:
			url_list = []
			rid = row[0]
			name = fetchNameFromUrl(row[1])
			url_list.append(row[1])
			url_list.append(row[2])
			url_list.append(row[3])
		    	json_data = crawlpage(rid, name, url_list)
			jsonArray.append(json_data)
		rownum += 1
	mainJson['restaurants'] = jsonArray
	print mainJson
	jsondata = json.dumps(mainJson)
	jsonFile.write(jsondata)
	ifile.close()
	jsonFile.close()
	uploadJsonToServer()

crawlCsvAndCreateJsonFile('sample-restaurants-link.csv', 'restaurants.json');
