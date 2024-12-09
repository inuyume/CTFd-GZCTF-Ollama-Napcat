import time
from datetime import timezone, timedelta
import requests
from dateutil.parser import isoparse
import logging
from rich.logging import RichHandler
import certifi
from rich.status import Status
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# NapCatQQ API的基础URL
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
base_url = "" #Napcat url
def send_group_message(group_id, message):
    url = f"{base_url}/send_group_msg"
    params = {
        "group_id": group_id,
        "message": message,
        "access_token": ""
    }
    response = requests.get(url, params=params, verify=False)

    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message")
        print(response.status_code, response.text)

INTERVAL = 2  # 间隔时间
FORMAT = "%(message)s"
BOT_QQ = ''  # bot qq号
GROUP_NOTICE_ID = ''  # 发送的群号
API_URL = ''  # 比赛通知api
BANNER = ''
NOW_ID = 0
TEMPLATES = {
    'Normal': '【比赛公告】\n内容：%s\n时间：%s',
    'NewChallenge': '【新增题目】\n[%s]\n时间：%s',
    'NewHint': '【题目提示】\n[%s]有新提示，请注意查收\n时间：%s',
    'FirstBlood': '【一血播报】\n恭喜%s拿下[%s]一血\n时间：%s',
    'SecondBlood': ' 【二血播报】\n恭喜%s拿下[%s]二血\n时间：%s',
    'ThirdBlood': ' 【三血播报】\n恭喜%s拿下[%s]三血\n时间：%s'
}


def processTime(t):
    t_truncated = t[:26] + t[26:].split('+')[0]
    input_time = isoparse(t_truncated)
    input_time_utc = input_time.replace(tzinfo=timezone.utc)
    beijing_timezone = timezone(timedelta(hours=8))
    beijing_time = input_time_utc.astimezone(beijing_timezone)
    return beijing_time.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':

    a= 0
    logging.basicConfig(
        level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    log = logging.getLogger("rich")
    notices = requests.get(API_URL, verify=False).json()
    print(notices)
    notices = sorted(notices, key=lambda x: x['id'])
    NOW_ID = notices[-1]['id']
    #NOW_ID -= 1
    status = Status('Waiting for new notice')
    status.start()
    while True:
        try:
            print(requests.get(url='',  verify=False).text)
            notices = requests.get(url="",  verify=False).json()
        except KeyboardInterrupt:
            log.info('Exit bot')
            break
        except Exception:
            log.warning('Warning: request failed')
            continue
        notices = sorted(notices, key=lambda x: x['id'])
        for notice in notices:
            if notice['id'] > NOW_ID:
                message = TEMPLATES[notice['type']] % tuple(notice['values'] + [processTime(notice['time'])])
                log.info(f'sending to {GROUP_NOTICE_ID} message: \n{message}')
                send_group_message(GROUP_NOTICE_ID, message)
                NOW_ID = notice['id']
        try:
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            log.info('Exit bot')
            break
    status.stop()
