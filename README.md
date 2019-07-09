![BranchDB](/assets/banner.png?raw=true)
# BranchDB - A Multilevel Database
<p>This is a layer for MongoDB, written in Python 3, that behaves as a multilevel/hierarchical database.</p>
<h3> WARNING: Currently at alpha state! It should NOT be used to handle anything important!</h3>
<p>BranchDB works by assigning collections to objects (documents), creating, this way, affiliations between these elements. In other words, a document can contain not only JSON values, but also a whole collection. Furthermore, this creates a parent-child relationship between object and collection that can be used to mimic the behavior of an hierarchical database.</p>

# How It Works
<H3>Indexing</H3>
<p>Indexing is the most important element of BranchDB, it is through the index that the relationships are established. In its current form, a collection named "index" holds a document for each affiliation that is created, with its ObjectId and path.</p>
<H3>Identification</h3>
<p>The ObjectId, created by MongoDB when adding a document to the index collection, is used to name the collection that will be created as a child. This ensures that there will never be two collections with the same name, as MongoDB guarantees that two automatically generated ObjectIds, in the same collection, will never be equal.</p>
<H3>Paths</H3>
<p>Every collection on BranchDB has its own path, this allows collections to remember who are their ancestors. Moreover, a path is made from the ObjectIds of each ancestor of the element, going from the root directory to the element's parent.</p>

# Usage
<p>All the documentation will be added after completion of the missing essential features, which are stated below. For the time being, <b>example.py</b> can be used to understand the basic functionality of BranchDB.</p>

# Missing Essential Features
- <b>Users and permissions</b>: the whole reason this was created, it should allow each permission group to have a certain kind of access to the multiple levels of the database.
- <b>Queries with multiple actions</b>: right now, changes to the database are done one at a time. Example: you can't update more than one document with a single command.
- <b>Delete ancestors</b>: in the current implementation, elements can only be deleted after their descendants have been removed.
- <b>Sync local cache</b>: cache, currently, won't be updated if any change to index/collections is done remotely.
- <b>Obtain affiliations as JSON</b>: should assemble and return a JSON representation of the affiliations.
- <b>Add own exceptions</b>: even though python's own exceptions fit well, it would be better if BranchDB exceptions were unique to it. This is an essential feature since it would change the way you interact with the module.

</br>
<p>Mongo, MongoDB, and the MongoDB leaf logo are registered trademarks of MongoDB, Inc.</p>