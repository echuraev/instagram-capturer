#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from pathlib import PurePath

import json
import os
import xlsxwriter

RESULT_DIR = PurePath(os.path.dirname(os.path.abspath(__file__)), 'data_json')
TIME_LIST = []
POST_ORDER = {}

def transform_data(path):
    """transform result data from structure:
        `time -> comp_name -> posts_data` to `comp_name -> post_shortcode -> data`
        Data contains the following fields:
        {
            'id',
            'description',
            'shortcode',
            'comments_disabled',
            'publish_timestamp',
            'dimensions' = {'width', 'height'},
            'content_url' # Link to image or video file
            'is_video',
            'collect_time' = [{'time', 'comments_count', 'likes_count'}, ...]
        }
    """
    res_data = {}
    for dir_datetime in os.listdir(path):
        json_file = str(PurePath(path, dir_datetime, 'data.json'))
        TIME_LIST.append(dir_datetime)
        with open(json_file, 'r') as f:
            data = json.load(f)
        for comp, posts in data.items():
            if comp not in res_data:
                res_data[comp] = {}
            if comp not in POST_ORDER:
                POST_ORDER[comp] = []
            for post in posts:
                if post['taken_at_timestamp'] not in POST_ORDER[comp]:
                    POST_ORDER[comp].append(post['taken_at_timestamp'])
                shortcode = post['shortcode']
                collect_time = {
                        'time': dir_datetime,
                        'comments_count': post['edge_media_to_comment']['count'],
                        'likes_count': post['edge_media_preview_like']['count'],
                    }
                if shortcode not in res_data[comp]:
                    post_data = {
                        'id': post['id'],
                        'description': post['edge_media_to_caption']['edges'][0]['node']['text'],
                        'shortcode': shortcode,
                        'comments_disabled': post['comments_disabled'],
                        'publish_timestamp': post['taken_at_timestamp'],
                        'dimensions': post['dimensions'],
                        'content_url': post['display_url'],
                        'is_video': post['is_video'],
                        'collect_time': [collect_time],
                    }
                    res_data[comp][shortcode] = post_data
                else:
                    if collect_time not in res_data[comp][shortcode]['collect_time']:
                        res_data[comp][shortcode]['collect_time'].append(collect_time)

    TIME_LIST.sort()
    return res_data

def create_workbook(dir_name, prefix, data):
    Path(dir_name).mkdir(parents=True, exist_ok=True)
    for comp_name in data:
        name = prefix + '_' + comp_name + '.xlsx'
        workbook = xlsxwriter.Workbook(PurePath(dir_name, name))
        ws = workbook.add_worksheet()

        bold = workbook.add_format({'bold': True})
        data_rows = [
            'Short code:',
            'Type:',
            'Publish date:',
            'Publish time:',
            'Url:',
            'Description:',
            'Dimension (WxH):',
            'Comments disabled:',
            'Counter type:',
        ]
        for i in range(len(data_rows)):
            ws.write(i, 0, data_rows[i], bold)

        col = 1
        order = POST_ORDER[comp_name]
        order.sort()
        for shortcode in data[comp_name]:
            print(shortcode)
            pdata = data[comp_name][shortcode]
            col_ind = order.index(pdata['publish_timestamp']) * 2 + col
            ws.merge_range(0, col_ind, 0, col_ind + 1, shortcode)
            ws.merge_range(1, col_ind, 1, col_ind + 1, 'photo' if pdata['is_video'] is False else 'video')
            ws.merge_range(2, col_ind, 2, col_ind + 1, datetime.fromtimestamp(pdata['publish_timestamp']).strftime('%d.%m.%Y'))
            ws.merge_range(3, col_ind, 3, col_ind + 1, datetime.fromtimestamp(pdata['publish_timestamp']).strftime('%H:%M:%S'))
            ws.merge_range(4, col_ind, 4, col_ind + 1, pdata['content_url'])
            ws.merge_range(5, col_ind, 5, col_ind + 1, pdata['description'])
            ws.merge_range(6, col_ind, 6, col_ind + 1, str(pdata['dimensions']['width']) + 'x' + str(pdata['dimensions']['height']))
            ws.merge_range(7, col_ind, 7, col_ind + 1, 'False' if pdata['comments_disabled'] is False else 'True')
            ws.write(8, col_ind, 'Likes', bold)
            ws.write(8, col_ind + 1, 'Comments', bold)

            row = len(data_rows)
            for time in pdata['collect_time']:
                print(time)
                ind = TIME_LIST.index(time['time'])
                t = datetime.strptime(time['time'], '%Y%m%d_%H%M%S').strftime('%d.%m.%Y %H:%M:%S')
                ws.write(row + ind, 0, t)
                ws.write(row + ind, col_ind, time['likes_count'])
                ws.write(row + ind, col_ind + 1, time['comments_count'])

        workbook.close()

if __name__ == '__main__':
    data = transform_data(RESULT_DIR)
    create_workbook('results', 'results', data)

