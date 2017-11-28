#-*- coding: utf-8 -*- 
import re
import os
import time
import datetime

from django.db.models import Q
from django.conf import settings
from django.contrib.gis.utils import GeoIP

from bs4 import BeautifulSoup
from base.models import APILogger, Profile
from base.models_dic import Country
from kinoinfo_folder.func import del_separator, low

def get_formated_date(format):
    """
    получить отформатированную текущую дату, время
    """
    now = datetime.datetime.now()
    return now.strftime(format)


def get_client_ip(request):
    """
    получение IP пользователя
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    return ip


def identification_ip(login, ip):
    """
    проверка IP посетителя, для идентификации клиента API
    """
    # получаю данные о клиентах из конфиг. файла
    soup = BeautifulSoup(open('%s/conf.xml' % settings.API_CLIENTS_PATH))
    # перебираю существующих клиентов
    for i in soup.findAll('client'):
        # если логин посетителя и логин клиента совпадают то:
        if i['nic'] == login:
            # беру его диапозон IP из конфига
            # разбиваю IP по точке для получения последней цифровой части
            # начало диапозона
            ip_first = i['ip'].split('.')
            # конец диапозона
            ip_last = i['to'].split('.')
            # если у клиента точный ip
            if ip_first[2] == ip_last[2] and ip_first[3] == ip_last[3]:
                ip_client = '%s.%s.%s.%s' % (ip_first[0], ip_first[1], ip_first[2], ip_first[3])
                if ip_client == ip: return True
            # если у клиента диапозон ip по 4 октету
            elif ip_first[2] == ip_last[2] and ip_first[3] != ip_last[3]:        
                for j in xrange(int(ip_last[3])+1):
                    ip_client = '%s.%s.%s.%s' % (ip_first[0], ip_first[1], ip_first[2], j)
                    if ip_client == ip: return True
            # если у клиента диапозон ip по 3 и 4 октету
            elif ip_first[2] != ip_last[2]: 
                for j in xrange(int(ip_last[2])+1):
                    for k in xrange(int(ip_last[3])+1):
                        ip_client = '%s.%s.%s.%s' % (ip_first[0], ip_first[1], j, k)
                        if ip_client == ip: return True
    # если IP адрес пользователя и IP адрес клинта совпадают, возвращаю 'True', иначе 'False'
    return False


def clear_quotes(var):  
    """
    очистка переменных от лишних символов (для корректной xml структуры)
    """
    if isinstance(var, unicode):
        var = var.encode('utf-8')
        
    return str(var).replace('&#039;', '')\
                    .replace('&#034;', '')\
                    .replace('"', '')\
                    .replace('&', '&#38;')\
                    .replace('<i>', '')\
                    .replace('</i>', '')\
                    .replace('<br />', ' ')\
                    .replace('<br>', '$')\
                    .replace('<', '')\
                    .replace('>', '')\
                    .replace('', '')\
                    .replace('#..\\Кинорынок\\62_готовые\\ЦПШ.doc#\\t1,8521,8586,0,, HYPERLINK http://www.rasput', '')\
                    .replace('#..\\Documents and Settings\\Administrator\\Local Settings\\Temporary Inter', '')\
                    .strip()


def clear_links(var):
    """
    очистка ссылок от лишних символов
    """
    soup = BeautifulSoup(var)
    # исправляю некорректный url
    result = var.replace('http:\\\\', 'http://')
    # исправленный url положил в 'result'
    # в ссылке ищу тег 'a'
    for link in soup.findAll('a'):
        # если нахожу, то получаю значение и привожу к кодировке utf-8
        result = link.string.encode('utf-8')
        # полученное значение положил в 'result'
    # ищу в 'result' необходимую последовотельность символов
    r = re.search('\#\w+', result) is None
    # результат поиска записываю в 'r'
    # если результат поиска положительный то:
    if r == False:
        # извлекаю url
        res = re.findall('[a-zA-Z0-9\.\:\/\?\&\=\-\+\%\_]+', result)
        # извлеченный url попадает в словарь 'res'
        # и наконец в конечный 'result' записываю url из словаря 'res'
        result = res[0]
    # возвращаю чистую переменную
    return clear_quotes(result)

def age_limits(film_limits):
    '''
    Ограничения по возрасту
    '''
    limit = ''
    if film_limits:
        if '13' in film_limits: limit = '12+'
        elif '12' in film_limits: limit = '12+'
        elif '16' in film_limits: limit = '16+'
        elif '18' in film_limits: limit = '18+'
        elif '21' in film_limits: limit = '21+'
        elif '6' in film_limits: limit = '6+'
        elif u'без' in film_limits: limit = '0+'
    return limit


def api_logger(request, method, event):
    user_ip = get_client_ip(request)
    if request.user.is_anonymous():
        u_ip = user_ip.split('.')
        cut_u_ip = '%s.%s.%s.' % (u_ip[0], u_ip[1], u_ip[2])
        try:
            profile = Profile.objects.filter(Q(interface__ip_address=user_ip) | Q(interface__ip_address__istartswith=cut_u_ip))[0]
            user = profile.user
        except IndexError:
            user = None
    else:
        user = request.user
    d = datetime.datetime.now()
    text = {
        1: 'Создание дампа',
        2: 'Обращение к методу API',
        3: 'Скачивание дампа',
        4: 'Попытка скачать несуществующий дамп',
    }
    details = text.get(event)
    APILogger(user=user, date=d, details=details, ip=user_ip, method=method, event=event).save()



def resize_image(width, img_url, img_obj=None, height=None):
    import urllib2
    import cStringIO
    from PIL import Image
    
    if img_url:
        req = urllib2.Request(img_url)
        img_file = cStringIO.StringIO(urllib2.urlopen(req).read())
    else:
        img_file = cStringIO.StringIO(img_obj)
    
    img = Image.open(img_file)
    current_width = img.size[0]
    if current_width > width:
        wpercent = (width / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((width, hsize), Image.ANTIALIAS)
        if not height:
            return img
            
    if height:
        if img.size[1] > height:
            hpercent = (height / float(img.size[1]))
            wsize = int((float(img.size[0]) * float(hpercent)))
            img = img.resize((wsize, height), Image.ANTIALIAS)
        return img

        
def get_country_by_ip(ip):
    from api.views import create_dump_file
    g = GeoIP()
    country = None
    try:
        name = g.country(ip)['country_name']
        if name == 'Russian Federation':
            name = 'Russia'
        elif name == 'United States':
            name = 'USA'
        elif name == 'Moldova, Republic of':
            name = 'Moldova'
        elif name == 'United Kingdom':
            name = 'UK'
        elif name == 'Iran, Islamic Republic of':
            name = 'Iran'
        try:
            country = Country.objects.get(name_en=name)
        except Country.DoesNotExist:
            pass
            '''
            if name:
                with open('%s/dump_geoip_nof_country.xml' % settings.NOF_DUMP_PATH, 'r') as f:
                    xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
                
                name_slug = low(del_separator(name))
                countries_slugs = [i.get('slug') for i in xml_data.findAll('country')]
                
                data_nof_country = ''
                if name_slug not in countries_slugs:
                    data_nof_country = '<country name="%s" slug="%s"></country>' % (name, name_slug)
                    
                xml_data = str(xml_data).replace('<html><head></head><body><data>','').replace('</data></body></html>','')
                xml_data = '<data>%s%s</data>' % (xml_data, data_nof_country)
                create_dump_file('geoip_nof_country', settings.NOF_DUMP_PATH, xml_data)
            '''
    except TypeError: pass
    return country


def getApiDescrFileName(request, lang = None):
    fileName = settings.API_EX_PATH +'/api_description.txt'
    if lang is None:
        lang, tmp = getUserLang(request)
    if not lang == 'ru': 
        fileName = '{0}.{1}'.format(fileName, '(en)')
    return fileName


def getUserLang(request):
    lang = request.session.get('django_api_language', None)
    if not lang:
        lang = str(request.META.get('HTTP_ACCEPT_LANGUAGE', 'ru'))[:2]
        if lang is not None and lang not in ('ru','uk'):
            lang = 'en'
        else:
            lang = 'ru'

#    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)

    try:
        request.session['django_api_language'] = lang
    except:
        pass

    return lang, request

