# -*- coding: utf8 -*-

import os
import sys
import argparse
import time
import re
import datetime
import codecs
from pathlib import Path
import yaml

parsed_args = None
parsed_config = None

def print_tm(message):
    print(datetime.datetime.now().strftime('%F %T.%f'), " ", message)

def get_exe_in_path(exeName: str):
    folders = os.getenv('PATH').split(os.path.pathsep)
    for folder in folders:
        exePath = os.path.join(folder, exeName)
        if os.path.exists(exePath) and os.access(exePath, os.X_OK):
            return exePath
    return None


def get_cmd_args_text_lines(args):
    return re.sub(r'\s*,\s*(\w+)\s*=\s*', '\n\\1 = ', re.sub(r'^Namespace\((.+)\)', r'\1', str(args)))


def get_parsed_args():
    global parsed_args
    if parsed_args:
        return parsed_args
    defaultConfigFile = os.path.join(
        os.path.dirname(__file__), 'ticket_config.yaml')
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     usage='use "%(prog)s --help" for more information',
                                     description='Example like:' + os.linesep
                                     + '\t %(prog)s -i ' +
                                     defaultConfigFile + os.linesep
                                     + u'\t %(prog)s -i 大北到武汉高铁动车.yaml' +
                                     os.linesep
                                     + u'\t %(prog)s -i 大北到武汉高铁动车.yaml -u user -p passxxx' + os.linesep
                                     + u'\t %(prog)s -i 大北到武汉高铁动车.yaml -t "12:30:00" -d "2019-02-14" -r "Z38,Z202,Z162"' + os.linesep
                                     + u'\t %(prog)s -i 武汉到北京直达.yaml  -m 1 -t "12:30:00" -d "2019-02-14,2019-02-15" -r "Z38,Z202,Z162"' + os.linesep
                                     + u'\t %(prog)s -i 武汉到北京直达.yaml  -m 1 -t "12:30:00" -d "2019-02-14" -r "Z38,Z202,Z162"' + os.linesep
                                     + os.linesep + 'Usage see below:'
                                     )

    parser.add_argument('-i', '--input-file', dest='InputFile', type=str, default='',
                        required=True, help=f'Input file path. Such as {defaultConfigFile}')
    parser.add_argument('-u', '--user', dest='User', type=str,
                        required=False, default='', help='UserName')
    parser.add_argument('-p', '--pass', dest='Pass', type=str,
                        required=False, default='', help='Pass')
    parser.add_argument('-o', '--order-type', dest='order_type', type=int,
                        required=False, default=2, help=u'下单模式: 1 模拟网页自动捡漏下单（不稳定），2 模拟车次后面的购票按钮下单')
    parser.add_argument('-m', '--order-model', dest='order_model', type=str,
                        required=False, default='', help=u'刷新模式: 1 为预售，整点刷新, 2 是捡漏')
    parser.add_argument('-t', '--open-time', dest='open_time', type=str,
                        required=False, default='', help=u'预售放票时间如：13:30:00 , 如果是捡漏模式，可以忽略')
    parser.add_argument('-d', '--station-dates', dest='station_dates', type=str,
                        required=False, default='', help=u'车票日期组：如 "2019-02-14,2019-02-15"')
    parser.add_argument('-r', '--station-trains', dest='station_trains', type=str,
                        required=False, default='', help=u'火车组：如 "G586,G80, Z38,Z202,Z162"')
    parser.add_argument('-s', '--set-type', dest='set_type', type=str,
                        required=False, default='', help=u'席座类型：如 "软卧,二等座"')
    parser.add_argument('-v', '--sleep-intervals', dest='sleep_intervals', type=str,
                        required=False, default='3.5, 9.9', help=u'睡眠间隔：如 "0.5,3.0" 或 "3.0,5.0"')
    parser.add_argument('-j', '--just-show-args', dest='JustShowArgs',
                        default=False, action="store_true", help=u'显示配置后退出.')
    parser.add_argument('--RAIL_DEVICEID', default='', dest='RAIL_DEVICEID', type=str)
    parser.add_argument('--RAIL_EXPIRATION', default=0, dest='RAIL_EXPIRATION', type=int)
    parser.add_argument('--cdn', dest='justFilterCDN', default=False, action="store_true", help='过滤cdn, 刷新CDN文件')
    parser.add_argument('--test-mail-send', dest='justTestMail', default=False, action="store_true", help='测试邮箱和server, server需要打开开关')
    parser.add_argument('--ticket-type', dest='ticket_type', type=int, default=2,
                        help=u'刷票模式：1=刷票 2=候补+刷票')
    parser.add_argument('-c', '--use-cdn', dest='use_cdn', default=False, action="store_true",
                        help=u'是否开启cdn查询')
    parser.add_argument('--passengers', dest="passengers", type=str, default='', help=u'Passengers, separated by comma.')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    args = parser.parse_args()
    intervals = re.split(r'\s*,\s*', args.sleep_intervals)
    print(f'Default user = {args.User}, config file = {args.InputFile} , order-type = {args.order_type}, ticket-type = {args.ticket_type}'
     + f', order-model = {args.order_model}, use-cdn = {args.use_cdn}, open_time = {args.open_time} , sleep-intervals = {intervals}')

    envPass = os.getenv(args.User)
    if (len(args.Pass) < 1 and envPass):
        args.Pass = envPass
    parsed_args = args
    return args

def get_yaml_config():
    global parsed_config
    if parsed_config:
        return parsed_config
    # os.path.join(os.path.dirname(__file__) + '/ticket_config.yaml')
    cmdArgs = get_parsed_args()
    path = cmdArgs.InputFile
    try:  # 兼容2和3版本
        with open(path, encoding="utf-8") as f:
            s = yaml.load(f, Loader=yaml.SafeLoader)
    except Exception:
        with open(path) as f:
            s = yaml.load(f)
    cfg = s.decode() if isinstance(s, bytes) else s

    if (len(cmdArgs.User) > 1):
        cfg['set']['12306account'][0]['user'] = cmdArgs.User

    user = cfg['set']['12306account'][0]['user']
    if (len(cmdArgs.Pass) > 1):
        cfg['set']['12306account'][1]['pwd'] = cmdArgs.Pass

    cfg['order_type'] = cmdArgs.order_type

    if (len(cmdArgs.order_model) > 0):
        cfg['order_model'] = int(cmdArgs.order_model)

    if (len(cmdArgs.open_time) > 0):
        cfg['open_time'] = cmdArgs.open_time
        print('len(cmdArgs.open_time) = ' + str(len(cmdArgs.open_time)))

    if (len(cmdArgs.station_dates) > 0):
        cfg['set']['station_dates'] = re.split(r'\s*,\s*', cmdArgs.station_dates)

    if (len(cmdArgs.station_trains) > 0):
        cfg['set']['station_trains'] = re.split(r'\s*,\s*', cmdArgs.station_trains)

    if (len(cmdArgs.set_type) > 0):
        cfg['set']['set_type'] = re.split(r'\s*,\s*', cmdArgs.set_type)

    if (len(cfg['set']['12306account'][1]['pwd']) < 1):
        print(cfg)
        raise Exception('Password not set for ' + user + ' in config file ' +
                        cmdArgs.InputFile + ', nor set in environment variable of ' + user)

    if (cmdArgs.JustShowArgs):
        print(cfg)
        # sys.exit()
    parsed_config = cfg
    return cfg


if __name__ == '__main__':
    print(get_parsed_args())
