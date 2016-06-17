#!/usr/bin/env python
import re
import json
import codecs
import sys
import getopt
import requests
import time
import pprint

#### TODO: OAuth tokens expire after a few months. See  https://feedly.com/v3/auth/dev
oauthtoken = 'OAuth A3sdfsdf-ZsdfsA2-wsdfFK:feedlydev'

verbose=False
if len(sys.argv) > 1 and sys.argv[1] == '-v':
  verbose=True

streamWriter = codecs.lookup('utf-8')[-1]
sys.stdout = streamWriter(sys.stdout)

def markasread(feedly_items, rules):
  mark_ids = []
  retard_ids = []
  pp = pprint.PrettyPrinter()
  for article in feedly_items:
    #print "NEW ARTICLE %s: %s" % (article['origin']['streamId'], article['title'])
    for rule in rules:
      if ((rule['streamId'] == article['origin']['streamId']) or (rule['streamId'] == 'ALL')):
        #print "RULE:"
        #pp.pprint(rule)
        #print("SCAN:", article[rule['filter_on']])
        for keyword in rule['keywords']:
          #pp.pprint(keyword)
          p = re.compile(keyword, re.I)
          if rule['filter_on'] in article:
            if (type(article[rule['filter_on']]) is list):
                #print "LIST"
                for item in article[rule['filter_on']]:
                    m = p.search( item )
                    if ( m != None ):
                      mark_ids.append( article['id'] )
                      if verbose: print "MATCHLISTITEM! %s : %s %s" % (keyword, article['origin']['streamId'], article[rule['filter_on']])
            #else:
            elif (type(article[rule['filter_on']]) is unicode):
                m = p.search( article[rule['filter_on']] )
                if ( m != None ):
                  mark_ids.append( article['id'] )
                  if verbose: print "MATCHSTR! %s : %s %s" % (keyword, article['origin']['streamId'], article[rule['filter_on']])
  if mark_ids:
    payload = '{"action":"markAsRead","type":"entries","entryIds":["%s"]}' % '", "'.join(mark_ids)
    post = requests.post('http://cloud.feedly.com/v3/markers?ct=Menere+0.7.2.2', data=payload, headers=headers)
    payload = '{"entryIds":["%s"]}' % '", "'.join(mark_ids)
    # add label "autoreader"
    put = requests.put('http://cloud.feedly.com/v3/tags/user%2ff5b27b59-da91-4101-929f-2d3ea4f5ca46%2ftag%2fautoreader?ct=Menere+0.7.2.2', data=payload, headers=headers)
  return

def deduplicate_wired(feedly_items):
  mark_ids = []
  seen = set()
  try:
    for article in feedly_items:
      try:
        title=article['title']
      except KeyError:
        title=article['origin']['title']
      if title not in seen:
        seen.add(title)
      else:
        mark_ids.append( article['id'] )
        #print "%s : %s" % (article['origin']['streamId'], article['title'])
  except KeyError:
    print "WARNING! No title on article."
    print "%s" % (article['origin']['streamId'])
    print ', '.join("%s: %s" % item for item in article.items())
    pass
  if mark_ids:
    payload = '{"action":"markAsRead","type":"entries","entryIds":["%s"]}' % '", "'.join(mark_ids)
    post = requests.post('http://cloud.feedly.com/v3/markers?ct=Menere+0.7.2.2', data=payload, headers=headers)
    payload = '{"entryIds":["%s"]}' % '", "'.join(mark_ids)
    # add label "duplicate"
    put = requests.put('http://cloud.feedly.com/v3/tags/user%2ff5b27b59-da91-4101-929f-2d3ea4f5ca46%2ftag%2fduplicate?ct=Menere+0.7.2.2', data=payload, headers=headers)
  return

def lectureenretard(feedly_items):
  retard_ids = []
  for article in feedly_items:
    oldtimestamp = int(time.time() - 2419200 )  # 2505600=29 jours   2419200=28 jours
    oldtimestamp *= 1000 # millis
    if (article['published'] < oldtimestamp):
      if verbose: print "lectureenretard: %s" % article['title']
      retard_ids.append( article['id'] )
  if retard_ids:
    payload = '{"entryIds":["%s"]}' % '", "'.join(retard_ids)
    # add label "lectureenretard"
    put = requests.put('http://cloud.feedly.com/v3/tags/user%2ff5b27b59-da91-4101-929f-2d3ea4f5ca46%2ftag%2flectureenretard?ct=Menere+0.7.2.2', data=payload, headers=headers)
  return

# A few items:
#url = 'http://cloud.feedly.com/v3/streams/user%2ff5b27b59-da91-4101-929f-2d3ea4f5ca46%2fcategory%2fglobal.all/contents?ct=Menere+0.7.2.2&count=4&ranked=newest&newerThan=1376489059495'
# All Unread:
url = 'http://cloud.feedly.com/v3/streams/user%2ff5b27b59-da91-4101-929f-2d3ea4f5ca46%2fcategory%2fglobal.all/contents?ct=Menere+0.7.2.2&count=1000&unreadOnly=True'
headers = {'Accept':'*/*', 'Authorization':oauthtoken}
r = requests.get(url, headers=headers)
#print r.request.headers 
#print r.text
if r.status_code == 401:
  print "OAuth token has expired (renew it at https://feedly.com/v3/auth/dev using zboubi@gmail.com)"
  exit(1)
data = r.json()
#print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

rules = []
rules.append({
              'streamId' : 'ALL',
              'filter_on': 'title',
              'keywords' : ['windows 10','ask ariely','net neutrality','meditation','cosplay','costume','windows 10','3d print','Super Bowl', 'Superbowl']
            })
rules.append({
              'streamId' : 'feed/http://lifehacker.com/vip.xml',
              'filter_on': 'title',
              'keywords' : [ 'wallpaper','windows downloads','open thread','featured desktop','featured workspace','announcements','ask the readers','help yourself','best time to buy','^gawker','^deadspin','^kotaku','^gizmodo','^jezebel','^how we work','and more deals']
            })
rules.append({
              'streamId' : 'feed/http://lifehacker.com/vip.xml',
              'filter_on': 'keywords',
              'keywords' : [ 'kinja deals']
            })
rules.append({
              'streamId' : 'feed/http://fulltextrssfeed.com/feeds.wired.com/wired/index',
              'filter_on': 'title',
              'keywords' : ['wired space photo']
            })
rules.append({
              'streamId' : 'feed/http://www.ritholtz.com/blog/feed/',
              'filter_on': 'title',
              'keywords' : ['media appearance','housing',' reads$']
            })
rules.append({
              'streamId' : 'feed/http://www.ritholtz.com/blog/feed/',
              'filter_on': 'author',
              'keywords' : ['^(?!Barry Ritholtz)']
            })
rules.append({
              'streamId' : 'feed/http://fulltextrssfeed.com/feeds.newscientist.com/science-news',
              'filter_on': 'title',
              'keywords' : ['today on new scientist']
            })
rules.append({
              'streamId' : 'feed/http://www.adafruit.com/blog/feed/',
              'filter_on': 'title',
              'keywords' : ['show and tell','ask an? ','part finder friday','in stock','^new product','^new guide:','^updated product','^updated tutorial','from the mail bag','distributor spotlight','#piday','#3DPrinting','3D Hangout','Layer by Layer']
            })
rules.append({
              'streamId' : 'feed/http://fulltextrssfeed.com/iscxml.sans.org/rssfeed.xml',
              'filter_on': 'title',
              'keywords' : ['isc stormcast', 'security advisory for ']
            })
rules.append({
              'streamId' : 'feed/http://www.lesnumeriques.com/rss.xml',
              'filter_on': 'title',
              'keywords' : ['casque audio', 'casque nomade', 'nikon','barre de son','enceinte','tests de la semaine','^bon plan',' intras','fuji','olympus','leica','semaine Focus','panasonic','focus num','compact expert','pentax']
            })
rules.append({
              'streamId' : 'feed/http://www.vice.com/rss',
              'filter_on': 'title',
              'keywords' : ['bad cop blotter', 'comics: ','cry-baby of the ','vice vs video game','lgbt',' trans ','racist']
            })

markasread(data['items'], rules)
lectureenretard(data['items'])
deduplicate_wired(data['items'])

