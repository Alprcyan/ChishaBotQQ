# -*- coding: utf-8 -*-

from random import randrange
from time import time
import json
from re import search

DINNER = '晚餐'
WORKING_LIST = 'working_dictionary'
USER_HOME = ''
FILE_PATH = USER_HOME + '.qqbot-tmp/whatToEat4DinnerForQICQData.json'

hardcoded_dic = {
    DINNER: ['肯德基', '麦当劳', '必胜客', '汉堡王'],
    WORKING_LIST: '晚餐'
}
HUB = {
    'default': hardcoded_dic
}
w2e4d_data_file_loaded = False


def file_init() -> None:
    global HUB
    global w2e4d_data_file_loaded
    try:
        with open(FILE_PATH) as f:
            new_initial_dic = json.load(f)
            try:
                new_initial_dic['default']
            except KeyError:
                new_initial_dic = HUB
            HUB = new_initial_dic
    except FileNotFoundError:
        with open(FILE_PATH, 'w') as f:
            json.dump(HUB, f)
    HUB['__version__'] = '1.0.1'
    w2e4d_data_file_loaded = True


def get_dict(contact=None) -> dict:
    global HUB
    global w2e4d_data_file_loaded
    if not w2e4d_data_file_loaded:
        file_init()
    if contact is not None:
        try:
            val = HUB[contact]
        except KeyError:
            val = hardcoded_dic.copy()
            HUB[contact] = val
    else:
        val = hardcoded_dic.copy()
    return val


def save_dic(contact, contact_dic) -> None:
    global HUB
    global w2e4d_data_file_loaded
    HUB[contact] = contact_dic
    with open(FILE_PATH, 'w') as f:
        json.dump(HUB, f)


class PerContactDictionaryValue(object):
    def __init__(self, contact):
        contact = str(contact)
        self.contact = contact
        self.dict = get_dict(contact)
        self.working_list = str(self.dict[WORKING_LIST])
        self.closed = False
        self.last_choice = None
        self.last_index = -1
        self.enable_talk = False
        self.last_rand_get_time = 0.0
        self.count_since_last = 0
        self.count_alternative_rand = 0
        self.alternative_rand_li = self.dict[self.working_list][:]
        self.last_reply_time = 0.0

    def add_items_without_save(self, name):
        if isinstance(name, list):
            for item in name:
                self.add_items_without_save(item)
        else:
            self.alternative_rand_li.append(name)
            try:
                self.dict[self.working_list]
            except KeyError:
                self.dict[self.working_list] = []
            self.dict[self.working_list].append(name)

    def add_items_and_save(self, name) -> None:
        self.add_items_without_save(name)
        save_dic(self.contact, self.dict)

    def clean(self) -> list:
        self.alternative_rand_li = []
        li = self.dict[self.working_list]
        self.dict[self.working_list] = []
        return li

    def dict_size(self) -> int:
        return len(self.dict) - 1

    def current_list_size(self) -> int:
        return len(self.dict[self.working_list])

    def delete_items(self, args) -> list:
        deleted = []
        if isinstance(args, list):
            try:
                indexes = []
                for item in args:
                    indexes.append(int(item))
            except ValueError:
                for name in args:
                    for i, e in enumerate(self.dict[self.working_list]):
                        if e == name:
                            deleted.append(self.dict[self.working_list].pop(i))
                    for i, e in enumerate(self.alternative_rand_li):
                        if e == name:
                            del self.alternative_rand_li[i]
            else:
                indexes = reversed(sorted(indexes))
                for index in indexes:
                    name = self.dict[self.working_list].pop(index)
                    deleted.append(name)
                    for i, e in enumerate(self.alternative_rand_li):
                        if e == name:
                            del self.alternative_rand_li[i]
        else:
            deleted = self.delete_items([args])
        save_dic(self.contact, self.dict)
        return deleted

    def get_entries(self) -> list:
        li = []
        for key in self.dict:
            if key != WORKING_LIST:
                li.append(key)
        return li

    def delete_lists(self, names) -> list:
        deleted = []
        if isinstance(names, list):
            for name in names:
                try:
                    if name != WORKING_LIST and name != self.working_list:
                        deleted.append(self.dict.pop(name))
                except KeyError:
                    pass
        else:
            deleted = self.delete_lists([names])
        save_dic(self.contact, self.dict)
        return deleted

    def rand_get(self) -> str:
        size = self.current_list_size()
        name = None
        if size > 0:
            if size > 1:
                next_index = self.last_index
                while next_index == self.last_index:
                    next_index = randrange(size)
            else:
                next_index = 0
            self.last_index = next_index
            try:
                name = self.dict[self.working_list][next_index]
                self.alternative_rand_li = self.dict[self.working_list][:]
                for index, value in enumerate(self.alternative_rand_li):
                    if value == name:
                        del self.alternative_rand_li[next_index]
            except KeyError:
                pass
        self.last_rand_get_time = time()
        self.count_since_last = 0
        return name

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

    def get_list(self, name=None, contact=None) -> list:
        global HUB
        contact = str([contact, self.contact][contact is None])
        name = [name, self.working_list][name is None]
        try:
            return HUB[contact][name][:]
        except KeyError:
            return []

    def is_working_list(self, name) -> bool:
        if name == self.working_list:
            return True
        return False

    def get_working_list_name(self) -> str:
        return self.working_list

    def set_working_list(self, list_name):
        self.working_list = list_name
        self.dict[WORKING_LIST] = list_name
        try:
            self.alternative_rand_li = self.dict[list_name][:]
        except KeyError:
            self.dict[list_name] = []
            self.alternative_rand_li = []
        save_dic(self.contact, self.dict)

    def change_list_name(self, old_name, new_name) -> None:
        try:
            self.dict[new_name] = self.dict.pop(old_name)
            if old_name == self.working_list:
                self.working_list = new_name
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

    def is_recent(self) -> bool:
        return time() - self.last_rand_get_time < 15 or self.count_since_last < 5

    def increase_counter(self) -> None:
        self.count_since_last += 1


w2e4d_main_dictionary = {}


def onQQMessage(bot, contact, member, content) -> None:
    a_str = str(contact.qq)

    try:
        val = w2e4d_main_dictionary[a_str]
    except KeyError:
        val = PerContactDictionaryValue(contact.qq)
        w2e4d_main_dictionary[a_str] = val
    assert isinstance(val, PerContactDictionaryValue)
    old_content = content.strip()
    content = str(old_content.lower())

    val.increase_counter()

    responded = True

    if time() - val.last_reply_time > 1 and not bot.isMe(contact, [member, contact][member is None]):
        if content == 'hello':
            bot.SendTo(contact, '你好')
        elif content == '--stop':
            bot.SendTo(contact, '我死了')
            bot.Stop()
        elif val.is_open():
            if content == 'random':
                name = val.rand_get()
                if name is not None:
                    bot.SendTo(contact, '我的选择是：' + name)
                else:
                    bot.SendTo(contact, '当前列表中没有项目')
            elif content == 'dice':
                bot.SendTo(contact, str(int(randrange(6) + 1)))
            elif search('^add (.)+', content):
                content = old_content[4:]
                names = str(content).splitlines()
                for name in names:
                    name = name.strip()
                    if name != 'list':
                        val.add_items_and_save(name)
                bot.SendTo(contact, '已添加：' + ''.join(
                    ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(names)))
            elif search('^set( )?list (.)+', content):
                index = old_content.index('list') + 5
                list_name = old_content[index:].strip().replace(' ', '_')
                val.set_working_list(list_name)
                bot.SendTo(contact, '当前列表已设置为' + list_name)
            elif search('^list( )?lists$', content):
                li = val.get_entries()
                names = []
                for name in li:
                    if val.is_working_list(name):
                        name = name + ' *'
                    names.append(name)
                bot.SendTo(contact, '此对话共有' + str(len(names)) + '个列表：' + ''.join(
                    ('\n\t' + str(e)) for e in names))
            elif search('^list( )?items(( )+(\S)+)?$', content):
                list_name = content[content.index('ms') + 3:]
                list_name = [list_name, val.get_working_list_name()][len(list_name) == 0].strip().replace(' ', '_')
                names = val.get_list(list_name)
                bot.SendTo(contact,
                           '列表\'' + list_name + '\'中共有' + str(len(names)) + '个项目：' + ''.join(
                               ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(names)))
            elif search('^delete list (.)+$', content):
                names = old_content.split()[2:]
                deleted = val.delete_lists(names)
                bot.SendTo(contact, '已删除列表：' + ''.join(('\n\t' + str(e)) for e in deleted))
                bot.SendTo(contact, '请使用命令 \'set list list_name\' 设置新的列表')
            elif search('^delete (.)+$', content):
                items = old_content.split()[1:]
                names = val.delete_items(items)
                bot.SendTo(contact,
                           '已删除：' + ''.join(('\n\t' + str(e)) for e in reversed(names)))
            elif search('^change name (\S)+ (\S)+$', content):
                list_names = content[12:].split()
                old_name = list_names[0]
                new_name = list_names[1]
                val.change_list_name(old_name, new_name)
                onQQMessage(bot, contact, member, 'list lists')
            elif search('^get( )?list', content):
                onQQMessage(bot, contact, member, 'list items')
            elif search('^copy (\d){5,12} (\S)+', content):
                try:
                    qq, name = old_content.split()[1:]
                except KeyError:
                    bot.SendTo(contact, '参数错误。举例：\'copy 10001 马化腾的晚餐\'')
                    return
                src_list = val.get_list(name, qq)
                if len(src_list) == 0:
                    bot.SendTo(contact, '源列表为空或不存在，请重试')
                    return
                val.add_items_and_save(src_list)
                bot.SendTo(contact, '已添加')
            elif content == '--clean-list':
                li = val.clean()
                bot.SendTo(contact, '已清空列表\'' + val.get_working_list_name() + '\'：\n\t' + str(li))
            elif search('^\[@me\]( )+close$', content):
                val.close()
                bot.SendTo(contact, 'Bye bye bye')
            elif content == '-help':
                a_str = '支持命令: \n\t' \
                        '\'set list list_name\'：将当前列表设置为list_name\n\t' \
                        '\'delete list list_name\'：删除名为list_name的列表，不可为当前列表\n\t' \
                        '\'change name old_list_name new_list_name\'：将old_list_name更名为new_list_name\n\t' \
                        '\'list items\'：列出当前列表的所有项目\n\t' \
                        '\'list lists\'：列出该对话的所有列表名\n\t' \
                        '\'add item_name\'：将item_name添加到当前列表\n\t' \
                        '\'delete item_name\'：删除当前列表中的对应项目，以换行隔开\n\t' \
                        '\'random\'：从当前列表中随机选择\n\t' \
                        '\'copy qq src_list_name\'：将src_list_name中的项目添加到自己的当前列表\n\t' \
                        '\'今晚吃啥\''
                bot.SendTo(contact, a_str)
            elif search('^(\S)*([今明昨后前])?(\S)?(早|晚|中午|夜宵)(\S)?吃(啥|什么|什麼)(\S)*$', content):
                name = val.rand_get()
                if name is not None:
                    if (name != '鸡' and name != '吃鸡') or not content.__contains__('晚'):
                        bot.SendTo(contact, '吃' + name + '！')
                    else:
                        bot.SendTo(contact, '大吉大利，晚上吃鸡！')
                    val.last_choice = name
                else:
                    bot.SendTo(contact, '喝西北风吧')
            elif val.is_recent() and search('^(\S)*(吃不起|没钱|不吃|换一个|不喜欢|不想吃|不好吃|吃过了)(\S)*$', content):
                name = val.alternative_rand()
                if name is not None:
                    bot.SendTo(contact, '那就吃' + name)
                else:
                    bot.SendTo(contact, '这也不吃那也不吃，你吃屁去吧')
            else:
                responded = False
        elif search('^\[@me\]( )+open$', content):
            val.open()
            bot.SendTo(contact, '我又回来了')
        else:
            responded = False

        if responded:
            val.last_reply_time = time()
