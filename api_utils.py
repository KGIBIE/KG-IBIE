# coding=utf-8
import jieba, math, utils, os, requests, pymongo, re
import numpy as np
import bs4
from bs4 import BeautifulSoup



def GetAPI(apiurl, data):
	#data['apikey'] = apikey
	for _ in range(3):
		try:
			r = requests.post('http://shuyantech.com/api/'+apiurl, data=data, timeout=0.5)
			return r.json()
		except: pass
	return {}

def Ment2Ent(ments):
	query = '\t'.join(ments) if type(ments) is not type('') else ments
	return GetAPI('cndbpedia/ment2entmulti', {'q':query}).get('ret', [])

def GetDesc(ent):
	return (GetAPI('cndbpedia/value', {'q':ent, 'attr':'DESC'}).get('ret', [])+[''])[0]

def GetAVP(ent):
	return GetAPI('cndbpedia/avpair', {'q':ent}).get('ret', [])

def GetClick(ents):
	query = '\t'.join(ents) if type(ents) is not type('') else ents
	return GetAPI('cndbpedia/entclick', {'q':query}).get('ret', [])

def GetConcepts(ent):
	#query = '\t'.join(ents) if type(ents) is not type('') else ents 
	return GetAPI('cnprobase/concept', {'q':ent}).get('ret', [])

def GetEntities(ent):
	#query = '\t'.join(ents) if type(ents) is not type('') else ents 
	return GetAPI('cnprobase/entity', {'q':ent}).get('ret', [])

def GetTags(ents):
	query = '\t'.join(ents) if type(ents) is not type('') else ents 
	return GetAPI('cndbpedia/valuemulti', {'q':query, 'attr':'CATEGORY_ZH'}).get('ret', [])

if __name__ == '__main__':
	print('completed')