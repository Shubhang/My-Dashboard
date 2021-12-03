jdsupra_urls = [
		['https://www.jdsupra.com/law-news/labor-employment/', 'Labor & Employment '], #0
		['https://www.jdsupra.com/law-news/finance-banking-law/', 'Finance & Banking '], #1
		['https://www.jdsupra.com/law-news/commercial-contracts-law/', 'General Business '], #2
		# ['https://www.jdsupra.com/law-news/civil-procedure/', 'Civil Procedure '], 
		['https://www.jdsupra.com/law-news/science-technology-law/', 'Science, Computers & Technology '],  #3
		['https://www.jdsupra.com/law-news/international-trade-law/', 'International Trade '], #4
		['https://www.jdsupra.com/law-news/securities-law/', 'Securities '],  #5
		['https://www.jdsupra.com/law-news/health-law/', 'Health '],  #6
		['https://www.jdsupra.com/law-news/business-organizations/', 'Business Organization '], #7
		# ['https://www.jdsupra.com/law-news/elections-and-politics/', 'Elections & Politics '], 
		['https://www.jdsupra.com/law-news/administrative-law/', 'Administrative Agency '], #8
		['https://www.jdsupra.com/law-news/ip-law/', 'Intellectual Property '], #9
		['https://www.jdsupra.com/law-news/tax-law/', 'Tax '], #10
		['https://www.jdsupra.com/law-news/privacy/', 'Privacy '], #11
		['https://www.jdsupra.com/law-news/consumer-protection-law/', 'Consumer Protection '], #12
		['https://www.jdsupra.com/law-news/communications-media-law/', 'Communications & Media '], #13
		# ['https://www.jdsupra.com/law-news/civil-rights/', 'Civil Rights '], 
		# ['https://www.jdsupra.com/law-news/environmental-law/', 'Environmental '], 
		['https://www.jdsupra.com/law-news/environment-energy-law/', 'Energy & Utilities '], #14
		['https://www.jdsupra.com/law-news/insurance-law/', 'Insurance '], #15
		# ['https://www.jdsupra.com/law-news/civil-remedies/', 'Civil Remedies '],
		['https://www.jdsupra.com/law-news/residential-real-estate-law/', 'Residential Real Estate '], #16
		# ['https://www.jdsupra.com/law-news/constitutional-law/', 'Constitutional Law '],
		['https://www.jdsupra.com/law-news/antitrust-trade-regulation/', 'Antitrust & Trade Regulation '], #17
		# ['https://www.jdsupra.com/law-news/government-contracting/', 'Government Contracting ']
	]

res = {}

for u in jdsupra_urls:
    res.update({u[1]: u[0]})

print(res)