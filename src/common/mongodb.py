#!/usr/bin/python3
# -*- coding: utf-8 -*-
# cython: language_level=3
from datetime import datetime

import pymongo
from bson.objectid import ObjectId

from src.common.constant import DEFINE_MONGO_TIME_FIELDS
from src.common.log import logger


class DatabaseHandler(object):
    # @abstractmethod
    def name(self):
        pass

    # @abstractmethod
    def write(self, table, cond, insert, update):
        pass

    # @abstractmethod
    def read(self, table, cond, show, sort):
        pass


class DatabaseHandlerDefault(DatabaseHandler):
    _name = "default"

    def __init__(self):
        self.__mongodb = {"host": "127.0.0.1", "port": "27017", "user": "admin", "passwd": "", "db": "ts3"}
        self.__mongocli = None
        self.__time_fields = DEFINE_MONGO_TIME_FIELDS

    def __mongodb_connstr(self):
        return 'mongodb://%s:%s/' % (self.__mongodb["host"], self.__mongodb["port"])

    def name(self):
        return self._name

    def __active(self):
        if self.__mongocli:
            try:
                self.__mongocli.admin.command('ismaster')
            except:
                self.__mongocli = pymongo.MongoReplicaSetClient(self.__mongodb_connstr())
        else:
            self.__mongocli = pymongo.MongoReplicaSetClient(self.__mongodb_connstr())

        return self.__mongocli

    def write_many(self, table, insert_list):
        if not table:
            logger.warning("write quest args 'table' must be not null string")
            return False
        if not isinstance(insert_list, list):
            logger.warning("write many args 'insert_list' must be list,like [{'test': 'test'}]")
            return False
        if not self.__active():
            logger.warning("can't connect to mongoDB server")
            return False
        if not insert_list:
            logger.warning("write many args 'insert_list' is empty list")

        coll = self.__mongocli[self.__mongodb["db"]][table]
        if not coll.insert_many(insert_list):
            return False
        return True

    def write(self, table, cond, insert, update, change_notify=False, upsert=True):
        conds = {}

        if not table:
            logger.warning("write quest args 'table' must be not null string")
            return False

        if type(cond) != dict or type(insert) != dict or type(update) != dict:
            logger.warning("write quest args 'cond' and 'insert' and 'update' must be dict")
            return False

        if not self.__active():
            logger.warning("cann't connect to mongoDB server")
            return False

        coll = self.__mongocli[self.__mongodb["db"]][table]
        conds.update(cond)
        if "_id" in conds:
            conds["_id"] = ObjectId(conds["_id"])

        if coll.find(conds).count() > 0:
            values = update
        else:
            values = update
            values.update(insert)

        if len(values) == 0:
            return False

        for i in self.__time_fields:
            if i in values:
                values[i + "_display"] = datetime.fromtimestamp(values[i]).strftime('%Y-%m-%d %H:%M:%S')
        if not coll.update_one(conds, {"$set": values}, upsert=upsert):
            logger.warning("insert/update %s coll error" % table)
            return False
        return True

    def update_many(self, table, cond, update, change_notify=False, upsert=True):
        conds = {}

        if not table:
            logger.warning("write quest args 'table' must be not null string")
            return False

        if type(cond) != dict or type(update) != dict:
            logger.warning("write quest args 'cond' and 'insert' and 'update' must be dict")
            return False

        if not self.__active():
            logger.warning("cann't connect to mongoDB server")
            return False

        coll = self.__mongocli[self.__mongodb["db"]][table]
        conds.update(cond)
        if "_id" in conds:
            conds["_id"] = ObjectId(conds["_id"])

        values = update
        if len(values) == 0:
            return False
        for i in self.__time_fields:
            if i in values:
                values[i + "_display"] = datetime.fromtimestamp(values[i]).strftime('%Y-%m-%d %H:%M:%S')
        if not coll.update_many(conds, {"$set": values}, upsert=upsert):
            logger.warning("insert/update %s coll error" % table)
            return False
        return True


    def read(self, table, cond, show=None, sort=None):
        if not table:
            logger.warning("read quest args 'table'must be not null string")
            return None

        if type(cond) != dict:
            logger.warning("read quest args 'cond' and 'show' and 'sort' must be dict")
            return None

        if not self.__active():
            logger.warning("cann't connect to mongoDB server")
            return None

        datas = []

        coll = self.__mongocli[self.__mongodb["db"]][table]
        result = coll.find(cond, projection=show, sort=sort)

        if result is not None:
            for i in result:
                if "_id" in i and show is not None and "_id" in show and show["_id"] == 1:
                    i["_id"] = str(i["_id"])
                else:
                    del i["_id"]

                datas.append(i)

        return datas

    def delete(self, table, cond):
        if not table:
            logger.warning("delete quest args 'table'must be not null string")
            return False

        if cond is None or (type(cond) != dict and type(cond) != list):
            logger.warning("delete quest args 'cond' must be dict")
            return False

        if not self.__active():
            logger.warning("can't connect to mongoDB server")
            return False

        if type(cond) == dict:
            cond = [cond]

        coll = self.__mongocli[self.__mongodb["db"]][table]

        for c in cond:
            if not coll.delete_many(c):
                logger.warning("delete %s coll failed" % table)
                return False
        return True

    def delete_one_document(self, table, cond):
        if not table:
            logger.warning("delete quest args 'table'must be not null string")
            return False
        if cond is None or (type(cond) != dict and type(cond) != list):
            logger.warning("delete quest args 'cond' must be dict")
            return False
        if not self.__active():
            logger.warning("can't connect to mongoDB server")
            return False
        if type(cond) == dict:
            cond = [cond]
        coll = self.__mongocli[self.__mongodb["db"]][table]
        for c in cond:
            if not coll.delete_one(c):
                logger.warning("delete %s coll failed" % table)
                return False
        return True

    def clear_collection(self,table):
        if not table:
            logger.warning("remove quest args 'table'must be not null string")
            return None
        if not self.__active():
            logger.warning("cann't connect to mongoDB server")
            return None
        coll = self.__mongocli[self.__mongodb["db"]][table]
        coll.remove()


class DatabaseHandlerTest(DatabaseHandlerDefault):
    pass


# DATABASE_HANDLER_LIST = [DatabaseHandlerDefault(), DatabaseHandlerTest()]

DATABASE_HANDLER = {"default": DatabaseHandlerDefault(),
                    "test": DatabaseHandlerTest()}


def db_handler_get(name):
    return DATABASE_HANDLER.get(name)
