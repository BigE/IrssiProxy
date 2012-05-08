#!/usr/bin/env python
# vim: set fileencoding=utf8 :

import pygtk
pygtk.require('2.0')
import gobject
import gtk
import pynotify
import os.path
import re
import socket
import threading

__author__="Eric Gach <eric@php-oop.net>"
__date__ ="$Jan 13, 2012 12:47:17 PM$"
__version__ = "0.1-dev"

class IrssiProxy(gtk.Window):
	"""
	TODO: Still need to implement away/back feature.
	"""
	def __init__(self):
		super(IrssiProxy, self).__init__(gtk.WINDOW_TOPLEVEL)
		pynotify.init("IrssiProxy")
		self.set_title("IrssiProxy Configuration")
		self.set_default_size(400, 300)
		self._icon = os.path.realpath(os.path.dirname(__file__)+"/resources/65704.png")
		self._initStatusIcon()
		self._initLayout()
		self._irc = None
		self.connect("delete-event", self.delete)
		self.connect("destroy", self.destroy)
		self.set_icon_from_file(self._icon)
		self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		self.show()

	def addNetwork(self, widget, data=None):
		addNetwork = gtk.Dialog("Add Network", self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

		#host
		hBoxHost = gtk.HBox()
		labelHost = gtk.Label("Host")
		hBoxHost.pack_start(labelHost, False, False, 10)
		entryHost = gtk.Entry()
		hBoxHost.pack_end(entryHost, True, True, 10)
		addNetwork.vbox.pack_start(hBoxHost, False, False, 10)

		#port
		hBoxPort = gtk.HBox()
		labelPort = gtk.Label("Port")
		hBoxPort.pack_start(labelPort, False, False, 10)
		entryPort = gtk.Entry()
		entryPort.set_text('6667')
		entryPort.set_width_chars(10)
		hBoxPort.pack_start(entryPort, False, False, 10)
		addNetwork.vbox.pack_start(hBoxPort, False, False, 10)

		#password
		hBoxPass = gtk.HBox()
		labelPass = gtk.Label("Password")
		hBoxPass.pack_start(labelPass, False, False, 10)
		entryPass = gtk.Entry()
		entryPass.set_visibility(False)
		hBoxPass.pack_end(entryPass, True, True, 10)
		addNetwork.vbox.pack_start(hBoxPass, False, False, 10)

		addNetwork.show_all()
		r = addNetwork.run()
		if (r == gtk.RESPONSE_ACCEPT):
			print "so I should add the network %s with the port %i and password %s? OK!" % (entryHost.get_text(), int(entryPort.get_text()), entryPass.get_text())
		addNetwork.destroy()

	def delete(self, widget, data=None):
		self.hide()
		# Stop the window from being deleted - since we have a tray icon
		return True

	def destroy(self, widget, data=None):
		if self._irc != None:
			self._irc.stop()
		gtk.main_quit()

	def on_connect(self, widget, data=None):
		self._irc = IrssiProxyConnection(self, self._host.get_text(), self._port.get_text(), self._password.get_text())
		self._irc.start()

	def on_disconnect(self, widget, data=None):
		self._irc.stop()
		self._irc = None

	def popup_statusIcon_menu(self, status_icon, button, activate_time, *args):
		menu = gtk.Menu()
		about = gtk.MenuItem("About")
		about.connect("activate", self.show_about)
		menu.append(about)
		quit = gtk.MenuItem("Quit")
		quit.connect("activate", self.destroy)
		menu.append(quit)
		menu.show_all()
		menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, status_icon)

	def push_msg(self, message):
		pass

	def show(self, icon = None):
		super(IrssiProxy, self).show()

	def show_about(self, widget, data=None):
		about_dialog = gtk.AboutDialog()
		about_dialog.set_destroy_with_parent(True)
		about_dialog.set_name("IrssiProxy Notification")
		about_dialog.set_version(__version__)
		about_dialog.set_authors([__author__])
		about_dialog.run()
		about_dialog.destroy()

	def _checkRegex(self, entry):
		regex = entry.get_text()
		print "checking: %s" % (regex)
		try:
			re.compile(regex)
			entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
		except re.error, e:
			print e
			entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('red'))

	def _initColumns(self, treeView):
		renderPixbuf = gtk.CellRendererPixbuf()
		column = gtk.TreeViewColumn("Connected", renderPixbuf, pixbuf=0)
		column.set_sort_column_id(0)
		treeView.append_column(column)

		renderText = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Irssi Host/Port", renderText, text=1)
		column.set_sort_column_id(1)
		treeView.append_column(column)

	def _initLayout(self):
		# Main Box
		mainVBox = gtk.VBox(False, 20)
		# Servers box
		sw = gtk.ScrolledWindow()
		sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		mainVBox.pack_start(sw, True, True, 0)

		# Add buttons for interacting with the servers
		buttonHBox = gtk.HBox(False, 20)
		remove = gtk.Button("Delete", gtk.STOCK_DELETE)
		buttonHBox.pack_end(remove, False, False, 10)
		add = gtk.Button("Add", gtk.STOCK_ADD)
		add.connect("clicked", self.addNetwork)
		buttonHBox.pack_end(add, False, False, 10)
		mainVBox.pack_end(buttonHBox, False, False, 10)

		# Setup the server list
		servers = self._initModel()
		treeView = gtk.TreeView(servers)
		treeView.set_rules_hint(True)
		sw.add(treeView)
		self._initColumns(treeView)

		mainVBox.show_all()
		remove.hide()
		self.add(mainVBox)

	def _initStatusIcon(self):
		statusIcon = gtk.status_icon_new_from_file(self._icon)
		statusIcon.set_title("IrssiProxy")
		statusIcon.connect("popup-menu", self.popup_statusIcon_menu)
		statusIcon.connect("activate", self.show)
		statusIcon.set_tooltip('IrssiProxy Notifications')

	def _initModel(self):
		self._connNo = self.render_icon(gtk.STOCK_NO, gtk.ICON_SIZE_BUTTON, "Not Connected")
		self._connYes = self.render_icon(gtk.STOCK_YES, gtk.ICON_SIZE_BUTTON, "Connection Established")
		servers = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING)
		servers.append([self._connNo, "php-oop.net/2227"])
		return servers

class IrssiProxyConnection(threading.Thread):
	def __init__(self, irssi, host, port, password):
		self.stopthread = threading.Event()
		self.irssi = irssi
		self.host = host
		self.port = port
		self.password = password
		threading.Thread.__init__(self)

	def run(self):
		gtk.threads_enter()
		self.irssi.btnConnect.set_sensitive(False)
		self.irssi.push_msg("Connecting to %s ... " % (self.host))
		gtk.threads_leave()
		for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
			e = None
			af,socktype,proto,canoname,sa = res
			try:
				self.sock = socket.socket(af, socktype, proto)
			except socket.error, e:
				self.sock = None
				continue
			try:
				self.sock.connect(sa)
			except socket.error, e:
				self.sock = None
				continue
		if e:
			gtk.threads_enter()
			self.irssi.btnConnect.set_sensitive(True)
			gtk.threads_leave()
			raise e

		gtk.threads_enter()
		self.irssi.btnDisconnect.set_sensitive(True)
		self.irssi.push_msg("Connected to %s" % (self.host))
		gtk.threads_leave()
		self.sock.setblocking(0)
		self.sock.settimeout(0.5)
		self.send("PASS %s" % (self.password))
		self.send("NICK IrssiProxy")
		self.send("USER IrssiProxy 0 * :IrssiProxy")
		while not self.stopthread.isSet():
			try:
				data = self.recv()
				if data == b'':
					print "Server disconnected"
					self.stop()
					continue
				print "Recv: %s" % (data.strip())
				m = re.match(":([^\s]+)![^\s]+\sPRIVMSG\s([^\s]+)\s:(.*)", data)
				if m is not None and re.search(self.irssi.match.get_text(), m.group(3)):
					gtk.threads_enter()
					if not m.group(3).find(chr(1)+"ACTION"):
						text = "* "+m.group(1)+" "+m.group(3).replace(chr(1)+"ACTION", "").replace(chr(1),"")
					else:
						text = m.group(3)
					n = pynotify.Notification("%s on %s → %s" % (m.group(1), m.group(2), text))
					n.set_urgency(pynotify.URGENCY_NORMAL)
					n.set_timeout(10)
					n.connect("closed", lambda e : n.close())
					n.show()
					gtk.threads_leave()
			except socket.error, e:
				if e.errno != 11 and e.errno is not None:
					self.stop()
					print e
		self.sock.close()
		self.sock = None
		gtk.threads_enter()
		self.irssi.btnDisconnect.set_sensitive(False)
		self.irssi.btnConnect.set_sensitive(True)
		self.irssi.push_msg("Disconnected...")
		gtk.threads_leave()

	def recv(self):
		return self.sock.recv(2048)

	def send(self, buffer):
		print "Sent: " + buffer
		len = self.sock.sendall(buffer + "\r\n")
		if len == 0:
			print "Server disconnected"
			self.stop()

	def stop(self):
		if self.sock:
			self.sock.shutdown(socket.SHUT_RDWR)
		self.stopthread.set()

if __name__ == "__main__":
	gtk.gdk.threads_init()
	IrssiProxy()
	gtk.gdk.threads_enter()
	gtk.main()
	gtk.gdk.threads_leave()
