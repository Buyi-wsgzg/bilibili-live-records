# !/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'Buyi'

'''
项目: B站直播回放下载

版本1: 无需登录或者cookie，直接即可下载直播回放，多线程，无弹幕版

'''

import requests, time, urllib.request, threading
import os, sys, multiprocessing
from moviepy.editor import *

import imageio
imageio.plugins.ffmpeg.download()

# 下载视频
'''
 urllib.urlretrieve 的回调函数：
def callbackfunc(blocknum, blocksize, totalsize):
    @blocknum:  已经下载的数据块
    @blocksize: 数据块的大小
    @totalsize: 远程文件的大小
'''


def Schedule_cmd(blocknum, blocksize, totalsize):
    speed = (blocknum * blocksize) / (time.time() - start_time)
    # speed_str = " Speed: %.2f" % speed
    speed_str = " Speed: %s" % format_size(speed)
    recv_size = blocknum * blocksize

    # 设置下载进度条
    f = sys.stdout
    pervent = recv_size / totalsize
    percent_str = "%.2f%%" % (pervent * 100)
    n = round(pervent * 50)
    s = ('#' * n).ljust(50, '-')
    f.write(percent_str.ljust(8, ' ') + '[' + s + ']' + speed_str)
    f.flush()
    # time.sleep(0.1)
    f.write('\r')

# 字节bytes转化K\M\G
def format_size(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.3fG" % (G)
        else:
            return "%.3fM" % (M)
    else:
        return "%.3fK" % (kb)


#  下载直播回放
def down_record(title, record, url, start_url):
    currentVideoPath = os.path.join(os.getcwd(), 'bilibili_record', record)  # 当前目录作为下载目录
    lock.acquire()
    try:
        if not os.path.exists(currentVideoPath):
            os.makedirs(currentVideoPath)
    finally:
        lock.release()
    opener = urllib.request.build_opener()
    # 请求头
    opener.addheaders = [
        ('Host', 'upos-hz-mirrorcosu.acgvideo.com'),  #注意修改host
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'),
        ('Accept', '*/*'),
        ('Accept-Language', 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en;q=0.7'),
        ('Accept-Encoding', 'identity'),
        ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
        ('Referer', start_url),  # 注意修改referer
        ('Origin', 'https://live.bilibili.com'),
        ('Connection', 'keep-alive'),
        ('Sec-Fetch-Mode', 'cors'),
        ('Sec-Fetch-Site', 'cross-site')
    ]
    urllib.request.install_opener(opener)
    # 创建文件夹存放下载的视频
    # if not os.path.exists(currentVideoPath):
    #     os.makedirs(currentVideoPath)

    urllib.request.urlretrieve(url=url, filename=os.path.join(currentVideoPath, r'{}'.format(title)),
                                       reporthook=Schedule_cmd)  # 写成mp4也行  title + '.flv'

# 合并视频
def combine_video(record_id, quality=0):
    video_path = os.path.join(os.getcwd(), 'bilibili_record', record_id)  # 下载目录
    if len(os.listdir(video_path)) >= 2:
        # 视频大于一段才要合并
        print('[下载完成,正在合并视频...]:' + record_id)
        # 定义一个数组
        L = []
        # 遍历所有文件, 视频按照时间戳排序
        for file in sorted(os.listdir(video_path), key=lambda x: time.mktime(time.strptime(x[x.index("-") + 1:x.rindex(".")], "%Y-%m-%d-%H-%M-%S"))):
            # 如果后缀名为 .mp4/.flv
            if os.path.splitext(file)[1] == '.flv':
                # 拼接成完整路径
                filePath = os.path.join(video_path, file)
                # 载入视频
                video = VideoFileClip(filePath)
                # 添加到数组
                L.append(video)
        # 拼接视频
        final_clip = concatenate_videoclips(L)
        # 生成目标视频文件
        cpu_nums = multiprocessing.cpu_count()  # 计算当前处理器核数
        if quality:
            final_clip.write_videofile(os.path.join(video_path, r'{}.avi'.format(record_id)), codec='png',
                                       threads=cpu_nums, fps=24, remove_temp=False, verbose=False)
        else:
            final_clip.write_videofile(os.path.join(video_path, r'{}.mp4'.format(record_id)), codec='mpeg4',
                                       threads=cpu_nums, fps=24, remove_temp=False, verbose=False)
        print('[视频合并完成]' + record_id)
    else:
        # 视频只有一段则直接打印下载完成
        print('[视频合并完成]:' + record_id)

if __name__ == '__main__':
    start_time = time.time()
    # 用户输入av号或者视频链接地址
    print('*' * 30 + 'B站直播回放下载小助手' + '*' * 30)
    start = input('请输入您要下载的B站直播回放链接地址:')
    try:
        quality = input('请输入您要下载视频的合并转码格式(mp4:0;avi:1)(选择0或者1,默认为0):')
        quality = int(quality)
    except ValueError:
        print("默认您选择的格式为MP4格式(默认选择0)")
        quality = 0
    # record_id = re.search(r'/rid=([a-zA-Z0-9]+)/*', start).group(1)
    record_id = start.split('/')[-1]
    # print(record_id)
    start_url = f"https://api.live.bilibili.com/xlive/web-room/v1/record/getLiveRecordUrl?rid={record_id}&platform=html5"

    # 获取直播回放的url
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    html = requests.get(start_url, headers=headers).json()
    # print(html)
    data = html['data']
    url_list = []
    for i, item in enumerate(data['list']):
        url_list.append(item['url'])
    # print(url_list)
    title_list = []
    threadpools = []
    lock = threading.Lock()
    for url in url_list:
        title = url.split('?')[0].split('/')[-1]
        title = str(title).replace(':', '-')
        title_list.append(title)
        start_time = time.time()
        # down_record(title, url, start_url)
        # thread pools
        th = threading.Thread(target=down_record, args=(title, record_id, url, start_url))
        threadpools.append(th)

    # thread start!
    for th in threadpools:
        th.start()
    # waiting all threads run over
    for th in threadpools:
        th.join()

    print(title_list)
    combine_video(record_id, quality)

    end_time = time.time()  # 结束时间
    print('下载总耗时%.2f秒,约%.2f分钟' % (end_time - start_time, int(end_time - start_time) / 60))
    # 如果是windows系统，下载完成后打开下载目录
    currentVideoPath = os.path.join(os.getcwd(), 'bilibili_record')  # 当前目录作为下载目录
    if (sys.platform.startswith('win')):
        os.startfile(currentVideoPath)

# 直播回放下载测试: https://live.bilibili.com/record/R1xx411c79q
# 下载总耗时409.65秒,约6.82分钟
