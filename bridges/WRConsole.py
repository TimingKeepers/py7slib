#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
The WRConsole class extends the consolebridge class; it allows to add a cache to the consolebridge for storing the last update's values.


@file
@author Fran Romero
@date October 13, 2015
@copyright LGPL v2.1
@ingroup bridges
'''

#------------------------------------------------------------------------------|
#                   GNU LESSER GENERAL PUBLIC LICENSE                          |
#                 ------------------------------------                         |
# This source file is free software; you can redistribute it and/or modify it  |
# under the terms of the GNU Lesser General Public License as published by the |
# Free Software Foundation; either version 2.1 of the License, or (at your     |
# option) any later version. This source is distributed in the hope that it    |
# will be useful, but WITHOUT ANY WARRANTY; without even the implied warrant   |
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser   |
# General Public License for more details. You should have received a copy of  |
# the GNU Lesser General Public License along with this  source; if not,       |
# download it from http://www.gnu.org/licenses/lgpl-2.1.html                   |
#------------------------------------------------------------------------------|

#-------------------------------------------------------------------------------
#                                   Import                                    --
#-------------------------------------------------------------------------------

import re
import time
import sys
import serial
import datetime
from _ast import Param
import cmd
import threading

'''
los input que habra que dejar al final
#from subprocess import check_output
from py7slib.bridges.consolebridge import ConsoleBridge
#from bridges.ethbone import EthBone
from py7slib.bridges.serial_linux import *
from py7slib.bridges.serial_windows import *
from py7slib.core.p7sException import *
#from bridges.sdb import SDBNode
#from core.gendrvr import BusCritical, BusWarning
'''

#los input para que no de errores eclipse
from py7slib.bridges.consolebridge import *
import py7slib.bridges.serial_bridge as ser
import VUART_bridge as virt
from py7slib.core.p7sException import *
from py7slib.core.gendrvr import BusCritical, BusWarning
from py7slib.core.ewberrno import *
#from paramStrCmd import *


lock = threading.Lock()

class WRConsole(ConsoleBridge):
    '''
    Class to handle connection with WR devices using a cache to store the last update's values.

    This class implements the interface defined in ConsoleBridge abstract class.
    '''
    

    

    def __init__(self, interface='serial', verbose=False):
        '''
        Constructor

        Args:
            interface (str) : Indicates the bus used for the connection.
            verbose (bool) : Enables verbose output

        Raises:
            BadInput exception if any of the input parameters are not valid.
        '''
        
        self.interface = None
        self.cache = {}
        self.bridge = None
        
        # Input control
        '''if interface == "serial":
            self.interface = "serial"
            self.bridge = ser.SerialBridge('serial', port, False)
        elif interface == "eth":
            self.interface = "eth"
            self.bridge = virt.VUART_bridge('eth', port, False)
        elif interface == "pci":
            self.interface = "pci"
            self.bridge = virt.VUART_bridge('pci', port, False)
        else:
            raise BadData(self.errno.EIFACE, 'serial, eth, pci.')'''
            
            


    def reset_values(self, interface, port, verbose=False):
        
        '''
        Reset all values

        Args:
            interface (str) : Indicates the bus used for the connection.
            port (str) : Port name. Examples: "/dev/tty/USB0" for Linux, and
            "COM0" for Windows.
            verbose (bool) : Enables verbose output

        Raises:
            BadInput exception if any of the input parameters are not valid.
        '''
        
        del self.cache
        self.cache = {}
        self.bridge = None
        
        if interface == "serial":
            self.interface = "serial"
            self.bridge = ser.SerialBridge('serial', port, False)
        elif interface == "eth":
            self.interface = "eth"
            self.bridge = virt.VUART_bridge('eth', port, False)
            self.bridge.open()
        elif interface == "pci":
            self.interface = "pci"
            self.bridge = virt.VUART_bridge('pci', port, False)
        else:
            raise BadData(self.errno.EIFACE, 'serial, eth, pci.')



    def open(self, ethbone_dbg=False, baudrate=115200, rdtimeout=0.1, wrtimeout=0.1, interchartimeout=0.0005, ntries=2):

        '''
        Method to open a new connection with a WR device.

        Args:
            ethbone_dbg (bool) : Flag to enable verbose output for the EtherBone driver.
            baudrate (int) : Baudrate used in the WR-LEN serial port
            wrtimeout (int) : Timeout before read after writing
            interchartimeout (int) : Timeout between characters
            rdtimeout (int) : Read timeout
            ntries (int) : How many times retry a read or a write

        Raises:
            
        '''
        if self.interface == "eth" or self.interface == "pci":
            self.bridge.open(ethbone_dbg)
        elif self.interface == "serial":
            self.bridge.open(ethbone_dbg, baudrate, rdtimeout, wrtimeout, interchartimeout, ntries)
        else:
            print "Error: bridge desconocido."




    def isOpen(self):
        '''
        This method checks wheter device connection is stablished.

        Returns:
            True if open() method has previously called, False otherwise.
        '''
        return self.bridge.isOpen()

    def close(self):
        '''
        Method to close an existing connection with a WR device.

        Raises:
            ConsoleError : When the connection fails closing.
        '''
        self.bridge.close()
        self.bridge = None
        

    def flushInput(self):
        '''
        Method to clear read buffer of the VUART

        Use this method before calling sendCommand the first time in order to
        clear the data in the read buffer of the Virtual UART
        '''
        self.bridge.flushInput()
        


    def sendCommand(self, param, cmd, key, buffered=True, cache = True):
        '''
        Method to pass a command to the Device

        This method writes a command to the input and retrieves the device
        response (if buffered is true).
        
        Args:
            param (Param) : Param object who calls this function. It is used only when this param not exist in cache. If param == None only return the param value without update nothing
            cmd (str) : Command name
            key (str) : Instruction for calling to the param
            buffered (Boolean) : If buffered is True, this method return the reponse to the cmd
            cache (Boolean) : If cache is True it will update de cache

        Returns:
            Outputs a list of str from WR-LEN.
        '''
        repeat = 0
        out = "No return"
        while repeat <2:
            try:
            #if True:
                global lock
                if cache == True:
                    if self.cache.has_key(cmd):#if the parameter exists in the cache
                        parameter = self.cache[cmd]
                        updated_time = parameter.getUpdatedTime()
                        if updated_time == 0 : #si hay que refrescar el valor del parametro siempre
                            #refrescamos el valor
                            lock.acquire()
                            #print "sendcommand  con cache y refrescando siempre adquirimos cerrojo"
                            if self.interface == "serial" :
                                out = self.bridge.sendCommand(key, buffered)
                            else :
                                out = self.bridge.sendCommand(key)
                            lock.release()
                            #print "sendcommand con cache y refrescando siempre dejamos cerrojo"
                            self.cache[cmd].setValue(out, False)
                        elif updated_time == -1: #si nunca hay que refrescar el valor del parametro
                            out = self.cache[cmd].getValue()
                        else: #si el comando tiene fecha refresco
                            now = datetime.datetime.now()
                            if (now > updated_time) : #si ya ha pasado la fecha de refresco
                                #refrescamos el parametro
                                lock.acquire()
                                #print "sendcommand  con cache y refrescando a veces adquirimos cerrojo"
                                out = self.bridge.sendCommand(key, buffered)
                                lock.release()
                                #print "sendcommand  con cache y refrescando a veces dejamos el errojo"
                                self.cache[cmd].setValue(out)
                            else :
                                out = self.cache[cmd].getValue()
                    else : #if the parameter not exists in the cache
                        #metemos el comando en la cache
                        lock.acquire()
                        #print "sendcommand scon cache y sin el parametro en ella adquirimos cerrojo"
                        if self.interface == "serial" :
                            out = self.bridge.sendCommand(key, buffered)
                        else :
                            out = self.bridge.sendCommand(key)
                        lock.release()
                        #print "sendcommand con cache y sin el parametro en ella dejamos cerrojo"
                        if param != None :
                            self.cache[cmd] = param
                            self.cache[cmd].setValue(out)
                    repeat = 2
                else :
                    lock.acquire()
                    #print "sendcommand sin cache adquirimos cerrojo"
                    if self.interface == "serial" :
                        out = self.bridge.sendCommand(key, buffered)
                    else :
                        out = self.bridge.sendCommand(key)
                    #if cmd == 'sfp add':
                        #print "en sendCommand de wrconsole out vale"
                        #print out
                        #print " y key vale"
                        #print key
                    lock.release()
                    #print "sendcommand sin cache dejamos cerrojo"
                    '''if cmd != 'timing_statistics': # we updated the statistics in the node
                        if self.cache.has_key(cmd):#if the parameter exists in the cache
                            self.cache[cmd].setValue(out)
                        else :
                            if param != None :
                                self.cache[cmd] = param
                                self.cache[cmd].setValue(out)'''
                    repeat = 2
                if buffered == True:
                    return out
                else:
                    return 'No return'
            except Exception as e:
                lock.release()
                repeat = repeat + 1
                if repeat >= 2:
                    print "el comando que falla es " + cmd
                    raise (e)
                    #print "error en sendCommand de WRConsole"
                    #return None
                else:
                    time.sleep(1)
    
    
    
    @staticmethod
    def scan(bus, subnet) :
        '''
        Method to scan WR devices connected to the PC.

        This method look for devices connected through the following interfaces:
        · Serial interface
        · PCIe bus.
        · Ethernet in devices with Etherbone included.

        Args:
            bus (str) : Scan in all interfaces, or only for a specific interface.
            Options available:
                · "all" : Scan all interfaces.
                · "pci" : Scan only devices conneted to the PCI bus.
                · "eth" : Scan only devices conneted to Ethernet with Etherbone.
                · "serial" : Scan only devices conneted to a serial port.
            subnet(str) : Subnet IP address to scan for devices. Only used with
            option "eth" or "all". Example: subnet="192.168.7.0/24".


        Returns:
            A dict where the keys are the seen before. The value is a list with
            ports/ip dirs. availables. When there're no conneted devices, an
            empty list is returned. A example:
            {'pci':[], 'eth':["192.168.1.3"], 'serial':["/dev/ttyUSB0",
            "dev/ttyUSB1"]}

        Raises:
            ConsoleError : When one of the specified interfaces could not be scanned.
        '''

        devices = ConsoleBridge.scan(bus, subnet)

        return devices
    
    
    @staticmethod
    def getModel(bus, port, console) :
        '''
        Method to get if the device is a LEN, SPEC, etc.

        Args:
            bus (str) : Scan in all interfaces, or only for a specific interface.
            Options available:
                · "pci" : Scan only devices conneted to the PCI bus.
                · "eth" : Scan only devices conneted to Ethernet with Etherbone.
                · "serial" : Scan only devices conneted to a serial port.
            port (str) : port where the device is connected to the PC

        Returns:
            String with the device model

        Raises:
            
        '''

        # Call the child-classes' scan method
        try :
            global lock
            model = ''
            if bus == "pci" :
                #device = virt.VUART_bridge('pci', port)
                if console.bridge.isOpen() == False:
                    console.bridge.open()
                lock.acquire()
                #print "getmodel pci adquirimos cerrojo"
                #model = device.sendCommand('ver')
                model = console.bridge.sendCommand('ver')
                lock.release()
                #print "getmodel pci dejamos cerrojo"
        
            elif bus == "eth" :
                #print "en getmodel de wrconsole el bus es eth"
                #device = virt.VUART_bridge('eth', port)
                if console.bridge.isOpen() == False:
                    console.bridge.open()
                lock.acquire()
                #print "getModel eth adquirimos cerrojo"
                #model = device.sendCommand('ver')
                model = console.bridge.sendCommand('ver')
                lock.release()
                #print "getModel eth dejamos cerrojo"
        
            elif bus == "serial" :
                #print "en getmodel de wrconsole el bus es serial"
                #device = ser.SerialBridge('serial', port)
                #print "si el bridge esta abierto devuelve true y el resultado es"
                #print console.bridge.isOpen()
                #print "y el interface es"
                #print console.interface
                if console.bridge.isOpen() == False:
                    console.bridge.open()
                #print "intentamos coger el cerrojo"
                lock.acquire()
                #print "en getmodel serial cogemos el cerrojo"
                #model = device.sendCommand('ver')
                model = console.bridge.sendCommand('ver')
                lock.release()
                #print "getModel  serial dejamos cerrojo"
                #print "en getmodel de wrconsole model vale"
                #print model
    
            '''except:
                # Throw it to a upper layer
                raise BadData(38, 'Function getModel() not found')'''
    
            model = model.split('EEPROM FRU info is valid:')
            if len(model) > 1:
                model = model[1]
                #print 'ahora model vale'
                #print model
                if 'FRU DEVICE  : WRLEN' in model :
                    model = 'LEN'
                elif 'ZEN' in model :
                    model = 'ZEN'
                else :
                    model = 'UNKNOWN'
            else :
                model = 'SPEC'
        except:
            lock.release()
            model = 'UNKNOWN'
        return model


