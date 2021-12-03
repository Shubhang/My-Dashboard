# import json
# import requests
# api_key = '718B338CC4'
# api_url = 'https://api.smmry.com'
from progress.bar import Bar
import urllib.request
from lxml import html
import requests
import json
from bs4 import BeautifulSoup
import re, pdb, sys, math
from collections import defaultdict
import datetime
from .reduction import Reduction


## globals
natlaw_urls = {
	'Antitrust Law': 'https://www.natlawreview.com/practice-groups/antitrust-FTC-competition-mergers',
	'Bankruptcy & Restructuring': 'https://www.natlawreview.com/practice-groups/Bankruptcy-Restructuring-Debt',
	'Biotech, Food & Drug': 'https://www.natlawreview.com/practice-groups/Biotech-FDA-Drug-Food',
	'Business of Law': 'https://www.natlawreview.com/practice-groups/Legal-Marketing-Law-Firm-Business',
	'Construction & Real Estate': 'https://www.natlawreview.com/practice-groups/Construction-Real-Estate',
	'Cybersecurity Media & FCC': 'https://www.natlawreview.com/practice-groups/Media-Privacy-Internet-FCC',
	'Election & Legislative': 'https://www.natlawreview.com/practice-groups/election-lobbying-campaign', 
	'Environmental & Energy': 'https://www.natlawreview.com/practice-groups/Environment-Energy-EPA', 
	'Family, Estates & Trusts': 'https://www.natlawreview.com/practice-groups/divorce-estate-trusts-family', 
	'Financial, Securities & Banking': 'https://www.natlawreview.com/practice-groups/Financial-SEC-Bank-Security', 
	'Global': 'https://www.natlawreview.com/practice-groups/global-legal-news-trade-law', 
	'Health Care Law': 'https://www.natlawreview.com/practice-groups/Healthcare-Health-Law-OIG', 
	'Immigration': 'https://www.natlawreview.com/practice-groups/Immigration-USCIS-Visa', 
	'Insurance': 'https://www.natlawreview.com/practice-groups/insurance-reinsurance-surety', 
	'Intellectual Property Law': 'https://www.natlawreview.com/practice-groups/IP-Patent-Trademark-Copyright', 
	'Labor & Unemployment': 'https://www.natlawreview.com/practice-groups/Labor-Employment-NLRB-EEOC', 
	'Litigation': 'https://www.natlawreview.com/practice-groups/Litigation-Dispute-Trial', 
	'Public Services, Infrastructure, Transportation': 'https://www.natlawreview.com/practice-groups/Public-Service-Infrastructure-Transportation', 
	'Tax': 'https://www.natlawreview.com/practice-groups/Tax-Treasury-IRS', 
	'White Collar Crime & Consumer Rights': 'https://www.natlawreview.com/practice-groups/White-Collar-Crime-and-Consumer-Rights'
}


jdsupra_urls = {
	'Labor & Employment': 'https://www.jdsupra.com/law-news/labor-employment/', 
	'Finance & Banking': 'https://www.jdsupra.com/law-news/finance-banking-law/', 
	'General Business': 'https://www.jdsupra.com/law-news/commercial-contracts-law/', 
	'Science, Computers & Technology': 'https://www.jdsupra.com/law-news/science-technology-law/', 
	'International Trade': 'https://www.jdsupra.com/law-news/international-trade-law/', 
	'Securities': 'https://www.jdsupra.com/law-news/securities-law/', 
	'Health': 'https://www.jdsupra.com/law-news/health-law/', 
	'Business Organization': 'https://www.jdsupra.com/law-news/business-organizations/', 
	'Administrative Agency': 'https://www.jdsupra.com/law-news/administrative-law/', 
	'Intellectual Property': 'https://www.jdsupra.com/law-news/ip-law/', 
	'Tax': 'https://www.jdsupra.com/law-news/tax-law/', 
	'Privacy': 'https://www.jdsupra.com/law-news/privacy/', 
	'Consumer Protection': 'https://www.jdsupra.com/law-news/consumer-protection-law/', 
	'Communications & Media': 'https://www.jdsupra.com/law-news/communications-media-law/', 
	'Energy & Utilities': 'https://www.jdsupra.com/law-news/environment-energy-law/', 
	'Insurance': 'https://www.jdsupra.com/law-news/insurance-law/', 
	'Residential Real Estate': 'https://www.jdsupra.com/law-news/residential-real-estate-law/', 
	'Antitrust & Trade Regulation': 'https://www.jdsupra.com/law-news/antitrust-trade-regulation/'
}

def articleSummary(url, source):
	'''
	source: nat_law_review, jdsupra
	'''

	reduction = Reduction()
	reduction_ratio = 0.2

	if source == 'nat_law_review':

		# logic for scraping nat_law_review
		req = requests.get(url)
		soup = BeautifulSoup(req.content, 'html.parser')
		text = soup.findAll("p")
		if text == []:
			# failed to generate summary
			return 0
		kill = 0
		for i, item in enumerate(text):
			if item.text == "About this Author":
				kill = i
		text = ' '.join([item.text for item in text[:kill]])
		return str(text[:1000] + '...')
		# return ''.join([' '.join(reduction.reduce(text, reduction_ratio)), '.'])[:-1] # remove double . at end

	elif source == 'jdsupra':

		# logic for scraping jdsupra
		req = requests.get(url)
		soup = BeautifulSoup(req.content, 'html.parser')
		theDiv = soup.find('div', attrs={'class': 'jds-main-content'})
		text = theDiv.find_all("p")
		# text_lists = theDiv.find_all("li") # lists in article. Ignore for now
		if soup.find('div', attrs={'class': 'defaulttag'}):
			text = soup.find('div', attrs={'class': 'defaulttag'}).find_all('p')
		
		if text == []:
			# failed to generate article
			return 0
		
		try:
			if text[-1].find_all("a")[0].text == "View source":
				text.pop(-1)
		except:
			pass # last p doesn't have a link in it
		
		text = ' '.join([item.text for item in text])
		return str(text[:1000] + '...')
		# return ''.join([' '.join(reduction.reduce(text, reduction_ratio)), '.'])[:-1] # remove double . at end


def yahooToNatlawURL(yahooSector):
	n = natlaw_urls
	yahoo_to_natlaw_mapping = {
	'Basic Materials':[
		['Construction & Real Estate', n['Construction & Real Estate']]
	],
	'Communication Services':[
		['Cybersecurity Media & FCC', n['Cybersecurity Media & FCC']]
	],
	'Consumer Cyclical': None,
	'Consumer Defensive': None,
	'Energy':[
		['Environmental & Energy', n['Environmental & Energy']]
	],
	'Financial Services':[
		['Financial, Securities & Banking', n['Financial, Securities & Banking']], 
		['Insurance', n['Insurance']], 
		['Public Services, Infrastructure, Transportation', n['Public Services, Infrastructure, Transportation']]
	],
	'Healthcare':[
		['Health Care Law', [n['Health Care Law']]]
	],
	'Industrials': [
		['Public Services, Infrastructure, Transportation', n['Public Services, Infrastructure, Transportation']]
	],
	'Real Estate':[
		['Construction & Real Estate', n['Construction & Real Estate']]
	],
	'Technology':[
		['Cybersecurity Media & FCC', n['Cybersecurity Media & FCC']], 
		['Intellectual Property Law', n['Intellectual Property Law']]
	],
	'Utilities': [
		['Environmental & Energy', n['Environmental & Energy']],
		['Public Services, Infrastructure, Transportation', n['Public Services, Infrastructure, Transportation']]
	]
	}

	URLs = [
		['Antitrust Law', natlaw_urls['Antitrust Law']]
	]

	if yahoo_to_natlaw_mapping[yahooSector] == None:  # Check special None case
		pass  
	else:
		URLs.extend(yahoo_to_natlaw_mapping[yahooSector])
	return URLs


def yahooToJdsupra(yahooSector):
	j = jdsupra_urls
	yahoo_to_jdsupra_mapping = {
	'Basic Materials':[
		['International Trade', j['International Trade']]
	],
	'Communication Services':[
		['Intellectual Property', j['Intellectual Property']], 
		['Communications & Media', j['Communications & Media']]
	],
	'Consumer Cyclical': None,
	'Consumer Defensive': [
		['Consumer Protection', j['Consumer Protection']]
	],
	'Energy':[
		['Energy & Utilities', j['Energy & Utilities']]
	],
	'Financial Services':[
		['Finance & Banking', j['Finance & Banking']], 
		['Securities', j['Securities']], 
		['Business Organization', j['Business Organization']], 
		['Tax', j['Tax']], 
		['Insurance', j['Insurance']]
	],
	'Healthcare':[
		['Health', j['Health']]
	],
	'Industrials': [
		['Labor & Employment', j['Labor & Employment']], 
		['Business Organization', j['Business Organization']], 
		['Administrative Agency', j['Administrative Agency']]
	],
	'Real Estate':[
		['Residential Real Estate', j['Residential Real Estate']]
	],
	'Technology':[
		['Science, Computers & Technology', j['Science, Computers & Technology']], 
		['Intellectual Property', j['Intellectual Property']], 
		['Privacy', j['Privacy']]
	],
	'Utilities': [
		['Energy & Utilities', j['Energy & Utilities']]
	]
	}


	URLs = [
		['General Business', jdsupra_urls['General Business']], 
		['Antitrust & Trade Regulation', jdsupra_urls['Antitrust & Trade Regulation']]
	]
	if yahoo_to_jdsupra_mapping[yahooSector] == None: # Check special None case
		pass
	else:
		URLs.extend(yahoo_to_jdsupra_mapping[yahooSector])
	return URLs


def getCompliance(companyObject, source, custom_sectors=[], multiplier=3):

	legal_sources = ['nat_law_review', 'jdsupra']
	# 'http://www.natlawreview.com'
	# https://www.jdsupra.com/law-news/
	# factiva?
	if source not in legal_sources:
		raise Exception(f'Invalid legal source. Valid legal sources are {legal_sources}')


	# set sectors
	if custom_sectors != []:
		complianceURLs = custom_sectors
	else:
		# get company sector URLs
		yahoo_sector = companyObject.getSector()
		if source == 'nat_law_review':	
			complianceURLs = yahooToNatlawURL(yahoo_sector)  
		elif source == 'jdsupra':
			complianceURLs = yahooToJdsupra(yahoo_sector)

	bar = Bar('Processing', max=multiplier*len(complianceURLs))
	summaries = []
	dates = []
	summarySectors = []
	titles = []
	links = []
	for URL in complianceURLs:
		page = requests.get(URL[1]) # index 1 is URL, 0 is sector
		tree = html.fromstring(page.content)

		# get summary, date, and sector summary is from
		accessed_indexes = []
		for i in range(multiplier):
			bar.next()
			summarySectors.append(URL[0])

			if source == 'nat_law_review':
				base_url = 'http://www.natlawreview.com'

				def get_date(index):
					# get and format date
					date = tree.xpath('//*[@id="content"]/div[3]/div[2]/table/tbody/tr['+str(index+1)+']/td[1]')[0].text_content()
					r = re.compile("([0-9]+)([a-zA-Z]+)")  
					date = ' '.join(r.match(str(date).strip()).groups())
					return date
				
				# try articles until we can make a summary
				j = multiplier
				article_link = tree.xpath('//*[@id="content"]/div[3]/div[2]/table/tbody/tr['+str(i+1)+']/td[2]/a/@href')[0]
				article_title = tree.xpath('//*[@id="content"]/div[3]/div[2]/table/tbody/tr['+str(i+1)+']/td[2]/a/text()')[0]
				url =  base_url + article_link
				summary = articleSummary(url, source)
				if summary:
					summaries.append(summary)
					dates.append(get_date(i))
					titles.append(article_title)
					links.append(url)
				else:
					success = False
					while not success:
						try:
							article_link = tree.xpath('//*[@id="content"]/div[3]/div[2]/table/tbody/tr['+str(j+1)+']/td[2]/a/@href')[0]
							article_title = tree.xpath('//*[@id="content"]/div[3]/div[2]/table/tbody/tr['+str(j+1)+']/td[2]/a/text()')[0]
							url =  base_url + article_link
							summary = articleSummary(url, source)
							if summary:
								if j in accessed_indexes:
									j += 1
								else:
									summaries.append(summary)
									dates.append(get_date(j))
									titles.append(article_title)
									links.append(url)
									accessed_indexes.append(j)
									success = True
							else:
								j += 1
						except:
							# reached end of articles
							summaries.append(None)
							dates.append(None)
							titles.append(None)
							links.append(None)


			elif source == 'jdsupra':
				base_url = 'https://www.jdsupra.com'

				def get_date(index):
					# get and format date
					date = tree.xpath('//*[@id="PracticeCenterForm"]/div[3]/div[2]/div[1]/div[2]/div['+str(index+1)+']/div[2]/div/time')[0].text_content()
					s = datetime.datetime.strptime(date, "%m/%d/%Y")
					date = s.strftime('%d %b')
					return date

				# try articles until we can make a summary
				j = multiplier
				article_link = tree.xpath('//*[@id="PracticeCenterForm"]/div[3]/div[2]/div[1]/div[2]/div['+str(i+1)+']/div[2]/h2/a/@href')[0]
				article_title = tree.xpath('//*[@id="PracticeCenterForm"]/div[3]/div[2]/div[1]/div[2]/div['+str(i+1)+']/div[2]/h2/a/text()')[0]
				url =  base_url + article_link
				summary = articleSummary(url, source)
				if summary:
					summaries.append(summary)
					dates.append(get_date(i))
					titles.append(article_title)
					links.append(url)
				else:
					success = False
					while not success:
						try:
							article_link = tree.xpath('//*[@id="PracticeCenterForm"]/div[3]/div[2]/div[1]/div[2]/div['+str(j+1)+']/div[2]/h2/a/@href')[0]
							article_title = tree.xpath('//*[@id="PracticeCenterForm"]/div[3]/div[2]/div[1]/div[2]/div['+str(j+1)+']/div[2]/h2/a/text()')[0]
							url =  base_url + article_link
							summary = articleSummary(url, source)
							if j in accessed_indexes:
									j += 1
							else:
								summaries.append(summary)
								dates.append(get_date(j))
								titles.append(article_title)
								links.append(url)
								accessed_indexes.append(j)
								success = True
						except:
							# reached end of articles
							summaries.append(None)
							dates.append(None)
							titles.append(None)
							links.append(None)
							
    
	bar.finish()
	summaries_with_info = []

	# build article + date + sector
	for i in range(len(summaries)):
		entry = {}
		entry.update({'date': dates[i]})
		entry.update({'sector': summarySectors[i]})
		entry.update({'text': summaries[i]})
		entry.update({'title': titles[i]})
		entry.update({'link': links[i]})
		summaries_with_info.append(entry)

	return summaries_with_info



