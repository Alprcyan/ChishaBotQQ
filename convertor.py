# -*- coding: utf-8 -*-

import json


def main():
    main_dic = {}
    with open('data.json') as f:
        sub_dic = json.load(f)
    for key in sub_dic:
        value = sub_dic[key]
        main_dic[key] = {}
        main_dic[key]['晚餐'] = value
    with open('data2.json', 'w') as f:
        json.dump(main_dic, f)


if __name__ == '__main__':
    main()
