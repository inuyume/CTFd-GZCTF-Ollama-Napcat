import threading

from flask import Flask, request, jsonify
import requests
import pprint
import json
from bs4 import BeautifulSoup
import time
from datetime import timezone, timedelta
from dateutil.parser import isoparse
import logging
from rich.logging import RichHandler
from rich.status import Status

app = Flask(__name__)

# NapCatQQ API的基础URL
base_url = "http://ip:3000"
# ollama
llama_url = "http://ip:11434/api/chat"
header = {
    'Content-Type': 'application/json'
}

# 用于存储对话上下文的列表
conversation_history = []


def ollama(input_data):
    # 将用户输入添加到对话历史
    conversation_history.append({
        "role": "user",
        "content": input_data
    })

    data = {
        "model": "", # 模型名称
        "messages": conversation_history,
        "stream": True
    }

    reply_content = ""
    try:
        with requests.post(url=llama_url, data=json.dumps(data), headers=header, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    try:
                        text = json.loads(line.decode('utf-8'))
                        if "message" in text and "content" in text['message']:
                            reply_content += text['message']['content']

                        # 如果已经收到完整的回复内容，跳出循环
                        if text.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue

            # 将模型回复添加到对话历史中
            conversation_history.append({
                "role": "assistant",
                "content": reply_content,
            })

            return reply_content

    except TypeError as error:
        return str(error)

#爬取hello CTF 的国内赛事名单
def get_domestic_events_as_string(url):
    # 获取网页内容
    res = requests.get(url)

    html_content = res.text

    # 解析网页内容
    soup = BeautifulSoup(html_content, 'html.parser')

    # 定位到国内赛事的部分
    domestic_events_section = soup.find('h2', id='_2')
    next_h2 = domestic_events_section.find_next('h2', id='_3')  # 找到国际赛事部分

    # 提取国内赛事部分的内容
    domestic_events_content = []
    for sibling in domestic_events_section.find_next_siblings():
        if sibling == next_h2:
            break
        domestic_events_content.append(sibling)

    # 解析每个<details>标签内容并生成格式化字符串
    events_string = ""
    for details in domestic_events_content:
        if details.name == 'details' and 'quote' in details.get('class', []):
            summary = details.find('summary').text.strip()
            match_type = details.find('strong', string='比赛类型').next_sibling.strip()
            registration_time = details.find('strong', string='报名时间').next_sibling.strip()
            events_string += f"Summary: {summary}\n"
            events_string += f"比赛类型: {match_type}\n"
            events_string += f"报名时间: {registration_time}\n"
            events_string += "-" * 50 + "\n"

    return events_string

# 对接CTF BI数据大屏
血量url = ""
签到url = ""


def bi(url):
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
        'Content-type': 'application/json',
        'Referer': 'http://bi.campus.nynusec.com/',
        'Host': 'bi.campus.nynusec.com',
        'Origin': 'http://bi.campus.nynusec.com',
        'Accept': 'application/json, text/plain, */*',
        'Content-Length': "115",
        "LINK-PWD-TOKEN": "" #BI的token
    }
    data = {
        "filter": [],
        "linkageFilters": [],
        "drill": [],
        "resultCount": 1000,
        "resultMode": "all",
        "queryFrom": "panel",
        "cache": False
    }

    res = requests.post(url=url,
                        headers=header,
                        data=json.dumps(data))
    xie = res.json()['data']['data']['data']
    list_ = []
    for k in range(len(res.json()['data']['data']['tableRow'])):
        list_z = []
        for i, j in res.json()['data']['data']['tableRow'][k].items():
            # print(j, end=" ")
            list_z.append(j)
        list_.append(list_z)
    # pprint.pprint(签到list)
    return list_


def 血量(data):
    result = ""
    for i in data:
        time = i[0]
        parts = i[1].split(' ')
        nickname = parts[1]
        achievement = ' '.join(parts[3:])

        result += f"时间: {time}\n"
        result += f"昵称: {nickname}\n"
        result += f"题目: {achievement}\n"
        result += "-" * 40 + "\n"
    return result


def 签到状况(data):
    # 使用字典存储每个人的最新记录
    attendance_dict = {}

    for i in data:
        name = i[0]
        action = i[1]
        time = i[2]

        # 如果当前记录是签退，或者字典中还没有该人的记录，则更新字典
        if action == '签退' or name not in attendance_dict:
            attendance_dict[name] = (action, time)

    # 格式化输出
    result = ""
    for name, (action, time) in attendance_dict.items():
        result += f"昵称: {name}\n"
        result += f"状态: {action}\n"
        result += f"时间: {time}\n"
        result += "-" * 40 + "\n"

    return result


def send_group_message(group_id, message):
    url = f"{base_url}/send_group_msg"
    params = {
        "group_id": group_id,
        "message": message,
        "access_token": ""
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message")
        print(response.status_code, response.text)


def send_group_image():
    pass




@app.route('/', methods=['POST'])
def handle_request():
    # 打印接收到的请求
    # print("Headers:", request.headers)
    # pprint.pprint(request.json)
    # pprint.pprint("Body:", request.get_data(as_text=True))
    # pprint.pprint(request.json['message'])
    # pprint.pprint(request.json['message'][0]['data']['qq'])
    bot_id = ""#机器人qq号
    group_id_arr = [] #群聊qq号
    try:
        # pprint.pprint(request.json)
        # pprint.pprint(request.json['raw_info'][2]['type'])
        group_id = request.json['group_id']
        # print(group_id)
        if group_id in group_id_arr:
            if 'message' in request.json:
                print("a")
                pprint.pprint(request.json)
                # print(request.json['message'][0]['data']['qq'])
                # print(request.json['message'][0]['type'])
                if '比赛平台' in request.json['raw_message']:
                    print("aaaaq")
                    send_group_message(group_id, "")
                    pprint.pprint(request.json['message'])
                elif request.json['message'][0]['data']['qq'] == bot_id and request.json['message'][0]['type'] == 'at':
                    message_text = request.json['message'][1]['data']['text']
                    # print(message_text)
                    if 'test' == message_text:
                        send_group_message(group_id, "hello world")
                    elif "echo " in message_text and "[" not in message_text:
                        send_group_message(group_id, message_text[message_text.index("echo ") + 5:])
                    elif ' 国内赛事' == message_text:
                        url = "https://hello-ctf.com/Event/Upcoming_events/"
                        events_str = get_domestic_events_as_string(url)
                        print(events_str)
                        send_group_message(group_id, events_str)
                    elif ' 血量' == message_text and request.json["group_id"] == :
                        send_group_message(group_id, 血量(bi(血量url)))
                    elif ' 签到状况' == message_text and request.json["group_id"] == :
                        send_group_message(group_id, 签到状况(bi(签到url)))
                    else:
                        if request.json["group_id"] == 787343585 or request.json["user_id"] == : #用户qq号，只对指定用户有反应
                            res = ollama(message_text)
                            # print(res)
                            send_group_message(group_id, res)
                        else:
                            pass
            else:
                pass
        else:
            pass
    except Exception as error:
        print(error)
    # 拍一拍
    try:
        if request.json['group_id'] == :
            # pprint.pprint(request.json['raw_info'][3]['uid'])
            # pprint.pprint(request.json['raw_info'][2]['type'])
            if request.json['raw_info'][2]['type'] == 'nor' and request.json['raw_info'][3][
                'uid'] == '':  # uid 每个账号都是固定的
                send_group_message(787343585, "ご主人様、何かお手伝いできることはありますか?")
            else:
                pass
        elif request.json['group_id'] == :#特定群号
            if request.json['raw_info'][2]['type'] == 'nor' and request.json['raw_info'][3][
                'uid'] == '':  # uid 每个账号都是固定的
                send_group_message(123, "tql") #123为发送消息的群号
            else:
                pass
        else:
            pass

    except Exception as e:
        print(e)

    # 你可以在这里处理请求，调用NapCatQQ API，或执行其他操作

    return "Request received", 200


@app.route('/ctfd', methods=['POST'])
def ctfd_request():
    text = request.get_data(as_text=True)
    # print(f"text={text}")
    print(text)
    data = json.loads(text)

    # 提取信息
    group_id_send = data['group_id']
    message_send = data['message']
    # print(group_id_send)
    # print(message_send)
    try:
        send_group_message(, message_send)  # 2群
        # send_group_message(, message_send) #1群
        # print(f"Sending message to group {group_id_send}: {message_send}")
        # print("Message sent successfully")
        return jsonify({'status': 'success', 'message': 'Message sent successfully!'}), 200
    except Exception as e:
        print(e)
        # print("Message sent successfully")


if __name__ == '__main__':
    # 创建线程
    thread1 = threading.Thread(target=app.run(host='0.0.0.0', port=5555), daemon=True)
    # 启动线程
    thread1.start()
    # 主线程等待子线程完成
    thread1.join()
    # app.run(host='0.0.0.0', port=5555)
