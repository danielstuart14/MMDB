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
import itertools

# MongoDB Connection
class connect():
	def __init__(self, server, name):
		print("Initializing client...")
		client = pymongo.MongoClient(server)
		client.admin.command('ismaster')

		if not(name in client.database_names()):
			print("Creating %s database..." % name)
		self.db = client[name]

		if not(self.__collectionExists("root")) or not(self.__collectionExists("index")):
			print("Creating root and index collections...")
			self.__createCollection("root")
			self.__createCollection("index")

		print("Client ready!\n")

	# Collection Functions
	def __getCollections(self):
		return self.db.collection_names()

	def __collectionExists(self, collection):
		if collection in self.__getCollections():
			return True
		return False

	def __createCollection(self, collection):
		self.db.create_collection(collection)

	def __readCollection(self, collection):
		return list(self.db[collection].find({}))

	def __deleteCollection(self, collection):
		if collection in ["index","root"]:
			raise PermissionError("%s can't be deleted!" % collection)
		if not(self.__collectionExists(collection)):
			raise FileNotFoundError("%s doesn't exist!" % collection)
		if self.isAncestor(collection):
			raise FileExistsError("%s has descendants!" % collection)

		self.db[collection].drop()

	def __pathToCollection(self, path):
		if path == "/":
			return "root"
		if path != "index":
			ret = list(self.db["index"].find({"path": path}).limit(1))
			if len(ret) == 1:
				return str(ret[0]["_id"])
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

		return str(insert.inserted_id)

	def readObject(self, obj_id, path):
		collection = self.__pathToCollection(path)
		return self.__readObject(obj_id, collection)

	def __readObject(self, obj_id, collection):
		id = {}
		id["_id"] = ObjectId(obj_id)

		ret = list(self.db[collection].find(id).limit(1))
		if len(ret) == 1:
			return ret[0]
		raise FileNotFoundError(obj_id + " at " + collection + " doesn't exist!")

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
			raise FileExistsError(obj_id + " at " + collection + " has a path!")

		id = {}
		id["_id"] = ObjectId(obj_id)
		self.db[collection].remove(id, True)
	
	def getObjects(self, path):
		if path == "/":
			collection = "root"
		else:
			collection = self.__getChild(path)
			if collection == None:
				return []
		return self.__readCollection(collection)

	def objectExists(self, value, path):
		collection = self.__pathToCollection(path)
		return self.__objectExists(value, collection)

	def __objectExists(self, value, collection):
		if isinstance(value, str):
			if ObjectId.is_valid(value):
				value = {"_id": ObjectId(value)}
			else:
				value = json.loads(value)

		return bool(self.db[collection].count_documents(value, limit = 1))

	def searchObject(self, value, path):
		collection = self.__pathToCollection(path)
		return self.__searchObject(value, collection)

	def __searchObject(self, value, collection):
		if collection == "index":
			raise PermissionError("Index isn't searchable!")
		if isinstance(value, str):
			value = json.loads(value)

		ret = list(self.db[collection].find(value).limit(1))
		if len(ret) == 1:
			return ret[0]
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

	def isAncestor(self, obj_id, path=None):
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

	def __getChild(self, obj_id, path=""):
		if path == "":
			path = obj_id
		else:		
			if not(path.endswith("/")):
				path += "/"
			path += obj_id

		search = {}
		search["path"] = path
		ret = list(self.db["index"].find(search).limit(1))
		if len(ret) == 1:
			return str(ret[0]["_id"])
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
		if self.isAncestor(child):
			raise FileExistsError(obj_id + " at " + path + " has descendants!")
		self.__deleteCollection(child)
		self.__deleteObject(child, "index")

	def getStructure(self, path="/"):
		if not(path.endswith("/")):
			path += "/"

		regex = path.replace("/", "\/")
		regex =  regex + ".*"
		value = {"path": {"$regex": regex}}
		objects = self.db["index"].distinct("path", value)

		if objects:
			objects.sort(key=len)
			objects = [list(obj) for (i, obj) in itertools.groupby(objects, key=len)]
			
			def createStructure(objects, regex=""):
				if regex != "":
					regex = re.compile(regex)
					objects[0] = list(filter(regex.match, objects[0]))
				if not(objects[0]):
					return None
			
				ret = {}
				separator = len(objects[0][0]) - 24

				if len(objects) == 1:
					for obj in objects[0]:
						ret[obj[separator:]] = None
					return ret
				for obj in objects[0]:
					ret[obj[separator:]] = createStructure(objects[1:], obj)
				return ret
			return createStructure(objects)
		return {}