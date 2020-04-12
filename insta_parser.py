#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from pathlib import PurePath

import json
import random
import requests
import time

PAGES = {
    'bmw': 'https://www.instagram.com/bmw/',
    'infiniti_usa': 'https://www.instagram.com/infinitiusa/',
    'audi': 'https://www.instagram.com/audi/',
}

class InstaParser:
    def __init__(self):
        # Found here: https://stackoverflow.com/questions/49265339/instagram-a-1-url-not-working-anymore-problems-with-graphql-query-to-get-da/49341049#49341049
        #self.json_url = 'https://www.instagram.com/graphql/query/?query_hash=472f257a40c653c64c666ce877d59d2b&variables={"id":"43109246","first":12,"after":""}'
        pass

    def __sleep(self):
        pass
        #time.sleep(random.randint(0, 2)) # insure to not reach a time limit

    def __get_json_url(self, page_id, first, after):
        url = 'https://www.instagram.com/graphql/query/?query_hash=472f257a40c653c64c666ce877d59d2b&variables='
        variables = '{"id": "' + str(page_id) + '","first":' + str(first) + ',"after":"' + str(after) + '"}'
        return url + variables

    def __get_post_json_url(self, post):
        return 'https://www.instagram.com/p/' + post['shortcode'] + '/?__a=1'

    def __get_page_id(self, url):
        req_url = url + '?__a=1'
        r = requests.get(req_url)
        data = json.loads(r.text)
        self.__sleep()
        return data['logging_page_id'].split('_')[1]

    def __get_page_info(self, page_id, first = 120, after = ""):
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

    def parse(self, url, till_str='00:00:00 01.01.2020'):
        page_id = self.__get_page_id(url)
        end_cursor = ""
        posts = []
        break_loop = False
        till_datetime = datetime.strptime(till_str, '%H:%M:%S %d.%m.%Y')

        while True:
            if break_loop is True:
                break

            data = self.__get_page_info(page_id, after = end_cursor)
            end_cursor = data['page_info']['end_cursor']
            for p in data['edges']:
                post = p['node']
                #post_data = self.__get_post_info(post)
                #if post_data['taken_at_timestamp'] < till_datetime.timestamp():
                if post['taken_at_timestamp'] < till_datetime.timestamp():
                    break_loop = True
                    break
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
        posts = insta.parse(url)
        data[name] = posts
        print('Got {0} posts for {1}'.format(len(posts), name))
    insta.write_data('./data_json', data)

