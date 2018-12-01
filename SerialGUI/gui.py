#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'kevencastro7'


import commands
import notify2
import signal
import gi
import serial
import time
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, GObject, Gdk, Notify
from fase import MicroServiceBase
import matplotlib
import matplotlib.pyplot as plt
import timeit


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
	self.update = False
	self.samples = 1004	
	self.topLine = 0
	self.novasamostras = 4

        """ LOAD ALL OBJECTS """
        self.gtk_builder = Gtk.Builder()
        self.gtk_builder.add_from_file('interface.glade')
        for app_object in self.gtk_builder.get_objects():
            if type(app_object) != Gtk.Adjustment and type(app_object) != Gtk.CellRendererText:
                widget_id = Gtk.Buildable.get_name(app_object)
                self.app_objects[widget_id] = app_object
        self.app_objects['MAIN_WINDOW'].set_title("Serial")
        self.app_objects['MAIN_WINDOW'].connect("delete-event", self.main_quit)
        self.app_objects['MAIN_WINDOW'].show()
	self.buffer = []

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


    def serialRead(self):
	while self.conectado:
		try:

			x = self.ser.read(1)
		except:
			x = 0
		if x == '|':
			try:
				n = ord(self.ser.read(1))
			except:
				break
			try:
				for i in range(1,int(n)+1):
					self.buffer.append(ord(self.ser.read(1)))
				self.ser.flushInput()
			except:
				break
			self.update = True
			print self.buffer
			del n
		del x

    def calculator(self):
	fig, ax = plt.subplots()
	ax.plot(self.axisX[1:self.samples-self.novasamostras], self.axisY[1:self.samples-self.novasamostras])

	ax.set(xlabel='samples', ylabel='Tensao(V)',
	       title='ADC')
	ax.grid()
	plt.ylim(-1.5, 1.5) 
	fig.savefig("test.png")
	plt.cla()
	plt.clf()
	plt.close(fig)
	del fig, ax
	
    def initGraph(self):
	self.axisX = []
	self.axisY = []
	for i in range(0,self.samples):
		self.axisX.append(i)
		self.axisY.append(0.0)

    def updateSamples(self):
	buffers = self.buffer
	self.buffer = []
	self.novasamostras = len(buffers)
	for i in range(1,self.samples-self.novasamostras):
	    self.axisY[i] = self.axisY[i+1]
	for i in range(0,self.novasamostras):
	    self.axisY[self.samples-(4-i)] = (int(buffers[i])-45)/30.0

	

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
		self.ser.write(msg)
		self.gui_clear_msg()
	    except:
		print 'Erro ao enviar a mensagem'
	else:
	    print 'Não conectado'
	
    """#############################################################################################################"""
    """########################################### GUI UPDATE FUNCTIONS ############################################"""
    """#############################################################################################################"""

    @gtk_thread_safe
    def gui_set_status(self, text):
        self.app_objects['status'].set_label(text)

    @gtk_thread_safe
    def gui_clear_msg(self):
        self.app_objects['msg'].set_text('')

    @gtk_thread_safe
    def gui_set_image(self):
	self.app_objects['image'].clear
	self.app_objects['image'].set_from_file('test.png')



    """#############################################################################################################"""
    """################################################### TASKS  ##################################################"""
    """#############################################################################################################"""
    @MicroServiceBase.task
    def MainTask(self):
        Gtk.main()

    @MicroServiceBase.task
    def TaskConect(self):
	while True:
	    if self.connect:

		try:
			print self.app_objects['host'].get_text() 
			self.ser = serial.Serial(
			       	port=self.app_objects['host'].get_text() ,
			       	baudrate = 115200,
			       	parity=serial.PARITY_NONE,
			       	stopbits=serial.STOPBITS_ONE,
			       	bytesize=serial.EIGHTBITS,
			       	timeout=10
			   	)
			self.ser.flushInput()
			self.ser.flushOutput()
			#self.ser.open()
			self.conectado = True
			self.gui_set_status('Desconectar')
			print 'Conectado com Sucesso'
		except:
			print 'Não foi possível conectar'
		self.connect = False
	    elif self.disconnect:
		try:
			self.ser.close()
			self.conectado = False
			self.gui_set_status('Conectar')
			print 'Desconectado com Sucesso'
		except:
			print 'Não foi possível desconectar'
	    	self.disconnect = False

    @MicroServiceBase.task
    def TaskRead(self):
        self.initGraph()
        while True:
		self.serialRead()
    '''
    @MicroServiceBase.task
    def UpdateImg(self):
	while True:
		while self.conectado:
			self.gui_set_image()
			time.sleep(0.2)
    '''
    @MicroServiceBase.task
    def CalcImg(self):
	self.initGraph()
	self.calculator()
	self.gui_set_image()
	while True:
		while self.conectado:
			self.calculator()
			self.gui_set_image()
			time.sleep(0.05)
    @MicroServiceBase.task
    def HandleUpdate(self):
	while True:
		while self.update:
			try:
				self.updateSamples()
			except:
				pass
			self.update = False

     
GraphicalUserInterface().execute(enable_tasks=True)
