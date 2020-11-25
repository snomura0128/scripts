import requests
import json
import os


def notify(message, *args):
    # 設定ファイルからtokenを取得する。
    json_file = open(os.path.dirname(__file__) + '/settings.json', 'r')
    json_data = json.load(json_file)
    # 設定
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + json_data["line_notify_token"]}
    # メッセージ
    payload = {'message': message}
    # 画像を含むか否か
    if len(args) == 0:
        requests.post(line_notify_api, data=payload, headers=headers)
    else:
        # 画像
        file = {"imageFile": open(args[0], "rb")}
        requests.post(line_notify_api, data=payload, headers=headers, files=file)
