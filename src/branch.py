"""
BranchDB - A Multilevel Database

A layer for MongoDB that behaves as a multilevel/hierarchical database

Author: Daniel P. Stuart

This software is licensed under Apache License 2.0
"""
import pymongo
import json
from bson.objectid import ObjectId
import re

# MongoDB Connection
class connect():
	def __init__(self, server, name, cache=False):
		print("Initializing client...")
		client = pymongo.MongoClient(server)
		client.admin.command('ismaster')

		if not(name in client.database_names()):
			print("Creating %s database..." % name)
		self.db = client[name]
		self.cache = False
		self.cacheHang = False

		if not(self.__collectionExists("root")) or not(self.__collectionExists("index")):
			print("Creating root and index collections...")
			self.__createCollection("root")
			self.__createCollection("index")

		if cache:
			self.cacheEnable()
		print("Client ready!\n")

	# Collection Functions
	def __getCollections(self):
		if self.cache:
			return self.collectionNames
		return self.db.collection_names()

	def __collectionExists(self, collection):
		if collection in self.__getCollections():
			return True
		return False

	def __createCollection(self, collection):
		self.db.create_collection(collection)
		if self.cache:
			self.collectionNames.append(collection)

	def __readCollection(self, collection):
		return list(self.db[collection].find({}))

	def __deleteCollection(self, collection):
		if collection in ["index","root"]:
			raise PermissionError("%s can't be deleted!" % collection)
		if not(self.__collectionExists(collection)):
			raise FileNotFoundError("%s doesn't exist!" % collection)
		if self.__isAncestor(collection):
			raise FileExistsError("%s has descendants!" % collection)

		self.db[collection].drop()
		if self.cache:
			self.collectionNames.remove(collection)

	def __pathToCollection(self, path):
		if path == "/":
			return "root"
		if path != "index":
			if self.__objectExists({"path": path}, "index"):
				if self.cache:
					return list(self.index.keys())[list(self.index.values()).index(path)]
				return str(self.db["index"].find({"path": path}).limit(1)[0]["_id"])
			raise FileNotFoundError("Path %s doesn't exist!" % path)
		return path

	# Object Functions
	def createObject(self, value, path):
		collection = self.__pathToCollection(path)
		return self.__createObject(value, collection)

	def __createObject(self, value, collection):
		if isinstance(value, str):
			value = json.loads(value)

		insert = self.db[collection].insert_one(value)

		if collection == "index" and self.cache:
			self.index[str(insert.inserted_id)] = value["path"]
		return str(insert.inserted_id)

	def readObject(self, obj_id, path):
		collection = self.__pathToCollection(path)
		return self.__readObject(obj_id, collection)

	def __readObject(self, obj_id, collection):
		id = {}
		id["_id"] = ObjectId(obj_id)
		if not(self.__objectExists(id, collection)):
			raise FileNotFoundError(obj_id + " at " + collection + " doesn't exist!")

		if collection == "index" and self.cache:
			id["path"] = self.index[obj_id]
			return id
		return self.db[collection].find(id).limit(1)[0]

	def updateObject(self, value, obj_id, path):
		collection = self.__pathToCollection(path)
		self.__updateObject(value, obj_id, collection)

	def __updateObject(self, value, obj_id, collection):
		if collection == "index":
			raise PermissionError("Index can't have its objects updated!")

		id = {}
		id["_id"] = ObjectId(obj_id)

		changes = {}
		if isinstance(value, str):
			changes["$set"] = json.loads(value)
		else:
			changes["$set"] = value
		self.db[collection].update(id,changes)

	def deleteObject(self, obj_id, path):
		collection = self.__pathToCollection(path)
		self.__deleteObject(obj_id, collection)

	def __deleteObject(self, obj_id, collection):
		if not(self.__objectExists(obj_id, collection)):
			raise FileNotFoundError(obj_id + " at " + collection + " doesn't exist!")
		if collection != "index" and self.hasPath(obj_id, collection):
			raise FileExistsError(obj_id + " at " + collection + " has a child!")

		id = {}
		id["_id"] = ObjectId(obj_id)
		self.db[collection].remove(id, True)
		if collection == "index" and self.cache:
			del self.index[obj_id]

	def objectExists(self, value, path):
		collection = self.__pathToCollection(path)
		return self.__objectExists(value, collection)

	def __objectExists(self, value, collection):
		if isinstance(value, str):
			if ObjectId.is_valid(value):
				if collection == "index" and self.cache:
					return value in self.index
				value = {"_id": ObjectId(value)}
			else:
				value = json.loads(value)

		if collection == "index" and self.cache:
			if "_id" in value:
				return str(value["_id"]) in self.index
			if isinstance(value["path"], str):
				return value["path"] in self.index.values()
			if "$regex" in value["path"]:
				regex = re.compile(value["path"]["$regex"])
				if any(regex.match(path) for path in self.index.values()):
					return True
				return False
		return bool(self.db[collection].count_documents(value, limit = 1))

	def searchObject(self, value, path):
		collection = self.__pathToCollection(path)
		return self.__searchObject(value, collection)

	def __searchObject(self, value, collection):
		if collection == "index":
			raise PermissionError("Index isn't searchable!")
		if isinstance(value, str):
			value = json.loads(value)

		if self.__objectExists(value, collection):
			return self.db[collection].find(value).limit(1)[0]
		return None

	# Index Functions
	def getPath(self, obj_id, path):
		if not(path.endswith("/")):
			path += "/"
		return (path + obj_id)

	def __getPath(self, collection):
		if collection == "root":
			return "/"

		parent = self.__readObject(collection, "index")
		return parent["path"]

	def hasPath(self, obj_id, path):
		value = {}

		if not(path.endswith("/")):
			path += "/"
		value["path"] = path + obj_id
		return self.__objectExists(value, "index")

	def isAncestor(self, obj_id, path):
		return self.__isAncestor(obj_id, path)

	def __isAncestor(self, obj_id, path=None):
		if path == None and self.__collectionExists(obj_id):
			path = self.__getPath(obj_id)
		else:
			path = self.__getChild(obj_id, path)
			if path == None:
				return False
			path = self.__getPath(path)

		path += "/"
		path = path.replace("/", "\/")
		value = {"path": {"$regex": path}}
		return self.__objectExists(value, "index")

	def createPath(self, obj_id, path):
		value = {}

		if not(path.endswith("/")):
			path += "/"
		value["path"] = path + obj_id

		if self.__objectExists(value, "index"):
			raise FileExistsError("%s already has a child!" % value["path"])
		id = self.__createObject(value, "index")
		self.__createCollection(str(id))
		return value["path"]

	def __getChild(self, obj_id, path):		
		if not(path.endswith("/")):
			path += "/"
		path += obj_id

		search = {}
		search["path"] = path
		if self.__objectExists(search, "index"):
			if self.cache:
				return list(self.index.keys())[list(self.index.values()).index(path)]
			return str(self.db["index"].find(search).limit(1)[0]["_id"])
		return None

	def getChildren(self, obj_id, path):
		collection = self.__getChild(obj_id, path)
		if collection == None:
			return []
		return self.__readCollection(collection)

	def deletePath(self, obj_id, path):
		child = self.__getChild(obj_id, path)
		if child == None:
			raise FileNotFoundError(obj_id + " at " + path + " doesn't have a child!")
		if self.__isAncestor(child):
			raise FileExistsError(obj_id + " at " + path + " has descendants!")
		self.__deleteCollection(child)
		self.__deleteObject(child, "index")

	def getDescendants(self, obj_id=None, path=None):
		ret = {}
		if obj_id == None and path == None:
			for obj in self.__readCollection("root"):
				id = str(obj["_id"])
				ret[id] = self.getDescendants(id, "/")
			return ret

		if not(self.hasPath(obj_id, path)):
			return None

		objects = self.getChildren(obj_id, path)
		if not objects:
			return None

		if not(path.endswith("/")):
			path += "/"

		for obj in objects:
			id = str(obj["_id"])
			ret[id] = self.getDescendants(id, path + obj_id)
		return ret	

	# Cache Functions
	def __getCache(self):
		try:
			collectionNames = self.db.collection_names()
			index = {}
			for obj in self.db["index"].find():
				index[str(obj["_id"])] = obj["path"]
		except Exception as e:
			raise EnvironmentError(type(e).__name__)
		else:
			self.collectionNames = collectionNames
			self.index = index

	def waitCache(self):
		if self.cacheHang:
			print("Waiting previous cache operation to be finished...")
			while self.cacheHang:
				pass

	def cacheEnable(self):
		self.waitCache()
		if self.cache:
			raise AssertionError("Cache is already enabled!")
		print("Caching collections and index...")
		self.cacheHang = True

		try:
			self.__getCache()
		except Exception as e:
			self.cacheHang = False
			raise EnvironmentError("%s exception was caught while enabling cache!" % str(e))
		self.cache = True
		self.cacheHang = False

	def cacheDisable(self):
		self.waitCache()
		if not(self.cache):
			raise AssertionError("Cache is already disabled!")
		print("Disabling cache...")
		self.cache = False

	def cacheUpdate(self):
		self.waitCache()
		if not(self.cache):
			raise AssertionError("Cache must first be enabled!")
		print("Updating cache...")
		self.cacheHang = True
		self.cache = False

		try:
			self.__getCache()
		except Exception as e:
			self.cacheHang = False
			raise EnvironmentError("%s exception was caught while updating cache!" % str(e))
		self.cache = True
		self.cacheHang = False