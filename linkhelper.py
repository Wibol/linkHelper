#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This is a Hexchat addon based on 'link-title.py' (https://github.com/Poorchop/hexchat-scripts/blob/master/link-title.py) and 'shortn' (https://github.com/ishu3101/shortn/blob/master/shortn.py). Thanks to 'Pdog' and 'ishu3101' for their job.

# SETTINGS #
shortener = 'vgd' # You can choose between "vgd" and "isgd" shortener services.
exlist = ('#linux-es') # Channels exclusion list. Eg: ('#channel1') or ('#channel1','channel2').
uagent = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'} # A valid browser User-Agent
############

import hexchat
import html
import requests
import threading

__module_name__ = 'LinkHelper'
__module_author__ = 'Wibol'
__module_version__ = '1.0'
__module_description__ = 'Displays the "nick", "html title" and "short URL" in Hexchat when a HTTP URL is posted in IRC channels.'

events = ('Channel Message', 'Channel Action',
          'Channel Msg Hilight', 'Channel Action Hilight',
          'Channel Notice', 'Server Notice',
          'Private Message', 'Private Message to Dialog',
          'Private Action', 'Private Action to Dialog')

apis = {
	'vgd' : 'https://v.gd/create.php?format=json&url=',
	'isgd' : 'https://is.gd/create.php?format=json&url='
}

def print_title(url, chan, nick, mode, cont):
    if 'http://' in url or 'https://' in url: # Checking HTTP URL
        title = get_response(url, uagent) # Getting URL response avoiding User-Agent lockout
        if (title != None) and (chan not in exlist): # Checking URL title exists and exclusion channel list
            surl = shorten(url) # Getting short URL
            msg = '\x0307{2}: \x03\x02{0} > \x02\x0310{4} \x03'.format(title, url, nick, mode, surl) # Formating message
            cont.command('TIMER 1 DOAT {0} ECHO {1}'.format(chan, msg)) # Displaying URL info message
    return

def get_response(url, agent):
    try:
        response = requests.get(url, headers= agent, cookies= {'CONSENT': 'PENDING+944'})
        response.close()
        if response.ok:
            if response.headers['content-type'].split('/')[0] == 'text':
                html_doc = response.text
                title = snarfer(html_doc)
                title = html.unescape(title)
                title = title.lstrip()
                return title
            else:
                hexchat.prnt('LinkHelper info: Not supported "Content-type" = ' + response.headers['content-type'] + '.')
        else:
            hexchat.prnt('LinkHelper info: HTTP code = ' + str(response.status_code))
    except:
        hexchat.prnt('LinkHelper info: No URL response.')
        return None

def snarfer(html_doc, encoding=''):
    try:
        snarf = html_doc[html_doc.index('<title')+6:html_doc.index('</title>')][:431]
        snarf = snarf[snarf.index('>')+1:]
    except ValueError:
        snarf = ''
    return snarf

def shorten(url):
    try: # Trying to shorten URL
        sresponse = requests.get(apis[shortener] + url)
        surl = sresponse.json()['shorturl']
    except Exception as err:
        hexchat.prnt('LinkHelper info: A shortening error occurred.')
        surl = url
    return surl

def event_cb(word, word_eol, userdata, attr):
    # ignore znc playback
    if attr.time:
        return
    
    word = [(word[i] if len(word) > i else '') for i in range(4)]
    cur_context = hexchat.get_context()
    chan = cur_context.get_info('channel')
    
    for w in word[1].split():
        stripped_word = hexchat.strip(w, -1, 3)
        
        url = stripped_word

        if url.endswith(','):
            url = url[:-1]
                
        threading.Thread(target=print_title, args=(url, chan, word[0], word[2], cur_context)).start()

    return hexchat.EAT_NONE

for event in events:
    hexchat.hook_print_attrs(event, event_cb)

hexchat.prnt( 'Loaded ' +__module_name__ + ' ' + __module_version__ + ' by ' + __module_author__ + '. ' + __module_description__)
