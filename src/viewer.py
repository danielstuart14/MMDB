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
        self.server = ""
        self.database = ""
        self.column = None

        win = builder.get_object("AppWindow")
        win.connect("destroy", Gtk.main_quit)
        win.show_all()

        self.conWin = builder.get_object("ConWindow")
        self.errorWin = builder.get_object("ErrorWindow")

        self.tree = builder.get_object("TreeView")
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
            tree = self.db.getDescendants()
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
            self.tree.remove_column(self.column)

    def jsonToTree(self, json):
        self.model = Gtk.TreeStore(str)
        self.jsonToModel(json)

        self.tree.set_model(self.model)
        cellRenderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn("Objects", cellRenderer, text=0)
        self.tree.append_column(self.column)
    
    def appendModel(self, value, parent=None):
        return self.model.append(parent,[value])
    
    def jsonToModel(self, json, parent=None):
        for i in list(json):
            newIter = self.appendModel(i, parent)
            if isinstance(json[i], dict):
                    self.jsonToModel(json[i], newIter)

app = TreeViewer()
Gtk.main()