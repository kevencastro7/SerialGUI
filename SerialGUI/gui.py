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
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

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
	self.line = ['line1','line2','line3','line4','line5','line6']
	self.topLine = 0
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

    def get_buff(self,L):
	return self.app_objects[self.line[L]].get_text()

    def write_line(self,text):
	for i in range(4,-1,-1):
	    self.gui_set_line(self.get_buff(i),i+1)
	self.gui_set_line(text,0)

    def serialRead(self):
	while self.conectado:
		try:
			x = int(self.ser.read(1))
		except:
			x = 0
		if x == 1:
			n = self.ser.read(1)
			x = self.ser.read(int(n))
			self.write_line(x)
			self.updateSamples(int(x))
			del n
		del x

    def calcutator(self):
	fig, ax = plt.subplots()
	ax.plot(self.axisX, self.axisY)

	ax.set(xlabel='samples', ylabel='ADC',
	       title='ADC')
	ax.grid()
	plt.ylim(0, 4100) 
	fig.savefig("test.png")
	canvas = FigureCanvas(fig)
	#canvas.set_size_request(400,400)
	self.gui_set_plot(canvas)
	plt.cla()
	plt.clf()
	plt.close(fig)
	del fig, ax
	
    def initGraph(self):
	self.axisX = []
	self.axisY = []
	for i in range(0,100):
		self.axisX.append(i)
		self.axisY.append(0)

    def updateSamples(self,new_value):
	for i in range(99,0,-1):
	    self.axisY[i] = self.axisY[i-1]
	self.axisY[0] = new_value

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
    def gui_set_line(self, text,L):
        self.app_objects[self.line[L]].set_text(text)

    @gtk_thread_safe
    def gui_clear_line(self, line):
        self.app_objects['read'].set_text('')

    @gtk_thread_safe
    def gui_set_image(self):
	self.app_objects['image'].clear
	self.app_objects['image'].set_from_file('test.png')

    @gtk_thread_safe
    def gui_set_plot(self,canvas):
	self.gui_clear_plot()
	self.app_objects['plot'].add_with_viewport(canvas)	

    @gtk_thread_safe
    def gui_clear_plot(self):
	self.app_objects['plot'].remove(self.app_objects['plot'].get_child())



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
			       	timeout=1
			   	)
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
    """
    @MicroServiceBase.task
    def SerialRead(self):
        while True:
		while self.conectado:
			time.sleep(0.1)
        		n = self.ser.inWaiting()
			x = self.ser.read(1)
			if x:
				self.write_line(str(x))
				print str(x)
    """

    @MicroServiceBase.task
    def TaskRead(self):
        while True:
		self.serialRead()

    @MicroServiceBase.task
    def UpdateImg(self):
	while True:
		while self.conectado:
			self.gui_set_image()
			time.sleep(0.2)

    @MicroServiceBase.task
    def CalcImg(self):
	self.initGraph()
	while True:
		while self.conectado:
			self.calcutator()
			time.sleep(0.05)

   
GraphicalUserInterface().execute(enable_tasks=True)
