# -*- coding=utf-8 -*-
import argparse
import sys
import os
from config.CmdArgs import get_parsed_args


def parser_arguments(argv):
    """
    不应该在这里定义，先放在这里
    :param argv:
    :return:
    """
    # parser = argparse.ArgumentParser()
    # parser.add_argument("operate", type=str, help="r: 运行抢票程序, c: 过滤cdn, t: 测试邮箱和server酱，server酱需要打开开关")

    # return parser.parse_args(argv)
    return get_parsed_args()


if __name__ == '__main__':
    args = parser_arguments(sys.argv[1:])
    cdnFile = os.path.abspath(os.path.join(os.path.dirname(__file__), 'filter_cdn_list'))
    if not os.path.exists(cdnFile) or args.justFilterCDN:
        from agency.cdn_utils import filterCdn
        filterCdn()
    elif args.justTestMail:  # args.operate == "t":
        from config.emailConf import sendEmail
        from config.serverchanConf import sendServerChan
        sendEmail(u"订票小助手测试一下")
        sendServerChan("订票小助手测试一下")
    else:  # args.operate == "r":
        from init import select_ticket_info
        select_ticket_info.select().main()
