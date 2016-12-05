#-*- coding: utf-8 -*-
'''
Created on 2016. 11. 30
Updated on 2016. 12. 05
@author: Zeck
'''
from __future__ import print_function


class EC2(object):
	data = {}
	keys = ['Name', 'ID', 'IP', 'State', 'KeyName', 'AMI', 'InsType', 'SecurityGroup']

	def __init__(self, _instance=None):
		if _instance is None:
			pass

		# # TODO::will be changed
		self.data = dict((key, u'') for key in self.keys)
		name = u''
		if _instance.tags is not None:
			for tag in _instance.tags:
				if tag['Key'] == 'Name':
					name = tag['Value']

		self.data['Name'] = name
		self.data['ID'] = _instance.id
		self.data['IP'] = _instance.public_ip_address
		self.data['State'] = _instance.state['Name']
		self.data['KeyName'] = _instance.key_name
		self.data['AMI'] = _instance.image_id
		self.data['InsType'] = _instance.instance_type
		if len(_instance.security_groups)>0:
			self.data['SecurityGroup'] = _instance.security_groups[0]['GroupId']
		pass

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
		self.data[key] = value

	def __repr__(self):
		string = u', '.join(u'%s(%s)' % (key, self.data[key]) for key in self.keys)
		return u'{%s}' % string

	def json(self):
		string = u', '.join( u'"%s":"%s"'%(key, self.data[key]) for key in self.keys)
		return  u'{%s}' % string
