from config import MEILISEARCH_MASTER_KEY
import os
import meilisearch
import subprocess
import time
from pymongo import MongoClient
from config import ATLAS_USERNAME, ATLAS_PASSWORD, ATLAS_DATABASE, MEILISEARCH_MASTER_KEY, MEILISEARCH_HOSTNAME
import random
from loguru import logger

class MongoDbRetriever:

    @logger.catch
    def __init__(self, mongo_db, mongo_db_collection) -> None:
        self.mongo_uri = f"mongodb+srv://{ATLAS_USERNAME}:{ATLAS_PASSWORD}@{ATLAS_DATABASE}.mongodb.net/?retryWrites=true&w=majority"
        self.mongo_client = MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[mongo_db]
        self.mongo_db_collection = self.mongo_db[mongo_db_collection]
        sort = [("_id", -1)]
        projection = {"_id": 0}
        docs = self.mongo_db_collection.find(projection=projection, sort=sort)
        self.mongo_db_documents = list(docs)

        #if link_retriever:
        #    self.mongo_db_query = {"title": {"$ne": ""}}
        #else:
        #    self.mongo_db_query = {"id": {"$ne": ""}, "download_link": {"$ne": ""}}
        #self.mongo_db_sort = [("_id", -1)]
        #self.mongo_db_project = {"_id": 0}
        #self.mongo_db_documents = self.mongo_db_collection.find(self.mongo_db_query, sort=self.mongo_db_sort, projection=self.mongo_db_project)
        #self.msearch_documents = list(self.mongo_db_documents)
        ##self.index.add_documents(documents=self.msearch_documents)
        #if not link_retriever:
        #    self.msearch_client.delete_index("annotation_index")
        #    self.msearch_index = self.msearch_client.index('annotation_index')
        #    self.msearch_index.add_documents(self.msearch_documents)
        #print(self.msearch_client.get_task(0))
    
    @logger.catch
    def search(self, query, X_Session_Id):
        logger.info(f"Session: {X_Session_Id} | query is being searched: {query}")
        documents = self.msearch_index.search(query, {"limit": 100})
        #logger.info(f"documents are retrieved: {documents}")
        return documents['hits']
    
    @logger.catch
    def search_mongodb(self, query, X_Session_Id):
        logger.info(f"Session: {X_Session_Id} | query is being searched: {query}")
        documents = self.mongo_db_collection.aggregate([
                {
                        "$search": {
                            "index": "reaction_index",
                            "text": {
                                "query": query,
                                "path": {
                                "wildcard": "*"
                                }
                            }
                            }
                    }, {
                        '$limit': 100
                    }, {
                        "$match": {
                            "$expr": {
                                "$not": {
                                    "$eq": [
                                        "$title", ""
                                    ]
                                }
                            }
                        }
                    }, {
                        '$sort': {
                            '_id': -1
                        }
                    }
                ])
        #logger.info(f"documents are retrieved: {documents}")
        return list(documents)

    @logger.catch
    def retrieve_download_link(self, tweet_id, X_Session_Id):
        logger.info(f"Session: {X_Session_Id} | tweet_id is being asked to download: {tweet_id}")
        # Find the tweet_id's that match the tweet_id
        query = {"id": tweet_id}
        projection = {"_id": 0, "download_link": 1}
        documents = self.mongo_db_collection.find(query, projection)
        return list(documents)[0]['download_link']
    
    @logger.catch
    def retrieve_random_one(self, X_Session_Id):
        logger.info(f"Session: {X_Session_Id} | random video is being retrieved")
        # Find the tweet_id's that match the tweet_id
        #query = {"title": {"$ne": ""}}
        #projection = {"_id": 0, "tweet_id": 1, "download_link": 1}
        #documents = self.mongo_db_collection.find(query, projection)
        #return random.choice([i["tweet_id"] for i in list(documents)])
        document = self.mongo_db_collection.aggregate([
            {
            "$sample": {
            "size": 1
            }
        },
        {
                        "$match": {
                            "$expr": {
                                "$not": {
                                    "$eq": [
                                        "$title", ""
                                    ]
                                }
                            }
                        }
                    },
        ])
        return list(document)[0]['tweet_id']
    
    @logger.catch
    def retrieve_filters(self):
        logger.info(f"retrieve_filters has been called")
        # Find the tweet_id's that match the tweet_id
        query = {"title": {"$ne": ""}}
        projection = {"_id": 0, "title": 0, "content": 0}
        documents = self.mongo_db_collection.find(query, projection)
        ret_dict = {
            "people": set(),
            "tags": set(),
            "program": set(),
            "music": set(),
            "animal": set(),
            "sport": set()
        }
        for doc in documents:
            for k, v in doc.items():
                if k in ret_dict.keys():
                    if isinstance(v, list):
                        ret_dict[k].update(set([i.strip() for i in v if (i.strip() != "") and (i != "-")]))
                    else:
                        if (v.strip() != "") and (v != "-"):
                            ret_dict[k].add(v.strip())
        #logger.info(f"retrieve_filters has been called: {ret_dict}")
        return ret_dict
    
    @logger.catch
    def retrieve_annotation(self, tweet_id, X_Session_Id):
        logger.info(f"Session: {X_Session_Id} | annotation is being retrieved: {tweet_id}")
        # Find the tweet_id's that match the tweet_id
        query = {"tweet_id": tweet_id}
        projection = {"_id": 0, "title": 0}
        documents = self.mongo_db_collection.find(query, projection)
        return list(documents)[0]
    
    @logger.catch
    def retrieve_popular_videos(self, rangeFilter, X_Session_Id):
        logger.info(f"Session: {X_Session_Id} | popular videos are being retrieved: {rangeFilter}")
        # Find the tweet_id's that match the tweet_id
        query = {"title": {"$ne": ""}}
        projection = {"_id": 0, "id": 1}
        sort = [("views", -1)]
        documents = self.mongo_db_collection.find(query, sort=sort, projection=projection).limit(20)
        #logger.info(f"Session: {X_Session_Id} | popular videos are being retrieved: {rangeFilter}")
        return list(documents)
    
    @logger.catch
    def filter_by_status(self, statuses, X_Session_Id):
        logger.info(f"Session: {X_Session_Id} | filter_by_status is being called: {statuses}")
        # Find the tweet_id's that match the tweet_id
        query = {"title": {"$ne": ""}}
        projection = {"_id": 0}
        documents = self.mongo_db_collection.find(query, projection=projection)
        documents = [i for i in documents if i['tweet_id'] in statuses]
        return list(documents)[:9]