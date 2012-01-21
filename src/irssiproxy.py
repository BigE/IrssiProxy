#!/usr/bin/env python
# vim: set fileencoding=utf8 :

import pygtk
pygtk.require('2.0')
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
	def __init__(self):
		super(IrssiProxy, self).__init__(gtk.WINDOW_TOPLEVEL)
		pynotify.init("IrssiProxy")
		self.set_title("IrssiProxy Configuration")
		self.set_default_size(320, 240)
		self._icon = os.path.realpath(os.path.dirname(__file__)+"/resources/65704.png")
		self._initStatusIcon()
		self._initLayout()
		self._irc = None
		self.connect("delete-event", self.delete)
		self.connect("destroy", self.destroy)
		self.set_icon_from_file(self._icon)
		self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		self.show()

	def delete(self, widget, data=None):
		self.hide()
		# Stop the window from being deleted
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
		quit = gtk.MenuItem("Quit")
		about = gtk.MenuItem("About")
		about.connect("activate", self.show_about)
		quit.connect("activate", self.destroy)
		menu.append(about)
		menu.append(quit)
		menu.show_all()
		menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, status_icon)

	def push_msg(self, message):
		self._statusBar.pop(self._context)
		self._statusBar.push(self._context, message)

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

	def _initLayout(self):
		# Main Box
		mainVBox = gtk.VBox(False, 20)
		# Server Box
		serverHBox = gtk.HBox(False, 20)
		serverHBox.pack_start(gtk.Label("Irssi Proxy Server"), False, False, 10)
		self._host = gtk.Entry()
		serverHBox.pack_end(self._host, False, False, 10)
		mainVBox.pack_start(serverHBox, False, False, 10)
		# Port Box
		portHBox = gtk.HBox(False, 20)
		portHBox.pack_start(gtk.Label("Irssi Proxy Port"), False, False, 10)
		self._port = gtk.Entry()
		self._port.set_width_chars(8)
		self._port.set_text("6667")
		portHBox.pack_end(self._port, False, False, 10)
		mainVBox.pack_start(portHBox, False, False, 10)
		# Password Box
		passHBox = gtk.HBox(False, 20)
		passHBox.pack_start(gtk.Label("Irssi Proxy Password"), False, False, 10)
		self._password = gtk.Entry()
		self._password.set_visibility(False)
		passHBox.pack_end(self._password, False, False, 10)
		mainVBox.pack_start(passHBox, False, False, 10)
		# Match Box
		matchHBox = gtk.HBox(False, 20)
		matchHBox.pack_start(gtk.Label("Regex to Match"), False, False, 10)
		self.match = gtk.Entry()
		self.match.connect("changed", self._checkRegex)
		matchHBox.pack_end(self.match, False, False, 10)
		mainVBox.pack_start(matchHBox, False, False, 10)
		# Status bar
		self._statusBar = gtk.Statusbar()
		self._context = self._statusBar.get_context_id("General Settings")
		self._statusBar.push(self._context, "Disconnected...")
		mainVBox.pack_end(self._statusBar, False, False, 10)
		# Button Box
		buttonHBox = gtk.HBox(False, 20)
		self.btnDisconnect = gtk.Button("Disconnect", gtk.STOCK_DISCONNECT)
		self.btnDisconnect.set_sensitive(False)
		self.btnDisconnect.connect("clicked", self.on_disconnect)
		buttonHBox.pack_end(self.btnDisconnect, False)
		self.btnConnect = gtk.Button("Connect", gtk.STOCK_CONNECT)
		self.btnConnect.connect("clicked", self.on_connect)
		buttonHBox.pack_end(self.btnConnect, False)
		mainVBox.pack_end(buttonHBox, False, False, 10)
		# show everything
		mainVBox.show_all()
		self.add(mainVBox)

	def _initStatusIcon(self):
		statusIcon = gtk.status_icon_new_from_file(self._icon)
		statusIcon.set_title("IrssiProxy")
		statusIcon.connect("popup-menu", self.popup_statusIcon_menu)
		statusIcon.connect("activate", self.show)
		statusIcon.set_tooltip('IrssiProxy Notifications')

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
		self.send("PASS %s" % (self.password))
		self.send("NICK IrssiProxy")
		self.send("USER IrssiProxy 0 * :IrssiProxy")
		while not self.stopthread.isSet():
			try:
				data = self.recv()
				print "Recv: %s" % (data.strip())
				m = re.match(":([^\s]+)![^\s]+\sPRIVMSG\s([^\s]+)\s:(.*)", data)
				if m is not None and re.search(self.irssi.match.get_text(), m.group(3)):
					n = pynotify.Notification("%s on %s → %s" % (m.group(1), m.group(2), m.group(3)))
					n.set_urgency(pynotify.URGENCY_NORMAL)
					n.set_timeout(10)
					n.connect("closed", lambda e : n.close())
					n.show()
			except socket.error, e:
				if e.errno != 11:
					self.stop()
					print e
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
		return self.sock.sendall(buffer + "\r\n")

	def stop(self):
		self.stopthread.set()

if __name__ == "__main__":
	gtk.gdk.threads_init()
	IrssiProxy()
	gtk.gdk.threads_enter()
	gtk.main()
	gtk.gdk.threads_leave()
