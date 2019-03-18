#!/usr/bin/env python
# -*- coding: utf-8-*-    
#author: wowdd1
#mail: developergf@gmail.com
#data: 2014.12.08

import os
import sys
import re, mmap
import itertools
import unicodedata
from update.all_subject import default_subject
import requests
import sys
from bs4 import BeautifulSoup;
from record import Record
from record import PriorityRecord
from record import CourseRecord
from record import ReferenceRecord
from record import PaperRecord
from record import ContentRecord
from record import EnginRecord
from record import Tag
import time, datetime
import feedparser
import urllib
import subprocess
from config import Config
from extension_manager import ExtensionManager
reload(sys)
sys.setdefaultencoding('utf8')
from record import Tag
from slackclient import SlackClient
import urllib


regex = re.compile("\033\[[0-9;]*m")
py3k = sys.version_info[0] >= 3
if py3k:
    unicode = str
    basestring = str
    itermap = map
    uni_chr = chr
else:
    itermap = itertools.imap
    uni_chr = unichr

class Utils:    
    cc_map = {
        'black': '30',
        'darkred': '31',
        'darkgreen': '32',
        'brown': '33', #dark yellow  
        'darkblue': '34',
        'darkmagenta': '35',
        'darkcyan': '36',
        'darkwhite': '37',
        'red': '1;31',
        'green': '1;32',
        'yellow': '1;33',
        'blue': '1;34',
        'magenta': '1;35',
        'cyan': '1;36',
        'white': '1;37',
    }
    search_engin_dict = {}
    search_engin_type_engin_dict = {}
    search_engin_type_2_engin_title_dict = {}
    search_engin_type = []
    engin_extension = []
    search_engin_url_dict = {}

    ddg_search_engin_dict = {}
    ddg_search_engin_type = []
    ddg_search_engin_url_dict = {}

    ddg_mode = False

    alexa_dict = {}

    def __init__(self):
        self.loadEngins()
        self.tag = Tag()
        self.suportFrameCache = {}
        self.extensionManager = ExtensionManager()

    def setEnginMode(self, engin):
        if engin.find(':duckduckgo') != -1:
            self.ddg_mode = True 
            return True
        return False

    def getExtensions(self):
        extensions = []
        if os.path.exists(Config.engin_extension_file):
            f = open(Config.engin_extension_file, 'rU')
            for line in f.readlines():
                if line.strip() != '':
                    extensions.append(line.strip())
        return extensions

    def getExtensionCommandArgs(self, rID, rTitle, url, client, module, command, fileName):

        form = {}
        form['check'] = 'false'
        form['rID'] = rID
        form['rTitle'] = rTitle
        form['url'] = url
        form['name'] = module
        form['command'] = command
        form['fileName'] = fileName
        form['originFileName'] = fileName
        form['client'] = client;

        return form


    def toExtension(self, sourceExtension, targetExtension, form_dict):
        form_dict['name'] = targetExtension
        form_dict['targetDataId'] = form_dict['targetDataId'].replace(sourceExtension, targetExtension)
        form_dict['divID'] = form_dict['divID'].replace(sourceExtension, targetExtension)
        form_dict['targetid'] = form_dict['targetid'].replace(sourceExtension, targetExtension)
        form_dict['objID'] = form_dict['objID'].replace(sourceExtension, targetExtension)

        return self.handleExtension(form_dict)


    def handleExtension(self, form):

        if form['rID'] == "":
            return ""
        return self.extensionManager.doWork(form, self)

    def write2File(self, fileName, lines):
        if os.path.exists(fileName):
            f = open(fileName, 'w')
            if len(lines) > 0:
                for line in lines:
                    #print line
                    f.write(line)
            else:
                f.write('')
                f.close() 

    def loadFiles(self, folder, fileType):
        cur_list = os.listdir(folder + '/')
        result = ''
        f_list = []
        f_list_2 = []
        for f in cur_list:
            if f.startswith('jquery'):
                f_list.append(f)
            else:
                f_list_2.append(f)
        cur_list = f_list + f_list_2
        for f in cur_list:
            if f.endswith(fileType):
                result += ''.join(open(folder + '/' + f, 'rU').readlines())
        return result

    def loadAlexa(self):
        if os.path.exists('db/rank/top500web-alexa2016'):
            f = open('db/rank/top500web-alexa2016', 'rU')
            for line in f.readlines():
                record = Record(line)
                title = record.get_title().strip()
                key = title[0 : 1]
                if self.alexa_dict.has_key(key):
                    self.alexa_dict[key].append(record)
                else:
                    self.alexa_dict[key] = [record]
        #print self.alexa_dict

    def loadEngins(self):
        if len(self.search_engin_dict) == 0 and os.path.exists(Config.engin_list_file):
            f = open(Config.engin_list_file,'rU')
            all_lines = f.readlines()
            for line in all_lines:
                record = EnginRecord(line)
                if record.get_title() != '':
                    url = record.get_url().strip()
                    self.search_engin_url_dict[record.get_title().strip()] = url
                    self.search_engin_dict[record.get_title().strip()] = record
                    desc = record.get_description().strip()
                    categorys = desc.split(' ')
                    for category in categorys:
                        if self.search_engin_type_engin_dict.has_key(category):
                            self.search_engin_type_engin_dict[category].append(url)
                        else:
                            self.search_engin_type_engin_dict[category] = [url]

                        if self.search_engin_type_2_engin_title_dict.has_key(category):
                            self.search_engin_type_2_engin_title_dict[category].append(record.get_title().strip())
                        else:
                            self.search_engin_type_2_engin_title_dict[category] = [record.get_title().strip()]
                        
            
            self.search_engin_type_2_engin_title_dict['star'] = self.sortEnginList(self.search_engin_type_2_engin_title_dict['star'])
        if len(self.search_engin_type) == 0 and os.path.exists(Config.engin_type_file):
            f = open(Config.engin_type_file,'rU')
            all_lines = f.readlines()
            for line in all_lines:
                if line.startswith('#'):
                    continue
                if line.strip() != '':
                    self.search_engin_type.append(line.strip().strip())
        if len(self.engin_extension) == 0 and os.path.exists(Config.engin_extension_file):
            f = open(Config.engin_extension_file,'rU')
            all_lines = f.readlines()
            for line in all_lines:
                if line.startswith('#'):
                    continue
                if line.strip() != '':
                    self.engin_extension.append(line.strip().strip())

    def loadDDGEngins(self):
        year = int(time.strftime('%Y',time.localtime(time.time())))
        if os.path.exists('db/metadata/engin_list-duckduckgo' + str(year)):
            f = open('db/metadata/engin_list-duckduckgo' + str(year),'rU')
            all_lines = f.readlines()
            for line in all_lines:
                record = PriorityRecord(line)
                if record.get_title() != '':
                    self.ddg_search_engin_url_dict[record.get_title().strip()] = record.get_url().strip()
                    self.ddg_search_engin_dict[record.get_title().strip()] = record
        if os.path.exists('db/metadata/engin_type-duckduckgo' + str(year)):
            f = open('db/metadata/engin_type-duckduckgo' + str(year),'rU')
            all_lines = f.readlines()
            for line in all_lines:
                if line.startswith('#'):
                    continue
                record = Record(line)
                if record.get_title() != '':
                    self.ddg_search_engin_type.append(record.get_title().strip())

    def fixUrl(self, baseUrl, url):
        link = url
        if url.startswith('./'):
            url = url[1:]
        if url.find('/', url.find('/') + 1) != -1 and baseUrl.find('/', baseUrl.find('//') + 2) != -1:
            baseUrl = baseUrl[0 : baseUrl.find('/', baseUrl.find('//') + 2) + 1]
        if url.startswith('//'):
            url = 'http:' + url
        if url.startswith('http') == False:
            if baseUrl.endswith('/') and url.startswith('/'):
                link = baseUrl + url[1:]
            elif baseUrl.endswith('/') == False and url.startswith('/') == False:
                if baseUrl.find('/', baseUrl.find('//') + 2) != -1:
                    link = baseUrl[0 : baseUrl.rfind('/')] + '/' + url
                else:
                    link = baseUrl + '/' + url

            else:
                link = baseUrl + url

        if link.startswith('//'):
            return 'http:' + link
        return link

    def gen_pages(self, currentPage, totalPage, libraryUrl):
        html = '<div style="margin-left:auto; text-align:center;margin-top:2px; margin-right:auto;">'
        if currentPage > 1:
            html += '<a href="javascript:toPage(' + str(currentPage - 1) + ", '" + libraryUrl.replace("'", '"') +"');" + '"><font size="5"> <</font></a>'
            html += '&nbsp;&nbsp;&nbsp;&nbsp;'
        for page in range(0, totalPage):
            
            if page + 1 == currentPage:
                html += '<a href="javascript:toPage(' + str(page + 1) + ", '" + libraryUrl.replace("'", '"') +"');" + '"><font size="5" color="#00BFFF"><b>' + str(page + 1) +'</b></font></a>&nbsp;'
            else:
                html += '<a href="javascript:toPage(' + str(page + 1) + ", '" + libraryUrl.replace("'", '"') + "');" +'">' + str(page + 1) +'</a>&nbsp;'
        if currentPage < totalPage -1:
            html += '&nbsp;&nbsp;&nbsp;&nbsp;'
            html += '<a href="javascript:toPage(' + str(currentPage + 1) + ", '" + libraryUrl.replace("'", '"') +"');" + '"><font size="5"> ></font></a>'
        html += '<div style="height: 11px; width: 100px"></div></div>'
        return html

    def gen_menu(self, source):
        db_root = '<a target="_blank" href="http://' + Config.ip_adress + '/?db=?" style="margin-right:6px">Home</a>'
        html = '<div style="margin-left:auto; text-align:center;margin-top:2px; margin-right:auto; ">' + db_root
        for link_dict in Config.fav_links.items():
            src = link_dict[1]
            if src.startswith('http') == False:
                src = 'http://' + src
            html += self.enhancedLink(src, link_dict[0], style='style="margin-right:6px"', library=source, module='main') + '&nbsp;'
        html += '</div><div style="height: 21px; width: 100px"></div>'
        return html

    def gen_libary(self, root=False, user_name='', user_image='', source=''):
        html = ''
        db_root = ''
        origin_user_name = user_name
        if Config.default_library != '':
            user_name = Config.default_library
            if user_name.endswith('-library'):
                user_name = user_name[0 : user_name.rfind('-')]
        #if root:
        #    db_root = '<a target="_blank" href="http://' + Config.ip_adress + '/?db=?" style="margin-right:6px">Home</a>'
        if user_name != None and user_name != '':
            lines = 0
            if os.path.exists('db/library/' + user_name + '-library'):
                f = open('db/library/' + user_name + '-library')
                lines = len(f.readlines())
                f.close()
            html = '<div style="float:right; margin-top:2px; margin-right:10px ">' + db_root
            '''
	    for link_dict in Config.fav_links.items():
		html += '<a target="_blank" href="http://' + link_dict[1] + '" style="margin-right:6px">' + link_dict[0] + "</a>"
            '''
            if user_image != '':
                html += '<img src="' + user_image + '" width="20" height="20" style="border-radius: 50%;"/>'
            content = user_name

            if Config.display_all_library:
                html += self.gen_libary2(user_name, source, libraryList=Config.menu_library_list)
            else:
                html += self.enhancedLink("http://' + Config.ip_adress + '/?db=library/&key=?", 'library', library=source, module='main') + '&nbsp;'

            #html +=  self.enhancedLink('http://' + Config.ip_adress + '/?db=library/&key=' + user_name + '-library&column=3&width=' + Config.default_width, content + '<font size="2">(</font><font size="2" color="#999966">' + str(lines) + '</font><font size="2">)</font>', library=source, module='main') + '&nbsp'
            html +=  self.enhancedLink('http://' + Config.ip_adress + '/?db=library/&key=' + user_name + '-library', content + '<font size="2">(</font><font size="2" color="#999966">' + str(lines) + '</font><font size="2">)</font>', library=source, module='main') + '&nbsp'

            html += self.gen_library_more(source) + '</div>'
        else:
            html = '<div style="float:right; margin-top:2px; margin-right:10px">' + db_root + self.enhancedLink("http://' + Config.ip_adress + '/login", 'Login', library=source, module='main') + '</div>'
        html += '<div style="height: 21px; width: 100px"></div>'

        return html

    def gen_libary2(self, user, source, libraryList=[], inLibary=True):
        html = ''
        file_list = os.listdir("db/library/")
        count = 0
        for item in file_list:
            if item.startswith('.'):
                continue
            if Config.default_library == '' and item.find(user) != -1:
                continue
            if Config.default_library != '' and item.find(Config.default_library) != -1:
                continue
            passItem = False
            found = False
            if len(libraryList) > 0:
                for library in libraryList:
                    if item == library:
                        found = True
                if inLibary:
                    passItem = not(found)      
                else:
                    passItem = found            

            if passItem:
                continue
            count += 1
            f = open('db/library/' + item)
            lines = len(f.readlines())
            f.close()
            #html += self.enhancedLink('http://' + Config.ip_adress + '/?db=library/&key=' + item + '&column=3&width=' + Config.default_width,  item.replace('-library', '') + '<font size="2">(</font><font size="2" color="#999966">' + str(lines) + '</font><font size="2">)</font>', library=source, module='main') + '&nbsp;'
            html += self.enhancedLink('http://' + Config.ip_adress + '/?db=library/&key=' + item,  item.replace('-library', '') + '<font size="2">(</font><font size="2" color="#999966">' + str(lines) + '</font><font size="2">)</font>', library=source, module='main') + '&nbsp;'

            if count > 5 :
                count = 0
                #html += '<br/>' #need adjust config content_margin_top

        return html
        
    def gen_library_more(self, source):
        return self.enhancedLink('', "more", module='menu', library=source, resourceType='menu', dialogMode=True, dialogPlacement='bottom') 

    def getAlexaRank(self, engin):
        engin = engin.lower().strip()
        if len(self.alexa_dict) > 0:
            key = engin.strip()[0 : 1].lower()
            for k, v in self.alexa_dict.items():
                if k.lower() == key:
                    for r in v:
                        title = r.get_title().lower().strip()
                        if title.find(engin) != -1 or engin.find(title) != -1:
                            return r.get_id()[r.get_id().find('-') + 1 : ].strip()
        return '0'

                
    def removeDoubleSpace(self, text):
        text = text.replace('\n',' ')
        while (text.find('  ') != -1):
            text = text.replace('  ', ' ')
        return text

    def validEngin(self, engin):
        records = self.search_engin_dict.keys()
        if self.ddg_mode:
            records = self.ddg_search_engin_dict.keys()
        for item in records:
            if item.lower() == engin.lower():
                return True
        print "invalided search engin: " + engin
        return False

    def caseLine(self, line):
        if line.isupper() == False:
            return line
        if self.check_contain_chinese(line):
            return line
            
        if line.strip().find(' ') == -1:
            return line
        new_line = ''
        for item in line.split(' '):
            new_line += item[0 : 1] + item[1:].lower() + ' '
        return new_line


    def shortFileName(self, file_name):
        pos = 0
        while (file_name.find('/', pos) != -1):
            pos = file_name.find('/', pos) + 1
        return file_name[pos : ]

    cache_records = {}

    """
    matchType: by id(1)  by title(2) by line(3)

    """
    def getRecord(self, keyword, use_subject='', path='', return_all=False, log=False, use_cache=True, matchType=1, accurate=True):
        #print path + 'xxx'

        cacheKey = keyword
        if path != '':
            cacheKey += '-' + path
        if self.cache_records.has_key(cacheKey) and use_cache:
            if log:
                print 'return cached record for ' + keyword
            if return_all:
                return self.cache_records[cacheKey]
            else:
                return self.cache_records[cacheKey][0]
        subject = default_subject;
        if use_subject != "":
            subject = use_subject
        if path == '':
            path = self.getPath(subject)
        if log:
            print 'searching %s'%keyword + " in " + subject + '  matchType:' + str(matchType)
        record_list = []
        if log:
            print keyword
            print path
        files = ''
        if os.path.isfile(path):
            files = [path]
        else:
            files = self.find_file_by_pattern(keyword, path)

        print files
        for file_name in files:
            if os.path.isfile(file_name) == False:
                continue
            if log:
                print file_name
            f = open(file_name)
            for line in f.readlines():
                record = Record(line)
                record.set_path(file_name)
                found_tag = False

                if matchType == 1: # by id 
                    if accurate:
                        if record.get_id().lower().strip() == keyword.lower().strip():
                            found_tag = True
                    else:
                        if record.get_id().lower().find(keyword.lower().strip()) != -1:
                            found_tag = True
                elif matchType == 2: # by title
                    if accurate:
                        if record.get_title().lower().strip() == keyword.lower().strip():
                            found_tag = True
                    else:
                        if record.get_title().lower().strip().find(keyword.lower().strip()) != -1:
                            found_tag = True
                elif matchType == 3: # by line
                    if record.line.lower().strip().find(keyword.lower().strip()) != -1:
                        found_tag = True
                if found_tag:
                    if log:
                        print "found " + record.get_id() + ' ' + record.get_title() + ' ' + record.get_url() + ' in ' + self.shortFileName(file_name)
                    if return_all:
                        record_list.append(record)
                    else:
                        self.cache_records[cacheKey] = [record]
                        return record
        if return_all:
            if len(record_list) > 0:
                self.cache_records[cacheKey] = record_list
                return record_list
            else:
                if log:
                    print "no record found in " + subject +" db"
                return record_list.append(Record(''))
        else:
            if log:
                 print "no record found in " + subject +" db"
            return Record('')

    def getPath(self, subject):
        return os.getcwd() + "/db/" + subject + "/"

    def getEnginUrl(self, engin):
        if self.ddg_mode:
            return self.ddg_search_engin_url_dict[engin]
        if self.search_engin_url_dict.has_key(engin):
            return self.search_engin_url_dict[engin]
        else:
            return ''

    def getEnginUrlOtherInfo(self, record):
        r = CourseRecord(record.line)
        if r.get_author() != None:
            author = r.get_author().strip() 
            if author != '':
                return "&user=" + author.replace(' ', '%20');
        return ""

    def getEnginUrlEx(self, engin, keyword, query=''):
        url = ''

        keyword = self.preprocessSearchKeyword(keyword, engin, '')
        if engin != '':

            url = self.getEnginUrl(engin)
            if url.find('%s') != -1:
                url = self.toAccountUrl(url, keyword.strip())
            else:
                url += keyword.strip()
        if engin == "crunchbase" and query.find(':') != -1:
            url = self.getEnginUrl(engin) + keyword.strip().replace(' ', '-')
            query = query[query.find(':') + 1 :].strip()
            if query == 'star':
                query = 'organization'
            url = self.toAccountUrl(url, query.strip())

        return url

    def preprocessSearchKeyword(self, keyword, engin, url):
        if (engin != '' and engin == 'github*topic') or (url != '' and url.find('github.com/topic') != -1):
            keyword = keyword.strip().replace(' ', '-').replace('%20', '-')
        return keyword

    def toAccountUrl(self, url, keyword):
        if keyword.find('@') != -1 and keyword.strip().startswith('@') == False:
            temp1 = keyword.split('@')
            temp2 = url.split('%s')
            new_url = url
            #print '1======' + new_url + '<br>'
            for i in range(0, len(temp1)):
                index = new_url.find('%s') + 1
                #print new_url[0: index + 1] + '<br>'
                #print new_url[index + 1:].strip() + '<br>'
                new_url = new_url[0: index + 1].replace('%s', temp1[i]) + new_url[index + 1:].strip()
            #print '======' + new_url + '<br>'
            return new_url
        return url.replace("%s", keyword.strip())

    def getEnginHtmlLink(self, engin, keyword, color=''):
        if color != '':
            return ' <a href="' + self.getEnginUrlEx(engin, keyword) + '" target="_blank"> <font size="2" color="' + color + '">' + engin + '</font></a>'
        else:
            return ' <a href="' + self.getEnginUrlEx(engin, keyword) + '" target="_blank"> <font size="2" color="#999966">' + engin + '</font></a>'

    def getRecommendType(self, fileName):
        if os.path.exists(Config.engin_type_file):
            f = open(Config.engin_type_file, 'rU')
            engin_types = []
            for line in f.readlines():
                if line.startswith('#') or line.strip() == '':
                    continue
                engin_types.append(line.strip())
            f.close()
            for et in engin_types:
                if fileName.rfind(et) != -1:
                    return et
        return ''


    def recommendEngins(self, folder):
        engins = []
        if Config.recommend_engin_type != '':
            if Config.recommend_engin_type.find(' ') != -1:
                engin_types = Config.recommend_engin_type.split(' ')
                per_engin_for_type = Config.recommend_engin_num / len(engin_types)
                for enginType in engin_types:
                    engins += self.realGetEnginList([enginType], self.search_engin_dict.values())[0 : per_engin_for_type]

            else:
                engins = self.realGetEnginList([Config.recommend_engin_type], self.search_engin_dict.values())
        else:
            etype = self.getRecommendType(folder)
            if etype != '':
                engins = self.realGetEnginList([etype], self.search_engin_dict.values())
            elif folder.find('neuro') != -1 or folder.find('biology') != -1 or folder.find('lifescience') != -1:
                engins = self.realGetEnginList(['dxy.cn', 'wikipedia', 'biostars', 'neurostars', 'youtube', 'google', 'baidu', 'gene', 'pubmed', 'ebi', 'gen.lib', 'amazon'], self.search_engin_dict.values(), match_title=True)


        if len(engins) == 0:
            return self.realGetEnginList(['star'], self.search_engin_dict.values())
        else:
            #engins = sorted(engins, key=lambda engin:self.search_engin_dict[engin].get_priority(), reverse=True)
            #for e in engins:
            #    print e + ' p:' + self.search_engin_dict[e].get_priority()

            if len(engins) < Config.recommend_engin_num:
                return engins
            return engins[0 : Config.recommend_engin_num]

    def getTopEngin(self, tag):
        engins = self.getEnginList('d:' + tag.strip())
        if len(engins) > 0:
            return engins[0]
        else:
            return ''


    def getEnginList(self, engins, folder='', sort=False, recommend=False):
        if engins.startswith('description:') or engins.startswith('d:'):
            key = engins[engins.find(':') + 1 :].strip()
            engin_list = []
            tags = engins[engins.find(':') + 1 :].strip().split(' ')
            cachedEngins = []
            tags2 = []

            if len(tags) > 0 and ''.join(tags).strip() != '':
                for tag in tags:
                    if self.search_engin_type_2_engin_title_dict.has_key(tag.strip()):
                        cachedEngins = cachedEngins + self.search_engin_type_2_engin_title_dict[tag.strip()]
                    else:
                        tags2.append(tag.strip())
                if len(tags2) == 0:
                    self.search_engin_type_2_engin_title_dict[key] = cachedEngins
                    if sort:
                        self.search_engin_type_2_engin_title_dict[key] = self.sortEnginList(cachedEngins)
                    return self.search_engin_type_2_engin_title_dict[key]
                else:
                    tags = tags2

                #print engins
                if self.ddg_mode:
                    self.search_engin_type_2_engin_title_dict[key] = self.getDDGEnginList(tags)
                else:
                    self.search_engin_type_2_engin_title_dict[key] = self.realGetEnginList(tags, self.search_engin_dict.values())

                if len(cachedEngins) > 0:
                    self.search_engin_type_2_engin_title_dict[key] = cachedEngins + self.search_engin_type_2_engin_title_dict[key]
                    if sort:
                        self.search_engin_type_2_engin_title_dict[key] = self.sortEnginList(self.search_engin_type_2_engin_title_dict[key])

            if self.search_engin_type_2_engin_title_dict.has_key(key) and len(self.search_engin_type_2_engin_title_dict[key]) == 0 and recommend:
                self.search_engin_type_2_engin_title_dict[key] = self.recommendEngins(folder)
            
            if self.search_engin_type_2_engin_title_dict.has_key(key):
                return self.search_engin_type_2_engin_title_dict[key] 
            else:
                return []
        else:
            return engins.split(' ')



    def realGetEnginList(self, tags, records, match_title=False, sort=True):
        engin_list = []
        if len(tags) == 0:
            return engin_list
        for record in records:
            if match_title:
                engin = record.get_title().strip()
                str_tags = ' ' + ' '.join(tags) + ' '
                if str_tags.find(' ' + engin + ' ') != -1:
                    engin_list.append(engin)
            else:
                desc = record.get_description().strip()
                desc = desc[desc.find(':') + 1 :].strip()
                for tag in tags:
                    if desc.find(tag) != -1:
                        #engin = record.get_title().strip()
                        engin_list.append(record.get_title().strip())
        if sort:
            return self.sortEnginList(engin_list)
        return engin_list

    def sortEnginList(self, engin_list):
        return sorted(engin_list, key=lambda engin:self.search_engin_dict[engin].get_priority(), reverse=True)

    def getDDGEnginList(self, tags):
        if len(self.ddg_search_engin_type) == 0 or len(self.ddg_search_engin_dict) == 0:
            self.loadDDGEngins()
        return self.realGetEnginList(tags, self.ddg_search_engin_dict.values())

    def getEnginPriority(self, engin):
        record = None
        if self.ddg_mode:
            record = self.ddg_search_engin_dict[engin]
        else:
            record = self.search_engin_dict[engin]
        return record.get_priority()

    def getAllEnginList(self):
        engin_list = []
        records = None
        if self.ddg_mode:
            records = self.ddg_search_engin_dict.values()
        else:
            records = self.search_engin_dict.values()
        for record in records:
            engin = record.get_title().strip()
            engin_list.append(record.get_title().strip())
        return engin_list

    def getDefaultEnginHtml(self, title, default_links_row):
        count = 0
        html = ''
        for e in self.getEnginList('d:default'):
            html += self.getEnginHtmlLink(e, title)
            count += 1
            if count == default_links_row:
                return html
        return html

    def getEnginListLinks(self, engins, topic, rID='', query = '', color="#999966", fontSize=11, i=0, j=0, useQuote=False, module='', library='', pluginsMode=False):
        if self.ddg_mode:
            return self.getDDGEnginListLinks(engins, topic, rID, query, color, fontSize)
        if topic == '':
            return ''
        result = {}
        keyword = topic.strip()
        engin_display = ''
        for engin in engins:
            engin_display = engin
            engin_display = self.getEnginIcon(engin)
            
            #if engin_display == 'sanity':
            #    engin_display = 'arxiv-sanity'
            if self.searchByID(engin):
                keyword = rID.strip()
            else:
                keyword = topic.strip()
            if Config.hiden_content_after_search and pluginsMode == False:
                script = "var pid = this.parentNode.parentNode.id; hidenMoreContent(pid, 1);"
                style = "color:" + color + '; font-size: ' + str(fontSize) + "pt;"
                result[engin] = self.enhancedLink(self.getEnginUrlEx(engin, keyword, query), self.formatEnginTitle(engin_display), style=style, script=script, useQuote=useQuote, module=module, library=library, searchText=keyword, rid='#rid')
            else:
                style = "color:" + color + '; font-size:' + str(fontSize) + "pt;"
                result[engin] = self.enhancedLink(self.getEnginUrlEx(engin, keyword, query), self.formatEnginTitle(engin_display), style=style, useQuote=useQuote, module=module, library=library, searchText=keyword, rid='#rid')
            result[engin] += '&nbsp;'
        return result

    def formatEnginTitle(self, engin):

        record = self.search_engin_dict[engin]
        shortname = record.get_shortname()
        if shortname != None and shortname != '':
            return shortname.strip()

        if len(engin) > 10:
            return '[' + engin[0 : len(engin) - (len(engin) / 2) - 1] + ']'
        return engin

    def getEnginIcon(self, engin):
        if Config.disable_icon:
            return engin
        record = self.search_engin_dict[engin]
        icon = record.get_icon()
        if icon != None and icon.strip() != '':
            return '<image margin-right:"2px" width="18px" height="18px" alt="' + engin + '" src="' + icon.strip() + '"/>'
        else:
            return engin

    def getDDGEnginListLinks(self, engins, topic, id='', query = '', color="#999966", fontSize=11):
        return {}

    def getDescDivs(self, divid, enginType, keyword, links_per_row, scrip, color, color2, fontSize, dataMarginTop='', disableNavEngins=False):
        result = '<div id="' + divid + '" style="display: none;">'
        if disableNavEngins == False:
            engin_list = self.getEnginList('d:' + enginType)
            #print engin_list
            remain = len(engin_list)
            last = 0
            count = 0
            while remain > 0:
                #print '---'
                #print 'remain' + str(remain)
                #print 'links_per_row' + str(links_per_row)
                #print 'last' + str(last)
                if remain > links_per_row:
                    engin_list_dive = engin_list[last : last + links_per_row]
                else:
                    engin_list_dive = engin_list[last : ]
                    remain = 0
                #print engin_list_dive
                div = '<div id="' + divid + '-' + str(count) + '" ">'
                link_count = 0
                for e in engin_list_dive:
                    link_count += 1
                    if link_count % 2 == 0:
                        div += self.genLinkWithScript2(scrip, e.strip() , color2, self.priority2fontsize(e.strip(), self.getEnginPriority(e.strip()),fontSize)) + '&nbsp;'
                    else:
                        div += self.genLinkWithScript2(scrip, e.strip(), color, self.priority2fontsize(e.strip(), self.getEnginPriority(e.strip()),fontSize)) + '&nbsp;'
                remain -= links_per_row
                last += links_per_row
                #print remain
                #print last
                div += '</div>'
                count += 1
                result += div
        result += "</div>" 
        if dataMarginTop != '':
            result += '<div id="' + divid + '-data" style="border-radius: 10px 10px 10px 10px; margin-top:' + dataMarginTop + 'px;"></div>'
        else:
            result += '<div id="' + divid + '-data" style="border-radius: 10px 10px 10px 10px;"></div>'
        
        return result



    def output2Disk(self, records, module, fileName, outputFormat='', ignoreUrl=False, append=False):
        data = ''
        if outputFormat == 'markdown':
            data += '## ' + fileName.replace('%20', ' ') + '\n'
            data += '- ### ' + module + '\n'
        fileName = fileName.strip().replace('"', '').replace("'", '').replace('%20', ' ').replace('(', '').replace(')', '').replace(' ', '-').replace('|', '').lower() 
        if outputFormat != '':
            if outputFormat == 'markdown':
                fileName += '.md'
            else:
                fileName += '-' + outputFormat
        else:
            fileName += str(datetime.date.today().year)
        count = 0
        for record in records:
            count += 1
            url = record.get_url().strip()
            if ignoreUrl:
                url = ''
            if outputFormat == 'markdown':
                if record.line.find(' parentid:') != -1 and record.get_parentid().strip() != '':
                    data += '    '
                data += '- [ ] [' + record.get_title().strip() + '](' + url + ')\n'
            else:
                data += record.get_id().strip() + '-' + str(count) + ' | ' + record.get_title().strip() + ' | ' + url + ' | ' + record.get_describe().strip() + '\n'
        outputDir = Config.output_data_to_new_tab_path + module + '/'
        if outputFormat != '':
            outputDir += outputFormat + '/'
        if os.path.exists(outputDir) == False:
            os.makedirs(outputDir)

        flag = 'w'

        if append:
            flag = 'a'

        f = open(outputDir + fileName, flag)
        f.write(data)
        f.close()

        url = ''
        if outputFormat.strip() != '':
            url += 'edit ' + os.getcwd() + '/' + outputDir + fileName
            return url

        url += 'http://' + Config.ip_adress + '/?db=' + Config.output_data_to_new_tab_path.replace('db/', '')
        url += module + '/'
        if outputFormat.strip() != '':
            url += outputFormat + '/'
        
        url += '&key=' + fileName
        return url

    def bestMatchEngin(self, text, resourceType=''):
        #TODO get best engin by resourceType
        #print resourceType
        if text.startswith('http'):
            return text
        if resourceType != '' and ' '.join(self.tag.tag_list_direct_link).find(resourceType) != -1:
            return self.getEnginUrl('glucky')
        return self.getEnginUrl(Config.smart_link_engin)

    def bestMatchEnginUrl(self, text, resourceType='', source=''):
        if source.find('github') != -1 and resourceType.find('author') != -1:
            return 'http://github.com/' + text
        url = self.bestMatchEngin(text, resourceType=resourceType)
        return self.toQueryUrl(url, text)

    def clientQueryEnginUrl(self, originUrl, text, resourceType, module):
        result = {}
        engin = ''
        url = self.toQueryUrl(self.getEnginUrl(Config.smart_link_engin), text)
        
        if originUrl != '':
            url = originUrl

        result[Config.smart_link_engin] = url

        if resourceType !='' and Config.smart_engin_for_tag.has_key(resourceType.strip()):
            result = {}
            for u in self.expandEngins(Config.smart_engin_for_tag[resourceType.strip()]):
                result[u.strip()] = self.toQueryUrl(self.getEnginUrl(u), text)

        '''
        if module != '' and Config.smart_engin_for_extension.has_key(module.strip()):
            result = {}
            for u in self.expandEngins(Config.smart_engin_for_extension[module.strip()]):
                result[u.strip()] = self.toQueryUrl(self.getEnginUrl(u), text)  
        '''
        return result

    dialog_engin_cache = None

    def expandEngins(self, engins):
        result = []
        if isinstance(engins, str):
            engins = [engins]
        for e in engins:
            if e.find(':') != -1:
                result = result + self.getEnginList(e, sort=True)
            else:
                result.append(e)
        return result

    def clientQueryEnginUrl2(self, text, resourceType='', enginArgs=''):
        result = {}
        engins = []
        if resourceType == 'social-tag':
            text = text.replace('#', '')
        if resourceType != '' and Config.smart_engin_for_tag.has_key(resourceType):
            engins = self.expandEngins(Config.smart_engin_for_tag[resourceType])
        elif len(Config.smart_engin_for_dialog) > 0:
            engins = self.expandEngins(Config.smart_engin_for_dialog)
        elif self.dialog_engin_cache != None:
            engins = self.dialog_engin_cache
        else:
            if Config.recommend_engin_type_for_dialog != '':
                if Config.recommend_engin_type_for_dialog.find(' ') != -1:
                    engin_types = Config.recommend_engin_type_for_dialog.split(' ')
                    per_engin_for_type = Config.recommend_engin_num / len(engin_types)
                    for enginType in engin_types:
                        engins += self.getEnginList('d:' + enginType, sort=True)[0 : per_engin_for_type]
                else:
                    engins = self.getEnginList('d:' + Config.recommend_engin_type_for_dialog, sort=True)
            else:
                if resourceType != '' and Config.recommend_engin_by_tag and ' '.join(self.search_engin_type).find(resourceType) != -1:
                    engins = self.getEnginList('d:' + resourceType, sort=True)
                else:
                    if enginArgs != '' and enginArgs.startswith('d:'):
                        engins = self.getEnginList(enginArgs, sort=True)
                    else:
                        engins = self.getEnginList('d:star', sort=True)
            self.dialog_engin_cache = engins.append('glucky');

        for engin in engins:
            result[engin] = self.toQueryUrl(self.getEnginUrl(engin), text)

        return result

    def clientQueryDirs(self, path, rID='', fileName=''):
        dirs = []

        for item in os.listdir(path):
            full_path = os.path.join(os.getcwd() + '/' + path + '/', item)
            if os.path.isfile(full_path) == False:
                dir_path = (path + '/' + item).replace('//', '/')
                dirs.append(dir_path)
                dirs += self.clientQueryDirs(dir_path)
        return dirs

    def genTagLink(self, text, module, library, rid, resourceType, dialogMode, aid, crossref='', accountTag='', suffix=':', searchText='', fileName=''):
        #if crossref:
        #    dialogMode = False
        htmlText = '<font color="#66CCFF">' + text + '</font>'
        if fileName == '':
            fileName = library
        return self.enhancedLink('', htmlText, module=module, library=library, fileName=fileName, rid=rid, resourceType=resourceType, urlFromServer=True, dialogMode=dialogMode, aid=aid, isTag=True, log=False, searchText=searchText) + suffix


    smartLinkTagCache = {}
    def isSmartLinkTag(self, tag, list_smart_link):
        if tag == '':
            return False
        prefix = ''
        if tag.find(':') != -1:
            prefix = tag[0 : tag.find(':') + 1].strip()
        else:
            prefix += tag + ':'

        if self.smartLinkTagCache.has_key(prefix):
            #print 'isSmartLinkTag cache'

            return True


        reslut = ' '.join(list_smart_link).find(prefix) != -1

        if reslut:
            self.smartLinkTagCache[prefix] = ''

        return reslut


    directLinkTagCache = {}
    def isDirectLinkTag(self, tag, list_direct_link):

        if tag == '':
            return False
        prefix = ''
        if tag.find(':') != -1:
            prefix = tag[0 : tag.find(':') + 1].strip()
        else:
            prefix += tag + ':'


        if self.directLinkTagCache.has_key(prefix):
            #print 'isDirectLinkTag cache'
            return True

        result = ' '.join(list_direct_link).find(prefix) != -1

        if result:
            self.directLinkTagCache[prefix] = ''
        return result

    def isAccountTag(self, tag, tag_list_account):
        #print tag + '<br>'
        #if tag.strip().startswith('archiv'):
        #    print tag_list_account
        if tag == '':
            return False
        prefix = ''
        if tag.find(':') != -1:
            prefix = tag[0 : tag.find(':') + 1].strip()
        else:
            prefix += tag + ':'



        return tag_list_account.has_key(prefix)




    def accountMode(self, tag_list_account, tag_list_account_mode, engin, resourceType):
        if Config.smart_engin_lucky_mode_for_account:
            accountTags = ' '.join(tag_list_account)
            accountModeTags = ' '.join(tag_list_account_mode)
            return accountTags.find(engin + ':') != -1 and accountModeTags.find(resourceType + ':') != -1
        return False

    def toQueryUrl(self, url, text):
        if text.startswith('http'):
            return text

        text = self.preprocessSearchKeyword(text, '', url)
        if url.startswith('http') == False and self.search_engin_dict.has_key(url):
            url = self.getEnginUrl(url)

        query_text = text.replace('"', ' ').replace("'", ' ').replace(' ', "%20") 
        if url.find('%s') != -1:
            url = self.toAccountUrl(url, query_text.strip())
        else:
            url += query_text
        return url


    def getValueOrTextCheck(self, text):
        if text.find('(') != -1 and text.strip().endswith(')'):
            if text.find('+') != -1:
                newText, value = self.getValueOrTextSplit(text)
                if value.find('+') == -1:
                    return False
                for v in value.split('+'):
                    if self.getValueOrTextCheck(v) == False:
                        if v.find('(') == -1 and v.find(')') == -1:
                            return True
                        else:
                            return False
            return True
        return False

    def getValueOrTextSplit(self, text):
        value = text[text.find('(') + 1 :].strip()
        value = value[0 : value.rfind(')')].strip()
        newText = text[0 : text.find('(')].strip() 
        #if self.isShortUrl(value):
        #    value = 'http://' + value
        return newText, value

    def isUrlFormat(self, text):
        if text.startswith('http') or self.isShortUrl(text):
            return True
        return False
        
    def isShortUrl(self, text):
        if text.find('http') != -1:
            text = text.replace('http://', '').replace('https://', '')
        if text.startswith('bit.ly') or text.startswith('goo.gl'):
            return True
        return False

    def getValueOrText(self, text, returnType='text'):
        if self.getValueOrTextCheck(text):
            #print 'text:' + text + ' accountTag:' + str(accountTag) + ' returnType:' + returnType + '<br>'
            newText, value = self.getValueOrTextSplit(text)
            if returnType == 'text':
                #print newText + '<br>'
                return newText
            elif returnType == 'value':
                #print value + '<br>'
                return value

        return text.encode('utf-8')

    #hook user usage data

    def getCrossref(self, keyword, path='db/library'):
        cmd = 'grep -riE "' + keyword + '" ' + path
        print cmd
        output = ''
        try:
            output = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            return ''
        adict = {}
        titleDict = {}
        for line in output.split('\n'):
            fileName = line[0 : line.find(':')].strip().replace('//', '/')
            firstIndex = line.find('|')
            rID = line[line.find(':') + 1 : firstIndex].strip().replace(' ', '%20')
            title = line[firstIndex + 1 : line.find('|', firstIndex + 1)].strip()
            if title != '':
                if title.find(',') != -1:
                    title = title.replace(',', '')
                if title.find('+') != -1:
                    title = title[0 : title.find('+')]
                if title.find('#') != -1:
                    title = title[0 : title.find('#')]
                if titleDict.has_key(title):
                    continue
                if adict.has_key(fileName):
                    adict[fileName].append(title)
                else:
                    adict[fileName] = [title]
                titleDict[title] = title
        result = ''
        print '---getCrossref---'
        for k, v in adict.items():
            #print k + ' #' + '#'.join(v)
            prefix = ''
            if k.startswith('db/'):
                prefix = k[3:]
            ft = '+'.join(v).strip()
            if ft.endswith('+'):
                ft = ft[0 : len(ft) - 2]
            result += prefix + '#' + ft
            if k != adict.items()[len(adict) - 1][0]:
                result += ', '

        
        if result != '':
            result = 'crossref:' + result
        print result
        return result

    def getSubSearchinDescList(self, searchDescList, parentCmd, loopSearch=True):
        descList = [] 
        for descItem in searchDescList:
            if descItem.find('searchin:') != -1:
                subSearchinDesc = descItem[descItem.find('searchin:') + len('searchin:') :]
                print 'subSearchinDesc of ' + parentCmd + ':' + subSearchinDesc
                for subCmd in subSearchinDesc.split(','):
                    subCmd = subCmd.strip()
                    if self.searchHistory.has_key(subCmd.lower()) == False:
                        print 'search subCmd:' + subCmd
                        self.searchHistory[subCmd.lower()] = ''
                        sunSearchDescList = self.searchLibrary(subCmd, '', noDiv=True, unfoldSearchin=False, noFilterBox=True, returnMatchedDesc=True, isRecursion=True)
                        print sunSearchDescList
                        if len(sunSearchDescList) > 0:
                            descList = descList + sunSearchDescList
                            if loopSearch:
                                descList = descList + self.getSubSearchinDescList(sunSearchDescList, subCmd, loopSearch=loopSearch)
                    else:
                        print subCmd + ' already be searched###'

        return descList

    searchHistory = {}
    def searchLibrary(self, title, url, style='', noDiv=False, nojs=False, unfoldSearchin=True, noFilterBox=False, returnMatchedDesc=False, isRecursion=False):
        print 'searchLibrary ' + title
        if title.startswith('!'):
            return self.genDefaultPluginInfo(title[1:])
        elif title.endswith('!'):
            return self.genDefaultPluginInfo(title[0:len(title) - 1])
    
        if title == '' or title.lower() == Config.history_quick_access_name.lower():
            f = open('extensions/history/data/quick-access-history', 'r')
            html = ''
            desc = ''
            for line in f.readlines():
                if line.strip() == '':
                    continue
                r = Record(line)
                lineDesc = r.get_describe()
    
                desc = self.mergerDesc(desc, lineDesc)
    
            if desc != '':
                tag = Tag()
                html = self.genDescHtml(desc, Config.course_name_len, tag.tag_list, iconKeyword=True, fontScala=1, module='searchbox')
    
            f.close()
    
            return html
        if isRecursion == False:
            self.searchHistory = {}
    
        titleFilter = ''
        descFilter = ''
        contentFilter = ''
        searchinLoopSearch = Config.searchinLoopSearch
        searchinLoopSearchMore = Config.searchinLoopSearch

        tList = [title]
        if title.find('&') != -1:
            tList = title.split('&')
    
        resultHtmlList = []
        for t in tList:
            title = t.strip()
            if title != '':
                descCacheList = []
        
                if title.find('/') != -1 and title.startswith('library/') == False:
                    parts = title.split('/')
                    descFilter = parts[1].strip()
                    title = parts[0].strip()
                    if len(parts) == 3:
                        contentFilter = parts[2]
        
                titleList = [title]
        
                if title.find('+') != -1:
                    titleList = title.split('+')
                resultHtml = ''
                for title in titleList:

                    title = title.strip()
                    originTitle = title
                    deepSearch = True
                    accurateMatch = False
                    startMatch = False
                    endMatch = False
                    reMatch = False

                    if title.startswith('->'):
                        title = title.replace('->', '?searchin:')

                    if title.startswith('>>>'):
                        title = title.replace('>>>', '>')
                        searchinLoopSearch = True
                        searchinLoopSearchMore = True

                    if title.startswith('>>'):
                        title = title.replace('>>', '>')
                        searchinLoopSearch = True
                        searchinLoopSearchMore = False
        
                    if title.startswith('?') or title.endswith('?'):
                        if title.startswith('?'):
                            title = title[1:]
                            deepSearch = False
                        elif title.endswith('?'):
                            title = title[0:len(title) - 1]
                            deepSearch = False  
                        if title.find(':') != -1:
                            titleFilter = title[0 : title.find(':') + 1]
                            title = title[title.find(':') + 1 :]  
        
                    if title.startswith(':'):
                        parts = []
                        title = title[1:]
                        if title.find(' of ') != -1:
                            parts = title.split(' of ')
                        elif title.find(' from ') != -1:
                            parts = title.split(' from ')
        
                        if len(parts) == 2:
                            title = parts[1].strip()
                            descFilter = parts[0].strip()
                        elif len(parts) == 3:
                            title = parts[2].strip()
                            descFilter = parts[1].strip()
                            contentFilter = parts[0].strip()
        
                        if title.find(' and ') != -1:
                            title = title.replace(' and ', '*')
                        if title.find(',') != -1:
                            title = title.replace(',', '*')
                        accurateMatch = True
                    elif title.startswith('>'):
                        title = title[1:]
                        accurateMatch = True
                    elif title.endswith('>'):
                        title = title[0:len(title) - 1]
                        accurateMatch = True
        
                    if title.startswith('^'):
                        title = title[1:]
                        accurateMatch = True
                        startMatch = True
                    elif title.endswith('^'):
                        title = title[0:len(title) - 1]
                        accurateMatch = True
                        startMatch = True
        
                    if title.startswith('$'):
                        title = title[1:]
                        accurateMatch = True
                        endMatch = True
                    elif title.endswith('$'):
                        title = title[0:len(title) - 1]
                        accurateMatch = True
                        endMatch = True
        
                    titles = title.split('*')
                    #print titles
                    for titleItem in titles:
                        titleItem = titleItem.strip()
                        crossref = ''
                        print titleItem
                        if titleItem != '':
                        #    kg = KnowledgeGraph()
                            if titleItem.startswith('library/'):
                                crossref = 'crossref:' + titleItem[0 : titleItem.find('->')]    
                                titleItem = titleItem[titleItem.find('->') + 2 :]
                            else:
                                crossref = self.getCrossref(titleItem)
                        print crossref
                        #return ''
                        if crossref != '':
                            crossrefList = []
                            if crossref.find(',') != -1:
                                crossrefList = crossref.split(',')
                            else:
                                crossrefList = [crossref]
                
                            html = ''
                            searchinHtml = ''
                            resultDict = {}
                            #print crossrefList
                            for cr in crossrefList:
                                cr = cr.replace('crossref:', '')
                                if cr.find('#') != -1:
                                    #print cr
                                    result = self.getCrossrefUrls(cr)
                                    #print result
                                    for k, v in result.items():
                                        resultDict[k] = v
                                else:
                                    #print cr
                                    k, v = self.getCrossrefUrl(cr)
                                    resultDict[k] = v
                                    #print k + ' ' + v
                
                 
                            linkDict = self.genPluginInfo(resultDict, returnDict=True)
                
                            rCount = 0
                            #print linkDict
                            for k, v in resultDict.items():
                                #print k + ' ' + v
                                path = ''
                                rTitle = ''
                                for sv in v.split('&'):
                                    if sv.find('db') != -1:
                                        path += 'db/' + sv[sv.find('db') + 3:]
                                    if sv.startswith('key'):
                                        path += sv[sv.find('key') + 4:]
                                    if sv.startswith('filter'):
                                        rTitle = sv[sv.find('filter') + 7:]
                                print path + ' ' + rTitle
                
                                r = self.getRecord(rTitle, path=path, matchType=2, use_cache=False)
    
                                if r != None and r.line.strip() != '' and r.get_id().strip() != '':
                                    #print r.line + '))0' + r.get_id()
                                    library = path[path.rfind('/') + 1 :]
                                    print library
                                    tag = Tag()
                                    print '-----'
                                    print titleItem
                                    #return ''
                                    #desc = r.get_desc_field2(utils, title, tag.get_tag_list(library), toDesc=True, prefix=False)
                                    matchedTextList, descList = r.get_desc_field3(self, titleItem, tag.get_tag_list(library), toDesc=True, prefix=False, deepSearch=deepSearch, accurateMatch=accurateMatch, startMatch=startMatch, endMatch=endMatch)
                                    #print descList
                                    #print matchedTextList
                                    once = True
                                    count = 0
                                    rCount += 1
                                    for desc in descList:
                                        if desc != None and desc != '':
                                            #print k
                                            print desc
                                            matchedText = ''
                                            if len(matchedTextList) - 1 >= count: 
                                                matchedText = matchedTextList[count]
                                            
                                            count += 1
                                            crossref = ''
                                            start = desc.find('searchin:')
                                            end = 0
                                            searchinDesc = ''
                                            if start != -1:
                                                descPart1 = desc[0 : start]
                                                descPart2 = desc[start : ]
                                                descPart3 = ''
                                                end = self.next_pos(descPart2, len('searchin:'), 1000, self.tag.tag_list)
                                                if end != -1:
                                                    descPart3 = descPart2[0 : end]
                                                    descPart2 = descPart2[end :]

                                                desc = descPart1.strip() + ' ' + descPart2.strip() + ' ' + descPart3.strip()

                                                searchinDesc = descPart3
                                                print desc

                                            descHtml = ''

                                            if descFilter != '' and searchinDesc != '' and searchinLoopSearch:
                                                for cmd in titleList:
                                                    if self.searchHistory.has_key(cmd.lower()) == False:
                                                        self.searchHistory[cmd.lower()] = ''
                                                cmds = searchinDesc[searchinDesc.find(':') + 1 :].split(',')
                                                for cmd in cmds:
                                                    cmd = cmd.strip()
                                                    if self.searchHistory.has_key(cmd.lower()) == False:
                                                        print 'search cmd:' + cmd
                                                        self.searchHistory[cmd.lower()] = ''
                                                        searchDescList = self.searchLibrary(cmd, '', noDiv=True, unfoldSearchin=False, noFilterBox=True, returnMatchedDesc=True, isRecursion=True)
                                                        print searchDescList
                                                        if len(searchDescList) > 0:
                                                            descCacheList = descCacheList + searchDescList
                                                            print 'searchinLoopSearchMore:' + str(searchinLoopSearchMore)
                                                            if searchinLoopSearchMore:
                                                                subSearchDescList = self.getSubSearchinDescList(searchDescList, cmd, loopSearch=searchinLoopSearchMore) 

                                                                if len(subSearchDescList) > 0: 
                                                                    descCacheList = descCacheList + subSearchDescList                                                                       


                                            fontScala = 1                     

                                            if returnMatchedDesc == False:
                                                descHtml = self.genDescHtml(desc, Config.course_name_len, tag.tag_list, iconKeyword=True, fontScala=fontScala, module='searchbox', nojs=nojs, unfoldSearchin=False, parentOfSearchin=originTitle)
                                                if searchinDesc != '':
                                                    searchinHtml += self.genDescHtml(searchinDesc, Config.course_name_len, tag.tag_list, iconKeyword=True, fontScala=1, module='searchbox', nojs=nojs, unfoldSearchin=unfoldSearchin, parentOfSearchin=originTitle)

                                            if titleFilter != '':
                                                descTemp = ''
                                                index1 = desc.find(titleFilter)
                                                index2 = desc.find(':', index1 + len(titleFilter))
                                                if index1 != -1:
                                                    if index2 != -1:
                                                        descTemp = desc[index1 : index2]
                                                    else:
                                                        descTemp = desc[index1 :]
                                                if descTemp.lower().find(title.lower()) != -1:
                                                    #print desc + '111' + descTemp
                                                    descCacheList.append(desc) 
                                                else:
                                                    descHtml = ''
    
                                            else:
                                                descCacheList.append(desc)
    
                                            if matchedText != '' and descHtml != '':
                                                #once = False
                                                script = ''
                                                script2 = ''
                                                if matchedText.strip()  != '':
                                                    crossref = path[path.find('/') + 1 :].strip() + '#' + rTitle + '->' + matchedText.strip() 
                                                    #script = "exclusiveCrossref('plugin', '" + matchedText + "' ,'' ,'" + crossref + "');"
                                                    script = "typeKeyword('>" + matchedText + "', '')"
                                                    script2 = "typeKeyword('->" + matchedText + "', '')"
                                                else:
                                                    crossref = path[path.find('/') + 1 :].strip() + '#' + rTitle
            
                                                    crossrefHtml = '<font style="font-size:10pt; font-family:San Francisco; color:red">' + crossref + '</font>'
            
                                                if script != '':
                                                    libraryText = path[path.find('/') + 1 :].strip()
                                                    libraryPart = '<font style="font-size:10pt; font-family:San Francisco; color:red">' + libraryText + '</font>'
                                                    titlePart = '<font style="font-size:10pt; font-family:San Francisco; color:red">' + rTitle + '</font>'
                                                    arrowPart = '<font style="font-size:10pt; font-family:San Francisco; color:red">-></font>'
                                                    matchedTextPart = '<font style="font-size:10pt; font-family:San Francisco; color:red">' + matchedText.strip() + '</font>'
                                                    crossrefHtml = '<a target="_blank" href="' + Config.ip_adress + '/?db=library/&key=' + libraryText[libraryText.rfind('/') + 1 :] + '">' + libraryPart + '</a>' +\
                                                                    '<font style="font-size:10pt; font-family:San Francisco; color:red">#</font>' +\
                                                                    '<a target="_blank" href="' + Config.ip_adress + '/?db=library/&key=' + libraryText[libraryText.rfind('/') + 1 :] + '&filter=' + rTitle.replace(' ', '%20') + '">' + titlePart + '</a>' +\
                                                                    '<a target="_blank" href="javascript:void(0);" onclick="' + script2 + '">' + arrowPart + '</a>' +\
                                                                    '<a target="_blank" href="javascript:void(0);" onclick="' + script + '">' + matchedTextPart + '</a>'
            
                                                countStr = matchedText.replace(' ', '-').lower().strip() + '-' + str(rCount) + '-' + str(count)
                                                linkID = 'a-plugin-more-' + countStr
                                                ref_divID = 'div-plugin-' + countStr
                                                ref_div_style = 'style="display: none;"'
                                                #rID = 'custom-plugin-' + countStr
                                                rID = 'custom-plugin-' + r.get_id().strip() + '-pg'
                                                #print rID
                                                originTitle = crossref.replace('->', '==')
                                                url = ''
                                                appendID = countStr
                                                script = ''
                                                script = self.genMoreEnginScript(linkID, ref_divID, rID.replace(' ', '-') + '-' + str(appendID), originTitle, url, originTitle, hidenEnginSection=True)
                                                moreHtml = self.genMoreEnginHtml(linkID, script.replace("'", '"'), '...', ref_divID, '', False, descHtml='', content_divID_style=ref_div_style).strip();
                                                #print script
                                                #print moreHtml
            
                                                html += crossrefHtml + ' ' + moreHtml + '<br>'
    
            
                                            if descHtml != '':
                                                if linkDict.has_key(k):
                                                    script = ''
                                                    moreHtml = ''
                                                    if r.get_title().strip() == k:
                                                        parentText = matchedText.strip().lower().replace(' ', '-')
                                                        if parentText != '':
                                                            parentText = parentText + '-'
                                                        linkID = 'a-plugin-' + parentText + 'parent-more-' + k.lower().replace(' ', '-') + '-' + str(rCount) + '-' + str(count) + '-0'
                                                        ref_divID = 'div-' + parentText + k.lower().replace(' ', '-') + '-' + str(rCount) + '-' + str(count) + '-0'
                                                        ref_div_style = 'style="display: none;"'
                                                        rID = r.get_id().strip()
                                                        originTitle = r.get_title().strip()
                                                        if crossref.find('->') != -1:
                                                            originTitle = crossref[0: crossref.find('->')] + '==' + originTitle
                                                        script = self.genMoreEnginScript(linkID, ref_divID, rID, originTitle, '', originTitle, hidenEnginSection=True)
                                                        moreHtml = self.genMoreEnginHtml(linkID, script.replace("'", '"'), '...', ref_divID, '', False, descHtml='', content_divID_style=ref_div_style).strip();
                                                                                   
                                                     
                                                    '''
                                                    if crossref.find('#') != -1:
                                                        lib = crossref[0 : crossref.find('#')].replace('library/', '').replace('-library', '')
                                                        lib = lib[0 : 1].upper() + lib[1:]
                                                        url = Config.ip_adress + '/?db=library/&key=' + lib
    
                                                        html += '<a target="_blank" href="' + url + '"><font style="font-size:10pt; font-family:San Francisco;">' + lib + '</font></a> ' + self.getIconHtml(url) + ' '
                                                    '''
                                                    html += linkDict[k]

                                                    quickAccess = self.queryQuickAccess(r.get_id().strip())
                                                    if quickAccess != None:
                                                        html += self.genQuickAcessButton(quickAccess, 'plugin').strip()
                                                    if moreHtml != '':
                                                        html += ' ' + moreHtml
                                                    html += '<br>' 
                                                    html += descHtml + '<br>'
                                                    #linkDict[k] = ''
                                                else:
                                                    html += descHtml + '<br>'
                
                                path = ''
                
                            html2 = ''
                            if accurateMatch == False and titleFilter == '':
                                for k, v in linkDict.items():
                                    if v != '':
                                        html2 += v + '  '
                    
                            if html2 != '':
                                html = html + '<br>' + html2
                
            
                            if html != '' and noDiv == False:
                                html = '<div align="left" ' + style + '>' + html + '</div>' + searchinHtml
                            resultHtml += html
                #print descCacheList

                if returnMatchedDesc:
                    return descCacheList
                
                if descFilter != '':
                    filterDesc, filterHtml = self.genFilterHtml(descFilter, descCacheList, fontScala=-5)

                    if isRecursion == False and len(self.searchHistory) > 0:
                        print 'searchHistory:'
                        history = ''
                        filterHtml += self.getIconHtml('', title='searchin') + ':'
                        for k, v in self.searchHistory.items():
                            history += k + ' '

                            filterHtml += '<a href="javascript:void(0);" onclick="typeKeyword(' + "'" + k + "', ''" +')" style="color: rgb(153, 153, 102); font-size:9pt;">' + k + '</a> '


                        print history
                    if contentFilter != '':
                        print 'contentFilter:' + contentFilter
        
                        url = self.contentSearch(filterDesc, contentFilter, title=descFilter)
                        if url != '':
                            filterHtml += '<a target="_blank" href="' + url + '"><font style="font-size:10pt; font-family:San Francisco;">contentSearch</font></a>'
                    #style="padding-left: 455; padding-top: 5px;"
                    if noDiv == False:
                        filterHtml = '<div id="filter_div" align="left" ' + style + '>' + filterHtml + '</div>'

                    resultHtmlList.append(filterHtml)
                elif len(descCacheList) > 1 and noFilterBox == False:
                    data = subprocess.check_output('echo "' + '\n'.join(descCacheList) + '" > web_content/desc', shell=True)
                    resultHtmlList.append(self.genFilterBox() + resultHtml)
                else:
                    resultHtmlList.append(resultHtml)
            elif request.form.has_key('url') and request.form['url'].find(Config.ip_adress) == -1:
                form = self.getExtensionCommandArgs('plugin', '', request.form['url'], 'plugin', 'social', 'getPluginInfo', '')
                print form
                resultHtmlList.append(self.handleExtension(form))
        
            else:
                resultHtmlList.append(self.genPluginInfo(lastOpenUrlsDict))
  

        html = ''
        if len(resultHtmlList) > 1:
            html = '<br>'.join(resultHtmlList)
        elif len(resultHtmlList) == 1:
            result = resultHtmlList[0]
            if result != '':
                html = result
            else:
    
                html = self.genDefaultPluginInfo(title)

        return html

    def genDefaultPluginInfo(self, title):
        linkID = 'a-plugin-more-0'
        ref_divID = 'div-plugin-0'
        ref_div_style = 'style="display: none;"'
        rID = 'custom-plugin-0-pg'
        #print rID
        originTitle = title
        url = ''
        appendID = 0
        script = ''
        script = self.genMoreEnginScript(linkID, ref_divID, rID.replace(' ', '-') + '-' + str(appendID), originTitle, url, originTitle, hidenEnginSection=True)
        moreHtml = self.genMoreEnginHtml(linkID, script.replace("'", '"'), '...', ref_divID, '', False, descHtml='', content_divID_style=ref_div_style).strip();
                     
        result = '<div id="filter_div" align="left" style="padding-left: 455; padding-top: 5px;">' + title + ' ' +moreHtml + '</div>'
        return result
    
    def doExclusive(self, rID, title, url, desc):
       record = Record('custom-exclusive-' + rID + ' | '+ title + ' | ' + url + ' | ' + desc)
       return self.output2Disk([record], 'main', 'exclusive', append=Config.exclusive_append_mode) 
   
   
    
    
    def contentSearch(self, desc, filter, title=''):
    
        if filter == ':local':
            url = self.doExclusive('contentSearch-local', title, '' , desc + ' keyword:' + title + '(' + self.desc2ValueText(desc, tag.tag_list) + ')')
            return url
    
        textList =[]
        start = 0
        desc = desc.strip()
        tag = Tag()
        while True:
            end = self.next_pos(desc, start, 10000, tag.tag_list)
            if end < len(desc):
                text = desc[start : end].strip()
                textList.append(text)
                start = end
            else:
                text = desc[start : ]
                textList.append(text)
                break
        urlList = []
        for text in textList:
            tagStr = text[0: text.find(':') + 1].strip()
            tagValue =  text[text.find(':') + 1 : ].strip()
    
            if tagStr == 'website:':
                for v in tagValue.split(','):
                    if self.getValueOrTextCheck(v):         
                        url = self.getValueOrText(v, returnType='value')
                        if self.urlConvertable(url):
                            urlList.append(url)
            elif self.isAccountTag(tagStr, tag.tag_list_account):
                url = tag.tag_list_account[tagStr]
                if self.urlConvertable(url):
                    for v in tagValue.split(','):
                        v = v.strip()
                        urlList.append(url.replace('%s', v))
    
         
        #line = ' | contentSearch | ' + ','.join(urlList) + ' | argv=contain=' + filter
        url = ''
        if len(urlList) > 0:
            url = self.doExclusive('', 'contentSearch', ','.join(urlList) , 'argv:contain=' + filter)
            print url
        #print line
        return url
    
    def mergerDescList(self, descList):
        desc = ''
        for line in descList:
            if desc == '':
                desc = line
            else:
                desc = self.mergerDesc(desc, line)
        return desc    
    
    def genFilterHtml(self, command, descList, fontScala=0):
        desc = self.mergerDescList(descList)
    
        filterDesc = ''
        tag = Tag()
        if command != '':
            start = 0
            while True:
                end = self.next_pos(desc, start, 10000, tag.tag_list)
                if end < len(desc):
                    text = desc[start : end].strip()
                    filterDesc += self.doFilter(command.split('+'), text).strip() + ' '
                    start = end
                else:
                    text = desc[start : ]
                    filterDesc += self.doFilter(command.split('+'), text).strip() + ' '
    
                    break
            if filterDesc != '':
                filterDesc = filterDesc.strip()
                descHtml = self.genDescHtml(filterDesc, Config.course_name_len, tag.tag_list, iconKeyword=True, fontScala=fontScala, module='searchbox', previewLink=True)
    
                return filterDesc, descHtml
        return '', ''
    def doFilter(self, commandList, text):
        tagStr = text[0: text.find(':') + 1].strip()
        tagValue =  text[text.find(':') + 1 : ].strip()
    
        desc = ''
        for item in tagValue.split(','):
            originItem = item.strip()
            for command in commandList:
                command = command.strip()
                if command.find(':') != -1:
                    if command == ':all':
                        return text
                    
    
                    if command.endswith(':') and command.strip() == tagStr:
                        return text
                    elif command[0 : command.find(':') + 1] == tagStr or command.startswith(':'):
                        desc = tagStr
    
                        filter = ''
    
                        if command.startswith(':'):
                            filter = command[ 1 :]
                        else:
                            filter = command[command.find(':') + 1 :]
    
                        ftList = filter.split('*')
                        for tagItem in tagValue.split(','):
                            tagItem = tagItem.strip()
                            for ft in ftList:
                                ft = ft.strip()
                                if tagItem.lower().find(ft.lower()) != -1:
                                    desc += tagItem + ', '
                        if desc != '':
                            if tagStr == desc:
                                return ''
                            return desc[0 : len(desc) - 2]
    
                if command.startswith('>'):
                    command = command[1:]
                    item = self.getValueOrText(item, returnType='text')
                
                if item.lower().find(command.lower()) != -1:
                    prefix = ''
                    if tagStr == 'website:':
                        urlText = self.getValueOrText(originItem, returnType='text')
                        url = self.getValueOrText(originItem, returnType='value')
                        if len(urlText.split(' ')) < 3 and url.find(Config.ip_adress) == -1:
                            url = url.replace('https://', '').replace('http://', '').replace('www.', '')                    
                            prefix = url[0 : url.find('.')]
                    if prefix != '' and originItem.lower().startswith(prefix.lower()) == False:
                        desc += prefix + ' - ' + originItem + ', '
                    else:
                        desc += originItem + ', '
                    break
    
        if desc != '':
            desc = desc.strip()
            if desc.endswith(','):
                desc = desc[0 : len(desc) - 1]
            return tagStr + desc
        else:
            return ''
    
    def genFilterBox(self):
        command = ''
        script = "var text = $('#command_txt'); console.log('', text[0].value);"
        divID = 'filter_div'
        script += "var dataDiv = $('#" + divID + "'); dataDiv.html('');"
        script += "var postArgs = {command : text[0].value, divID : '" + divID + "'};";
        script += "$.post('/filter', postArgs, function(data) { \
                            var div = document.getElementById('filter_div');\
                            div.innerHTML = data;\
                        });"
        box = '<br><div style="text-align:center;width:100%;margin: 0px auto;"><input id="command_txt" style="border-radius:5px;border:1px solid" maxlength="256" tabindex="1" size="46" name="word" autocomplete="off" type="text" value="' + command + '">&nbsp;&nbsp;'\
              '&nbsp;&nbsp;<button alog-action="g-search-anwser" type="submit" id="command_btn" hidefocus="true" tabindex="2" onClick="' + script + '">Run</button></div><div id="filter_div" align="left" style="padding-left: 455; padding-top: 5px;"></div>'
        return box
    
    def genPluginInfo(self, dataDict, returnDict=False):
        html = ''
        lens = 0
        linkDict = {}
        for k, v in dataDict.items():
            lens += len(k)
            link = '<a target="_blank" href="' + v + '" style="font-family:San Francisco;"><font style="font-size:9pt; font-family:San Francisco;">' + k + '</font></a>'
            icon = self.getIconHtml(v)
            if returnDict:
                linkDict[k] = link + icon
            else:
                html += link + icon + '  '
            if lens > 70:
                lens = 0
                html += '<br>'
        if returnDict:
            return linkDict
        else:
            return html   
    

    def enhancedLink(self, url, text, aid='', refreshID='', style=Config.smart_link_style, script='', showText='', originText='', useQuote=False, module='', library='', img='', rid='', haveDesc=True, newTab=True, searchText='', resourceType='', urlFromServer=False, dialogMode=False, ignoreUrl=False, fileName='', dialogPlacement='top', isTag=False, log=True, nojs=False):

        url = url.strip()
        user_log_js = ''
        query_url_js = ''
        chanage_color_js = ''
        rid = rid.strip()
        text = text.replace('"', '').replace("'", '')
        #text = self.clearHtmlTag(text).replace('\n', '')

        if originText == '':
            originText = text
        if fileName == '':
            fileName = library

        if refreshID == '':
            refreshID = aid;

        newTabArg = 'false'
        haveDescArg = 'true'
        if newTab:
            newTabArg = 'true'
        if haveDesc == False:
            haveDescArg = 'false'
        #if originText.find('(') != -1:
        #    print originText
        #    print 'dialogMode:' + str(dialogMode)

        send_text = self.clearHtmlTag(originText).replace('\n', ' ')
        if send_text.find('<') != -1:
            send_text = self.clearHtmlTag(send_text)
        if searchText == '':
            searchText = send_text.strip()

        newTabArgs = 'false'
        isTagArgs = 'false'
        islog = 'true'
        if newTab:
            newTabArgs = 'true'
        if isTag:
            isTagArgs = 'true'

        if log == False:
            islog = 'false'
        if module != '' and ' '.join(Config.igon_log_for_modules).find(module) != -1:
            log = False
        if useQuote:
            # because array.push('') contain ', list.py will replace "'" to ""
            # so use  #quote as ', in appendContent wiil replace #quote back to '
            if log:
                user_log_js = "if (opened) { userlogEx(#quote" + aid+ "#quote,#quote" + refreshID + "#quote,#quote" + send_text + "#quote,#quote" + url + "#quote,#quote" + module + "#quote,#quote" + library + "#quote, #quote" + rid + "#quote, #quote" + searchText+ "#quote, #quote" + resourceType + "#quote);}"

            query_url_js = "queryUrlFromServer(#quote" + send_text + "#quote,#quote" + url + "#quote,#quote" + module + "#quote,#quote" + library + "#quote, #quote" + rid + "#quote, #quote" + searchText+ "#quote, " + newTabArgs + ", " + isTagArgs+ ", #quote" + fileName + "#quote," + islog + ");"
            if Config.background_after_click != '' and text.find('path-') == -1:
                chanage_color_js = "chanageLinkColor(this, #quote"+ Config.background_after_click +"#quote, #quote" + Config.fontsize_after_click + "#quote, #quote" + resourceType + "#quote);"

        else:
            if log:
                user_log_js = "if (opened) { userlogEx('" + aid + "','" + refreshID + "','"+ send_text + "','" + url + "','" + module + "','" + library + "', '" + rid + "', '" + searchText + "', '" + resourceType + "');}"
            query_url_js = "queryUrlFromServer('" + send_text + "','" + url + "','" + module + "','" + library + "', '" + rid + "', '" + searchText + "', '" + resourceType + "', " + newTabArgs + ", " + isTagArgs + ", '" + fileName + "'," + islog +");"
            if Config.background_after_click != '' and text.find('path-') == -1:
                chanage_color_js = "chanageLinkColor(this, '" + Config.background_after_click + "', '" + Config.fontsize_after_click + "');"

        open_js = 'var opened = true; '
        onHover_js = ''

        if url.startswith('http') == False and url != '':
            #js = "$.post('/exec', {command : 'open', fileName : '" + url + "'}, function(data){});"
            cmd = 'open'
            if url.endswith('.md'):
                cmd = 'edit'

            js = "exec('" + cmd + "','" + searchText + "','" + url + "');"
            onHover_js = "onHover('" + aid + "', '" + searchText + "', '" + url + "', '" + rid + "', '" + module + "', '" + fileName+ "', '" + haveDescArg + "');"

            link = '<a target="_blank" href="javascript:void(0);" onclick="' + js + chanage_color_js + open_js + user_log_js + '" onmouseover="' + onHover_js + '"'

            if style != '':
                link += ' style="' + style + '"'
                link +='>'
            if showText != '':
                link += showText + '</a>'
            else:
                link += text + '</a>'
            return link


        if ignoreUrl == False:
            if urlFromServer:
                user_log_js = ''
                open_js = query_url_js;
            else:
                urls = [url]    
                if (module != '' or resourceType != '') and url == '':
                    resultDict = self.clientQueryEnginUrl(url, searchText, resourceType, module)
                    if resultDict != None and len(resultDict) > 0:
                        urls = resultDict.values()
                for link in urls:
                    if link == '':
                        continue

                    if useQuote:
                        open_js += "opened = openUrl(#quote" + link + "#quote, #quote" + searchText + "#quote, " + newTabArg + ", " + newTabArg + ", #quote" + rid + "#quote, #quote" + resourceType + "#quote, #quote" + refreshID + "#quote, #quote" + module + "#quote, #quote" + fileName + "#quote);"
                        onHover_js+= "onHover(#quote" + aid + "#quote, #quote" + searchText + "#quote, #quote" + link + "#quote, #quote" + rid + "#quote, #quote" + module + "#quote, #quote" + fileName+ "#quote, #quote" + haveDescArg + "#quote);"
                    else:
                        open_js += "opened = openUrl('" + link + "', '" + searchText + "', " + newTabArg + ", " + newTabArg + ", '" + rid + "', '" + resourceType + "', '" + refreshID + "', '" + module + "', '" + fileName + "');"
                        onHover_js+= "onHover('" + aid + "', '" + searchText + "', '" + link + "', '" + rid + "', '" + module + "', '" + fileName+ "', '" + haveDescArg + "');"

                    if newTab == False:
                        break
        #open_js = ''
 
        result = ''
        
        if dialogMode:
            result = '<a href="#" class="bind_hover_card" data-toggle="popover" data-placement="' + dialogPlacement + '" data-trigger="hover" data-popover-content="' + rid + '#' + resourceType + '#' + aid + '#' + str(isTag) + '#' + originText + '" id="' + aid + '"' 
            if style != '':
                result += ' style="' + style + '"'
            result +='>'
        else:
            result = ''
            if nojs:
                result = '<a target="_blank" href="' + url + '"'

            else:
                result = '<a target="_blank" href="javascript:void(0);"'


                if aid != '' and aid.endswith('-') == False:
                    result += ' id=' + aid 
    
                if script != '':
                    script = script.replace('"', "'")
                    if useQuote:
                        script = script.replace("'", '#quote')
                    result += ' onclick="' + script + open_js + chanage_color_js + user_log_js + '"'
                else:
                    result += ' onclick="' + open_js + chanage_color_js + user_log_js + '"'
    
                if onHover_js != '' and aid != '':
                    result += ' onmouseover="' + onHover_js + '"'
    

            if style != '':
                result += ' style="' + style + '"'

            result += '>' 

        if img != '':
            result += img + '</a>'
        else:
            if showText != '':
                #print showText.encode('utf-8')
                #print result.encode('utf-8')
                result += showText
            else:
                result += originText#text
            result += '</a>'

        return result


    def toSmartLink(self, text, br_number=Config.smart_link_br_len, engin='', noFormat=False, showText='', module='', library='', rid='', resourceType='', aid=''):
        if text != '':
            url = ''
            if engin != '':
                url = self.toQueryUrl(self.getEnginUrl(engin.strip()), text)
            else:
                url = self.bestMatchEnginUrl(text, resourceType=resourceType)
            if noFormat:
                return self.enhancedLink(url, text, showText=showText, module=module, library=library, rid=rid, resourceType=resourceType, aid=aid)
            else:
                return self.enhancedLink(url, self.formatTitle(text, br_number), showText=showText, module=module, library=library, rid=rid, resourceType=resourceType, aid=aid)
        return text

    def formatTitle(self, title, br_number=Config.smart_link_br_len, keywords=[]):
        if title.find(': Amazon.com: Books') != -1:
            title = title.replace(': Amazon.com: Books', '')
            title = title[0 : title.rfind(':')]

        if len(title) > br_number:
            at = title.find(' ', br_number)
            if at != -1:
                return self.replaceKeyword(title[0 : at], keywords) + '<br>' + self.formatTitle(title[at:], br_number)
            else:
                return self.replaceKeyword(title, keywords)
        else:
            return self.replaceKeyword(title, keywords)

    def replaceKeyword(self, text, keywords=[]):
        if len(keywords) == 0:
            return text
        for kw in keywords:
            if text.find(kw.strip()) != -1:
                colorText = '<font color="red">' + kw.strip() + '</font>'
                return text.replace(kw, colorText)
        return text

    def priority2fontsize(self, engin, priority, baseFontSize):
        if priority.strip() == '':
            return baseFontSize
        if priority.strip() == '0':
            rank = int(self.getAlexaRank(engin))
            if rank == 0:
                return baseFontSize
            fontSize = int(self.revertRount((500 -rank) / 50.0 )) + 1
            #print 'rank:' + str(rank) + ' engin:' + engin + ' fontsize:' + str(fontSize)
            #print '<br/>'
            return baseFontSize + fontSize + 1
            
        else:
            priorityInt = int(priority.strip())
            return baseFontSize + priorityInt + 1
        
    def revertRount(self, number):
        if number > round(number):
            return round(number) + 1
        else:
            return round(number)
             
    def getNavLinkList(self, engin, searchEnginOnly=False):
        if self.ddg_mode:
            if len(self.ddg_search_engin_type) == 0 or len(self.ddg_search_engin_dict) == 0:
                self.loadDDGEngins()
            return self.ddg_search_engin_type
        else:
            if Config.extension_mode:
                return self.engin_extension
            else:
                if searchEnginOnly:
                    return self.search_engin_type
                else:
                    return self.search_engin_type + self.engin_extension
        #return ['paper', 'book', 'project', 'course', 'talk', 'organization', 'people', 'social']

    def getEnginTypes(self):
        return self.search_engin_type

    def getEnginExtensions(self):
        return self.engin_extension

    def getLastEnginType(self):
        return self.search_engin_type[len(self.search_engin_type) - 1]

    def genMoreEnginHtml(self, aid, script, text, content_divID, color='', doubleQ=True, descHtml='', descMarginTop=13, content_divID_style=''):
        #return ' <a id="' + aid +'" href="' + 'javascript:void(0);' + '" onClick="' + script + ';"> <font size="2" color="#999966">more</font></a>'
        div = '<div id="' + content_divID + '" ' + content_divID_style + '></div>';
        html = ''
        desc_divID = aid + '-desc'
        if descHtml != '':
            script += "hidendiv_3('" + desc_divID + "');"
        if color != '':
            if doubleQ:
                html = ' <font size="2"><a id="' + aid +'" href="' + 'javascript:void(0);' + '" onClick="' + script + '"><font color="' + color + '">' + text + '</font></a></font>'
            else:
                html = ' <font size="2"><a id="' + aid +'" href="' + 'javascript:void(0);' + '" onClick=' + script + '><font color="' + color + '">' + text + '</font></a></font>'
        else:
            if doubleQ:
                html = ' <font size="2"><a id="' + aid +'" href="' + 'javascript:void(0);' + '" onClick="' + script + '"><font color="#999966">' + text + '</font></a></font>'
            else:
                html = ' <font size="2"><a id="' + aid +'" href="' + 'javascript:void(0);' + '" onClick=' + script + '><font color="#999966">' + text + '</font></a></font>'
            html = html + div
        if descHtml != '':
            html += '<div id="' + desc_divID + '" style="display: none;margin-top:' + str(descMarginTop) + 'px;">' + descHtml + '</div>'
        return html

    def genMoreEnginScript(sefl, linkID, content_divID, id, title, url, info, hidenEnginSection=False):
        script = ''
        script += "setText('" + linkID +"');"
        script += "showdiv('" + content_divID + "','" + linkID +"');"
        title = title.replace('"', '%20').replace("'",'%20').replace('&', '%20').replace(' ', '%20')
        info = info.replace('"', '%20').replace("'",'%20').replace(' ', '%20')
        hidenEngin = 'false'
        if hidenEnginSection:
            hidenEngin = 'true'
        script += "appendContent('" + content_divID + "','" + id + "','" + title.strip().replace(" ", '%20') + "','" + url.strip().replace(" ", '%20') + "','" + info + "'," + hidenEngin + ");"
        return script

    def genMoreEnginScriptBox(sefl, linkID, content_divID, boxid):
        script = ''
        script += "setText('" + linkID +"');"
        script += "showdiv('" + content_divID + "', '" + linkID +"');"
        script += "appendContentBox('" + content_divID + "', '" + boxid + "');"
        return script

    def genLinkWithScript2(self, script, text, color='', fontSize=12, aid=''):
        #return ' <a id="' + aid +'" href="' + 'javascript:void(0);' + '" onClick="' + script + ';"> <font size="2" color="#999966">more</font></a>'
        atag = " <a "
        if aid != '':
            atag += ' id="' + aid + '" '
        if color != '':
            return atag + 'href="' + 'javascript:void(0);' + '" onClick=' + script + ' style="color:' + color + ' ; font-size: ' + str(fontSize) + 'pt;">' + text + '</a>'
        else:
            return atag + 'href="' + 'javascript:void(0);' + '" onClick=' + script + ' style="color: rgb(136, 136, 136);" font-size: ' + str(fontSize) + 'pt;>' + text + '</a>'

    def searchByID(self, engin):
        if engin.strip() == 'textbooksearch':
            return True
        return False

    def isEnginUrl(self, url):
        if url.find('soku.com') != -1 or url.find('google.com.hk/videohp') != -1:
            return True

        records = self.search_engin_dict.keys()
        if self.ddg_mode:
            records = self.ddg_search_engin_dict.keys()

        for key in records:
            if url.find(key) != -1:
                return True
        return False

    def getUrl(self, keyword, use_subject='', engin=''):
        urls = []
        url = ""
        subject = default_subject;
        if use_subject != "":
            subject = use_subject
        print 'searching %s'%keyword + " in " + subject

        for file_name in self.find_file_by_pattern(".*", self.getPath(subject)):
            f = open(file_name)
            for line in f.readlines():
                record = Record(line)
                if record.get_id().lower().strip() == keyword.lower().strip():
                    print "found " + record.get_id() + ' ' + record.get_title() + ' ' + record.get_url() + ' in ' + self.shortFileName(file_name)
                    title = record.get_title().strip()
                    if engin != "" and self.validEngin(engin) == True:
                        urls.append(self.getEnginUrl(engin.lower()) + title)
                    else:
                        urls.append(record.get_url().strip())

            f.close()


        if len(urls) > 1:
            for u in urls:
                if self.isEnginUrl(u) == False:
                    url = u
                    break
                if url == "":
                    url = urls[0]
        elif len(urls) == 1:
            url = urls[0]
        else:
            print "no url found in " + subject +" db"

        return url


    def toDescDict(self, desc, library):
        descDict = {}
        start = 0
        keywordList = self.tag.get_tag_list(library)
        while True:
            end = self.next_pos(desc, start, 10000, keywordList)
            if end < len(desc):

                item = desc[start : end].strip()
                if item.find(':') != -1:
                    descDict[item[0 : item.find(':')]] = item[item.find(':') + 1 :]

                start = end
            else:
                item = desc[start : ].strip()
                if item.find(':') != -1:
                    descDict[item[0 : item.find(':')]] = item[item.find(':') + 1 :]

                break

        #for k, v in descDict.items():
        #    print k + ':' + v

        return descDict

    def mergerDescDict(self, descDict1, descDict2):
        reslut = {}

        keySet1 = descDict1.keys()
        keySet2 = descDict2.keys()
        keySet = keySet1 + keySet2

        for k in keySet:
            if k == 'clickcount':
                continue
            if descDict1.has_key(k) and descDict2.has_key(k):
                desc1 = descDict1[k].encode('utf-8')
                desc2 = descDict2[k].encode('utf-8')

                desc1List = []

                descList = []

                if desc1.find(',') != -1:
                    desc1List = desc1.split(',')
                else:
                    desc1List = [desc1]

                for item in desc1List:
                    item = item.strip()

                    if item == '':
                        continue

                    if desc2.find(item) != -1:
                        continue
                    else:
                        descList.append(item)

                if len(descList) > 0:
                    desc1 = ', '.join(descList)
                    desc = desc1 + ', ' + desc2
                else:
                    desc = desc2

                reslut[k] = desc
            elif descDict1.has_key(k):
                reslut[k] = descDict1[k]
            else:
                reslut[k] = descDict2[k]

        return reslut

    def dict2Desc(self, descDict):
        desc = ''
        for k, v in descDict.items():
            desc += k + ':' + v.strip() + ' '

        return desc

    def getBatchOpenScript(self, textList, linkList, module, onePage=True):
        script = ''
        if Config.open_all_link_in_one_page and onePage:
            script = "openAllOnePage('" + ','.join(textList) + "', '" + ','.join(linkList) + "', '" + module + "');"
        else:
            script = "openAll('" + ','.join(textList) + "', '" + ','.join(linkList) + "');" 

        return script


    def getQuickAccessHistoryFileName(self):
        return 'extensions/history/data/' + Config.history_quick_access_name.lower().replace(' ', '-')+ '-history'

    def queryQuickAccess(self, rid):
        fileName = self.getQuickAccessHistoryFileName()

        if os.path.exists(fileName):
            #print 'queryQuickAccess:' + rid + ' '+ fileName

            r = self.getRecord(rid, path=fileName, use_cache=False)
            return r

        return None

    def queryAllTags(self, rid, fileName):
        r = self.getRecord(rid, path=fileName, use_cache=False)

        if r != None:
            line = rid + ' -all-tags | All Tags | http://nothing | clickcount:999'
            allTagsRecord = Record(line)

            return allTagsRecord

        return None

    def genAllInOnePage(self, textArray, urlArray, frameWidth=470, frameHeight=700, frameCheck=True, changeBG=True):
        html = ''
        suportLinkHtml = ''
        notSuportLinkHtml = ''
        suportLink = {}
        notSuportLink = {}
        url = ''
        style = ''
        if changeBG:
            style = '<style>body {width:100%; background-color:#E6E6FA;}</style>'
        head = '<html><head>' + style + '</head><body><table>'
        end = '</body></html>'
        count = 0
        for i in range(0, len(urlArray)):
            itemText = textArray[i].replace('%20', ' ').strip()
            itemUrl = urlArray[i].replace('%20', ' ').strip()
            space = ''


            if frameCheck:
    
                if self.suportFrame(itemUrl, 0.9):
                #if True:
            
                    print itemUrl + ' suport'
                    suportLink[itemText] = itemUrl
                    suportLinkHtml += '<a target="_black" href="' + itemUrl + '"><font style="font-size:10pt;">' + itemText + '</font></a>&nbsp;'
                else:
                    notSuportLink[itemText] = itemUrl
                    notSuportLinkHtml += '<a target="_black" href="' + itemUrl + '"><font style="font-size:10pt;">' + itemText + '</font></a>&nbsp;'
            else:
                suportLink[itemText] = itemUrl
                suportLinkHtml += '<a target="_black" href="' + itemUrl + '"><font style="font-size:10pt;">' + itemText + '</font></a>&nbsp;'

        count = 0
        row = ''
        htmlList = []
        frameCount = 0
        if Config.open_all_link_in_frameset_mode == False:
            for k, v in suportLink.items():
                frameCount += 1
                id = 'iframe' + str(frameCount)
                row += '<td><iframe  id="' + id + '" width="' + str(frameWidth) + '" height="' + str(frameHeight) + '" frameborder="0"  scrolling="auto" src="' + v +'" ></iframe></td><td width="60" ></td><td width="60" ></td><td width="60" ></td>'
                count = count + 1
                if count == 3:
                    html += '<tr>' + row + '</tr>'
                    count = 0
                    row = ''
    
            if row != '':
                html += '<tr>' + row + '</tr>' 
    
            newhtml = head + '<div style="width:100%; background-color:#E6E6FA"><div style="margin-left:auto; text-align:center;margin-top:2px; margin-right:auto; ">' + suportLinkHtml + \
            '&nbsp;&nbsp;/&nbsp;&nbsp; ' + notSuportLinkHtml + '</div><div style="height: 21px; width: 100px"></div>' + html + '</div>' + end
    
            htmlList = [newhtml]
        else:
            for k, v in suportLink.items():
                row += '<frame src="' + v +'" ></frame>'
                count = count + 1
                if count == 4:
                    frameset = '<frameset cols="25%,*,25%, 25%">' + row + '</frameset>'
                    html += frameset
                    htmlList.append(frameset)
                    count = 0
                    row = ''
    
            if row != '':
                if count == 1:
                    
                    frameset = '<frameset cols="100%">' + row + '</frameset>' 
                    html += frameset
                if count == 2:
                    frameset = '<frameset cols="*,50%">' + row + '</frameset>' 
                    html += frameset
                if count == 3:
                    frameset = '<frameset cols="*,30%,30%">' + row + '</frameset>' 
                    html += frameset
                htmlList.append(frameset)
    
        return htmlList, notSuportLink

    def genQuickAcessBtn(self, rid, module):
        return self.genQuickAcessButton(self.queryQuickAccess(rid), module)

    def genQuickAcessButton(self, record, module, iconType='quickaccess'):
        url = record.get_url().strip()
        urlDict = self.genDescLinks(record.get_describe().strip(), self.tag.tag_list)

        #print 'genQuickAcessButton:' + record.get_title()
        #print urlDict

        script = ''

        textList = []
        linkList = []

        if len(urlDict.items()) == 0:
            return ''
        for k, v in urlDict.items():
            if v == url:
                url = ''
            textList.append(k)
            linkList.append(v)
        if url != '':
            textList.append(Config.history_quick_access_name)
            linkList.append(url)

        script = self.getBatchOpenScript(textList, linkList, module)

        html = '<a target="_blank" href="javascript:void(0);" onclick="' + script + '">' + self.getIconHtml('', iconType) + '</a>'

        return html  


    def genDescLinks(self, desc, keywordList, library=''):
        start = 0
        desc = ' ' + desc
        linksDict = {}
        while True:
            end = self.next_pos(desc, start, 10000, keywordList, library=library)
            if end < len(desc):
                #print desc[start : end].strip()
                urlDict = self.genDescLinkHtml(desc[start : end], 100, library=library, returnUrlDict=True)
                start = end
                for k, v in urlDict.items():
                    linksDict[k] = v
            else:
                urlDict = self.genDescLinkHtml(desc[start : ], 100, library=library, returnUrlDict=True)
                for k, v in urlDict.items():
                    linksDict[k] = v
                break


        return linksDict

    def genDescHtml(self, desc, titleLen, keywordList, library='', genLink=True, rid='', aid='', refreshID='', iconKeyword=False, fontScala=0, splitChar="<br>", parentDesc='', module='', nojs=False, unfoldSearchin=True, parentOfSearchin='', previewLink=False):
        start = 0
        html = ''
        desc = ' ' + desc
        if genLink:
            while True:
                end = self.next_pos(desc, start, 10000, keywordList, library=library)
                if end < len(desc):
                    rawText = desc[start : end].strip()
                    if iconKeyword:
                        html += self.icon_keyword(self.genDescLinkHtml(rawText, titleLen, library=library, rid=rid, aid=aid, refreshID=refreshID, fontScala=fontScala, accountIcon=False, parentDesc=parentDesc, module=module, nojs=nojs, unfoldSearchin=unfoldSearchin, parentOfSearchin=parentOfSearchin, previewLink=previewLink), keywordList, rawText=rawText, parentOfSearchin=parentOfSearchin) + splitChar

                    else:
                        html += self.color_keyword(self.genDescLinkHtml(rawText, titleLen, library=library, rid=rid, aid=aid, refreshID=refreshID, fontScala=fontScala, parentDesc=parentDesc, module=module), keywordList, nojs=nojs, unfoldSearchin=unfoldSearchin, parentOfSearchin=parentOfSearchin, previewLink=previewLink) + splitChar
                    start = end
                else:
                    rawText = desc[start : ]
                    if iconKeyword:
                        html += self.icon_keyword(self.genDescLinkHtml(rawText, titleLen, library=library, rid=rid, aid=aid, refreshID=refreshID, fontScala=fontScala, accountIcon=False, parentDesc=parentDesc, module=module, nojs=nojs, unfoldSearchin=unfoldSearchin, parentOfSearchin=parentOfSearchin, previewLink=previewLink), keywordList, rawText=rawText, parentOfSearchin=parentOfSearchin) + splitChar

                    else:
                        html += self.color_keyword(self.genDescLinkHtml(rawText, titleLen, library=library, rid=rid, aid=aid, refreshID=refreshID, fontScala=fontScala, parentDesc=parentDesc, module=module, nojs=nojs, unfoldSearchin=unfoldSearchin, parentOfSearchin=parentOfSearchin, previewLink=previewLink), keywordList) + splitChar
                    break
        else:
            while True:
                end = self.next_pos(desc, start, titleLen, keywordList, library=library)
                if end < len(desc):
                    if iconKeyword:
                        html += self.icon_keyword(desc[start : end], keywordList) + splitChar

                    else:
                        html += self.color_keyword(desc[start : end], keywordList) + splitChar
                    start = end
                else:
                    if iconKeyword:
                        html += self.icon_keyword(desc[start : ], keywordList) + splitChar
                    else:
                        html += self.color_keyword(desc[start : ], keywordList) + splitChar
                    break

        return html


    def getLinkShowText(self, accountTag, originText, tagStr, linkCount, column_num='3', fontScala=0, accountIcon=True):
        text = self.getValueOrText(originText, returnType='text')
        col = int(column_num)
        font_size = 0
        if column_num == '1':
            font_size = '10'
        elif column_num == '2':
            font_size = '9'
        else:
            font_size = '8'
            if linkCount < 5:
                font_size = '11'
            elif linkCount < 7:
                font_size = '10'
            elif linkCount < 8:
                font_size = '9'

        if fontScala != 0:
            font_size = str(int(font_size) - fontScala)

        if accountTag or tagStr == 'social-tag':
            prefix = '@'
            icon = ''
            if accountIcon and Config.website_icons.has_key(tagStr):
                icon = self.getIconHtml('', title=tagStr, width=10, height=8)
            if tagStr == 'goodreads':
                text = text[text.find('-') + 1 :]
            elif tagStr == 'slack':
                prefix = '#'
            elif tagStr == 'social-tag':
                prefix = '#'
            #if (tag == 'github' or tag == 'bitbucket') and text.find('/') != -1:
            if text.find('/') != -1:
                text = text[text.rfind('/') + 1 : ]
            if text.find('___') != -1:
                text = text[text.rfind('___') + 3 : ]
            if text.find(prefix) != -1:
                text = text[text.find(prefix) + 1 :]

            text = text[0: self.getCutLen(tagStr, text)]
            if text.startswith(prefix) == False:
                text = prefix + text + icon
            return '<font style="color:#008B00; font-size:' + str(font_size) + 'pt; ' + Config.smart_link_style + '"><i>' + text.encode('utf-8') + '</i></font>'
        else:
            #return '<font style="font-size:' + str(font_size) + 'pt;" color="#8E24AA">' + text + '</font>'
             
            if Config.backgrounds[Config.background] != '':
                return '<font style="font-size:' + str(font_size) + 'pt;" color="#8E24AA" ' + Config.smart_link_style + '>' + text + '</font>'
            else:
                return '<font style="font-size:' + str(font_size) + 'pt; ' + Config.smart_link_style + '">' + text + '</font>'
            
        return text

    def getCutLen(self, tagStr, text):
        if self.getValueOrTextCheck(text):
            text = self.getValueOrText(text, returnType='text')
        if tagStr == 'github':
            return len(text)
        elif len(text) > 14 and self.check_contain_chinese(text) == False:
            return 14
        else:
            return len(text)

    def desc2ValueText(self, desc, tagList):
        start = 0
        valueText = ''
        while True:

            end = self.next_pos(desc, start, 1000, tagList) 

            if end > 0:
                item = desc[start : end].encode('utf-8')
                tag = item[0 : item.find(':')].strip()
                if tag == 'website':
                    valueText += item[item.find(':') + 1 :].replace(', ', '+') + '+'
                else:
                    valueText += tag + '(' + item[item.find(':') + 1 :].replace(', ', '*') + ')+'
                start = end

            if end >= len(desc):
                break

        valueText = valueText[0 : len(valueText) - 1]

        return valueText

    def valueText2Desc(self, originText, text='', value='', form=None, record=None, tagSplit=' ', prefix=True):
        if text == '' or value == '':
            text = self.getValueOrText(originText, returnType='text')
            value = self.getValueOrText(originText, returnType='value')

        if self.getValueOrTextCheck(originText):
            values = []
            if value.find('+') != -1:
                values = value.split('+')
            else:
                values = [value]
            result = ''
            desc = 'description:'
            website = 'website:'
            preData = ''
            #print originText
            #print values
            crossrefDesc = ''
            for v in values:
                print 'v:' + v
                #if v.endswith('))'):
                #    v = v[0 : len(v) - 1]
                subText = v
                subValue = v
                if self.getValueOrTextCheck(v):
                    subText = self.getValueOrText(v, returnType='text').strip()

                    subValue = self.getValueOrText(v, returnType='value').strip()

                    #if subValue.find('+') != -1:
                    #    result += ' ' + self.valueText2Desc(v)
                    #    continue
                    originSubValue = subValue
                    #print subText + ' ' + subValue

                    subValueIsEngin = False
                    if self.search_engin_dict.has_key(subValue):
                        subValue = self.getEnginUrl(subValue)
                        subValueIsEngin = True

                    if Config.smart_engin_for_tag.has_key(originSubValue):
                        subValue = 'http://_blank'
                        subValueIsEngin = True

                    if self.isAccountTag(text, self.tag.tag_list_account):
                        result = self.accountValue2Desc(subText, text, subValue, result, tagSplit)

                    elif self.isAccountTag(subText, self.tag.tag_list_account) or subText == 'alias' or subText == 'category' or subText == 'searchin':

                        result = self.accountValue2Desc(text, subText, subValue, result, tagSplit)


                    elif self.isUrlFormat(subValue):
                        subTextList = [subText]
                        if subText.startswith('[') and subText.endswith(']'):
                            subsubText = subText[1:len(subText) -1 ]

                            subTextList = self.splitText(subsubText)

                        for st in subTextList:
                            sv = subValue
                            if subValueIsEngin:
                                sv = self.toQueryUrl(subValue, st)
                            else:
                                if subValue.find('%s') != -1:
                                    sv = subValue.replace('%s', st)

                            if prefix:
                                website += text + ' - ' + st + '(' + self.validSubvalue(sv) + '), '
                            else:
                                website += st + '(' + self.validSubvalue(sv) + '), '

                    elif subText == 'crossref':
                        values = []
                        if subValue.find('*') != -1:
                            values = subValue.split('*')
                        else:
                            values = [subValue]
                        count = 0
                        for v in values:
                            count += 1
                            cDesc = self.crossref2Desc(v)
                            if cDesc != '':
                                if cDesc.startswith('website:'):
                                    website += cDesc[cDesc.find(':') + 1 :]
                                    if count != len(values):
                                        website += ', '
                                else:
                                    crossrefDesc += cDesc + ' '

                    elif self.getValueOrTextCheck(subValue):
                        newSubText = self.getValueOrText(subValue, returnType='text').strip()
                        newSubValue = self.getValueOrText(subValue, returnType='value').strip()
                        #print newSubText + ' ' + newSubValue

                        if self.isAccountTag(newSubText, self.tag.tag_list_account):
                            if result.find(newSubText + ':') != -1:
                                split = result.find(newSubText + ':') + len(newSubText) + 1
                                result = result[0 : split] + subText + '(' + newSubValue + '), ' + result[split:]
                            else:
                                result += newSubText + ':' + subText + '(' + newSubValue + ')' + tagSplit
                        elif self.search_engin_dict.has_key(newSubValue):
                            website += subText + '(' + self.validSubvalue(self.toQueryUrl(self.getEnginUrl(newSubValue), newSubText)) + '), '

                    else:
                        desc += subText + ' '

                elif self.isAccountTag(text, self.tag.tag_list_account):
                    result = self.accountValue2Desc(text, text, v, result, tagSplit)
                else:
                    desc += v + ' '
            
            result = result.strip()
            if website != 'website:':
                website = website.strip()
                if website.endswith(','):
                    website = website[0 : len(website) - 1]
                result += tagSplit + website
            if desc != 'description:':
                result += tagSplit + desc.replace('(', ' ')

            #print result
            if crossrefDesc != '':
                
                result = self.mergerDesc(result, crossrefDesc)

            #print result
            return result

        else:
            return ''

    def splitText(self, args):
        keys = []
        if args.find('**') != -1:
           args = args.split('**')
           for i in range(int(args[0]), int(args[1]), int(args[2])):
               keys.append(str(i))
        elif args.find('*') != -1:
            keys = args.split('*')
        return keys   

    def crossref2Record(self, crossref, rID=''):
        if crossref.find('==') != -1:
            crossref = crossref.replace('==', '->')
        print 'crossref2Record crossref:' + crossref
        path = 'db/' + crossref[0 : crossref.find('#')]
        field = ''
        rTitle = ''
        record = None
        if crossref.find('->') != -1:
            field = crossref[crossref.find('->') + 2 :]
            rTitle = crossref[crossref.find('#') + 1 : crossref.find('->')]
        else:
            rTitle = crossref[crossref.find('#') + 1 :]
        if field != '':
            desc = self.crossref2Desc(crossref)
            if rID == '':
                rID = 'crossref2record'
            record = Record(rID + ' | ' + field + ' | | ' + desc)
        else:
            record = self.getRecord(rTitle, path=path, matchType=2)

              
        return record

    def crossref2Desc(self, crossref):
        v = crossref
        crossrefDesc = ''
        #print '-----crossref2Desc-----'
        #print crossref
        r = None
        key, link = self.getCrossrefUrl(v)
        if v.find('/') != -1:
            text = v[v.rfind('/') + 1 :]
            if text.find('#') != -1:
                path = 'db/' + v[0 : v.rfind('#')]
                text = text[text.find('#') + 1 :]
                if text.find('->') != -1:
                    keywords = text[text.find('->') + 2 :]
                    text = text[0 : text.find('->')]
                    link = link[0 : link.find('->')]
                    print '--->yyy' + keywords + ' ' + path
                    for keyword in keywords.split('&'):
                        keyword = keyword.strip()
                        r = self.getRecord(text, path=path, matchType=2, use_cache=True, log=True)
                        if r != None and r.get_id().strip() != '':
                            matchedText, descList = r.get_desc_field3(self, keyword, self.tag.get_tag_list(''), toDesc=True, prefix=False, deepSearch=False, accurateMatch=True, startMatch=True, endMatch=True)
                            #print '--->xxx'
                            #print ' '.join(descList)
                            crossrefDesc = self.mergerDesc(crossrefDesc, ' '.join(descList))
                            #crossrefDesc += ' '.join(descList) + ' '
                        else:
                            print '**** crossref error ****:' + keyword + ' ' + v
                else:
                    crossrefDesc = 'website:' + text + '(' + self.validSubvalue(link) + ')'
            else:

                crossrefDesc = 'website:' + text + '(' + self.validSubvalue(link) + ')'

        #print crossrefDesc
        return crossrefDesc

    def mergerDesc(self, desc1, desc2):
        if desc1 == '':
            return desc2
        if desc2 == '':
            return desc1

        return self.dict2Desc(self.mergerDescDict(self.toDescDict(desc1, ''), self.toDescDict(desc2, '')))

    def accountValue2Desc(self, text, subText, subValue, result, tagSplit):
        print 'text:' + text + ' subText:' + subText + ' subValue:' + subValue
        subValue = self.validSubvalue(subValue)
        if subValue.startswith('http'):
            subValue = text + '(' + subValue + ')'
        if subValue.find('*') != -1:
            subValue = ', '.join(subValue.split('*'))

        if result.find(subText + ':') != -1:
            split = result.find(subText + ':') + len(subText) + 1
            result = result[0 : split] + subValue + ', ' + result[split:]
        else:
            result += subText + ':' + subValue + tagSplit

        #print result

        return result


    def validSubvalue(self, subValue):
        if subValue.find(')') != -1 and subValue.find('(') == -1:
            subValue = subValue.replace(')', '')

        return subValue

    def genPreviewLink(self, aid, text, url):

        js = "onHoverPreview('" + aid + "', '" + text + "', '" + url + "', 'searchbox', true);"

        html = '<a target="_blank" href="javascript:void(0);" onclick="' + js + '">' + self.getIconHtml('', 'preview') + '</a>'

        return html

    def genDescLinkHtml(self, text, titleLenm, library='', rid='', aid='', refreshID='', fontScala=0, accountIcon=True, returnUrlDict=False, haveDesc=False, parentDesc='', module='', nojs=False, unfoldSearchin=False, parentOfSearchin='', previewLink=False):
        tagStr = text[0: text.find(':') + 1].strip()
        tagValue =  text[text.find(':') + 1 : ].strip()

        html = ''
        count = 0
        urlDict = {}
        htmlSpace = ' '
        if fontScala < -4:
            htmlSpace = '&nbsp;' * 3

        if tagStr == 'website:':
            tagValues = tagValue.split(', ')
            for item in tagValues:
                count += 1
                newAID = aid + '-website-' + str(count)
                shwoText = self.getLinkShowText(False, item, tagStr.replace(':', ''), len(tagValues), fontScala=fontScala)

                if self.getValueOrTextCheck(item):
                    itemText = self.getValueOrText(item, returnType='text')
                    #print itemText
                    itemValue = self.getValueOrText(item, returnType='value')
                    urlDict[itemText] = itemValue
                    html += self.enhancedLink(itemValue, itemText, module=module, library=library, rid=rid, aid=newAID, refreshID=refreshID, resourceType=tagStr.replace(':', ''), showText=shwoText, dialogMode=False, originText=item, haveDesc=haveDesc, nojs=nojs)
                    iconHtml = self.getIconHtml(itemValue, title=itemText, desc=text, parentDesc=parentDesc)
                    if iconHtml != '':
                        html = html.strip() + iconHtml
                    if previewLink:
                        html += self.genPreviewLink(newAID, itemText, itemValue)
                else:
                    url = self.toQueryUrl(self.getEnginUrl('glucky'), item)
                    urlDict[item] = url
                    html += self.enhancedLink(url, item, module=module, library=library, rid=rid, aid=newAID, refreshID=refreshID, resourceType=tagStr.replace(':', ''), showText=shwoText, dialogMode=False, originText=item, haveDesc=haveDesc, nojs=nojs)
                    if previewLink:
                        html += self.genPreviewLink(newAID, item, url)
                if count != len(tagValues):
                    html += ',' + htmlSpace
        elif self.isAccountTag(tagStr, self.tag.tag_list_account):
            url = ''
            if self.tag.tag_list_account.has_key(tagStr):
                url = self.tag.tag_list_account[tagStr]
            else:
                url = utils.getEnginUrl('glucky')

            tagValues = tagValue.split(',')
            for item in tagValues:
                item = item.strip()
                count += 1
                newAID = aid + '-' + tagStr.replace(':', '').strip().lower() + '-' + str(count)
                shwoText = self.getLinkShowText(True, item, tagStr.replace(':', ''), len(tagValues), fontScala=fontScala, accountIcon=accountIcon)
                if self.getValueOrTextCheck(item):
                    itemText = self.getValueOrText(item, returnType='text')
                    #print itemText
                    link = self.getValueOrText(item, returnType='value')
                    if link.startswith('http') == False:
                        link = self.toQueryUrl(url, link)
                    urlDict[itemText] = link
                    html += self.enhancedLink(link, itemText, module=module, library=library, rid=rid, aid=newAID, refreshID=refreshID, resourceType=tagStr.replace(':', ''), showText=shwoText, dialogMode=False, originText=item, haveDesc=haveDesc, nojs=nojs)
                    html += self.getIconHtml('remark', title=itemText, desc=text, parentDesc=parentDesc)
                    if previewLink:
                        html += self.genPreviewLink(newAID, itemText, link)           
                else:
                    link = item
                    if link.startswith('http') == False:
                        link = self.toQueryUrl(url, item)
                    urlDict[item] = link
                    html += self.enhancedLink(link, item, module=module, library=library, rid=rid, aid=newAID, refreshID=refreshID, resourceType=tagStr.replace(':', ''), showText=shwoText, dialogMode=False, originText=item, haveDesc=haveDesc, nojs=nojs)
                    if previewLink:
                        html += self.genPreviewLink(newAID, item, link)  
                if count != len(tagValues):
                    html += htmlSpace

        elif tagStr == 'icon:':
            html += '<img src="' + tagValue + '" height="14" width="14" />'

        elif tagStr == 'searchin:':
            print 'unfoldSearchin:' + str(unfoldSearchin)
            tagStr = ''
            cmds = tagValue.split(',')
            result = ''
            searchResultDict = {}
            searchResultBRCountDict = {}
            for cmd in cmds:
                cmd = cmd.strip()
                if unfoldSearchin:
                    searchResult = self.searchLibrary(cmd, '', noDiv=True, unfoldSearchin=False, noFilterBox=True, isRecursion=True)
                    brCount = 0
                    brIndex = 0
                    while True:
                        brIndex = searchResult.find('<br>', brIndex)
                        if brIndex != -1:
                            brIndex += 5
                            brCount += 1
                        else:
                            break

                    if len(cmds) > 1:
                        searchResultBRCountDict[cmd] = brCount
                        searchResultDict[cmd] = searchResult 
                        #result += '<div align="left" style="padding-left: 0; padding-top: 2px; width:455px; height:' + str(divHeight) + 'px; float:left;">'
                    else:
                        result += '<div align="left" style="padding-left: 455; padding-top: 2px; width:auto; ">'
                        result += searchResult
                        result += '</div>'
                else:
                    result += '<a href="javascript:void(0);" onclick="typeKeyword(' + "'" + cmd + "', '" + parentOfSearchin + "'" +')" style="color: rgb(153, 153, 102); font-size:9pt;">' + cmd + '</a> '
            #if unfoldSearchin == False and tagValue.find(parentOfSearchin) == -1:
            #    result = '<a href="javascript:void(0);" onclick="typeKeyword(' + "'" + parentOfSearchin + "', '" + parentOfSearchin + "'" +')" style="color: rgb(153, 153, 102); font-size:9pt;">' + parentOfSearchin + '</a> ' + result

            #print result
            if len(searchResultDict) > 0:
                count = 0
                divHeight = 455
                maxHeight = 0
                itemCache = []
                for item in sorted(searchResultBRCountDict.items(), key=lambda searchResultBRCountDict:int(searchResultBRCountDict[1]), reverse=True):
                    count += 1
                    print item
                    cmd = item[0]
                    brCount = item[1]
                    brHeight = 20

                    lenght = len(self.clearHtmlTag(searchResultDict[item[0]]))

                    if lenght > 1200:
                        brHeight = 36
                    elif lenght > 600:
                        brHeight = 33
                    if brCount > 0:
                        divHeight = brCount * brHeight
                    print 'cmd:' + cmd + ' brCount=' + str(brCount) + ' divHeight=' + str(divHeight) + ' lenght=' + str(lenght)

                    if divHeight > maxHeight:
                        maxHeight = divHeight

                    if count == 3:
                        itemCache.append(item)
                        for i in itemCache:
                            result += '<div align="left" style="padding-left: 0; padding-top: 2px; width:455px; height:' + str(maxHeight) + 'px; float:left;">'  
                            result += searchResultDict[i[0]]
                            result += '</div>'
                        itemCache = []
                        count = 0
                    else:
                        itemCache.append(item)

                if len(itemCache) > 0:
                    for i in itemCache:
                        result += '<div align="left" style="padding-left: 0; padding-top: 2px; width:455px; height:' + str(maxHeight) + 'px; float:left;">'  
                        result += searchResultDict[i[0]]
                        result += '</div>'                    

                    

            if unfoldSearchin == False:
                result = self.getIconHtml('searchin:') + ':' + result

            html += result
        else:
            if returnUrlDict:
                return urlDict
            else:
                return ' ' + tagStr + self.formatTitle(tagValue)

        if returnUrlDict:
            return urlDict
        else:            
            return ' ' + tagStr + html

    def genCrossrefHtml(self, rid, aid, tag, content, library, split_char=','):
        html = ''
        if content.find('#') != -1:           
            result = self.getCrossrefUrls(content).items()
            for ft, link in result:
                text = '<font style="font-size:10pt;">' + ft + '</font>'
                db = content[0 : content.rfind('/') + 1].strip()
                if db.find('library/') != -1:
                    text = '<font style="font-size:10pt; color="red">' + ft[0:1] + '</font>' + '<font style="font-size:10pt;">' + ft[1:] + '</font>'
                html += self.enhancedLink(link, text, module='main', library=library, rid=rid, resourceType=tag, urlFromServer=False, dialogMode=False, aid=aid)
                if ft != result[len(result) -1][0]:
                    html += split_char + '&nbsp;'
                #if ft != filters[len(filters) -1]:
                #    html += '<br>'
        else:
            key, url = self.getCrossrefUrl(content) 

            html += self.enhancedLink(url, '<font style="font-size:10pt;">' + key + '</font>', module='main', library=library, rid=rid, resourceType=tag, urlFromServer=False, dialogMode=False, aid=aid) 

        return html 

    def getCrossrefUrls(self, content):
        data = content.strip().split('#')
        result = {}
        if len(data) < 2:
            return result
        filters = []
        if data[1].find('+') != -1:
            filters = data[1].split('+')
        else:
            filters = [data[1]]

        db = data[0][0 : data[0].rfind('/') + 1].strip()
        key = data[0][data[0].rfind('/') + 1 :].strip()
        for ft in filters:
            #print ft + '<br>'
            link = 'http://' + Config.ip_adress + '/?db=' + db + '&key=' + key + '&filter=' + ft
            result[ft] = link

        return result     

    def getCrossrefUrl(self, content):
        db = content[0 : content.rfind('/') + 1].strip()
        key = content[content.rfind('/') + 1 :].strip()
        if key.find('#') != -1:
            key = key.replace('#', '&filter=')
        link = 'http://' + Config.ip_adress + '/?db=' + db + '&key=' + key 
        return key, link

    def next_pos(self, text, start, titleLen, keywordList, htmlStyle=True, library=''):
        min_end = len(text)
        c_len = titleLen
        if htmlStyle:
            c_len = titleLen + 10
        for k in keywordList:
            end = text.find(' ' + k, start + 2)
            if text.find(' ' + k + ' ', end) != -1:
                continue
            if end != -1 and end + 1 < min_end:
                end += 1
                min_end = end

        if min_end == len(text):
            return min_end


        if min_end < len(text):
            startTag = text[start : text.find(':', start) + 1]
            smart_link_str = ' '.join(self.tag.get_list_smart_link(library))
            account_str = ' '.join(self.tag.tag_list_account.keys())

            if smart_link_str.find(startTag) != -1 or account_str.find(startTag) != -1:
                return min_end -1

            min_end -= 1
            if min_end - start > c_len:
                ret_end = start + c_len
                return self.space_end(text, start, ret_end, c_len, htmlStyle=htmlStyle)
            else:
                return min_end 

        if (len(text) - start) < c_len:
            return start + len(text) - start
        else:
            ret_end = start + c_len
            return self.space_end(text, start, ret_end, c_len, htmlStyle=htmlStyle)
           
    def space_end(self, text, start, end, c_len, htmlStyle=True): 
        if htmlStyle == False:
            return end

        ret_end1 = end
        ret_end2 = end
        while ret_end1 >= 0 and ret_end1 < len(text) and text[ret_end1] != ' ':
            ret_end1 -= 1
        if ret_end1 < 0:
            return 0
        while ret_end2 >= 0 and ret_end2 < len(text) and text[ret_end2] != ' ':
            ret_end2 += 1
        if ret_end2 >= len(text):
            return len(text)
        
        if (end - ret_end1) > (ret_end2 - end):
            return ret_end2
        if (ret_end2 - start) <= c_len:
            return ret_end2
        else:
            return ret_end1


    def icon_keyword(self, text, keywordList, isTag=True, color="#66CCFF", rawText='', parentOfSearchin=''):
        result = text
        #print len(keywordList)
        #print 'icon_keyword' + rawText
        for k in keywordList:
            if isTag:
                k = ' ' + k
                if result.find(k + ' ') != -1:
                    continue
            if result.find(k) == -1:
                continue
            k = k.strip()

            if Config.website_icons.has_key(k.replace(':', '')):
                script = ''
                if rawText != '':
                    tagStr = rawText[0 : rawText.find(':') + 1].strip()
                    tagValue = rawText[rawText.find(':') + 1 : ]
                    valueList = tagValue.split(',')
                    print tagStr
                    if len(valueList) > 1 and len(valueList) < 6:
                        if tagStr == 'website:':
                            urlList = []
                            textList = []
                            for item in valueList:
                                item = item.strip()
                                if self.getValueOrTextCheck(item):
                                    url = self.getValueOrText(item, returnType='value')
                                    textList.append(self.getValueOrText(item, returnType='text'))
                                else:
                                    url = self.toQueryUrl(self.getEnginUrl('glucky'), item)
                                    textList.append(item)

                                urlList.append(url)
                            script = ''
                            if False and Config.open_all_link_in_one_page:
                                script = "openAllOnePage('" + ','.join(textList) + "', '" + ','.join(urlList) + "', 'searchbox');"
                            else:
                                script = "batchOpenUrls('" + ','.join(urlList) + "');"
                    else:
                        script = "typeKeyword('" + parentOfSearchin + "/" + tagStr + "','" + parentOfSearchin + "');"

                image = "<img src=" + Config.website_icons[k.replace(':', '')] + ' width="14" height="12" style="border-radius:10px 10px 10px 10px; opacity:0.7;">'
                
                if script != '':
                    image = '<a target="_blank" href="javascript:void(0);" onclick="' + script + '">' + image + '</a>'
                result = self.replacekeyword(result, k, image + ':')

            else:
                result = self.replacekeyword(result, k, '<font color="' + color + '">' + k + '</font>')
        #print result
        return result.encode('utf-8')

   
    def color_keyword(self, text, keywordList, color_index=0, html_style=True, isTag=True, color1="#33EE22", color2="#66CCFF"):
        result = text
        for k in keywordList:
            if isTag:
                k = ' ' + k
                if result.find(k + ' ') != -1:
                    continue
            if result.find(k) == -1:
                continue
            k = k.strip()
            if (color_index - 1) % 2 == 0:
                if html_style == True:
                    result = self.replacekeyword(result, k, '<font color="' + color1 + '">' + k + '</font>')
                else:
                    result = result.replace(k, self.getColorStr('brown', k))
            else:
                if html_style == True:
                    result = self.replacekeyword(result, k, '<font color="' + color2 + '">' + k + '</font>')
                else:
                    result = result.replace(k, self.getColorStr('darkcyan', k))

        return result.encode('utf-8')

    def replacekeyword(self, data, k, colorKeyword):
        data = data.replace(' ' + k, ' ' + colorKeyword)
        data = data.replace(' ' + k[0 : 1].upper() + k[1:] + ' ', ' ' + colorKeyword)
        data = data.replace(' ' + k[0 : 1].upper() + k[1:], ' ' + colorKeyword)
        data = data.replace(' ' + k.upper(), ' ' + colorKeyword)
        return data

    def find_file_by_pattern(self, pattern='.*', base=".", circle=True):
        re_file = re.compile(pattern, re.I)
        #print pattern
        if base == ".":
            base = os.getcwd()
    
        final_file_list = []
        #print base  
        cur_list = []
        if os.path.isdir(base):
            cur_list = os.listdir(base)
        #print cur_list
        for item in cur_list:
            if item == ".svn" or item == ".git" or item == ".DS_Store":
                continue
    
            full_path = os.path.join(base, item)
            #print full_path
            if os.path.isfile(full_path) and full_path.find('db/') != -1:
                #print full_path
                '''
                with open(full_path, 'r+') as f:
                    try:
                        data = mmap.mmap(f.fileno(), 0)
                        if re_file.search(data):
                            final_file_list.append(full_path)
                    except Exception as e:
                        print str(e) + full_path
                '''
                p = self.find_file_by_pattern_path(re_file, full_path)
                if p != '':
                    final_file_list.append(p)

            else:
                final_file_list += self.find_file_by_pattern(pattern, full_path)
        return final_file_list

    def find_file_by_pattern_path(self, re, path):
        print path
        if os.path.exists(path) == False:
            return ''
        with open(path, 'r+') as f:
            try:
                data = mmap.mmap(f.fileno(), 0)
                if re.search(data):
                    return path
            except Exception as e:
                print str(e) + path
        return ''

    def sortLines(self, lines):
        if len(lines) > 0:
            record_list = []
            for line in lines:
                record_list.append(PaperRecord(line))
            if lines[0].find('published:') != -1:
                self.quickSort(record_list)
            else:
                 self.quickSort(record_list, 'id')
            ret_lines = []
            for r in record_list:
                ret_lines.append(r.line)

            return ret_lines
        else:
            return lines

    def sortRecords(self, records, sortType=''):
        return self.quickSort(records)

    def largeoreq(self, item1, item2, sortType):
        if sortType == "published":
            return item1.get_published().strip() >= item2.get_published().strip()
        #elif sortType == "title":
        #    t1 = item1.get_title().strip()[0 : 1].lower()
        #    t2 = item2.get_title().strip()[0 : 1].lower()
        #    return t1 >= t2

        else:
            return item1.get_id().strip() >= item2.get_id().strip()

    def lessoreq(self, item1, item2, sortType):
        if sortType == "published":
            return item1.get_published().strip() <= item2.get_published().strip()
        #elif sortType == "title":
        #    t1 = item1.get_title().strip()[0 : 1].lower()
        #    t2 = item2.get_title().strip()[0 : 1].lower()
        #    return t1 <= t2
        else:
            return item1.get_id().strip() <= item2.get_id().strip()

    def quickSort(self, alist, sortType="published"):
        self.quickSortHelper(alist,0,len(alist)-1, sortType)

    def quickSortHelper(self, alist,first,last, sortType):
        if first<last:

            splitpoint = self.partition(alist,first,last, sortType)

            self.quickSortHelper(alist,first,splitpoint-1, sortType)
            self.quickSortHelper(alist,splitpoint+1,last, sortType)

    def getIconHtml(self, url, title='', desc='', parentDesc='', width=14, height=12, radius=True):
        url = url.lower()
        if Config.enable_website_icon == False:
            return ''
        if os.path.isdir(url):
            url += '.dir'
            radius = False
            #print url

        if url.startswith('http') == False and parentDesc != '' and title != '':
            #print desc + '--->'
            #print parentDesc + '-->'
            #print title
            if parentDesc.lower().find(' ' + title.lower().strip() + '(') != -1:
                return self.genIconHtml(Config.website_icons['idea'], radius, width, height)
        src = ''
        if url.startswith('http') and url.endswith('btnI=1') == False:
            url = url[0 : url.find('/', url.find('//') + 2)]

        if url != '' and Config.website_icons.has_key(url):
            return self.genIconHtml(Config.website_icons[url], radius, width, height)
        elif title != '' and Config.website_icons.has_key(title):
            return self.genIconHtml(Config.website_icons[title], radius, width, height)
        else:

            if self.isShortUrl(url) and title != '':
                url = title
            for k, v in Config.website_icons.items():
                if url.lower().find(k.lower()) != -1:
                    src = v
                    break
            if src == '':
                if self.urlConvertable(url):
                    return self.genIconHtml(Config.website_icons['data'], radius, width, height)

            return self.genIconHtml(src, radius, width, height)

    def urlConvertable(self, url):
        urlPart = url[url.find('//') + 2 :]
        if urlPart.find('/') != -1:
            urlPart = urlPart[0 : urlPart.find('/')]
        for key in urlPart.split('.'):
            if key == 'www' or key == 'com' or key == 'net' or key == 'org':
                continue
            if Config.convert_dict.has_key(key):       
                return True
        return False

    def genIconHtml(self, src, radius, width, height):
        if src != '':
            if radius:
                return ' <img src="' + src + '" width="' + str(width) + '" height="' + str(height) + '" style="border-radius:10px 10px 10px 10px; opacity:0.7;">'
            else:
                return ' <img src="' + src + '" width="' + str(width) + '" height="' + str(height) + '">'
        return ''      

    def partition(self, alist,first,last, sortType):
        pivotvalue = alist[first]

        leftmark = first+1
        rightmark = last

        done = False
        while not done:

            while leftmark <= rightmark and self.largeoreq(alist[leftmark], pivotvalue, sortType):
                leftmark = leftmark + 1

            while self.lessoreq(alist[rightmark], pivotvalue, sortType) and rightmark >= leftmark:
                rightmark = rightmark -1

            if rightmark < leftmark:
                done = True
            else:
                temp = alist[leftmark]
                alist[leftmark] = alist[rightmark]
                alist[rightmark] = temp

        temp = alist[first]
        alist[first] = alist[rightmark]
        alist[rightmark] = temp


        return rightmark

    
    def getColorStr(self, color, t):
        return '\033[' + self.cc_map[color] + 'm{0}\033[0m'.format(t)

    def print_inx(self, foreground, newline, *kw):    
        if foreground in self.cc_map:
            for t in kw:
                print '\033[' + self.cc_map[foreground] + 'm{0}\033[0m'.format(t),
        else:
            for t in kw: print t,
        
        if newline: print
       
    def print_colorful(self, foreground, newline, *kw):    
        try:
            if foreground == 'darkyellow':
                foreground = 'brown'
      
            if os.name == 'nt':
                self.print_nt(foreground, newline, *kw)
            else:
                self.print_inx(foreground, newline, *kw)
        except:
            for t in kw: print t,
            if newline: print

    def to_unicode(self, value):
        if not isinstance(value, basestring):
            value = str(value)
        if not isinstance(value, unicode):
            value = unicode(value, "UTF-8", "strict")
        return value

    def char_block_width(self, char):
        # Basic Latin, which is probably the most common case
        #if char in xrange(0x0021, 0x007e):
        #if char >= 0x0021 and char <= 0x007e:
        if 0x0021 <= char <= 0x007e:
            return 1
        # Chinese, Japanese, Korean (common)
        if 0x4e00 <= char <= 0x9fff:
            return 2
        # Hangul
        if 0xac00 <= char <= 0xd7af:
            return 2
        # Combining?
        if unicodedata.combining(uni_chr(char)):
            return 0
        # Hiragana and Katakana
        if 0x3040 <= char <= 0x309f or 0x30a0 <= char <= 0x30ff:
            return 2
        # Full-width Latin characters
        if 0xff01 <= char <= 0xff60:
            return 2
        # CJK punctuation
        if 0x3000 <= char <= 0x303e:
            return 2
        # Backspace and delete
        if char in (0x0008, 0x007f):
            return -1
        # Other control characters
        elif char in (0x0000, 0x001f):
            return 0
        # Take a guess
        return 1

    def str_block_width(self, val):
        return sum(itermap(self.char_block_width, itermap(ord, regex.sub("", val))))

    '''
    def clearHtmlTag(self, html):
        while(html.find('<') != -1 and html.find('>') != -1):
            start = html.find('<')
            end = html.find('>')
            if start > end:
                break
            html = html.replace(html[html.find('<') : html.find('>') + 1], '')
        return html
    '''

    def encode_feedparser_dict(self, d):
        """
        helper function to get rid of feedparser bs with a deep copy.
        I hate when libs wrap simple things in their own classes.
        """
        if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
          j = {}
          for k in d.keys():
            j[k] = self.encode_feedparser_dict(d[k])
          return j
        elif isinstance(d, list):
          l = []
          for k in d:
            l.append(self.encode_feedparser_dict(k))
          return l
        else:
          return d

    def get_arxiv_entries(self, query):
        query_url = 'http://export.arxiv.org/api/query?search_query=' + query
        response = None
        try:
            response = urllib.urlopen(query_url).read()
        except Exception as e:
            exception = True
        #response = self.requestWithProxy(base_url+query).text
        if response != None:
            parse = feedparser.parse(response)
            return parse.entries
        return None

    def get_last_arxiv_version(self, query):
        for e in self.get_arxiv_entries(query):
            j = self.encode_feedparser_dict(e)
            return j['id'][j['id'].rfind('v') :]
        return 'v1'


    def gen_plugin_content(self, selection, url, search_box=True):
        '''
        f = open("web_content/chrome/input", 'w');
        f.write(' | ' + selection.replace('"', ' ').replace("'", " ").replace('\n', '').strip() + '| | ')
        f.close()
        cmd = "./list.py -i web_content/chrome/input -b 4  -c 1  -p -e 'd:star' -n -d "
        '''
        html = ''
        title = selection.replace('"', ' ').replace("'", " ").replace('\n', '').strip()
        if title != '':
            print str(datetime.datetime.now())

            cmd = "./list.py -i ' | " + title + " | " + url + " | ' -b 4  -c 1  -p -e 'd:star' -n -d "
            if search_box == False:
                cmd += ' -x '
            
            cmd += " > web_content/chrome/output.html"
            html = subprocess.check_output(cmd, shell=True)
            print str(datetime.datetime.now())
            #print data
            #data = "ddd"
            #f = open('web_content/chrome/output.html', 'w')
            #f.write(html)
            #f.close()

            print selection
        html = '<head>'
        script = ""
        html += '<script>' + script + '</script>'
        html += '<head><body>'
        if search_box:
            html = '<iframe  id="iFrameLink" width="600" height="300" frameborder="0"  src="http://' + Config.ip_adress + '/web_content/chrome/test.html"></iframe>'
        else:
            html = '<iframe  id="iFrameLink" width="600" height="210" frameborder="0"  src="http://' + Config.ip_adress + '/web_content/chrome/test.html"></iframe>'
        

        html += '<div id="info"></div></body>'

        return html
        #return '{"firstAccess" : "' + data + '"}'

    def suportFrame(self, url, sec):
        output = ''

        key = url.replace('https://', '').replace('http://', '').replace('www.', '')
        if key.find('/') != -1:
            key = key[ 0 : key.find('/')].strip()

        print 'suportFrame:'
        print 'url:' + url + ' key:' + key

        if key.startswith(Config.ip_adress):
            return True
        if self.suportFrameCache.has_key(key):
            return self.suportFrameCache[key]

        try:
            output = subprocess.check_output("curl --max-time " + str(sec) + " --head " + url, shell=True)
            print output
        except Exception as e:
            output = ''

        if output != '' and output.find('X-Frame-Options:') < 0:

            self.suportFrameCache[key] = True
            #print '\n'.join(self.suportFrameCache.keys())
            return True

        self.suportFrameCache[key] = False
        #print '\n'.join(self.suportFrameCache.keys())
        return False

    def websiteNotWorking(self, url, sec):
        output = ''
        try:
            cmd = "curl --max-time " + str(sec) + " --head " + url
            print cmd
            output = subprocess.check_output(cmd, shell=True)
            print output
        except Exception as e:
            output = ''
        if output.find('200 OK') == -1:
            return True
        return False

    def slack_message(self, message, channel='general'):
        token = '-'.join(Config.slack_token)
        sc = SlackClient(token)
        #print token
        sc.api_call('chat.postMessage', channel=channel, 
                    text=message, username='My Sweet Bot',
                    icon_emoji=':robot_face:')

    def toListHtml(self, titleList, urlList, htmlList, descHtmlList=None, splitNumber=0, moreHtml=True, showWebsiteIcon=True, rid='', aidList=[], refreshIDList=[], orginFilename=''):
        html = ''
        start = False 
        if splitNumber == 0:
          html = '<div class="ref"><ol>'
          start = True
        count = 0

        for i in range(0, len(titleList)):
          title = titleList[i]
          if title == '':
              continue
          count += 1
          if splitNumber > 0 and (count == 1 or count > splitNumber):
              if start:
                  html += '</ol></div>'
                  count = 1
                
              html += '<div style="float:left;"><ol>'
              start = True

          url = urlList[i]
          html += '<li><span>' + str(i + 1) + '.</span>'
          if url != '':
              html += '<p>'

              html += self.enhancedLink(url, title, module='history', library=orginFilename, aid=aidList[i], refreshID=refreshIDList[i])
              #'<a target="_blank" href="' + url + '">' + title + '</a>'
          else:
              html += '<p>' + self.utils.toSmartLink(title, Config.smart_link_br_len)

          if showWebsiteIcon:
              html += self.getIconHtml(urlList[i])

          if htmlList != None and len(htmlList) > 0:
              html += htmlList[i]
          if moreHtml:
              divID = 'div-' + aidList[i].replace('a-', '')
              linkID = aidList[i] + '-more'
              appendID = str(i + 1)
              script = self.genMoreEnginScript(linkID, divID, "loop-" + str(appendID), title, url, '-', hidenEnginSection=True)
              descHtml = ''
              if descHtmlList != None:
                descHtml = descHtmlList[i]
              html += self.genMoreEnginHtml(linkID, script.replace("'", '"'), '...', divID, '', False, descHtml=descHtml);


          html += '</p></li>'

        if start:
          html += '</ol></div>'
        return html

    def clearHtmlTag(self, htmlstr):
        if htmlstr.find('<') == -1:
            return htmlstr
            
        re_cdata=re.compile('//<!\[CDATA\[[^>]*//\]\]>',re.I)
        re_script=re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>',re.I)
        re_style=re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>',re.I)
        re_br=re.compile('<br\s*?/?>')
        re_h=re.compile('</?\w+[^>]*>')
        re_comment=re.compile('<!--[^>]*-->')
        s=re_cdata.sub('',htmlstr)
        s=re_script.sub('',s) 
        s=re_style.sub('',s)
        s=re_br.sub('\n',s)
        s=re_h.sub('',s) 
        s=re_comment.sub('',s)
        blank_line=re.compile('\n+')
        s=blank_line.sub('\n',s)
        s=self.replaceCharEntity(s)
        return s.strip()

    def replaceCharEntity(self, htmlstr):
        CHAR_ENTITIES={'nbsp':' ','160':' ',
                    'lt':'<','60':'<',
                    'gt':'>','62':'>',
                    'amp':'&','38':'&',
                    'quot':'"','34':'"',}
        
        re_charEntity=re.compile(r'&#?(?P<name>\w+);')
        sz=re_charEntity.search(htmlstr)
        while sz:
            entity=sz.group()
            key=sz.group('name')
            try:
                htmlstr=re_charEntity.sub(CHAR_ENTITIES[key],htmlstr,1)
                sz=re_charEntity.search(htmlstr)
            except KeyError:
                htmlstr=re_charEntity.sub('',htmlstr,1)
                sz=re_charEntity.search(htmlstr)
        return htmlstr

    def repalce(self, s,re_exp,repl_string):
        return re_exp.sub(repl_string,s)

    def reflection_call(self, module, cls, method, cls_arg=None, method_arg=None):
        __import__(module)
        m = sys.modules[module]
        for str in dir(m):
            if str == cls:
                att=getattr(m,str)
                obj = None
                if cls_arg != None:
                    obj = att(cls_arg)
                else:
                    obj = att()
                for att2 in dir(att):
                    if att2 == method:
                        func = getattr(obj, att2)
                        if method_arg != None:
                            return apply(func, (), method_arg)    
                        else:
                            return apply(func)

    def check_contain_chinese(self, check_str):
        for ch in check_str.decode('utf-8'):
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False
