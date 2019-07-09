"""
BranchDB - A Multilevel Database

Example File

Author: Daniel P. Stuart
"""
import branch
import json
import time

start = time.time()
server = "" # Insert here your server URL
name = "test" # Database name (It'll be created by BranchDB)

db = branch.connect(server, name, True) # Starts connection with cache enabled

# 1 - Creates an object/document
id = db.createObject('{"Name": "Test 1"}')
# 2 - Creates an affiliated collection 
id2 = db.createChild(id)
# 3 - Creates a new object/document inside collection id2
id3 = db.createObject('{"Name": "Test 2"}', id2)
# 4 - Creates an affiliated collection 
id4 = db.createChild(id3, id2)
# 5 - Creates a new object/document inside collection id4
id5 = db.createObject('{"Name": "Test 3"}', id4)

# 6 - Gets id3's child and compares if equal to id4
if db.getChild(id3, id2) == id4:
    print(" id3's child is equal to id4")

# 7 - Prints data in id5
print(db.readObject(id5, id4))
# 8 - Updates id5 and prints it again
db.updateObject(id5, '{"Name": "Test 4"}', id4)
print(db.readObject(id5, id4))
# 9 - Checks if there is an object with name Test 4 at id4
if db.searchObject('{"Name": "Test 4"}',id4) != None:
    print("Object with name Test 4 exists at id4")
# 10 - Deletes id5
db.deleteObject(id5, id4)

# 11 - Checks if id, id2, id3 and id4 are ancestors of something
if db.isAncestor(id):
    print("object id at root collection is an ancestor")
if db.isAncestor(id2):
    print("collection id2 is an ancestor")
if not(db.isAncestor(id3, id2)):
    print("Object id3 is not an ancestor") 
if not(db.isAncestor(id4)):
    print("collection id4 is not an ancestor") 
# 12 - Prints id4 path
print(db.getPath(id4))

# 13 - Deletes id3 child (id4)
db.deleteChild(id3, id2)

# 14 - Prints all collections
print(db.getCollections())

# 15 - Print all ids
print("id is " + id)
print("id2 is " + id2)
print("id3 is " + id3)
print("id4 is " + id4)
print("id5 is " + id5)

# 16 - Print time needed to execute all operations
finish = time.time()
print("Time from start to finish: %f seconds" % (finish - start))