# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import json


cnsId = 'your cns id'
cnsPass = 'your cns password'
year = 2018 # the year you want to check
urls = [
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_5.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_8.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_9.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_10.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_11.html".format(year)
]
allPages = [
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_2.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_3.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_4.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_5.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_6.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_7.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_8.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_9.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_10.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_11.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_12.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_13.html".format(year),
    "http://vu.sfc.keio.ac.jp/course_u/data/{}/csec14_15.html".format(year)
]


allId = set()
idToName = {}
idToPageId = {}
id07To14 = {}
checkedId = set()

for idx, url in enumerate(allPages):
    with urllib.request.urlopen(url) as f:
        html = f.read().decode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        # get idToName and idToPageId
        courses = soup.find('ul', class_='clist').find_all('a')
        for course in courses: 
            allId.add(course.string[:5])
            idToName[course.string[:5]] = course.string[6:]
            idToPageId[course.string[:5]] = idx
            
        # get id07To14
        titleTags = soup.find_all('div', class_='course_title')
        #print(titleTags)
        for titleTag in titleTags:
            ankor = titleTag.a
            titleId = titleTag.get_text()[:5]
            if titleId in checkedId: continue
            elif ankor == None:
                checkedId.add(titleId)
                continue
            else: syllabusUrl = ankor.get("href")
            print(titleTag.get_text().split('\n')[0])
            with urllib.request.urlopen(syllabusUrl) as f2:
                html2 = f2.read().decode('utf-8')
                soup2 = BeautifulSoup(html2, "html.parser")
                syllabusUrl2 = 'https://vu.sfc.keio.ac.jp/course2014/summary/syll_view_c.cgi'
                loginInfo = {"cns":cnsId, "u_pass":cnsPass, "cns_checkmode":"1", "yc":"", "ks":"", "lang":""}
                loginInfo["yc"] = soup2.find(attrs={'name': 'yc'}).get('value')
                loginInfo["ks"] = soup2.find(attrs={'name': 'ks'}).get('value')
                fullUrl = syllabusUrl2 + '?' + urllib.parse.urlencode(loginInfo)
                with urllib.request.urlopen(fullUrl) as response:
                    page = response.read().decode("euc-jp", "backslashreplace")
                    soup3 = BeautifulSoup(page, "html.parser")
                    lessonIds = soup3.find_all('span', class_='sm')
                    #print(lessonIds)
                    if len(lessonIds) == 2:
                        #print('2!')
                        id14 = lessonIds[0].get_text()[3:]
                        id07 = lessonIds[1].get_text()[3:]
                        #print(id07)
                        #print(id14)
                        id07To14[id07] = id14
                        checkedId.add(id14)
                    elif len(lessonIds) == 1: 
                        #print('1!')
                        checkedId.add(titleId)
                    else: # len() == 3
                        id14 = [lessonIds[0].get_text()[3:], lessonIds[1].get_text()[3:]]
                        id07 = lessonIds[2].get_text()[3:]
                        id07To14[id07] = id14
                        checkedId.add(titleId)


dfNode = pd.DataFrame({'id':list(idToName.keys())})
for row in range(dfNode.shape[0]):
    dfNode.at[row, 'name'] = idToName[dfNode.at[row, 'id']]
    dfNode.at[row, 'group'] = idToPageId[dfNode.at[row, 'id']]
dfNode = dfNode.astype({'group':int})

dfLink = pd.DataFrame(columns=['source', 'target', 'left', 'right'])


for url in allPages:
    with  urllib.request.urlopen(url) as f:
        html = f.read().decode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        courses = soup.find_all('div', class_='course')
        
        for idx, course in enumerate(courses):
            kanren = course.table.find(string='関連科目')
            zentei = course.table.find(string='前提科目（推奨）') # returns None if not found
            hissu = course.table.find(string='前提科目（必須）')
            relations = [kanren, zentei, hissu]
            courseId = course.find('div', class_='course_title').get_text()[:5]
            if courseId in allId:
                courseNode = dfNode[dfNode['id'].isin([courseId])]
                for i, relation in enumerate(relations):
                    if relation != None:
                        for content in relation.find_parent('tr').select('td:nth-of-type(2)')[0].find_all('a'):
                            idList = [ content.string[1:6] ]
                            if idList[0] in id07To14.keys(): idList = id07To14[idList[0]]
                            for id_ in idList:
                                if content.name == 'a' and id_ in allId:
                                    contentNode = dfNode[dfNode['id'].isin([id_])]
                                    if i == 0:
                                        dfLink = dfLink.append(pd.DataFrame({'source':contentNode.iat[0,0], 'target':courseNode.iat[0,0], 'left':['false'], 'right':['false']}), ignore_index=True)
                                    else:
                                        dfLink = dfLink.append(pd.DataFrame({'source':contentNode.iat[0,0], 'target':courseNode.iat[0,0], 'left':['false'], 'right':['true']}), ignore_index=True)
                 
tete = dfNode.to_json(orient='records', force_ascii=False)
toto = dfLink.to_json(orient='records')
output = '{{"nodes":{0},"links":{1}}}'.format(tete,toto)

with open('courses2.json', 'w') as f:
    f.write(output)