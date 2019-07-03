"""
BranchDB - A Multilevel Database

A layer for MongoDB that behaves as a multilevel/hierarchical database

Author: Daniel P. Stuart

This software is licensed under Apache License 2.0
"""
import pymongo
import json
from bson.objectid import ObjectId

# MongoDB Connection
class connect():
	def __init__(self, server, name):
		print("Initializing client...")
		client = pymongo.MongoClient(server)
		if not(name in client.database_names()):
			print("Creating %s database..." % name)
		self.db = client[name]
		if not(self.collectionExists("root")) or not(self.collectionExists("index")):
			print("Creating root and index collections...")
			self.createCollection("root")
			self.createCollection("index")
		self.collection = "root"
		print("Client ready!\n")
	
	# Collection Functions
	def getCollections(self):
		return self.db.collection_names()
	
	def collectionExists(self, collection):
		if collection in self.getCollections():
			return True
		return False

	def createCollection(self, collection):
		self.db.create_collection(collection)
	
	def readCollection(self, collection=""):
		if collection == "":
			collection = self.collection
		return list(self.db[collection].find({}))
	
	def deleteCollection(self, collection=""):
		if collection == "":
			collection = self.collection
		if collection in ["index","root"]:
			raise PermissionError("%s can't be deleted!" % collection)
		if self.isAncestor(collection):
			raise FileExistsError("%s has descendants!" % collection)
		self.db[collection].drop()
	
	def selectCollection(self, collection):
		self.collection = collection
	
	# Object Functions
	def createObject(self, value, collection=""):
		if collection == "":
			collection = self.collection
		if isinstance(value, str):
			value = json.loads(value)
		
		value = self.db[collection].insert_one(value)
		return str(value.inserted_id)

	def readObject(self, obj_id, collection=""):
		if collection == "":
			collection = self.collection
		
		id = {}
		id["_id"] = ObjectId(obj_id)
		if not(self.objectExists(id, collection)):
			raise FileNotFoundError(obj_id + " at " + collection + " doesn't exist!")
		return self.db[collection].find(id).limit(1)[0]

	def updateObject(self, obj_id, value, collection=""):
		if collection == "":
			collection = self.collection
		id = {}
		id["_id"] = ObjectId(obj_id)
		
		changes = {}
		if isinstance(value, str):
			changes["$set"] = json.loads(value)
		else:
			changes["$set"] = value
		self.db[collection].update(id,changes)

	def deleteObject(self, obj_id, collection=""):
		if collection == "":
			collection = self.collection
		if collection != "index" and self.hasChild(obj_id, collection):
			raise FileExistsError(obj_id + " at " + collection + " has a child!")

		id = {}
		id["_id"] = ObjectId(obj_id)
		self.db[collection].remove(id, True)
	
	def objectExists(self, value, collection=""):
		if collection == "":
			collection = self.collection
		if isinstance(value, str):
			if ObjectId.is_valid(value):
				value = {"_id": ObjectId(value)}
			else:
				value = json.loads(value)
		return bool(self.db[collection].count_documents(value, limit = 1))
	
	def searchObject(self, value, collection=""):
		if collection == "":
			collection = self.collection
		if isinstance(value, str):
			value = json.loads(value)

		if self.objectExists(value, collection):
			return self.db[collection].find(value).limit(1)[0]
		return None
	
	# Index Functions
	def getPath(self, collection=""):
		if collection == "":
			collection = self.collection
		if collection == "root":
			return "/"

		parent = self.readObject(collection, "index")
		return parent["path"]

	def hasChild(self, obj_id, collection=""):
		if collection == "":
			collection = self.collection
		value = {}
		path = self.getPath(collection)

		if not(path.endswith("/")):
			path += "/"
		value["path"] = path + obj_id
		return self.objectExists(value, "index")
	
	def isAncestor(self, obj_id, collection=""):
		if self.collectionExists(obj_id):
			path = self.getPath(obj_id)
		else:
			if collection == "":
				collection = self.collection
			
			path = self.getChild(obj_id, collection)
			if path == None:
				return False
			path = self.getPath(path)
		
		path += "/"
		path = path.replace("/", "\/")
		value = {"path": {"$regex": path}}
		return self.objectExists(value, "index")

	def createChild(self, obj_id, collection=""):
		if collection == "":
			collection = self.collection
		value = {}
		path = self.getPath(collection)

		if not(path.endswith("/")):
			path += "/"
		value["path"] = path + obj_id

		if self.objectExists(value, "index"):
			raise FileExistsError("%s already has a child!" % (path + obj_id))
		id = self.createObject(value, "index")
		self.createCollection(str(id))
		return str(id)
	
	def getParent(self, collection=""):
		if collection == "":
			collection = self.collection
		path = self.getPath(collection)
		path = path.split("/")
		return path[len(path) - 1]

	def getChild(self, obj_id, collection=""):
		if collection == "":
			collection = self.collection		
		path = self.getPath(collection)
		if not(path.endswith("/")):
			path += "/"
		path += obj_id

		search = {}
		search["path"] = path
		if self.objectExists(search, "index"):
			return str(self.db["index"].find(search).limit(1)[0]["_id"])
		return None

	def deleteChild(self, obj_id, collection=""):
		if collection == "":
			collection = self.collection
		
		child = self.getChild(obj_id, collection)
		if child == None:
			raise FileNotFoundError(obj_id + " at " + collection + " doesn't have a child!")
		if self.isAncestor(child):
			raise FileExistsError(obj_id + " at " + collection + " has descendants!")
		self.deleteCollection(child)
		self.deleteObject(child, "index")
