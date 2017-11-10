# -*- coding: utf-8 -*-

import json


class KeyKeys:
    DINNER = '晚餐'
    WORKING_LIST = 'working_dictionary'


def main():
    main_dic = {}
    with open('data.json') as f:
        sub_dic = json.load(f)
    for key in sub_dic:
        value = sub_dic[key]
        main_dic[key] = {}
        main_dic[key][KeyKeys.DINNER] = value
        main_dic[key][KeyKeys.WORKING_LIST] = KeyKeys.DINNER
    with open('data2.json', 'w') as f:
        json.dump(main_dic, f)


if __name__ == '__main__':
    main()
