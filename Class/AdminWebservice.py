import requests
import re
import json
from suds.client import Client
import logging
import cookielib
import os
import urlparse
import urllib

class WebService:

	# Initiate the WebService object which will contain
	# - The admin webservice
	# - The official webservice
	# - The session, which could be used to perform
	#	web requests
	# - Login credentials
	def __init__(self, domain, user_name, password):
		
		# Main variables
		self.user_name = user_name
		self.password = password
		self.domain = domain
		
		# Initiate supported webservice
		self.WSClient = self.getWSClient()
		self.WSToken = self.getWSToken()
		
		# Initiate admin webservice
		self.session = requests.Session()
		self.AdminClient = self.getAdminClient()
		
		# Save the default space for the user in order
		# to revert to it when the WebService is exited
		self.initial_space_key = self.getDefaultSpace()
		
		# Get current space Id
		self.selectedSpace = '?'
		
	# Get official webservice
	def getWSClient(self):
		url = 'https://' + self.domain + '/CommandWebService.asmx'
		return Client(url + '?wsdl', location=url)
		
	# Get token for official webservice
	def getWSToken(self):
		return str(self.WSClient.service.Login(self.user_name,self.password))
		
	# Get the client for the admin webservice
	def getAdminClient(self):
		server = 'https://' + self.domain
		
		# Log in
		login_url = server + '/Login.aspx'
		data = {}
		data['LoginForm2$UserName'] = self.user_name
		data['LoginForm2$Password'] = self.password

		r = self.submitForm(login_url, data)
		login_cookies = self.session.cookies.get_dict()
		
		# Check if the token can be retrieved from the post response
		# If it cannot be retrieved, then login was unsuccessful
		try:
			headers = {'X-XSRF-TOKEN': login_cookies['XSRF-TOKEN'] }
		except Exception as err:
			print 'Error: The user could not be logged in'
			exit()
			
		self.wsdl_location = self.getWSDLLocalURL()
		
		# Set up Admin Webservices
		AdminWebServiceClient = Client(self.wsdl_location,
								  headers=headers,
								  location=(server + '/AdminService.asmx'))

		# Add the cookies to the request
		cookie_jar = cookielib.CookieJar()

		for cookie in login_cookies:

			c = cookielib.Cookie(0, cookie, login_cookies[cookie], None, False,
								  self.domain, False, False, '/', True, True,
								  None, True, None, None, {'Httponly':None},
								  rfc2109=False)

			cookie_jar.set_cookie(c)

		AdminWebServiceClient.options.transport.cookiejar = cookie_jar
		
		return AdminWebServiceClient
		
	# Get a usable URL for the admin webservice WSDL
	def getWSDLLocalURL(self):
		path = os.path.abspath(__file__)
		dir_path = os.path.dirname(path)
		wsdl_path = os.path.join(dir_path, 'Admin WSDL', self.domain, 'WSDL.xml')
		
		if not os.path.exists(os.path.dirname(wsdl_path)):
			self.updateAdminWSDL()
		
		local_wsdl_url = urlparse.urljoin(
				'file:', urllib.pathname2url(wsdl_path))
				
		return local_wsdl_url;
		
	# Download the admin WSDL for the current domain 
	def updateAdminWSDL(self):		
		wsdl_url = 'https://' + self.domain + '/AdminService.asmx?WSDL'
		wsdl_response = self.session.get(wsdl_url)
		
		path = os.path.abspath(__file__)
		dir_path = os.path.dirname(path)
		wsdl_path = os.path.join(dir_path, 'Admin WSDL', self.domain, 'WSDL.xml')
		
		if not os.path.exists(os.path.dirname(wsdl_path)):
			os.makedirs(os.path.dirname(wsdl_path))
		
		f = open( wsdl_path, 'w' )
		f.write(wsdl_response.content)
		f.close
		
	# Submit an HTML form
	def submitForm(self, url, initial_data):
		r = self.session.get(url)
		cookies = dict(r.cookies)
		data = self.getForm(r.content)
		
		for key in data:
			if key not in initial_data:
				initial_data[key] = data[key]
				
		r = self.session.post(url, data=initial_data, verify=False, cookies=cookies)
		return r
		
	# Get the entries in an HTML form
	# Currently only supports input elements
	def getForm(self, html):
		
		# Populate the data variable with the
		# key => value from the form
		data = {}
		
		# Look for all the input HTML elements
		p = re.compile('input .*\/>')
		args = p.findall(html)
		for arg in args:

			p = re.compile('name\="([^"]*)"')

			if p.search(arg) is not None:
				key = p.search(arg).group(1)
				p = re.compile('value\="([^"]*)"')
				
				if p.search(arg) is not None:
					val = p.search(arg).group(1)
					data[key] = val
					
		# Look for all the select HTML elements
		p = re.compile('<select(.*?)</select>', re.MULTILINE)
		args = p.findall(html)
		args = re.findall('<select(.*?)</select>', html, re.S)
		for arg in args:
			p = re.compile('name\="([^"]*)"')

			if p.search(arg) is not None:
				key = p.search(arg).group(1)
				val = ''
				p = re.compile('<option selected="selected"(.*?)>')
				
				if p.search(arg) is not None:
						option = p.search(arg).group(0)
						p = re.compile('value\="([^"]*)"')
						
						if p.search(option) is not None:
							val = p.search(option).group(1)
							
				data[key] = val
		
		return data
		
	# Get the default space for the logged in user
	def getDefaultSpace(self):
		account_url = 'https://' + self.domain + '/Account.aspx'
		data = {}
		data_prefix = 'ctl00$mainPlaceholder$AccountDetails$'
		data[data_prefix+'EditButton.x'] = 30
		data[data_prefix+'EditButton.y'] = 17
		r = self.submitForm(account_url, data)
		data = self.getForm(r.content)
		return data[data_prefix+'SpaceDropDown']
		
	# Set the default space from the logged in user
	# The space_key needs to be supplied, where:
	# space_key = space_name/space_id
	def setDefaultSpaceFomKey(self, space_key):
		account_url = 'https://' + self.domain + '/Account.aspx'
		data = {}
		data_prefix = 'ctl00$mainPlaceholder$AccountDetails$'
		data[data_prefix+'EditButton.x'] = 30
		data[data_prefix+'EditButton.y'] = 17
		r = self.submitForm(account_url, data)
		cookies = self.session.cookies.get_dict()
		data = self.getForm(r.content)
		#data[data_prefix+'LanguageBox'] = 'en-GB'
		data[data_prefix+'SpaceDropDown'] = space_key
		data[data_prefix+'UpdateButton.x'] = 30
		data[data_prefix+'UpdateButton.y'] = 17
		r = self.session.post(account_url, data=data, verify=False, cookies=cookies)
		
	# Set default space for the logged in user
	# This allows changing the space that the admin
	# webservice points to
	def setDefaultSpace(self, space_id):
		space_key = self.getSpaceKey(space_id)
		self.setDefaultSpaceFomKey(space_key)
		
	# Update the admin webservice to point to the
	# specified space
	def changeToSpace(self, space_id):
		self.setDefaultSpace(space_id)
		self.session = requests.Session()
		self.AdminClient = self.getAdminClient()
		
	# Get space object from space id
	# This function relies on the official webservice
	def getSpace(self, space_id):
	
		returned_spaces = self.WSClient.service.listSpaces(self.WSToken)
		
		for space in returned_spaces.UserSpace:
			if space.id == space_id:
				return space
		
	# Get space object from space name
	# This function relies on the official webservice
	def getSpaceFromName(self, space_name):
	
		returned_spaces = self.WSClient.service.listSpaces(self.WSToken)
		
		for space in returned_spaces.UserSpace:
			if space.name == space_name:
				return space
		
	# Get space id from a space name
	def getSpaceIdFromName(self, space_name):
		space = self.getSpaceFromName(space_name)
		return space.id
				
	# Get space key from a space_id
	# The space key is used to change the default
	# space for the logged in user
	def getSpaceKey(self, space_id):
		space = self.getSpace(space_id)
		return space.name + '/' + space.id
		
	# Exit the webservice session
	# This function reverts the default space for
	# the logged in user
	def exitSession(self):
		self.setDefaultSpaceFomKey(self.initial_space_key)