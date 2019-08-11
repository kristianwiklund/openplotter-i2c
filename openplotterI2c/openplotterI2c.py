#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2019 by sailoog <https://github.com/sailoog/openplotter>
#                     e-sailing <https://github.com/e-sailing/openplotter>
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

import wx, os, webbrowser, subprocess, time, smbus
import wx.richtext as rt

from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import ports
from openplotterSettings import platform
from openplotterSettings import selectKey
from .startup import Check

class MyFrame(wx.Frame):
	def __init__(self):
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
		self.platform = platform.Platform()
		self.currentdir = os.path.dirname(__file__)
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-i2c',self.currentLanguage)

		wx.Frame.__init__(self, None, title=_('OpenPlotter I2C'), size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-i2c.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)

		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		toolHelp = self.toolbar1.AddTool(101, _('Help'), wx.Bitmap(self.currentdir+"/data/help.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolHelp, toolHelp)
		if not self.platform.isInstalled('openplotter-doc'): self.toolbar1.EnableTool(101,False)
		toolSettings = self.toolbar1.AddTool(102, _('Settings'), wx.Bitmap(self.currentdir+"/data/settings.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolSettings, toolSettings)
		self.toolbar1.AddSeparator()
		toolAddresses = self.toolbar1.AddTool(103, _('Detect I2C Addresses'), wx.Bitmap(self.currentdir+"/data/check.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolAddresses, toolAddresses)


		self.notebook = wx.Notebook(self)
		self.i2c = wx.Panel(self.notebook)
		self.output = wx.Panel(self.notebook)
		self.notebook.AddPage(self.i2c, _('Sensors'))
		self.notebook.AddPage(self.output, _('Output'))
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/i2c.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/output.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.CreateStatusBar()
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)
		self.Centre(True) 
		self.Show(True)

		self.pageI2c()
		self.pageOutput()
		self.checkInterface()

	def ShowStatusBar(self, w_msg, colour):
		self.GetStatusBar().SetForegroundColour(colour)
		self.SetStatusText(w_msg)

	def ShowStatusBarRED(self, w_msg):
		self.ShowStatusBar(w_msg, wx.RED)

	def ShowStatusBarGREEN(self, w_msg):
		self.ShowStatusBar(w_msg, wx.GREEN)

	def ShowStatusBarBLACK(self, w_msg):
		self.ShowStatusBar(w_msg, wx.BLACK) 

	def ShowStatusBarYELLOW(self, w_msg):
		self.ShowStatusBar(w_msg,(255,140,0)) 

	def OnToolHelp(self, event): 
		url = "/usr/share/openplotter-doc/i2c/i2c_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')

	def pageOutput(self):
		self.logger = rt.RichTextCtrl(self.output, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.LC_SORT_ASCENDING)
		self.logger.SetMargins((10,10))

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.logger, 1, wx.EXPAND, 0)
		self.output.SetSizer(sizer)

	def OnToolAddresses(self,e):
		addresses = ''
		try:
			addresses = subprocess.check_output(['i2cdetect', '-y', '0']).decode('utf-8')
		except:
			try:
				addresses = subprocess.check_output(['i2cdetect', '-y', '1']).decode('utf-8')
			except: pass
		self.logger.Clear()
		self.notebook.ChangeSelection(1)
		if addresses:
			self.logger.BeginTextColour((55, 55, 55))
			self.logger.WriteText(addresses)
		else:
			self.logger.BeginTextColour((255, 0, 0))
			self.logger.WriteText(_('Failed'))
		self.checkInterface()

	def checkInterface(self):
		cheking = Check(self.conf,self.currentLanguage )
		result = cheking.check()
		if result['red']:
			self.ShowStatusBarRED(result['red'])

	def pageI2c(self):
		self.listSensors = wx.ListCtrl(self.i2c, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listSensors.InsertColumn(0, ' ', width=16)
		self.listSensors.InsertColumn(1, _('Name'), width=135)
		self.listSensors.InsertColumn(2, _('Address'), width=100)
		self.listSensors.InsertColumn(3, _('Magnitude'), width=120)
		self.listSensors.InsertColumn(4, _('Signal K key'), width=220)
		self.listSensors.InsertColumn(5, _('Rate'), width=50)
		self.listSensors.InsertColumn(6, _('Offset'), width=50)
		self.listSensors.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListSensorsSelected)
		self.listSensors.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListSensorsDeselected)

		self.toolbar2 = wx.ToolBar(self.i2c, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.addButton = self.toolbar2.AddTool(201, _('Add'), wx.Bitmap(self.currentdir+"/data/add.png"))
		self.Bind(wx.EVT_TOOL, self.OnAddButton, self.addButton)
		self.editButton = self.toolbar2.AddTool(202, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditButton, self.editButton)
		self.removeButton = self.toolbar2.AddTool(203, _('Remove'), wx.Bitmap(self.currentdir+"/data/remove.png"))
		self.Bind(wx.EVT_TOOL, self.OnRemoveButton, self.removeButton)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.listSensors, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar2, 0)
		self.i2c.SetSizer(sizer)

		self.readSensors()
		self.onListSensorsDeselected()

	def readSensors(self):
		self.i2c_sensors_def = []
		self.i2c_sensors_def.append(['BME280','0x76',[_('pressure'),_('temperature'),_('humidity')],['environment.outside.pressure','','environment.inside.humidity']])
		self.i2c_sensors_def.append(['MS5607-02BA03','0x77',[_('pressure'),_('temperature')],['environment.outside.pressure','']])
		#self.i2c_sensors_def.append(['Si7020-A20','0x40',[_('humidity'),_('temperature')],['environment.inside.humidity','']])
		self.i2c_sensors = []
		
		data = self.conf.get('I2C', 'sensors')
		magn_list = '0123456789'
		try:
			self.i2c_sensors = eval(data)
		except:
			self.i2c_sensors = []

		self.listSensors.DeleteAllItems()
		for i in self.i2c_sensors:
			name = i[0]
			for ii in self.i2c_sensors_def:
				if name == ii[0]: 
					magn_list = ii[2]
					break
			address = i[1]
			c = 0
			for iii in i[2]:
				#print(str(c), name, address, magn_list[c], iii[0], str(iii[1]), str(iii[2]))
				self.listSensors.Append([str(c), name, address, magn_list[c], iii[0], str(iii[1]), str(iii[2])])
				if iii[0]: self.listSensors.SetItemBackgroundColour(self.listSensors.GetItemCount()-1,(255,215,0))
				c = c + 1

	def OnAddButton(self,e):
		dlg = addI2c(self.i2c_sensors_def)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			name = str(dlg.sensor_select.GetValue())
			if not name:
				self.ShowStatusBarRED(_('Failed. You must select a sensor.'))
				dlg.Destroy()
				return
			address = dlg.address.GetValue()
			if not address:
				self.ShowStatusBarRED(_('Failed. You must provide an address.'))
				dlg.Destroy()
				return
			new_sensor = []
			for item in self.i2c_sensors_def:
				if name == item[0]:
					new_sensor.append(name)
					new_sensor.append(address)
					new_sensor.append([])   
					for ii in item[3]:
						new_sensor[2].append([ii, 1.0, 0.0])
			if new_sensor:
				exist = False
				c = 0
				for i in self.i2c_sensors:
					if i[0] == new_sensor[0]: 
						self.i2c_sensors[c] = new_sensor
						exist = True
						break
					c = c + 1
				if exist == False: self.i2c_sensors.append(new_sensor)
				self.conf.set('I2C', 'sensors', str(self.i2c_sensors))
				self.readSensors()
		dlg.Destroy()

	def OnEditButton(self,e):
		selected = self.listSensors.GetFirstSelected()
		if selected == -1: return
		name = self.listSensors.GetItem(selected, 1)
		name = name.GetText()
		index = self.listSensors.GetItem(selected, 0)
		index = index.GetText()
		magn = self.listSensors.GetItem(selected, 3)
		magn = magn.GetText()
		sk = self.listSensors.GetItem(selected, 4)
		sk = sk.GetText()
		rate = self.listSensors.GetItem(selected, 5)
		rate = rate.GetText()
		offset = self.listSensors.GetItem(selected, 6)
		offset = offset.GetText()

		dlg = editI2c(name,magn,sk,rate,offset)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			sk = str(dlg.SKkey.GetValue())
			rate = dlg.rate.GetValue()
			offset = dlg.offset.GetValue()
			if not offset: offset = 0.0
			c = 0
			for i in self.i2c_sensors:
				if i[0] == name:
					self.i2c_sensors[c][2][int(index)][0] = sk
					self.i2c_sensors[c][2][int(index)][1] = float(rate)
					self.i2c_sensors[c][2][int(index)][2] = float(offset)
				c = c + 1
			self.conf.set('I2C', 'sensors', str(self.i2c_sensors))
			self.readSensors()
		dlg.Destroy()

	def OnRemoveButton(self,e):
		selected = self.listSensors.GetFirstSelected()
		if selected == -1: return
		name = self.listSensors.GetItem(selected, 1)
		name = name.GetText()
		c = 0
		for i in self.i2c_sensors:
			if str(i[0]) == name: 
				del self.i2c_sensors[c]
				break
			c = c + 1

		self.conf.set('I2C', 'sensors', str(self.i2c_sensors))
		self.readSensors()

	def onListSensorsSelected(self,e):
		i = e.GetIndex()
		valid = e and i >= 0
		if not valid: return
		self.toolbar2.EnableTool(202,True)
		self.toolbar2.EnableTool(203,True)

	def onListSensorsDeselected(self,e=0):
		self.toolbar2.EnableTool(201,True)
		self.toolbar2.EnableTool(202,False)
		self.toolbar2.EnableTool(203,False)


################################################################################

class addI2c(wx.Dialog):
	def __init__(self, i2c_sensors_def):

		title = _('Add I2C sensor')

		wx.Dialog.__init__(self, None, title=title, size=(450,430))
		panel = wx.Panel(self)
		label_detected = wx.StaticText(panel, label=_('detected'))

		self.list_detected = wx.ListCtrl(panel, -1, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
		self.list_detected.InsertColumn(0, _('Name'), width=330)
		self.list_detected.InsertColumn(1, _('Address'), width=100)
		self.list_detected.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectDetected)

		hline1 = wx.StaticLine(panel)

		label_add = wx.StaticText(panel, label=_('add/update sensor'))

		self.list_sensors = []
		for i in i2c_sensors_def:
			self.list_sensors.append(i[0])
		self.sensor_select = wx.ComboBox(panel, choices=self.list_sensors, style=wx.CB_READONLY, size = (200,-1))
		self.sensor_select.Bind(wx.EVT_COMBOBOX, self.onSelectSensor)

		self.address = wx.TextCtrl(panel)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)

		hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		hbox3.Add(self.sensor_select, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		hbox3.Add(self.address, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.ALL | wx.EXPAND, 5)
		hbox.Add(okBtn, 0, wx.ALL | wx.EXPAND, 5)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(label_detected, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 10)
		vbox.Add(self.list_detected, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 10)
		vbox.AddSpacer(10)
		vbox.Add(label_add, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 10)
		vbox.Add(hbox3, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(hline1, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.Add(hbox, 0, wx.ALL  | wx.EXPAND, 5)

		panel.SetSizer(vbox)
		self.panel = panel

		self.detection()

	def onSelectDetected(self, e):
		selectedDetected = self.list_detected.GetFirstSelected()
		name = self.list_detected.GetItem(selectedDetected, 0)
		address = self.list_detected.GetItem(selectedDetected, 1)
		self.sensor_select.SetValue(name.GetText())
		if name.GetText() in self.list_sensors: self.address.SetValue(address.GetText())

	def onSelectSensor(self, e):
		self.address.SetValue('')

	def detection(self):
		self.list_detected.DeleteAllItems()
		bus = smbus.SMBus(1)
		for addr in range(3, 178):
			try:
				bus.write_quick(addr)
				addr = hex(addr)
				if addr == '0x76': self.list_detected.Append(['BME280', addr])
				if addr == '0x77': self.list_detected.Append(['MS5607-02BA03', addr])
				#if addr == '0x40': self.list_detected.Append(['Si7020-A20', addr])
			except IOError: pass

################################################################################

class editI2c(wx.Dialog):
	def __init__(self,name,magn,sk,rate,offset):
		self.platform = platform.Platform()
		title = _('Edit')+(' '+name+' - '+magn)

		wx.Dialog.__init__(self, None, title=title, size=(500, 250))
		panel = wx.Panel(self)

		titl = wx.StaticText(panel, label=_('Signal K key'))
		self.SKkey = wx.TextCtrl(panel)
		self.SKkey.SetValue(sk)

		self.edit_skkey = wx.Button(panel, label=_('Edit'))
		self.edit_skkey.Bind(wx.EVT_BUTTON, self.onEditSkkey)

		if not self.platform.skDir:
			self.SKkey.Disable()
			self.edit_skkey.Disable()

		hline1 = wx.StaticLine(panel)

		self.rate_list = ['0.1', '0.25', '0.5', '0.75', '1.0', '5.0', '30.0', '60.0', '300.0']
		self.rate_label = wx.StaticText(panel, label=_('Rate (seconds)'))
		self.rate = wx.ComboBox(panel, choices=self.rate_list, style=wx.CB_READONLY)
		self.rate.SetValue(rate)

		self.offset_label = wx.StaticText(panel, label=_('Offset'))
		self.offset = wx.TextCtrl(panel)
		self.offset.SetValue(offset)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2.Add(self.SKkey, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		hbox2.Add(self.edit_skkey, 0, wx.RIGHT | wx.EXPAND, 5)

		hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		hbox3.Add(self.rate_label, 0, wx.ALL | wx.EXPAND, 5)
		hbox3.Add(self.rate, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)

		hbox4 = wx.BoxSizer(wx.HORIZONTAL)
		hbox4.Add(self.offset_label, 0, wx.ALL| wx.EXPAND, 5)
		hbox4.Add(self.offset, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.EXPAND, 0)
		hbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(titl, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 10)
		vbox.Add(hbox2, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(10)
		vbox.Add(hbox3, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(10)
		vbox.Add(hbox4, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(hline1, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.Add(hbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

	def onEditSkkey(self,e):
		dlg = selectKey.SelectKey(self.SKkey.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.SKkey.SetValue(key)
		dlg.Destroy()

################################################################################

def main():
	app = wx.App()
	MyFrame().Show()
	app.MainLoop()

if __name__ == '__main__':
	main()
