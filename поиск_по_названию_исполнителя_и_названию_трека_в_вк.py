# -*- coding: utf-8 -*-
"""Поиск по названию Исполнителя и Названию трека в ВК.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1JfWzZ6rYt8BTaaAE_bp8czMTkCICBK_O
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install requests
import requests
import csv
import time
# %pip install vk_api
# %pip install m3u8 
import vk_api

import getpass
from getpass import getpass
from vk_api.audio import VkAudio
import json
import pandas as pd

import os

"""Измененный метод VKAUDIO"""

from vk_api.exceptions import AccessDenied
from vk_api.utils import set_cookies_from_list,cookie_from_dict
import re
from bs4 import BeautifulSoup
import warnings
from vk_api.audio_url_decoder import decode_audio_url
import html

class VkUrez(object):
  __slots__ = ('_vk','user_id')
  DEFAULT_COOKIES = [
          {  # если не установлено, то первый запрос ломается
              'version': 0,
              'name': 'remixaudio_show_alert_today',
              'value': '0',
              'port': None,
              'port_specified': False,
              'domain': '.vk.com',
              'domain_specified': True,
              'domain_initial_dot': True,
              'path': '/',
              'path_specified': True,
              'secure': True,
              'expires': None,
              'discard': False,
              'comment': None,
              'comment_url': None,
              'rfc2109': False,
              'rest': {}
          }, {  # для аудио из постов
              'version': 0,
              'name': 'remixmdevice',
              'value': '1920/1080/2/!!-!!!!',
              'port': None,
              'port_specified': False,
              'domain': '.vk.com',
              'domain_specified': True,
              'domain_initial_dot': True,
              'path': '/',
              'path_specified': True,
              'secure': True,
              'expires': None,
              'discard': False,
              'comment': None,
              'comment_url': None,
              'rfc2109': False,
              'rest': {}
          }
      ]         

  def __init__(self, vk):#инициализация
        self.user_id=vk.method('users.get')[0]['id']
        self._vk = vk

        set_cookies_from_list(self._vk.http.cookies, self.DEFAULT_COOKIES)

        self._vk.http.get('https://m.vk.com/')  # load cookies



# метод прохода по трекам пользователя до первого трека удовлетворяющего условиям поиска
  def get_iter(self,owner_id=None, access_hash=None,track=None,artist=None):
          
          """ Получить список аудиозаписей пользователя (по частям)

          :param owner_id: ID владельца (отрицательные значения для групп)
          """

          if owner_id is None:
              owner_id =self.user_id # поменяй на свое

          offset_diff = 1000 # различия в offset
          offset = 0

          tt=[]
          tracks=[]
          while True:
              response =self._vk.http.post(
                  'https://m.vk.com/audio',
                  data={
                      'act': 'load_section',
                      'owner_id': owner_id,
                      'playlist_id': -1,
                      'offset': offset,
                      'type': 'playlist',
                      'access_hash': access_hash,
                      'is_loading_all': 1
                  },
                  allow_redirects=False
              ).json()

              if not response['data'][0]:
                  raise AccessDenied(
                      'You don\'t have permissions to browse {}\'s albums'.format(
                          owner_id
                      )
                  )

              ids = VkUrez.scrap_ids(
                  response['data'][0]['list'],artist,track
              )

              

              tt +=ids

              # если был найден трек удовлетворяющий условиям поиска, заканчиваем поиск и выводим информацию об треке
              if (len(tt)>0):
                #print(tt)
                tracks += [VkUrez.scrap_tracks(
                tt,
                self.user_id,
                self._vk.http
                )]
                #print(tracks)
                break
              if response['data'][0]['hasMore']:
                  offset += offset_diff
              else:
                  break
          return tracks




#метод проверки трека на условие поиска
  @staticmethod
  def poiskinZp(track,artist=None,title=None):
      t=0 #если =2 значит удовлетворяет условиям поиска
      
      if(artist==None):# если в поисковом запросе не фигурировал Исполнитель, то пропускаем
          t+=1
      else:
        if(artist.lower() in track[1].lower()):# если в поисковом запросе фигурировал Исполнитель, то проверяем на условие
            t+=1

      if(title==None):# если в поисковом запросе не фигурировало название трека, то пропускаем
            t+=1
      else:
        if(title.lower() in track[0].lower()):# если в поисковом запросе фигурировало название трека, то проверяем на условие
            t+=1

      if(t==2):
        return 1 #если исполнитель и название удовлетворяют поиску возвращает 1 иначе 0
      else:
        return 0

  
# проход по 1000 трекам пользователя, пока не найдем трек удовлетворяющий поисковым запросам
  @staticmethod
  def scrap_ids(audio_data,artist=None,title=None): 
        """ Парсинг списка хэшей аудиозаписей из json объекта """
        ids = []
        
        for track in audio_data:
            # в функцию проверки условия поиска передаются название трека и его исполнитель, если удовлетворяет, то вывод данных трека иначе переход на другой трек
            if(VkUrez.poiskinZp(( (html.unescape(str(track[3]))).rstrip().lstrip(), (html.unescape(str(track[4]))).rstrip().lstrip()),artist,title)==1):
              audio_hashes = track[13].split("/")
              url=""
              #print(track)
              # если существует ссылка на вк трека то записываем ее, иначе ссылка на аудиозаписи пользователя
              if(str(track[26])!="" and ("-" in str(track[26]))):
                url="https://vk.com/audio"+str(track[26])
              else:
                url="https://vk.com/audios"+str(track[1])
              
              full_id = (str(track[1]), str(track[0]), audio_hashes[2], audio_hashes[5],(html.unescape(str(track[3]))).rstrip().lstrip(), (html.unescape(str(track[4]))).rstrip().lstrip(),url)

              if all(full_id):              
                ids.append(full_id)
              break

        return ids


# преобразование данных найденного трека в json формат + добавление ссылки m3u8 на полученный трек
  @staticmethod
  def scrap_tracks(ids, user_id, http):

            result = http.post(
                'https://m.vk.com/audio',
                data={'act': 'reload_audio', 'ids': ','.join(['_'.join(i) for i in ids[:4]])}
            ).json()

            if result['data']:
                data_audio = result['data'][0]
                for audio in data_audio:
                    #print(audio)
                    artist = ids[0][5]
                    title = ids[0][4]
                    duration = audio[5]
                    link = ids[0][6]
                    m3u8_link=audio[2]

                    #редактирование m3u8 ссылки
                    if 'audio_api_unavailable' in m3u8_link:
                        m3u8_link = decode_audio_url(m3u8_link, user_id)

                    return {
                        'vk_url': link,
                        'm3u8_link': m3u8_link,
                        'artist': artist,
                        'title': title,
                        'duration': duration,
                    }

"""проверка работоспособности m3u8 ссылки"""

import subprocess
#link='https://cs1-74v4.vkuseraudio.net/s/v1/ac/Jpa1r8zfU4STDooLoUEnFe1-_gNdVn0vpt8MCqTNNodLhtuz5qDvc0r2sYdzXtuEjFEjb0GsR2ytADmEpVpCAEIsAWz1LyMf7cGIlqomBksnjo_whU2pfeR53PjIwRij5wk91ucUyAnAyLPf3FelfrQoUxiqleNgTpG6gK1sYQ/index.m3u8'
link='https://cs1-81v4.vkuseraudio.net/s/v1/ac/uIQ-6aaWTNKPjvuwJQEtR_WNBR1O_QoDeJotXsW1wy0bSc6Frh499eUJr9r1cKjEGLhq7krJN_ngt4ctS1J3EdDFK9i1JKJ1n7R3ZtyyWvGJj2aBJ3fegMCzAsMKJCV41r22aCMiHtrtdCOEd-c1JEJ2uxrmsaImECHuxy6QMnbK-Cw/index.m3u8'

print(subprocess.run(['ffmpeg', '-i', link, 'track.mp3']))

"""Класс основных функций"""

import signal
import sys

run = True# глобальная переменная использующаяся для безопасной остановки поиска

class main_funcs():

# для безопасной остановки глобального поиска
  @staticmethod
  def signal_handler(signal, frame):
      print(signal,frame)
      global run
      print("exiting")
      run = False

#функция поиска поледнего id
  @staticmethod
  def last_id(api):
    #сначала находим ткой id,которого нету в вк
    a=0
    b=1000000000
    while True:
      if not api.users.get(user_id=b):
        break
      else:
        a=b
        b=b+1000000000
    #пока не находим поседний id выполняется:
    while True:
      #1)если существует пользовател а и не существует пользователь b, к id b присваивается (половина разности b-a) +a,
      # иначе id a присваивается значение b , а значению b присваивается (половина разности b-a) +b,
      if(api.users.get(user_id=a)):
        if(not api.users.get(user_id=b)):
          b=a+((b-a)//2)
        else:
          c=b
          b=b+((b-a)//2)
          a=c
      
      if(api.users.get(user_id=b) and not api.users.get(user_id=(b+1))): #если существует пользователь b и не существует пользователь b+1 тогда был найден последний пользователь
        break
      else:
        # иначе, если a и b совпали проверяются условия выхода:
        if(b==a):
          if(api.users.get(user_id=b)): # если пользователь b существует проходим вправо до крайнего пользователя
            b+=1
            while api.users.get(user_id=(b+1)):
              b+=1
          else: # если пользователя b не существует проходим влево до крайнего пользователя
            b-=1
            while not api.users.get(user_id=b):
              b-=1
          break 
    return(b)
      


#функция поиска по запросам
  @staticmethod
  def poisk_ids2(api,session,all=0): # all условие поиска по людям (по всем пользователям - 1/ по ограниченному числу - 0)
    global run
    listUsers=[] #количество найденных пользователей

    count=-1 #количество человек которые нас интересуют
    artist="" #нужный артист
    title="" #нужная песня
    tpere="" #передумал искать
    try:
      while (artist=="" and title==""):
        while True:
          isa=input('хотите выйти из поиска?: да/нет ')
          if isa=="нет":
            break
          else:
            if isa=="да":
              tpere="да"
              break
        if tpere=="да":
          break

        print("заполните поисковые запросы")
        while True:
          isa=input('поиск по артисту?: да/нет ')
          if isa=="нет":
            break
          else:
            if isa=="да":
              artist=input('введите название артиста: ')
              break

        while True:
          isa=input('поиск по названию песни?: да/нет ')
          if isa=="нет":
            break
          else:
            if isa=="да":
              title=input('введите название песни: ')
              break
        print(artist+" "+title)

      if tpere=="да":
          return
    except:
      print("exiting")
      return

    last_Vk_Id=0

    try:
      if(all==1):
        print("идет поиск последнего id в вк (примерно 40 секунд)")
        last_Vk_Id=main_funcs.last_id(api)#получение последнего Id vk
        print("будет произведен поиск по ",last_Vk_Id," пользователям")
    except:
      print("exiting")
      return

    try:
      if all==0:
        while(count<=0):
          tru=1#проверяет являются ли введенные данные числом
          a=input('сколько людей вы хотите обойти (введите целое числовое значение от 1): ')
          
          try:
            a=int(a)
          except:
            tru=0
          if(tru==1):
            count=a
      else:    
        count=last_Vk_Id
    except:
      print("exiting")
      return
      
    #print(count)
    offset=1#смещние
    mc=1 # счетчик пройденных пользователей

    signal.signal(signal.SIGINT, main_funcs.signal_handler)
    print("если хотите выйти из поиска нажмите ctrl + c или остановите выполнение основной функции, данные не будут потеряны")
    print(count)
    while run:
      if all==0:
          if mc>count:# если мы прошли необходимое число пользователей
            break
      s_off=20 #количество пользователей хотим обойти за шаг

      if(count-offset<s_off): # если на последнем шагу, то обрезаем количество пользователей на шаг до недостающего количества
        s_off=count-offset
      
      #temp=api.users.get(user_ids=list(range(426036422,426036422+1)),fields="can_see_audio") # для тестирования программы

      temp=api.users.get(user_ids=list(range(offset,offset+s_off+1)),fields="can_see_audio") # получем данные s_off пользователей начиная с пользователя offset

      for j in temp: #для каждого пользователя в temp
        if(not run):
          break
        try:
          if(j["can_see_audio"]==1): # проверяем открыты ли у него аудиозаписи
            
            a=main_funcs.poiskzp111(session,j['id'],artist,title)# выполняем поиск по записям
            if len(a)>0:# если ре у пользователя есть aудио удовлетворяющие условиям поиска то записываем в список пользователя этого пользователя
              full_info={
                        'id': j["id"],
                        'first_name':j["first_name"],
                        'last_name':j["last_name"],
                            'vk_url': a[0]['vk_url'],
                            'm3u8_link': a[0]['m3u8_link'],

                            'artist': a[0]["artist"],
                            'title': a[0]["title"],
                            'duration': a[0]["duration"],
                        
                    }
              listUsers.append(full_info)
                  
          print(str(j['id'])+" "+str(mc))
        except: # страница пользователя удалена
          print(str(j["id"])+" "+str(mc)+" deleted")

        mc+=1
      offset+=21
    

    if (os.path.isfile('/content/vk_config.v2.json')):
      os.remove('/content/vk_config.v2.json')
    run=True
    return listUsers

# создание json файла и csv файла из списка пользователей удовлетворяющих условиям поиска
  @staticmethod
  def create_files(info):

    with open('data.json', 'w', encoding='utf-8') as f:#создание json файла
        json.dump(info, f, ensure_ascii=False, indent=4)

    with open('data.json', encoding='utf-8') as inputfile:#создание csv файла
        df = pd.read_json(inputfile)

    df.to_csv('csvdata.csv', encoding='utf-8', index=False)


#основная функция реализации поиска
  @staticmethod
  def main_func(argv=None):
    
        try:
          login=input('Enter your login: ')
          password = getpass("Пароль: ")
          session = vk_api.VkApi(login=login,password=password)# авторизация и получение api сессии
          session.auth()
          vkaudio =VkAudio(session)
        except:
          print('авторизация прошла неуспешно')
          return
      
        api=session.get_api()#получение доступа к api методам
        print("хотите пройти по всем пользователям - 1/ по ограниченному числу - 0")
        isa=0

        try:
          while True:
            isa=input('введите 0 или 1 ')
            if isa=="0":
              break
            else:
              if isa=="1":
                break
        except:
          print("exiting")
          return
        
        try:
          info=main_funcs.poisk_ids2(api,session,int(isa))# получение пользователей
        except:
          print("exiting")
          return

        try:
          if(len(info)!=0):
            print("Всего обнаружено: ",len(info)," пользователей" )
            print("Информация о найденных пользователях: ")
            print("____________________________________________________________________")

            for i in info:# вывод найденной информации
              print("id пользователя: ",i['id'])
              print("Имя пользователя: ",i['first_name'])
              print("Фамилия пользователя: ",i['last_name'])
              print("Исполнитель: ",i['artist'])
              print("Название: ",i['title'])
              print("Ссылка на трек в VK: ",i['vk_url'])
              print("Ссылка m3u8 на трек: ",i['m3u8_link'])
              print("____________________________________________________________________")
              #convert_to_mp3(i['m3u8_link'])
            main_funcs.create_files(info) # создание фалов данных
            print("файлы данных созданны")
          else:
            print("никого нет нашли")
          return info
        except:
          print("никого нет нашли")


#функция для обращения к классу VkUrez
  @staticmethod
  def poiskzp111(session,id=None,artist=None,title=None):  
      
      return VkUrez(session).get_iter(owner_id=id,track=title,artist=artist)

"""функция конвертации m3u8 ссылки в mp3 файл"""

import subprocess
def convert_to_mp3(link):
  print(subprocess.run(['ffmpeg', '-i', link, 'track.mp3']))

"""запуск программы"""

l=main_funcs.main_func()
l=l