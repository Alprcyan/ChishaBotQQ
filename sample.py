# -*- coding: utf-8 -*-

from random import randrange
from time import time
import json
from re import search

CHISHA_DINNER = '晚餐'
CHISHA_VER_1_0_2_WORKING_LIST = 'working_dictionary'
CHISHA_VER_1_1_0_WORKING_LIST = '__d29ya2luZ19kaWN0aW9uYXJ5Cg==__'
CHISHA_USER_HOME = ''
CHISHA_FILE_PATH = CHISHA_USER_HOME + '.qqbot-tmp/whatToEat4DinnerForQICQData.json'

chisha_hardcoded_dic = {
    CHISHA_DINNER: ['肯德基', '麦当劳', '必胜客', '汉堡王'],
    CHISHA_VER_1_1_0_WORKING_LIST: '晚餐'
}
chisha_HUB = {
    # key is str(contact). Value is a dict, which contains several lists of dishes strs.
    # the key WORKING_LIST map to a str, which is the key of working list.
    'default': chisha_hardcoded_dic
}
chisha_json_file_is_loaded = False  # set to true if the json file is loaded.


def chisha_load_json_file() -> None:
    global chisha_HUB
    global chisha_json_file_is_loaded
    try:
        with open(CHISHA_FILE_PATH) as f:
            new_initial_dic = json.load(f)
            try:
                new_initial_dic['default']
            except KeyError:
                new_initial_dic = chisha_HUB
            chisha_HUB = new_initial_dic
    except FileNotFoundError:
        with open(CHISHA_FILE_PATH, 'w') as f:
            json.dump(chisha_HUB, f, indent=4)
    try:
        if chisha_HUB['__version__'] < ' 1.1.0':
            new_dic = {}
            for contact in chisha_HUB:
                if isinstance(chisha_HUB[contact], dict):
                    for key in chisha_HUB[contact]:
                        if key != CHISHA_VER_1_0_2_WORKING_LIST:
                            new_dic[contact][key] = chisha_HUB[contact][key]
                        else:
                            new_dic[contact][CHISHA_VER_1_1_0_WORKING_LIST] = chisha_HUB[contact][key]
                else:
                    new_dic[contact] = chisha_HUB[contact][:]
            chisha_HUB = new_dic
    except KeyError:
        pass
    chisha_HUB['__version__'] = '1.1.0'
    chisha_json_file_is_loaded = True


def chisha_get_dict(contact=None) -> dict:
    """
    looking the contact up in the HUB. if there is no such contact in HUB,
        return a copy of the hardcoded_dic.
    :param contact: contact is a str with 5 to 12 digit.
    :return: a dict for the contact.
    """
    global chisha_HUB
    global chisha_json_file_is_loaded
    if not chisha_json_file_is_loaded:
        chisha_load_json_file()
    try:
        val = chisha_HUB[contact]
    except KeyError:  # no such contact in HUB
        val = chisha_hardcoded_dic.copy()
        for item in val:
            val[item] = val[item][:]
    return val


def chisha_save_dic(contact, contact_dic) -> None:
    """
    update HUB with the key contact and the value contact_dic.
    and save it to a json file.
    :param contact: The contact that owns the following dict
    :param contact_dic: the dict which is returned by function get_dict(contact)
    :return: None
    """
    global chisha_HUB
    global chisha_json_file_is_loaded
    chisha_HUB[contact] = contact_dic
    with open(CHISHA_FILE_PATH, 'w') as f:
        json.dump(chisha_HUB, f, indent=4)


class ChiShaDictionaryValueObject(object):
    """ The value object of the dict main_dictionary below"""

    def __init__(self, contact):
        """
        the constructor
        :param contact: is 5 to 12 digits
        """
        contact = str(contact)  # make sure it's a string
        self.__contact = contact
        self.__dict = chisha_get_dict(contact)  # this dict will be stored in HUB
        self.__working_list = self.__dict[CHISHA_VER_1_1_0_WORKING_LIST]
        self.__closed = False  # set to True to temporary disable the bot.
        self.__last_choice = None  # record for preventing repeated answer
        self.__last_index = -1
        self.__last_rand_get_time = 0.0

        # count the contacts since last message sent.
        # should be updated on message received.
        self.__count_since_last = 0

        # a copy of the working list, preventing repeated answers from command '不吃'
        self.__alternative_rand_list = self.__dict[self.__working_list][:]
        self.__last_reply_time = 0.0

    def __add_items_without_save__(self, name) -> None:
        """
        add items to the working list, no saving to json file or updating HUB.
        :param name: the item to be added.
        """
        if isinstance(name, list):
            for item in name:
                self.__add_items_without_save__(item)
        else:
            self.__alternative_rand_list.append(name)
            try:
                self.__dict[self.__working_list]
            except KeyError:
                self.__dict[self.__working_list] = []
            self.__dict[self.__working_list].append(name)

    def add_items_and_save(self, name) -> None:
        """
        add items to the working list, update HUB, and saving to json file.
        """
        self.__add_items_without_save__(name)
        chisha_save_dic(self.__contact, self.__dict)

    def clean(self) -> list:
        """
        clean the working list
        :return the working before cleaning.
        """
        self.__alternative_rand_list = []
        li = self.__dict[self.__working_list]
        self.__dict[self.__working_list] = []
        chisha_save_dic(self.__contact, self.__dict)
        return li

    def dict_size(self) -> int:
        """
        :return the number of lists for this contact.
        """
        return len(self.__dict) - 1

    def working_list_size(self) -> int:
        """
        :return the size
        """
        return len(self.__dict[self.__working_list])

    def delete_items(self, args) -> list:
        """
        delete items in the working list
        :param args: a list of indexes or names to be deleted
        :return: a list of deleted items.
        """
        deleted = []
        if isinstance(args, list):
            try:
                indexes = []
                for item in args:
                    indexes.append(int(item))
                # int(item) throws ValueError if item contains non-digit characters.
            except ValueError:
                for name in args:
                    for i, e in enumerate(self.__dict[self.__working_list]):
                        if e == name:
                            deleted.append(self.__dict[self.__working_list].pop(i))
                    for i, e in enumerate(self.__alternative_rand_list):
                        if e == name:
                            del self.__alternative_rand_list[i]
            else:  # no exception caught,
                indexes = reversed(sorted(indexes))
                for index in indexes:
                    try:
                        name = self.__dict[self.__working_list].pop(index)
                    except IndexError:
                        continue
                    deleted.append(name)
                    for i, e in enumerate(self.__alternative_rand_list):
                        if e == name:
                            del self.__alternative_rand_list[i]
        else:
            deleted = self.delete_items([args])  # self calling if args is not a list.
        chisha_save_dic(self.__contact, self.__dict)
        return deleted

    def get_entries(self) -> list:
        """
        :return: a list of list names in the dict.
        """
        li = []
        for key in self.__dict:
            if key != CHISHA_VER_1_1_0_WORKING_LIST:
                li.append(key)
        return li

    def delete_lists(self, names) -> list:
        """
        only works on lists which are not the working list
        :param names:
        :return: a list of deleted lists.
        """
        deleted = []
        if isinstance(names, list):
            for name in names:
                try:
                    if name != CHISHA_VER_1_1_0_WORKING_LIST and name != self.__working_list:
                        deleted.append(self.__dict.pop(name))
                except KeyError:
                    pass
        else:
            deleted = self.delete_lists([names])
        chisha_save_dic(self.__contact, self.__dict)
        return deleted

    def get_random_item(self) -> str:
        """
        guaranteed to choose a different item on a second call,
        unless there's only one item in the list
        :return: random item in the working list
        """
        size = self.working_list_size()
        name = None
        if size > 0:
            if size > 1:
                next_index = self.__last_index
                while next_index == self.__last_index:
                    next_index = randrange(size)
            else:
                next_index = 0
            self.__last_index = next_index
            try:
                name = self.__dict[self.__working_list][next_index]
                self.__alternative_rand_list = self.__dict[self.__working_list][:]
                for index, value in enumerate(self.__alternative_rand_list):
                    if value == name:
                        del self.__alternative_rand_list[next_index]
            except KeyError:
                pass
        self.__last_rand_get_time = time()
        self.__count_since_last = 0
        return name

    def alternative_rand(self) -> str:
        """
        randomly choose one from self.__dict[self.__working_list]
        guaranteed not to repeat before the list is empty.
        :return: an item from self.__dict[self.__working_list]
        """
        self.__last_index = -1
        val = len(self.__alternative_rand_list)
        if val > 0:
            next_index = randrange(val)
            things = self.__alternative_rand_list[next_index][:]
            del self.__alternative_rand_list[next_index]
        else:
            things = None
        self.__last_rand_get_time = time()
        self.__count_since_last = 0
        return things

    def list_item(self, list_name=None, contact=None) -> list:
        """

        :param list_name: the name of the list. None if you want the current working list.
        :param contact: the contact. None if you want lists in current contact's dict
        :return: the [name=None] list for [contact=None]. a empty list is returned if no such list.
        """
        global chisha_HUB
        contact = str([contact, self.__contact][contact is None])
        list_name = [list_name, self.__working_list][list_name is None]
        try:
            return chisha_HUB[contact][list_name][:]
        except KeyError:
            return []

    def is_working_list(self, list_name) -> bool:
        """
        Check if the giving list is the working list
        :param list_name: the name of the list
        :return: True if name equals to the working list, otherwise False.
        """
        if list_name == self.__working_list:
            return True
        return False

    def get_working_list_name(self) -> str:
        """
        get the name of the working list
        :return: a str of the name of the working list
        """
        return self.__working_list

    def set_working_list(self, list_name) -> None:
        """
        set the working list
        :param list_name: the name of list you want
        :return: None
        """
        if not isinstance(list_name, str):
            self.set_working_list(str(list_name))
        else:
            self.__working_list = list_name
            self.__dict[CHISHA_VER_1_1_0_WORKING_LIST] = list_name
            try:
                self.__alternative_rand_list = self.__dict[list_name][:]
            except KeyError:
                self.__dict[list_name] = []
                self.__alternative_rand_list = []
            chisha_save_dic(self.__contact, self.__dict)

    def change_list_name(self, old_name, new_name) -> None:
        """
        Change the list name of the list which is named old_name to new_name.
        Do nothing if the list doesn't exist.
        :param old_name: the old name
        :param new_name: the new name
        :return: None
        """
        try:
            self.__dict[new_name] = self.__dict.pop(old_name)
            if old_name == self.__working_list:
                self.__working_list = new_name
        except KeyError:
            pass

    def is_closed(self) -> bool:
        return self.__closed

    def is_open(self) -> bool:
        return not self.__closed

    def close(self) -> None:
        self.__closed = True

    def open(self) -> None:
        self.__closed = False

    def is_recent(self) -> bool:
        return time() - self.__last_rand_get_time < 15 or self.__count_since_last < 5

    def increase_counter(self) -> None:
        self.__count_since_last += 1


chisha_main_dictionary = {}


def onQQMessage(bot, contact, member, content) -> None:
    a_str = str(contact.qq)

    try:
        val = chisha_main_dictionary[a_str]
    except KeyError:
        val = ChiShaDictionaryValueObject(contact.qq)
        chisha_main_dictionary[a_str] = val

    old_content = content.strip()
    content = str(old_content.lower())

    val.increase_counter()

    responded = True

    if 1 < time() - val.__last_reply_time and not bot.isMe(contact, [member, contact][member is None]):
        if content == 'hello':
            bot.SendTo(contact, '你好')
        elif search('^\[@me\]( )+--stop$', content):
            bot.SendTo(contact, '我死了')
            bot.Stop()
        elif search('^\[@me\]( )+src$', content):
            bot.SendTo(contact, 'https://github.com/Alprcyan/ChishaBotQQ')
        elif member is not None and '山羊' in content:
            bot.SendTo(contact, 'member: ' + member + "\ncontent: "+ content)
        elif val.is_open():
            if content == 'random':
                name = val.get_random_item()
                if name is not None:
                    bot.SendTo(contact, '我的选择是：' + name)
                else:
                    bot.SendTo(contact, '当前列表中没有项目')
            elif search('^dice( (\S)+)+$', content):
                items = old_content.split()[1:]
                bot.SendTo(contact, items[randrange(len(items))])
            elif content == 'dice':
                bot.SendTo(contact, str(int(randrange(6) + 1)))
            elif search('^flip (\d)+$', content):
                results = [0, 0]
                times = int(content.split()[1])
                for i in range(times):
                    results[randrange(2)] += 1
                bot.SendTo(contact, '总计获得 ' + str(results[0]) + ' 次正面，' + str(results[1]) + ' 次反面')
            elif content == 'flip':
                bot.SendTo(contact, ['Tails', 'Heads'][randrange(2)])
            elif search('^add (.)+', content):
                content = old_content[4:]
                deleted = str(content).splitlines()
                for name in deleted:
                    name = name.strip()
                    if name != 'list':
                        val.add_items_and_save(name)
                bot.SendTo(contact, '已添加：' + ''.join(
                    ('\n\t' + str(e)) for index, e in enumerate(deleted)))
            elif search('^set( )?list (.)+$', content):
                index = old_content.index('list') + 5
                list_name = old_content[index:].strip().replace(' ', '_')
                val.set_working_list(list_name)
                bot.SendTo(contact, '当前列表已设置为' + list_name)
            elif search('^list( )?list$', content):
                li = val.get_entries()
                lists = []
                for name in li:
                    if val.is_working_list(name):
                        name = name + ' *'
                    lists.append(name)
                bot.SendTo(contact, '此对话共有' + str(len(lists)) + '个列表：' + ''.join(
                    ('\n\t' + str(e)) for e in lists))
            elif search('^list( )?item( (\S)+)?$', content):
                list_name = old_content[old_content.index('em') + 3:]
                list_name = [list_name, val.get_working_list_name()][len(list_name) == 0].strip().replace(' ', '_')
                deleted = val.list_item(list_name)
                bot.SendTo(contact,
                           '列表\'' + list_name + '\'中共有' + str(len(deleted)) + '个项目：' + ''.join(
                               ('\n\t' + str(index) + ', ' + str(e)) for index, e in enumerate(deleted)))
            elif search('^delete list (.)+$', content):
                deleted = old_content.split()[2:]
                deleted = val.delete_lists(deleted)
                bot.SendTo(contact, '已删除列表：' + ''.join(('\n\t' + str(e)) for e in deleted))
                bot.SendTo(contact, '请使用命令 \'set list list_name\' 设置新的列表')
            elif search('^delete range (\d)+ (\d)+$', content):
                ranges = content.split()[2:]
                indexes = []
                begin = int(ranges[0])
                end = int(ranges[1])
                begin, end = [(end, begin), (begin, end)][begin < end]
                end = [val.working_list_size(), end + 1][end < val.working_list_size()]
                for i in range(begin, end):
                    indexes.append(i)
                deleted = val.delete_items(indexes)
                bot.SendTo(contact,
                           '已删除：' + ''.join(('\n\t' + str(e)) for e in reversed(deleted)))
            elif search('^delete (.)+$', content):
                old_content = old_content[7:]
                items = old_content.splitlines()
                deleted = val.delete_items(items)
                bot.SendTo(contact,
                           '已删除：' + ''.join(('\n\t' + str(e)) for e in reversed(deleted)))
            elif search('^change name (\S)+ (\S)+$', content):
                list_names = content[12:].split()
                old_name = list_names[0]
                new_name = list_names[1]
                val.change_list_name(old_name, new_name)
                onQQMessage(bot, contact, member, 'list lists')
            elif search('^get( )?list$', content):
                onQQMessage(bot, contact, member, 'list items')
            elif search('^copy ((\d){5,12}|default) (\S)+$', content):
                try:
                    qq, name = old_content.split()[1:]
                except KeyError:
                    bot.SendTo(contact, '参数错误。举例：\'copy 10001 马化腾的晚餐\'')
                    return
                src_list = val.list_item(name, qq)
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
                        '\'set list $list_name\'：将当前列表设置为list_name\n\t' \
                        '\'delete list $list_name\'：删除名为list_name的列表，不可为当前列表\n\t' \
                        '\'change name $old_list_name $new_list_name\'：将old_list_name更名为new_list_name\n\t' \
                        '\'list item\'：列出当前列表的所有项目\n\t' \
                        '\'list list\'：列出该对话的所有列表名\n\t' \
                        '\'add $item_name\'：将item_name添加到当前列表\n\t' \
                        '\'delete $item_name|$index\'：删除当前列表中的对应项目，以换行隔开\n\t' \
                        '\'delete range $begin $end\': 删除当前列表中自 begin（含）到 end（含）的项目' \
                        '\'random\'：从当前列表中随机选择\n\t' \
                        '\'copy $qq $src_list_name\'：将指定对话中的src_list_name中的项目添加到自己的当前列表\n\t' \
                        '\'今晚吃啥\': 吃电子羊'
                bot.SendTo(contact, a_str)
            elif search('^((\S)*([今明昨后前])?(\S)?(早|晚|午|夜宵)(\S)?吃(啥|什么|什麼)(\S)*)|吃啥$', content):
                name = val.get_random_item()
                if name is not None:
                    if (name != '鸡' and name != '吃鸡') or not content.__contains__('晚'):
                        bot.SendTo(contact, '吃' + name + '！')
                    else:
                        bot.SendTo(contact, '大吉大利，晚上吃鸡！')
                    val.__last_choice = name
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
            val.__last_reply_time = time()
