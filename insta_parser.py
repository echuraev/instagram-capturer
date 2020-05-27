#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from pathlib import PurePath

import json
import os
import random
import requests
import time

PAGES = {
    'GenesisWorld': 'https://www.instagram.com/genesisworldwide/',
    'GenesisRussia': 'https://www.instagram.com/genesisrussia/',
    'BMWWorld': 'https://www.instagram.com/bmw/',
    'BMWRussia': 'https://www.instagram.com/bmwru/',
    'MercedesWorld': 'https://www.instagram.com/mercedesbenz/',
    'MercedesRussia': 'https://www.instagram.com/mbrussia/',
    'AudiWorld': 'https://www.instagram.com/audiofficial/',
    'AudiRussia': 'https://www.instagram.com/audirussia/',
    'LexusWorld': 'https://www.instagram.com/lexususa/',
    'LexusRussia': 'https://www.instagram.com/lexusrussia/',
    'InfinitiWorld': 'https://www.instagram.com/infiniti/',
    'InfinitiRussia': 'https://www.instagram.com/infiniti_russia/',
    'PorscheWorld': 'https://www.instagram.com/porsche/',
    'PorscheRussia': 'https://www.instagram.com/porsche_russia/',
    'CadillacWorld': 'https://www.instagram.com/cadillac/',
    'CadillacRussia': 'https://www.instagram.com/cadillacrussia/',
    'JaguarWorld': 'https://www.instagram.com/jaguar/',
    'JaguarRussia': 'https://www.instagram.com/jaguarrussia/',
    'VolvoWorld': 'https://www.instagram.com/volvocars/',
    'VolvoRussia': 'https://www.instagram.com/volvocarsrus/',
}
PARSE_COMMENTS = True
REPEAT_FAILS = True
RESULT_DIR = PurePath(os.path.dirname(os.path.abspath(__file__)), 'data_json')

class InstaParser:
    def __init__(self):
        pass

    def __sleep(self):
        time.sleep(random.randint(1, 2)) # insure to not reach a time limit

    def __get_json_url(self, page_id, first, after):
        url = 'https://www.instagram.com/graphql/query/?query_hash=472f257a40c653c64c666ce877d59d2b&variables='
        variables = '{"id": "' + str(page_id) + '","first":' + str(first) + ',"after":"' + str(after) + '"}'
        return url + variables

    def __get_json_comments_url(self, shortcode, first, after):
        url = 'https://www.instagram.com/graphql/query/?query_hash=33ba35852cb50da46f5b5e889df7d159&variables='
        variables = '{"shortcode": "' + str(shortcode) + '","first":' + str(first) + ',"after":"' + str(after) + '"}'
        return url + variables

    def __get_post_json_url(self, post):
        return 'https://www.instagram.com/p/' + post['shortcode'] + '/?__a=1'

    def __get_page_id(self, url):
        req_url = url + '?__a=1'
        r = requests.get(req_url)
        data = json.loads(r.text)
        self.__sleep()
        return data['logging_page_id'].split('_')[1]

    def __get_page_info(self, page_id, first = 100, after = ""):
        r = requests.get(self.__get_json_url(page_id, first, after))
        data = json.loads(r.text)
        if data["status"] != "ok":
            raise Exception('Error! Cannot get information for page! page_id = {0}, first = {1}, after = {2}'.format(page_id, first, after))
        self.__sleep()
        return data["data"]["user"]["edge_owner_to_timeline_media"]

    def __get_post_info(self, post):
        r = requests.get(self.__get_post_json_url(post))
        data = json.loads(r.text)
        self.__sleep()
        return data['graphql']['shortcode_media']

    def __get_comments(self, shortcode, first = 100, after = ""):
        r = requests.get(self.__get_json_comments_url(shortcode, first, after))
        data = json.loads(r.text)
        if data["status"] != "ok":
            raise Exception('Error! Cannot get information for page! shortcode = {0}, first = {1}, after = {2}'.format(shortcode, first, after))
        self.__sleep()
        return data["data"]["shortcode_media"]["edge_media_to_comment"]

    def __get_all_comments(self, shortcode):
        comments = []
        end_cursor = ""
        has_next_page = True

        while has_next_page is True:
            while True:
                try:
                    data = self.__get_comments(shortcode, after = end_cursor)
                    break
                except:
                    print("Repeat fails __get_comments")
                    if REPEAT_FAILS is False:
                        break;
                    time.sleep(random.randint(180, 240))
            has_next_page = data['page_info']['has_next_page']
            end_cursor = data['page_info']['end_cursor']
            for c in data['edges']:
                comments.append(c['node'])

        return comments

    def parse(self, url, till_str='00:00:00 01.01.2020'):
        page_id = self.__get_page_id(url)
        end_cursor = ""
        posts = []
        break_loop = False
        till_datetime = datetime.strptime(till_str, '%H:%M:%S %d.%m.%Y')
        i = 0

        while True:
            if break_loop is True:
                break

            while True:
                try:
                    data = self.__get_page_info(page_id, after = end_cursor)
                    break
                except:
                    if REPEAT_FAILS is False:
                        break
                    print("Repeat fails __get_page_info")
                    time.sleep(random.randint(180, 240))
            end_cursor = data['page_info']['end_cursor']
            if data['page_info']['has_next_page'] is False:
                break_loop = True

            for p in data['edges']:
                print('Start post: {0}'.format(i))
                post = p['node']
                #post_data = self.__get_post_info(post)
                #if post_data['taken_at_timestamp'] < till_datetime.timestamp():
                if post['taken_at_timestamp'] < till_datetime.timestamp():
                    break_loop = True
                    break
                if PARSE_COMMENTS is True:
                    post['all_comments'] = self.__get_all_comments(post['shortcode'])
                print('Done post: {0}'.format(i))
                i += 1
                posts.append(post)
                #posts.append(post_data)

        return posts

    def write_data(self, path, data):
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        pp = PurePath(path, now)
        Path(pp).mkdir(parents=True, exist_ok=True)
        out_file = PurePath(pp, 'data.json')
        with open(out_file, 'w') as f:
            json.dump(data, f)

if __name__ == '__main__':
    insta = InstaParser()
    data = {}
    for name, url in PAGES.items():
        print('Start parsing {0}'.format(name))
        posts = insta.parse(url)
        data[name] = posts
        print('Got {0} posts for {1}'.format(len(posts), name))
    insta.write_data(RESULT_DIR, data)

