# -*- coding: UTF-8 -*-
# This is a Hexchat addon based on 'link-title.py' (https://github.com/Poorchop/hexchat-scripts/blob/master/link-title.py) and 'shortn' (https://github.com/ishu3101/shortn/blob/master/shortn.py). Thanks to 'Pdog' and 'ishu3101' for their job.
#
# SETTINGS #
canales = ('#linux-es',) # Channel exclusion list. Eg: ('#channel1',) or ('#channel1','channel2').
apodos = ('NewsBot',) # Nick exclusion list. Eg: ('nickl1',) or ('nickl1','nick2').
agente = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0'} # A valid browser User-Agent
acortador = 'isgd' # You can choose between "isgd" and "vgd" shortener services.
############

import hexchat
import html
import requests
import threading

__module_name__ = 'LinkHelperBot'
__module_author__ = 'Wibol'
__module_version__ = '1.2'
__module_description__ = 'A Python3 Hexchat addon that sends to IRC channels the "nick", "html title" and "short URL" when a HTTP URL is posted.'

eventos = (
    'Channel Message', 'Channel Action',
    'Channel Msg Hilight', 'Channel Action Hilight',
    'Channel Notice', 'Server Notice',
    'Private Message', 'Private Message to Dialog',
    'Private Action', 'Private Action to Dialog'
)

apis = {
    'isgd' : 'https://is.gd/create.php?format=json&url=',
	'vgd' : 'https://v.gd/create.php?format=json&url='
}

def event_cb(word, word_eol, userdata, attributes):
    contexto = hexchat.get_context()
    canal = contexto.get_info('channel')
    apodo = hexchat.strip(word[0]) #Stripping nick attributes

    if attributes.time: # ignore znc playback
        return hexchat.EAT_HEXCHAT
    
    if (canal not in canales) and (apodo not in apodos):
        for elemento in word[1].split():
            palabra = hexchat.strip(elemento, -1, 3)
            if palabra.endswith(','):
                palabra = palabra[:-1]
            if ('http://' in palabra) or ('https://' in palabra): # Checking is HTTP URL
                threading.Thread(target=print_msg, args=(word[0], palabra, canal)).start()
            else:
                continue

    return hexchat.EAT_NONE

def print_msg(apodo, larga, canal):
    titulo = get_html(larga) # Getting URL response avoiding User-Agent lockout
    if (titulo != None): # Checking URL title exists and exclusion channel list
        corta = get_shortened(larga) # Getting short URL
        mensaje = '\x0307{}: \x03\x02{} > \x02\x0310{} \x03'.format(apodo, titulo, corta) # Formating message
        hexchat.command('TIMER 1 DOAT {} ECHO {}'.format(canal, mensaje)) # Displaying URL message

def get_html(larga):
    try:
        respuesta = requests.get(larga, headers= agente, cookies= {'CONSENT': 'PENDING+944'}, timeout=(2,4))
        respuesta.close()
        if respuesta.ok:
            if respuesta.headers['content-type'].split('/')[0] == 'text':
                texto = respuesta.text
                titulo = get_title(texto)
                titulo = html.unescape(titulo)
                titulo = titulo.strip()
                return titulo
            else:
                hexchat.prnt('LinkHelperBot info: Not supported "Content-type" = ' + respuesta.headers['content-type'] + '.')
        else:
            hexchat.prnt('LinkHelperBot info: HTTP code = ' + str(respuesta.status_code))
    except requests.exceptions.RequestException as error:
        hexchat.prnt('LinkHelperBot info: No URL response. ' + error)
        return None

def get_title(texto):
    try:
        titulo = texto[texto.find('<title') + 6 : texto.find('</title>')][:431]
        titulo = titulo[titulo.find('>') + 1 :]
    except ValueError as error:
        hexchat.prnt('LinkHelperBot info: A getting title error occurred. ' + str(error))
        titulo = ''
    return titulo

def get_shortened(larga):
    try: # Trying to shorten URL
        respuesta = requests.get(apis[acortador] + larga, timeout=(2,4))
        corta = respuesta.json()['shorturl']
        respuesta.close()
    except requests.exceptions.RequestException as error:
        hexchat.prnt('LinkHelperBot info: A shortening error occurred. ' + error)
        corta = larga
    return corta

for evento in eventos:
    hexchat.hook_print_attrs(evento, event_cb)

hexchat.prnt( 'Loaded ' +__module_name__ + ' ' + __module_version__ + ' by ' + __module_author__ + '. ' + __module_description__)
