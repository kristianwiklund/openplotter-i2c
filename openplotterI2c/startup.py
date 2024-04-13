#!/usr/bin/env python3

# This file is part of OpenPlotter.
# Copyright (C) 2022 by Sailoog <https://github.com/openplotter/openplotter-i2c>
#                       e-sailing <https://github.com/e-sailing/openplotter-i2c>
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

import subprocess, os, sys, time
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSignalkInstaller import connections

class Start():
	def __init__(self, conf, currentLanguage):
		self.initialMessage = ''

	def start(self):
		green = ''
		black = ''
		red = ''
		return {'green': green,'black': black,'red': red}

class Check():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-i2c',currentLanguage)
		self.initialMessage = _('Checking I2C sensors...')

	def check(self):
		platform2 = platform.Platform()
		green = ''
		black = ''
		red = ''

		data = self.conf.get('I2C', 'sensors')
		try: i2c_sensors = eval(data)
		except: i2c_sensors = {}

		if platform2.isRPI:
			if platform2.isInstalled('raspi-config'):
				output = subprocess.check_output('raspi-config nonint get_i2c', shell=True).decode(sys.stdin.encoding)
				if '1' in output:
					if i2c_sensors: 
						msg = _('Please enable I2C interface in Preferences -> Raspberry Pi configuration -> Interfaces.')
						if not red: red = msg
						else: red+= '\n    '+msg
					else:
						msg = _('I2C disabled')
						if not black: black = msg
						else: black+= ' | '+msg
				else: 
					msg = _('I2C enabled')
					if not black: black = msg
					else: black+= ' | '+msg

		#service
		if i2c_sensors:
			try:
				subprocess.check_output(['systemctl', 'is-active', 'openplotter-i2c-read.service']).decode(sys.stdin.encoding)
				msg = _('service running')
				if not green: green = msg
				else: green+= ' | '+msg
			except: 
				msg = _('service not running')
				if red: red += '\n   '+msg
				else: red = msg
		else:
			try:
				subprocess.check_output(['systemctl', 'is-active', 'openplotter-i2c-read.service']).decode(sys.stdin.encoding)
				msg = _('service running')
				if red: red += '\n   '+msg
				else: red = msg
			except: 
				msg = _('service not running')
				if not black: black = msg
				else: black+= ' | '+msg


		#access
		skConnections = connections.Connections('I2C')
		result = skConnections.checkConnection()
		if result[0] =='error':
			if not red: red = result[1]
			else: red+= '\n    '+result[1]
		if result[0] =='validated':
			msg = _('Access to Signal K server validated')
			if not black: black = msg
			else: black+= ' | '+msg

		return {'green': green,'black': black,'red': red}

