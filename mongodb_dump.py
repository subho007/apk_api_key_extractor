import datetime
import json
import logging
import os

import pymongo
from pymongo.errors import AutoReconnect
from retry_decorator import retry

from abstract_dump import AbstractDump

import config

COLLECTION_NAME = "key_dump"
STRINGS_COLLECTION_NAME = "all_strings"

class MongoDBDump(AbstractDump):

    def __init__(self):
        self.client = pymongo.MongoClient(config.mongodb.address, int(config.mongodb.port), username=config.mongodb.user, password=config.mongodb.password)
        self.db = client[config.mongodb.name]
        self.collection = db[COLLECTION_NAME]
        self.strings_collection = db[STRINGS_COLLECTION_NAME]

    @retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
    def dump_apikeys(self, entries, package, version_code, version_name):
        # noinspection PyUnusedLocal
        entries_dicts = []
        for entry in entries:
            entry_dict = entry.__dict__
            entry_dict['package'] = package
            entry_dict['versionCode'] = version_code
            entry_dict['versionName'] = version_name
            entries_dicts.append(entry_dict)
        if entries_dicts:
            self.collection.insert_many(entries_dicts, False)

    @retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
    def dump_strings(self, entries):
        operations = []
        for entry in entries:
            operations.append(UpdateOne({'_id': entry.value}, {'$inc': {'count': 1}}))
        if ( len(operations) > 0 ):
            strings_collection.bulk_write(operations,ordered=False)

    @retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
    def get_apikey_unverified(self):
        document = self.collection.find_one({"verified": None})
        return document


    @retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
    def set_apikey_verified(self, api_id):
        document_before = self.collection.find_one_and_update({'_id': api_id}, {"$set": {"verified": True}})
        if not document_before:
            logging.error("Unable to set api {0} as verified! Id not found.".format(api_id))


    @retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
    def remove_apikey(self, api_id):
        self.collection.remove(api_id)
