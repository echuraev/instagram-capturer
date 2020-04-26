#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from pathlib import PurePath

import json
import os
import xlsxwriter

RESULT_DIR = PurePath(os.path.dirname(os.path.abspath(__file__)), 'data_json')

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
        with open(json_file, 'r') as f:
            data = json.load(f)
        for comp, posts in data.items():
            if comp not in res_data:
                res_data[comp] = {}
            for post in posts:
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
            'Url:',
            'Description:',
            'Dimension (WxH):',
            'Comments disabled:',
            'Counter type:',
        ]
        for i in range(len(data_rows)):
            ws.write(i, 0, data_rows[i], bold)

        col = 1
        for shortcode in data[comp_name]:
            print(shortcode)
            pdata = data[comp_name][shortcode]
            ws.merge_range(0, col, 0, col + 1, shortcode)
            ws.merge_range(1, col, 1, col + 1, 'photo' if pdata['is_video'] is False else 'video')
            ws.merge_range(2, col, 2, col + 1, datetime.fromtimestamp(pdata['publish_timestamp']).strftime('%d.%m.%Y %H:%M:%S'))
            ws.merge_range(3, col, 3, col + 1, pdata['content_url'])
            ws.merge_range(4, col, 4, col + 1, pdata['description'])
            ws.merge_range(5, col, 5, col + 1, str(pdata['dimensions']['width']) + 'x' + str(pdata['dimensions']['height']))
            ws.merge_range(6, col, 6, col + 1, 'False' if pdata['comments_disabled'] is False else 'True')
            ws.write(7, col, 'Likes', bold)
            ws.write(7, col + 1, 'Comments', bold)

            row = len(data_rows)
            for time in pdata['collect_time']:
                print(time)
                t = datetime.strptime(time['time'], '%Y%m%d_%H%M%S').strftime('%d.%m.%Y %H:%M:%S')
                ws.write(row, 0, t)
                ws.write(row, col, time['likes_count'])
                ws.write(row, col + 1, time['comments_count'])
                row += 1

            col += 2

        workbook.close()

if __name__ == '__main__':
    data = transform_data(RESULT_DIR)
    create_workbook('results', 'results', data)

