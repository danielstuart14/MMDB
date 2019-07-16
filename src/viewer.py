import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import branch
import os

class TreeViewer:
    def __init__(self):
        builder = Gtk.Builder()
        path = os.path.join(os.path.dirname(__file__), "viewer.xml")
        builder.add_from_file(path)
        self.db = None
        self.column = None
        self.listColumn = None
        self.listmodel = None
        self.listPathColumn = None
        self.listPathModel = None

        win = builder.get_object("AppWindow")
        win.connect("destroy", Gtk.main_quit)
        win.show_all()

        self.conWin = builder.get_object("ConWindow")
        self.errorWin = builder.get_object("ErrorWindow")

        self.objWin = builder.get_object("ObjWindow")
        self.objWin.connect('delete-event', self.closeObjView)
        
        self.pathWin = builder.get_object("PathWindow")
        self.pathWin.connect('delete-event', self.closePathView)

        self.tree = builder.get_object("TreeView")
        self.list = builder.get_object("ListView")
        self.pathList = builder.get_object("ListViewPath")
        self.status = builder.get_object("statusIndicator")

        self.refreshButton = builder.get_object("refreshButton")
        self.refreshButton.set_sensitive(False)
        self.refreshButton.connect("clicked", self.refresh)

        builder.get_object("ConnectButton").connect("clicked", self.openConnect)
        builder.get_object("ConApply").connect("clicked", self.conApply)
        builder.get_object("ConClose").connect("clicked", self.conClose)
        builder.get_object("ErrorClose").connect("clicked", self.errorClose)

        self.urlBox = builder.get_object("urlbox")
        self.dbBox = builder.get_object("dbbox")
    
    def errorClose(self, button=None):
        self.errorWin.hide()
    
    def closeObjView(self, win, *data):
        self.objWin.hide()
        return True
    
    def closePathView(self, win, *data):
        self.pathWin.hide()
        return True

    def conClose(self, button=None):
        self.conWin.hide()

    def conApply(self, button):
        server = self.urlBox.get_text()
        database = self.dbBox.get_text()
        self.connect(server, database)
        self.conClose()

    def connect(self, server, database):
        print("Trying to connect...")
        try:
            self.db = branch.connect(server, database, True)
        except:
            print("Error while connecting")
            self.setStatusRed()
        else:
            print("Connected")
            self.refresh()

    def refresh(self, button=None):
        try:
            tree = self.db.getStructure()
            self.removeColumn()
            self.jsonToTree(tree)
        except:
            print("Error while refreshing list")
            self.setStatusRed()
        else:
            print("List refreshed")
            self.setStatusGreen()

    def setStatusGreen(self):
        self.status.set_from_stock("gtk-yes", -1)
        self.status.set_tooltip_text("Connected")
        self.refreshButton.set_sensitive(True)

    def setStatusRed(self):
        self.status.set_from_stock("gtk-no", -1)
        self.status.set_tooltip_text("Not connected")
        self.refreshButton.set_sensitive(False)
        self.errorWin.show_all()

    def openConnect(self, button):
        self.conWin.show_all()

    def removeColumn(self):
        if self.column != None:
            self.model.clear()
    
    def listViewObj(self, object, path, column):
        if self.listPathColumn != None:
            self.listPathModel.clear()
        self.listPathModel = Gtk.ListStore(str)
        itertree = self.model.get_iter(path)
        
        if self.model.get_value(itertree, 0) == "/":
            obj_id = ""
            path = "/"
        else:
            path = self.createPath(path)
            path = path.split("/")
            obj_id = path[-1:]
            obj_id = "/".join(obj_id)
            path = path[:-1]
            path = "/".join(path)
            if path == "":
                path = "/"
        
        try:
            if obj_id != "":
                children = list(self.db.getChildren(obj_id, path))
            else:
                children = list(self.db.getObjects(path))
        except:
            print("Error while obtaining objects")
            self.pathWin.hide()
            self.setStatusRed()
            return
        
        if not(path.endswith("/")):
            path += "/"
        self.path = path + obj_id
        for obj in children:
            obj_id = str(obj["_id"])
            self.listPathModel.append([obj_id])

        self.pathList.set_model(self.listPathModel)
        if self.listPathColumn == None:
            render = Gtk.CellRendererText()
            self.listPathColumn = Gtk.TreeViewColumn("Object IDs", render, text=0)
            self.pathList.append_column(self.listPathColumn)
            self.pathList.connect('row-activated', self.listView)
        self.pathWin.show_all()
        
    
    def listView(self, obj, path, column):
        if self.listColumn != None:
            self.listmodel.clear()
        self.listmodel = Gtk.ListStore(str, str)
        
        iterpath = self.listPathModel.get_iter(path)
        obj_id = self.listPathModel.get_value(iterpath, 0)
        print(obj_id)
        print(self.path)
        
        try:
            json = self.db.readObject(obj_id, self.path)
        except:
            print("Error while obtaining object")
            self.objWin.hide()
            self.setStatusRed()
            return

        for key in json:
            val = json[key]
            if not(isinstance(val, str)):
                val = str(val)
            self.listmodel.append([key, val])

        self.list.set_model(self.listmodel)
        if self.listColumn == None:
            self.listColumn = Gtk.TreeViewColumn("Keys and Values")
            key = Gtk.CellRendererText()
            val = Gtk.CellRendererText()
            self.listColumn.pack_start(key, True)
            self.listColumn.pack_start(val, True)
            self.listColumn.add_attribute(key, "text", 0)
            self.listColumn.add_attribute(val, "text", 1)
            self.list.append_column(self.listColumn)
        self.objWin.show_all()

    def createPath(self, path):
        itertree = self.model.get_iter(path)
        dbPath = self.model.get_value(itertree, 0)
        while True:
            path.up()
            if str(path) != "":
                itertree = self.model.get_iter(path)
                upperPath = self.model.get_value(itertree, 0)
                if upperPath == "/":
                    dbPath = "/" + dbPath
                    break
                dbPath = upperPath + "/" + dbPath
        return dbPath

    def jsonToTree(self, json):
        self.model = Gtk.TreeStore(str)
        root = self.appendModel("/")
        self.jsonToModel(json, root)

        self.tree.set_model(self.model)
        if self.column == None:
            cellRenderer = Gtk.CellRendererText()
            self.column = Gtk.TreeViewColumn("Paths", cellRenderer, text=0)
            self.tree.append_column(self.column)
            self.tree.connect('row-activated', self.listViewObj)

    def appendModel(self, value, parent=None):
        return self.model.append(parent,[value])

    def jsonToModel(self, json, parent=None):
        for i in list(json):
            newIter = self.appendModel(i, parent)
            if json[i]:
                    self.jsonToModel(json[i], newIter)

app = TreeViewer()
Gtk.main()