#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'kevencastro7'


import commands
import notify2
import signal
import socket
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, GObject, Gdk, Notify
from fase import MicroServiceBase

def gtk_thread_safe(gtk_user_function):
    def thread_safe_wrapper(*args):
        GObject.idle_add(gtk_user_function,*args)
    return thread_safe_wrapper

class GraphicalUserInterface(MicroServiceBase):
    def __init__(self):
        super(GraphicalUserInterface, self).__init__(self, sender_endpoint='ipc:///tmp/sender',
                                                     receiver_endpoint='ipc:///tmp/receiver')
        self.app_objects = dict()
        self.gtk_builder = None
        self.model = None
	self.connect = False
	self.conectado = False
	self.disconnect = False
        """ LOAD ALL OBJECTS """
        self.gtk_builder = Gtk.Builder()
        self.gtk_builder.add_from_file('interface.glade')
        for app_object in self.gtk_builder.get_objects():
            if type(app_object) != Gtk.Adjustment and type(app_object) != Gtk.CellRendererText:
                widget_id = Gtk.Buildable.get_name(app_object)
                self.app_objects[widget_id] = app_object
        self.app_objects['MAIN_WINDOW'].set_title("ClienteTCP")
        self.app_objects['MAIN_WINDOW'].connect("delete-event", self.main_quit)
        self.app_objects['MAIN_WINDOW'].show()

        # handlers
        self.handlers = {
            'bt_sair': self.bt_sair,
	    'bt_conectar' : self.bt_conectar,
	    'bt_enviar' : self.bt_enviar,
        }
        self.gtk_builder.connect_signals(self.handlers)

    def on_broadcast(self, service, data):
        pass

    def on_connect(self):
        pass

    def on_new_service(self, service, actions):
        pass

    def main_quit(self, arg1=None, arg2=None):
        Gtk.main_quit()
        self.exit()

    """#############################################################################################################"""
    """############################################### GUI HANDLERS ################################################"""
    """#############################################################################################################"""

    def bt_sair(self, button):
        self.main_quit()

    def bt_conectar(self, button):
	if self.conectado:
		self.disconnect = True
	else:
		self.connect = True

    def bt_enviar(self, button):
	if self.conectado:
	    msg = self.app_objects['msg'].get_text() 
	    try:
		self.tcp.send (msg)
		self.gui_set_status('Última Mensagem: ' + msg )
		self.gui_clear_msg()
	    except:
		self.gui_set_status('Erro ao enviar a mensagem')
	else:
		self.gui_set_status('Nao Conectado')
	
    """#############################################################################################################"""
    """########################################### GUI UPDATE FUNCTIONS ############################################"""
    """#############################################################################################################"""

    @gtk_thread_safe
    def gui_set_bt_status(self, text):
        self.app_objects['bt_status'].set_label(text)

    @gtk_thread_safe
    def gui_clear_msg(self):
        self.app_objects['msg'].set_text('')

    @gtk_thread_safe
    def gui_set_status(self, text):
        self.app_objects['status'].set_text(text)


    """#############################################################################################################"""
    """################################################### TASKS  ##################################################"""
    """#############################################################################################################"""
    @MicroServiceBase.task
    def MainTask(self):
        Gtk.main()

    @MicroServiceBase.task
    def CLienteTCP(self):
	while True:
	    if self.connect:
		HOST = self.app_objects['host'].get_text()     # Endereco IP do Servidor
		PORT = 5000            # Porta que o Servidor esta
		self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		dest = (HOST, PORT)
		try:
			self.tcp.connect(dest)
			self.conectado = True
			self.gui_set_bt_status('Desconectar')
			self.gui_set_status('Conectado com Sucesso')
		except:
			self.gui_set_status('Não foi possível conectar')
		self.connect = False
	    elif self.disconnect:
		try:
			self.tcp.close()
			self.conectado = False
			self.gui_set_bt_status('Conectar')
			self.gui_set_status('Desconectado com Sucesso')
		except:
			self.gui_set_status('Não foi possível desconectar')
	    	self.disconnect = False
GraphicalUserInterface().execute(enable_tasks=True)
