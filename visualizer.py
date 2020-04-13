#!/usr/bin/env python3

from pathlib import PurePath

import json
import os

RESULT_DIR = PurePath(os.path.dirname(os.path.abspath(__file__)), 'data_json')

def transform_data(path):
    """transform result data from structure:
        `time -> comp_name -> posts_data` to `comp_name -> post_shortcode -> time -> data`
        Data contains the following fields:
        {
            'id',
            'description',
            'shortcode',
            'comments_count',
            'comments_disabled',
            'publish_timestamp',
            'dimensions' = {'width', 'height'},
            'content_url' # Link to image or video file
            'likes_count'
            'is_video'
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
                if shortcode not in res_data[comp]:
                    res_data[comp][shortcode] = {}
                post_data = {
                    'id': post['id'],
                    'description': post['edge_media_to_caption']['edges'][0]['node']['text'],
                    'shortcode': shortcode,
                    'comments_count': post['edge_media_to_comment']['count'],
                    'comments_disabled': post['comments_disabled'],
                    'publish_timestamp': post['taken_at_timestamp'],
                    'dimensions': post['dimensions'],
                    'content_url': post['display_url'],
                    'likes_count': post['edge_media_preview_like']['count'],
                    'is_video': post['is_video'],
                }
                res_data[comp][shortcode][dir_datetime] = post_data

    return res_data

if __name__ == '__main__':
    data = transform_data(RESULT_DIR)

    with open('output.json', 'w') as f:
        json.dump(data, f)


