import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import branch
import os

class TreeViewer:
    def __init__(self):
        builder = Gtk.Builder()
        path = os.path.join(os.path.dirname(__file__), "viewer.xml")
        builder.add_from_file(path)
        self.db = None
        self.treeColumn = None
        self.ValColumn = None
        self.ObjColumn = None
        self.TreeModel = None
        self.ValModel = None
        self.ObjModel = None

        self.appWin = builder.get_object("AppWindow")
        self.appWin.connect("destroy", Gtk.main_quit)
        self.appWin.show_all()
        pos = self.appWin.get_position()

        self.conWin = builder.get_object("ConWindow")

        self.valWin = builder.get_object("ValWindow")
        self.valWin.connect("delete-event", self.closeValView)
        self.valWin.move(pos[0] + 420, pos[1])
        
        self.objWin = builder.get_object("ObjWindow")
        self.objWin.connect("delete-event", self.closeObjView)
        self.objWin.move(pos[0] - 420, pos[1])

        self.tree = builder.get_object("TreeView")
        self.valList = builder.get_object("ValView")
        self.objList = builder.get_object("ObjView")
        self.status = builder.get_object("statusIndicator")

        self.refreshButton = builder.get_object("refreshButton")
        self.refreshButton.set_sensitive(False)
        self.refreshButton.connect("clicked", self.refresh)

        builder.get_object("ConnectButton").connect("clicked", self.openConnect)
        builder.get_object("ConApply").connect("clicked", self.conApply)
        builder.get_object("ConClose").connect("clicked", self.conClose)

        self.urlBox = builder.get_object("urlbox")
        self.dbBox = builder.get_object("dbbox")
    
    def closeValView(self, win, *data):
        self.valWin.hide()
        return True
    
    def closeObjView(self, win, *data):
        self.objWin.hide()
        return True

    def conClose(self, button=None):
        self.conWin.hide()

    def conApply(self, button):
        server = self.urlBox.get_text()
        database = self.dbBox.get_text()
        self.connect(server, database)

    def connect(self, server, database):
        print("Trying to connect...")
        try:
            self.db = branch.connect(server, database, True)
        except Exception as e:
            self.conClose()
            self.setStatusRed("Error while connecting", str(e))
        else:
            print("Connected")
            self.refresh()
            self.conClose()

    def refresh(self, button=None):
        try:
            tree = self.db.getStructure()
            if self.treeColumn != None:
                self.treeModel.clear()
            self.jsonToTree(tree)
        except Exception as e:
            self.setStatusRed("Error while refreshing list", str(e))
        else:
            print("List refreshed")
            self.setStatusGreen()

    def setStatusGreen(self):
        self.status.set_from_stock("gtk-yes", -1)
        self.status.set_tooltip_text("Connected")
        self.refreshButton.set_sensitive(True)

    def setStatusRed(self, error, msg):
        print(error)
        print(msg)
        self.status.set_from_stock("gtk-no", -1)
        self.status.set_tooltip_text("Not connected")
        self.refreshButton.set_sensitive(False)

        dialog = Gtk.MessageDialog(self.appWin,
            Gtk.DialogFlags.MODAL,
            Gtk.MessageType.ERROR,
            Gtk.ButtonsType.CLOSE,
            "An error has occurred!")
        dialog.format_secondary_text(error)
        dialog.run()
        dialog.destroy()

    def openConnect(self, button):
        self.conWin.show_all()
    
    def objView(self, object, path, column):
        if self.ObjColumn != None:
            self.ObjModel.clear()
        self.ObjModel = Gtk.ListStore(str)
        itertree = self.treeModel.get_iter(path)
        
        if self.treeModel.get_value(itertree, 0) == "/":
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
        except Exception as e:
            self.objWin.hide()
            self.setStatusRed("Error while obtaining objects", str(e))
            return
        
        if not(path.endswith("/")):
            path += "/"
        self.path = path + obj_id
        for obj in children:
            obj_id = str(obj["_id"])
            self.ObjModel.append([obj_id])

        self.objList.set_model(self.ObjModel)
        if self.ObjColumn == None:
            render = Gtk.CellRendererText()
            self.ObjColumn = Gtk.TreeViewColumn("Object IDs", render, text=0)
            self.objList.append_column(self.ObjColumn)
            self.objList.connect("row-activated", self.valView)
        self.objWin.show_all()
    
    def valView(self, obj, path, column):
        if self.ValColumn != None:
            self.ValModel.clear()
        self.ValModel = Gtk.ListStore(str)
        
        iterpath = self.ObjModel.get_iter(path)
        obj_id = self.ObjModel.get_value(iterpath, 0)
        
        try:
            json = self.db.readObject(obj_id, self.path)
        except Exception as e:
            self.valWin.hide()
            self.setStatusRed("Error while obtaining object", str(e))
            return

        for key in json:
            val = json[key]
            if not(isinstance(val, str)):
                val = str(val)
            self.ValModel.append([key + ": " + val])

        self.valList.set_model(self.ValModel)
        if self.ValColumn == None:
            render = Gtk.CellRendererText()
            self.ValColumn = Gtk.TreeViewColumn("Values", render, text=0)
            self.valList.append_column(self.ValColumn)
        self.valWin.show_all()

    def createPath(self, path):
        itertree = self.treeModel.get_iter(path)
        dbPath = self.treeModel.get_value(itertree, 0)
        while True:
            path.up()
            if str(path) != "":
                itertree = self.treeModel.get_iter(path)
                upperPath = self.treeModel.get_value(itertree, 0)
                if upperPath == "/":
                    dbPath = "/" + dbPath
                    break
                dbPath = upperPath + "/" + dbPath
        return dbPath

    def jsonToTree(self, json):
        self.treeModel = Gtk.TreeStore(str)
        root = self.appendModel("/")
        self.jsonToModel(json, root)

        self.tree.set_model(self.treeModel)
        if self.treeColumn == None:
            cellRenderer = Gtk.CellRendererText()
            self.treeColumn = Gtk.TreeViewColumn("Paths", cellRenderer, text=0)
            self.tree.append_column(self.treeColumn)
            self.tree.connect("row-activated", self.objView)

    def appendModel(self, value, parent=None):
        return self.treeModel.append(parent,[value])

    def jsonToModel(self, json, parent=None):
        for i in list(json):
            newIter = self.appendModel(i, parent)
            if json[i]:
                    self.jsonToModel(json[i], newIter)

app = TreeViewer()
Gtk.main()