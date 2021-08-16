"""
Dress room module
"""
import json
import re
import time
import traceback
import urllib.parse
from typing import Optional

import requests
from vk_api import VkApi
from vk_api.longpoll import Event, VkLongPoll, VkEventType


class ActiveUsersAPI:
    """ Trader through Saymon say """

    API_URL = "https://vip3.activeusers.ru/app.php?act=%s&auth_key=%s&group_id=182985865&api_id=7055214"
    ACT_TYPE_ITEM = "item&id=%s"

    def __init__(self, bagid: str):
        self.bagid = bagid

    def compile(self, pattern: str):
        """ Compile the regular expression """
        return re.compile(pattern, re.IGNORECASE | re.UNICODE | re.DOTALL | re.MULTILINE)

    def buildQuery(self, data):
        """ Build PHP Array from JS Array """
        m_parents = list()
        m_pairs = dict()

        def renderKey(parents: list):
            """ Key decoration """
            depth, out_str = 0, ''
            for x in parents:
                s = "[%s]" if depth > 0 or isinstance(x, int) else "%s"
                out_str += s % str(x)
                depth += 1
            return out_str

        def r_urlencode(rawurl: str):
            """ Encode URL """
            if isinstance(rawurl, list) or isinstance(rawurl, tuple):
                for tmp_index in range(len(rawurl)):
                    m_parents.append(tmp_index)
                    r_urlencode(rawurl[tmp_index])
                    m_parents.pop()
            elif isinstance(rawurl, dict):
                for tmp_key, tmp_value in rawurl.items():
                    m_parents.append(tmp_key)
                    r_urlencode(tmp_value)
                    m_parents.pop()
            else:
                m_pairs[renderKey(m_parents)] = str(rawurl)
            return m_pairs

        return urllib.parse.urlencode(r_urlencode(data))

    def buildHeaders(self, length: int, referer: str):
        """ Request header """
        tmp_params = {
            'Host': 'vip3.activeusers.ru',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="88", "Chromium";v="88", ";Not A Brand";v="98"',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'DNT': '1',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/522.41 (KHTML, like Gecko) Chrome/89.0.1389.10 Safari/522.06',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://vip3.activeusers.ru',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': referer,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        if length > 0:
            tmp_params['Content-Length'] = str(length)
        # Completed array
        return tmp_params

    def useitem(self, itemid: int, action: int):
        """ Translate item params """
        tmp_referer = self.API_URL % (self.ACT_TYPE_ITEM % itemid, self.bagid)
        tmp_data = {
            "id": itemid,
            "m": action
        }
        tmp_url = self.API_URL % ("a_sell_item", self.bagid)
        # Отправим
        tmp_response = requests.post(tmp_url, tmp_data, headers=self.buildHeaders(7 + len(str(itemid)), tmp_referer))
        if (not tmp_response.ok) or (json.loads(tmp_response.text)["result"] == 1):
            print("  Использован %s" % itemid)
            return True
        else:
            print("  Не использован %s - %s" % (itemid, tmp_response.reason))
            return False


class DressRoom:
    """ Движок переодевалки """

    def __init__(self, token: str, bagid: str, sets: dict):
        """ Конструктор """
        self.session = VkApi(token=token)
        self.longpoll = VkLongPoll(self.session)
        self.activusers = ActiveUsersAPI(bagid)
        self.event: Optional[Event] = None
        self.reg_set = self.activusers.compile(r"^/сет(\d+)")
        self.sets = sets
        self.run()

    def run(self):
        """ Запуск жизненного цикла """
        print("> ready")
        while True:
            try:
                for self.event in self.longpoll.check():
                    if self.event.type == VkEventType.MESSAGE_NEW:
                        self.check()
            except Exception as e:
                print("Read poll failed %s %s" % (e, traceback.format_exc().replace("\n", " ")))
                time.sleep(3)

    def check(self):
        """ Проверка текущего сообщения торговца """
        tmp_match = self.reg_set.match(self.event.message)
        if tmp_match:
            self.dress(int(tmp_match[1]))

    def dress(self, setnum: int):
        """ Использование предметов сета """
        print(" accepted set #%d" % setnum)
        for tmp_item in self.sets[setnum]:
            self.activusers.useitem(tmp_item[0], tmp_item[1])
            time.sleep(1)
        print("> done")


DressRoom("TOKEN",
          "BAG",
          {
              0: [
                  # Одеть
                  [14242, 0],
                  [13583, 0],
              ],
              1: [
                  # Снять
                  [14243, 0],
                  [13553, 1],
              ]
          })
