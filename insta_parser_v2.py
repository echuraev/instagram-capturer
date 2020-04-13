#!/usr/bin/env python3

from instagram_private_api import Client, ClientCompatPatch

def read_credentials(path = ".credentials"):
    with open(path, 'r', encoding='utf-8') as f:
        login = f.readline().strip()
        password = f.readline().strip()
        return login, password

if __name__ == '__main__':
    login, password = read_credentials()
    print(login, password)
    api = Client(login, password)
    results = api.feed_timeline()
    items = [item for item in results.get('feed_items', [])
             if item.get('media_or_ad')]
    for item in items:
        # Manually patch the entity to match the public api as closely as possible, optional
        # To automatically patch entities, initialise the Client with auto_patch=True
        ClientCompatPatch.media(item['media_or_ad'])
        print(item['media_or_ad']['code'])
