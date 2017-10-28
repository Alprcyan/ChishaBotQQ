# -*- coding: utf-8 -*-

# https://github.com/pandolia/qqbot/

from random import randrange
from time import time
import json


class InfoData:
    hardcoded_list = ['肯德基', '麦当劳', '必胜客', '汉堡王']
    info_dictionary = {
        'default': {
            '晚餐': hardcoded_list
        }
    }
    initialized = False

    @staticmethod
    def file_init():
        try:
            with open('.qqbot-tmp/data.json') as fa:
                new_initial_dic = json.load(fa)
                try:
                    new_initial_dic['default']
                except KeyError as _:
                    new_initial_dic = InfoData.info_dictionary

                InfoData.info_dictionary = new_initial_dic
                fa.close()
        except FileNotFoundError as _:
            default_list = InfoData.info_dictionary['default']
            with open('.qqbot-tmp/data.json', 'w') as fb:
                json.dump(InfoData.info_dictionary, fb)
                fb.close()
        InfoData.initialized = True


class ListInfo:
    @staticmethod
    def get_default_list(contact=None) -> list:
        if not InfoData.initialized:
            InfoData.file_init()
        if contact is not None:
            try:
                val = InfoData.info_dictionary[contact]
            except KeyError as _:
                val = InfoData.hardcoded_list[:]
                InfoData.info_dictionary[contact] = val
            return val
        else:
            return InfoData.hardcoded_list[:]

    @staticmethod
    def save_list(contact, value_list):
        InfoData.info_dictionary[contact] = value_list
        with open('.qqbot-tmp/data.json', 'w') as fc:
            json.dump(InfoData.info_dictionary, fc)
            fc.close()


class PerContactDictionaryValue(object):
    def __init__(self, contact):
        self.contact = contact
        self.li = ListInfo.get_default_list(contact)
        self.isClosed = False
        self.last_choice = None
        self.last_index = -1
        self.enable_talk = False
        self.last_eat_what_time = 0.0
        self.count_since_last = 0
        self.count_alternative_rand = 0
        self.alternative_rand_li = self.li[:]
        self.last_reply_time = 0.0

    def add(self, name):
        self.alternative_rand_li.append(name)
        self.li.append(name)
        ListInfo.save_list(self.contact, self.li)

    def clean(self):
        self.alternative_rand_li.clean()
        self.li.clear()

    def size(self) -> int:
        return len(self.li)

    def delete(self, index):
        del self.li[index]
        ListInfo.save_list(self.contact, self.li)

    def rand(self) -> str:
        val = len(self.li)
        if val > 0:
            if val > 1:
                next_index = self.last_index
                while next_index == self.last_index:
                    next_index = randrange(val)
            else:
                next_index = 0
            self.last_index = next_index
            things = self.li[next_index]
            self.alternative_rand_li = self.li[:]
            del self.alternative_rand_li[next_index]
        else:
            things = None
        self.last_eat_what_time = time()
        self.count_since_last = 0
        return things

    def alternative_rand(self) -> str:
        self.last_index = -1
        val = len(self.alternative_rand_li)
        if val > 0:
            next_index = randrange(val)
            things = self.alternative_rand_li[next_index]
            del self.alternative_rand_li[next_index]
        else:
            things = None
        self.last_eat_what_time = time()
        self.count_since_last = 0
        return things

    def get_li(self) -> list:
        return self.li

    def closed(self) -> bool:
        return self.isClosed

    def close(self):
        self.isClosed = True

    def open(self):
        self.isClosed = False

    def set_talk(self):
        self.enable_talk = True

    def set_quiet(self):
        self.enable_talk = False

    def talk(self):
        return self.enable_talk

    def is_recent(self) -> bool:
        return time() - self.last_eat_what_time < 15 or self.count_since_last < 5

    def increase_counter(self):
        self.count_since_last += 1


my_dic = {}


def onQQMessage(bot, contact, member, content):
    a_str = str(contact.qq)

    try:
        val = my_dic[a_str]
    except KeyError as _:
        val = PerContactDictionaryValue(contact.qq)
        my_dic[a_str] = val
    assert isinstance(val, PerContactDictionaryValue)
    old_content = content
    content = str(content.strip().lower())

    val.increase_counter()

    if member is not None:
        a_str = str(member.qq)
    a_str = str(contact.qq + a_str)

    responded = False

    if time() - val.last_reply_time > 1 and (member is not None and not bot.isMe(contact, member)):
        if content == 'hello':
            bot.SendTo(contact, 'How are you')
            responded = True
        elif content == '--stop':
            bot.SendTo(contact, 'I\'m dead.')
            bot.Stop()
            responded = True
        elif not val.closed():
            if val.talk is False and content == 'enable talk':
                val.set_talk()
                # bot.SendTo(contact, '我开始说话咯')
                responded = True
            elif val.talk and content == 'disable talk':
                val.set_quiet()
                # bot.SendTo(contact, '我开始闭嘴咯')
                responded = True
            elif content == 'random':
                name = val.rand()
                if name is not None:
                    bot.SendTo(contact, 'My choice is: ' + name)
                else:
                    bot.SendTo(contact, 'No item found in the list.')
                responded = True
            elif content.startswith('add '):
                a_str = str(old_content[4:]).splitlines()
                for name in a_str:
                    val.add(name.strip())
                bot.SendTo(contact, 'Added: ' + ''.join(
                    ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(a_str)))
                responded = True
            elif content == 'get list' or content == 'getlist':
                length = len(val.get_li())
                bot.SendTo(contact, 'There are ' + str(length) + ' items in the list:' + ''.join(
                    ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(val.get_li())))
                responded = True
            elif content.startswith('delete '):
                numbers = content.split()[1:]
                names = []
                indexes = []
                for num in numbers:
                    indexes.append(int(num))
                indexes = reversed(sorted(indexes))
                for index in indexes:
                    index = int(index)
                    if index < -1:
                        continue
                    name = val.get_li()[index]
                    val.delete(index)
                    names.append(name)
                bot.SendTo(contact,
                           'Deleted: ' + ''.join(('\n\t' + str(e)) for e in reversed(names)))
                responded = True
            elif content == '[@me]  close':
                val.close()
                bot.SendTo(contact, 'Bye bye bye')
                responded = True
            elif content == '-help':
                a_str = 'Supported commands: \n\t' \
                        '\'create list\' \n\t' \
                        '\'get list\' \n\t' \
                        '\'add <item>\' \n\t' \
                        '\'delete <index0> [index1 ...]\' \n\t' \
                        '\'random\' \n\t' \
                        '\'今晚吃啥\''
                bot.SendTo(contact, a_str)
                responded = True
            elif (content.__contains__('今') or content.__contains__('明') or
                      content.__contains__('晚') or content.__contains__('中午') or
                      content.__contains__('夜宵') or content.__contains__('早')) and \
                    content.__contains__('吃') and \
                    (content.__contains__('什么') or content.__contains__('什麼') or content.__contains__('啥')):
                name = val.rand()
                if name is not None:
                    if (name != '鸡' and name != '吃鸡') or not content.__contains__('晚'):
                        bot.SendTo(contact, '吃' + name + '！')
                    else:
                        bot.SendTo(contact, '大吉大利，晚上吃鸡！')
                    val.last_choice = name
                else:
                    bot.SendTo(contact, '喝西北风吧')
                responded = True
            elif val.is_recent():
                if content.__contains__('吃不起') or (
                            content.__contains__('没') and content.__contains__('钱')) or \
                        content.startswith('不吃') or content.__contains__('没钱') or \
                        content.__contains__('换一个') or content.__contains__('不喜欢') or \
                        content.__contains__('不想吃'):
                    name = val.alternative_rand()
                    if name is not None:
                        bot.SendTo(contact, '那就吃' + name)
                    else:
                        bot.SendTo(contact, '这也不吃那也不吃，你吃屁去吧')
                    responded = True
        elif content == '[@me]  open':
            val.open()
            bot.SendTo(contact, 'I\'m back online!')
            responded = True

        if responded:
            val.last_reply_time = time()
