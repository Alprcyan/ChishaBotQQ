# -*- coding: utf-8 -*-

# https://github.com/pandolia/qqbot/

from random import randrange
from time import time
import json
from re import search


class KeyKeys:
    DINNER = '晚餐'
    WORKING_LIST = 'working_dictionary'


class InfoData:
    hardcoded_dic = {
        KeyKeys.DINNER: ['肯德基', '麦当劳', '必胜客', '汉堡王'],
        KeyKeys.WORKING_LIST: '晚餐'
    }
    info_hub_dictionary = {
        'default': hardcoded_dic
    }
    initialized = False

    @staticmethod
    def file_init() -> None:
        try:
            with open('.qqbot-tmp/data.json') as fa:
                new_initial_dic = json.load(fa)
                try:
                    new_initial_dic['default']
                except KeyError:
                    new_initial_dic = InfoData.info_hub_dictionary
                InfoData.info_hub_dictionary = new_initial_dic
        except FileNotFoundError:
            with open('.qqbot-tmp/data.json', 'w') as fb:
                json.dump(InfoData.info_hub_dictionary, fb)
        InfoData.initialized = True


class ItemLists:
    @staticmethod
    def get_dict(contact=None) -> dict:
        if not InfoData.initialized:
            InfoData.file_init()
        if contact is not None:
            try:
                val = InfoData.info_hub_dictionary[contact]
            except KeyError:
                val = InfoData.hardcoded_dic.copy()
                InfoData.info_hub_dictionary[contact] = val
        else:
            val = InfoData.hardcoded_dic.copy()
        return val

    @staticmethod
    def save_dic(contact, contact_dic) -> None:
        InfoData.info_hub_dictionary[contact] = contact_dic
        with open('.qqbot-tmp/data.json', 'w') as fc:
            json.dump(InfoData.info_hub_dictionary, fc)
            fc.close()


class PerContactDictionaryValue(object):
    def __init__(self, contact):
        self.contact = contact
        self.dict = ItemLists.get_dict(contact)
        self.working_list = str(self.dict[KeyKeys.WORKING_LIST])
        self.closed = False
        self.last_choice = None
        self.last_index = -1
        self.enable_talk = False
        self.last_rand_get_time = 0.0
        self.count_since_last = 0
        self.count_alternative_rand = 0
        self.alternative_rand_li = self.dict[self.working_list][:]
        self.last_reply_time = 0.0

    def add_item(self, name) -> None:
        self.alternative_rand_li.append(name)
        try:
            self.dict[self.working_list]
        except KeyError:
            self.dict[self.working_list] = []
        self.dict[self.working_list].append(name)
        ItemLists.save_dic(self.contact, self.dict)

    def clean(self) -> None:
        self.alternative_rand_li.clean()
        self.dict = {KeyKeys.WORKING_LIST: ''}

    def dict_size(self) -> int:
        return len(self.dict) - 1

    def current_list_size(self) -> int:
        return len(self.dict[self.working_list])

    def delete_items(self, args) -> list:
        deleted = []
        if isinstance(args, list):
            if isinstance(args[0], int):
                args = reversed(sorted(args))
                for index in args:
                    name = self.dict[self.working_list][index]
                    del self.dict[self.working_list][index]
                    deleted.append(name)
                    for i, e in enumerate(self.alternative_rand_li):
                        if e == name:
                            del self.alternative_rand_li[i]
            elif isinstance(args[0], str):
                for name in args:
                    for i, e in enumerate(self.dict[self.working_list]):
                        if e == name:
                            del self.dict[self.working_list][i]
                            deleted.append(name)
                    for i, e in enumerate(self.alternative_rand_li):
                        if e == name:
                            del self.alternative_rand_li[i]
        else:
            deleted = self.delete_items([args])
        ItemLists.save_dic(self.contact, self.dict)
        return deleted

    def get_entries(self) -> list:
        li = []
        for key in self.dict:
            if key != KeyKeys.WORKING_LIST:
                li.append(key)
        return li

    def delete_lists(self, names) -> list:
        deleted = []
        if isinstance(names, list):
            for name in names:
                try:
                    if name != KeyKeys.WORKING_LIST and name != self.working_list:
                        deleted.append(self.dict.pop(name))
                except KeyError:
                    pass
        else:
            deleted = self.delete_lists([names])
        ItemLists.save_dic(self.contact, self.dict)
        return deleted

    def rand_get(self) -> str:
        val = self.current_list_size()
        if val > 0:
            if val > 1:
                next_index = self.last_index
                while next_index == self.last_index:
                    next_index = randrange(val)
            else:
                next_index = 0
            self.last_index = next_index
            things = self.dict[self.working_list][next_index]
            self.alternative_rand_li = self.dict[self.working_list][:]
            del self.alternative_rand_li[next_index]
        else:
            things = None
        self.last_rand_get_time = time()
        self.count_since_last = 0
        return things

    def alternative_rand(self) -> str:
        self.last_index = -1
        val = len(self.alternative_rand_li)
        if val > 0:
            next_index = randrange(val)
            things = self.alternative_rand_li[next_index][:]
            del self.alternative_rand_li[next_index]
        else:
            things = None
        self.last_rand_get_time = time()
        self.count_since_last = 0
        return things

    def get_working_list(self, name=None) -> list:
        if name is not None:
            try:
                return self.dict[name][:]
            except KeyError:
                pass
        return self.dict[self.working_list][:]

    def get_working_list_name(self) -> str:
        return self.working_list

    def set_working_list(self, list_name):
        self.working_list = list_name
        try:
            self.alternative_rand_li = self.dict[list_name][:]
        except KeyError:
            self.dict[list_name] = []
            self.alternative_rand_li = []
        ItemLists.save_dic(self.contact, self.dict)

    def change_list_name(self, old_name, new_name) -> None:
        try:
            self.dict[new_name] = self.dict.pop(old_name)
        except KeyError:
            pass

    def is_closed(self) -> bool:
        return self.closed

    def is_open(self) -> bool:
        return not self.closed

    def close(self) -> None:
        self.closed = True

    def open(self) -> None:
        self.closed = False

    def set_talk(self) -> None:
        self.enable_talk = True

    def set_quiet(self) -> None:
        self.enable_talk = False

    def talk(self) -> bool:
        return self.enable_talk

    def is_recent(self) -> bool:
        return time() - self.last_rand_get_time < 15 or self.count_since_last < 5

    def increase_counter(self) -> None:
        self.count_since_last += 1


my_dic = {}


def onQQMessage(bot, contact, member, content) -> None:
    a_str = str(contact.qq)

    try:
        val = my_dic[a_str]
    except KeyError:
        val = PerContactDictionaryValue(contact.qq)
        my_dic[a_str] = val
    assert isinstance(val, PerContactDictionaryValue)
    old_content = content
    content = str(content.strip().lower())

    val.increase_counter()

    responded = True

    if time() - val.last_reply_time > 1 and not bot.isMe(contact, [member, contact][member is None]):
        if content == 'hello':
            bot.SendTo(contact, 'How are you')
        elif content == '--stop':
            bot.SendTo(contact, 'I\'m dead.')
            bot.Stop()
        elif val.is_open():
            if content == 'random':
                name = val.rand_get()
                if name is not None:
                    bot.SendTo(contact, 'My choice is: ' + name)
                else:
                    bot.SendTo(contact, 'No item found in the list.')
            elif search('^add (.)+', content):
                content = old_content[4:]
                names = str(content).strip().splitlines()
                for name in names:
                    name = name.strip()
                    if name != 'list':
                        val.add_item(name)
                bot.SendTo(contact, 'Added: ' + ''.join(
                    ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(names)))
            elif search('^set( )?list (.)+', content):
                index = content.index('list') + 5
                list_name = content[index:].strip().replace(' ', '_')
                val.set_working_list(list_name)
                bot.SendTo(contact, 'Working list set to ' + list_name)
            elif search('^list( )?lists$', content):
                li = val.get_entries()
                bot.SendTo(contact, 'There are ' + str(len(li)) + ' lists in the list:' + ''.join(
                    ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(li)))
            elif search('^list( )?(items)?$', content):
                li = val.get_working_list()
                bot.SendTo(contact, 'There are ' + str(len(li)) + ' items in the list:' + ''.join(
                    ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(li)))
            elif search('^delete list (.)+$', content):
                names = content.split()[2:]
                deleted = val.delete_lists(names)
                bot.SendTo(contact, 'Deleted lists: ' + ''.join(('\n\t' + str(e)) for e in reversed(deleted)))
                bot.SendTo(contact, 'Please set a new working list with command: \'set list <list name>\'')
            elif search('^delete (.)+$', content):
                items = content.split()[1:]
                try:
                    indexes = []
                    for item in items:
                        indexes.append(int(item))
                except ValueError:
                    names = val.delete_items(items)
                else:
                    names = val.delete_items(indexes)
                bot.SendTo(contact,
                           'Deleted: ' + ''.join(('\n\t' + str(e)) for e in reversed(names)))
            elif search('^change name (\S)+ (\S)+$', content):
                list_names = content[12:].split()
                old_name = list_names[0]
                new_name = list_names[1]
                val.change_list_name(old_name, new_name)
                onQQMessage(bot, contact, member, 'list lists')
            elif search('^get( )?list', content):
                bot.SendTo(contact, 'command ' + content + ' is deprecated, use \'list items\' instead')
                onQQMessage(bot, contact, member, 'list items')
            elif search('^\[@me\]( )+close$', content):
                val.close()
                bot.SendTo(contact, 'Bye bye bye')
            elif content == '-help':
                a_str = 'Supported commands: \n\t' \
                        '\'set list <list name>\' \n\t' \
                        '\'delete list\' \n\t' \
                        '\'change name <old list name> <new list name>\' \n\t' \
                        '\'list items\' \n\t' \
                        '\'list lists\' \n\t' \
                        '\'delete list \' \n\t' \
                        '\'add <item>\' \n\t' \
                        '\'delete item [index1 ...]\' \n\t' \
                        '\'random\' \n\t' \
                        '\'今晚吃啥\''
                bot.SendTo(contact, a_str)
            elif search('^(\S)*(今|明|昨|后|前)?(\S)?(早|晚|中午|夜宵)(\S)?吃(啥|什么|什麼)(\S)*$', content):
                name = val.rand_get()
                if name is not None:
                    if (name != '鸡' and name != '吃鸡') or not content.__contains__('晚'):
                        bot.SendTo(contact, '吃' + name + '！')
                    else:
                        bot.SendTo(contact, '大吉大利，晚上吃鸡！')
                    val.last_choice = name
                else:
                    bot.SendTo(contact, '喝西北风吧')
            elif val.is_recent() and search('^(\S)*(吃不起|没钱|不吃|换一个|不喜欢|不想吃|不好吃)(\S)*$', content):
                name = val.alternative_rand()
                if name is not None:
                    bot.SendTo(contact, '那就吃' + name)
                else:
                    bot.SendTo(contact, '这也不吃那也不吃，你吃屁去吧')
            else:
                responded = False
        elif search('^\[@me\]( )+open$', content):
            val.open()
            bot.SendTo(contact, 'I\'m back online!')
        else:
            responded = False

        if responded:
            val.last_reply_time = time()
