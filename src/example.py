"""
BranchDB - A Multilevel Database

Example File

Author: Daniel P. Stuart
"""
import branch
import time
import json

start = time.time()
server = "" # Insert here your server URL
name = "test" # Database name (It'll be created by BranchDB)

db = branch.connect(server, name, True) # Starts connection with cache enabled

# 1 - Creates an object/document
obj_1 = db.createObject('{"Name": "Test 1"}', "/")
# 2 - Creates a path for obj_1
path_1 = db.createPath(obj_1, "/")
# 3 - Creates a new object/document inside obj_1
obj_2 = db.createObject('{"Name": "Test 2"}', path_1)
# 4 - Creates a path for obj_2
path_2 = db.createPath(obj_2, path_1)
# 5 - Creates a new object/document inside obj_2
obj_3 = db.createObject('{"Name": "Test 3"}', path_2)

# 6 - Prints data in obj_3
print(db.readObject(obj_3, path_2))
# 7 - Updates obj_3 and prints it again
db.updateObject('{"Name": "Test 4"}', obj_3, path_2)
print(db.readObject(obj_3, path_2))
# 8 - Checks if there is an object with name Test 4 at obj_2
if db.searchObject('{"Name": "Test 4"}', path_2) != None:
    print("Object with name Test 4 exists at obj_2")
# 9 - Deletes obj_3
db.deleteObject(obj_3, path_2)

# 10 - Checks if obj_1 and obj_2 are ancestors of something
if db.isAncestor(obj_1, "/"):
    print("object obj_1 at root collection is an ancestor")
if not(db.isAncestor(obj_2, path_1)):
    print("Object obj_2 is not an ancestor") 

# 11 - Deletes obj_2 path (path_2)
db.deletePath(obj_2, path_1)

# 12 - Print ids and paths
if db.hasPath(obj_1, "/"):
    print(obj_1 + " has path : " + db.getPath(obj_1, "/"))
if not(db.hasPath(obj_2, path_1)):
    print(obj_2 + " doesn't have a path!")

# 13 - Prints database structure
print(json.dumps(db.getDescendants(), sort_keys=True, indent=4))

# 14 - Print time needed to execute all operations
finish = time.time()
print("Time from start to finish: %f seconds" % (finish - start))