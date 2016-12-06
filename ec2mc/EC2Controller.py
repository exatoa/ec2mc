#-*- coding: utf-8 -*-
'''
Created on 2016. 12. 03
Updated on 2016. 12. 05
@author: Zeck
'''
from __future__ import print_function
import os
import imp
import codecs
import threading
import time
import random
import types
from importlib import import_module
from Queue import Queue
from threading import Thread
from AmazonUtils import AmazonUtils
from AmazonInfo import *

import warnings
warnings.filterwarnings("ignore", category=UnicodeWarning)


class EC2Controller(object):
	'''
	Create and Manage EC2 instance to multiple accounts.
	Use this class with subclassing.
	You should offer the settings file as python script type to use this function.
	Reference description below about config variable
	If you want to make application in servers, you need to overwrite a function server_application.
	'''
	__name__ = u'EC2Controller'
	# User config file
	# this file should be python script and include following variables:
	#	* OUTPUT_PATH = u'/home/user/amazon/'
	#                   The location to save working files
	#                   We will make a file containing server informations
	#                   and also save key pairs in ./key_paris/ created from each account and each region
	#
	#	* NODENAME = u'nodename'
	#                the tag name for each instance to distinguish instances made by this program
	#
	#	* ACCOUNTS = {'identity':{'access_key':'...', 'secret_key':'...'}, ... }
	#				 The accounts information, you should give access_key and secret_access_key
	# 				 If you don't have the keys, visit the amazon page "My security credentials"
	# 				 and create new Access Key.
	#
	config = None

	# Internal object, this object has reference of AmazonUtils class.
	utils = None

	def __init__(self, _settings):
		self.config = self.import_setting(_settings)
		if self.config is None:
			raise Exception()

		self.LOCAL_STATUS_FILE = os.path.join(self.config.OUTPUT_PATH, u'Instances.py')
		self.KEY_PAIR_PATH = os.path.join(self.config.OUTPUT_PATH, u'key_pairs')
		self.utils = AmazonUtils(self.config.ACCOUNTS, self.KEY_PAIR_PATH)
		self.awsLock = threading.Lock()
		pass

	def import_setting(self, _settings):
		'''
		module import by filename
		:param _settings:
		:return:
		'''
		fullpath = os.path.abspath(_settings)
		path, name = os.path.split(fullpath)
		fp = None
		try:
			fp = open(fullpath, 'r')
			module = imp.load_source('module.name', path, fp)
		except Exception, e:
			module = None
		finally:
			# Since we may exit via an exception, close fp explicitly.
			if fp:
				fp.close()

		#verify settings
		for attr in ['NODE_NAME', 'OUTPUT_PATH', 'OS_TYPE', 'INSTANCE_TYPE', 'SECURITY_GROUP', 'ACCOUNTS']:
			if not hasattr(module, attr):
				return None

		if isinstance(module.NODE_NAME, types.StringTypes) is False:
			return None
		if isinstance(module.OUTPUT_PATH, types.StringTypes) is False:
			return None
		if isinstance(module.OS_TYPE, types.StringTypes) is False:
			return None
		if isinstance(module.INSTANCE_TYPE, types.StringTypes) is False:
			return None
		if isinstance(module.SECURITY_GROUP, types.DictionaryType) is False:
			return None
		if isinstance(module.ACCOUNTS, types.DictionaryType) is False:
			return None

		return module


	################################################################################
	# managing local instances information
	################################################################################
	def convert_instances_to_text(self, _instances=None):
		'''
		Convert to text from instances dictionary
		:param _instances: the dictionary contains instances information
		:return: text representing instances
		'''
		instances = _instances if _instances is not None else self.instances

		result = u''
		try:
			# convert text
			users = instances.keys()
			users.sort()
			result = u'{\n'
			for user in users:
				regions = instances[user].keys()
				regions.sort()

				regionJSON = u''
				for region in regions:
					machineJSON = u',\n'.join(u'\t\t\t' + machine.json() for machine in instances[user][region])
					if machineJSON != u'':
						regionJSON += u'\t\t"%s":[\n%s\n\t\t],\n' % (region, machineJSON)

				result += u'\t"%s":{\n%s\n\t},\n' % (user, regionJSON[:-2])

			if result.endswith(u',\n'):
				result = result[:-2] + u'\n'
			result = result + u'}'

		except Exception, e:
			return None
		return result

	def store_local_status(self, _infos):
		'''
		Convert from dictionary _infos to text and Save in Instances.py in OUTPUT PATH
		:param _infos: dictionary contains instances information
						{'user_identity':{'region_name':[EC2(), ...], ...}, ...}
		:return: boolean
		'''
		if os.path.exists(self.config.OUTPUT_PATH) is False:
			os.makedirs(self.config.OUTPUT_PATH)

		text = self.convert_instances_to_text(_infos)

		try:
			f = codecs.open(self.LOCAL_STATUS_FILE, 'w', 'utf-8')
			f.write(u'instances = ' + text)
			f.close()
		except IOError, e:
			return False
		return True

	def load_local_status(self):
		'''
		load local instances status from LOCAL_STATUS_FILE
		:return:
		'''
		if os.path.exists(self.LOCAL_STATUS_FILE) is False:
			return None

		fullpath = os.path.abspath(self.LOCAL_STATUS_FILE)
		path, name = os.path.split(fullpath)
		fp = None
		try:
			fp = open(fullpath, 'r')
			module = imp.load_source('module.name', path, fp)
		except Exception, e:
			module = None
		finally:
			# Since we may exit via an exception, close fp explicitly.
			if fp:
				fp.close()
		return module.instances

	################################################################################
	# retriving part
	################################################################################
	def load_remote_status(self, _users=None, _filter_name=None, _filter_state=None, _showProgress=False):
		'''
		Getting instance status in accounts corresponding _users
		if no parameters, this function returns all instances in accounts
		:param _users: User identities that you want to get
		:param _filter_name: A specific tag name that you want to get status
		:param _filter_state: Specific states of instances that you want to get
		:param _showProgress: show the progress in console
		:return: the information dictionary  {'user_identity': {'region_name':[EC2(), EC2(), ...], ...}, ...}
		'''
		users = self.config.ACCOUNTS.keys() if _users is None or len(_users)==0 else _users
		users.sort()
		regions = REGIONS.keys()
		regions.sort()

		results = dict((user, dict()) for user in users)  #initialize infos as {user1:{}, user2:{}, ...}
		for user in users:
			if _showProgress is True: print(u'\t' + user + u' checking...', end=u'')

			for region in regions:
				if _showProgress is True: print(REGIONS[region] + u', ', end=u'')

				instances = self.utils.get_instances_state(user, region, _filter_name=_filter_name, _filter_state=_filter_state)
				if len(instances)==0: continue
				results[user][region] = instances

			if _showProgress is True: print(u' Done.')
		return results

	def count_instances_each_user(self, _info):
		'''
		Make a summary of instances' count for each account
		:param _info:
		:return:
		'''
		users = _info.keys()
		users.sort()

		statistics = dict((user, 0) for user in self.config.ACCOUNTS.keys())  # initialize _info as {user1:{}, user2:{}, ...}
		for user in users:
			for region in _info[user].keys():
				statistics[user] += len(_info[user][region])

		return statistics

	def show_local_status(self):
		'''
		show local instances information
		result file이 있는 경우, 파일을 읽어서 보여주고 아니면 정보 새로로드.
		:return:
		'''
		# load instances infomation
		instances = self.load_local_status()

		users = instances.keys()
		users.sort()
		print(u'----------------* Usage Information (local)*----------------')
		print(self.convert_instances_to_text(instances))
		# for user in users:
		# 	print(user + u':::::')
		# 	regions = instances[user].keys()
		# 	regions.sort()
		# 	for region in regions:
		# 		for machine in instances[user][region]:
		# 			print(u'\t%s:: %s'%(REGIONS[region], machine))
		print(u'---------------------------------------------------------')
		pass

	def show_remote_status(self):
		results = self.load_remote_status(_showProgress=True)	#retrieving full information

		users = results.keys()
		users.sort()
		print(u'----------------* Usage Information (Remote)*----------------')
		print(self.convert_instances_to_text(results))
		# for user in users:
		# 	print(user + u':::::')
		# 	regions = results[user].keys()
		# 	regions.sort()
		# 	for region in regions:
		# 		for machine in results[user][region]:
		# 			print(u'\t%s:: %s' % (REGIONS[region], machine))
		print(u'---------------------------------------------------------')
		pass

	################################################################################
	# creation part
	################################################################################
	instances = {}		# the dictionary contains instances information,
						# This variable works in thread. use carefully
	work_queue = None	# work queue
	awsLock = None		# This program works in thread, so it needs the locks.
	dataLock = None		# This program works in thread, so it needs the locks.

	def creates(self, _nInstance, _nThreads):
		'''
		Craete EC2 instances as much as nInstance each account.
		This function finally make a result file that include each instances' status info.
		If a account has over _nInstance instance, this function don't caeate more instance.

		** If you want to make instances to fit for your application,
			you should override server_application function.
			I recommend you use fabric library. this library make you to control your remote instance with SSH.

		:param _nInstance: the number of instance that will make it each account
		:param _nThreads: the number of thread to work for creating works
		:return: True or False
		'''
		# collecting previous instance's information
		print(u'[%s] Checking previous state for all users...'%self.__name__)
		self.instances = self.load_remote_status(_filter_name=self.config.NODE_NAME, _filter_state='working', _showProgress=True)
		self.store_local_status(self.instances)
		print(u'[%s] Done.'%self.__name__)


		# show statistics
		statistics = self.count_instances_each_user(self.instances)
		statStr = u', '.join(u'%s(%d)'%(user, statistics[user]) for user in statistics.keys())
		print(u'[%s] statistics:: %s'%(self.__name__, statStr))

		# Create Instance at random place
		self.work_queue = Queue()
		for user in self.config.ACCOUNTS.keys():
			for idx in range(statistics[user], _nInstance):
				random_idx = random.randint(0, len(REGIONS) - 1)
				region = REGIONS.keys()[random_idx]
				self.work_queue.put((user, region))

		if self.work_queue.empty() is True:
			print(u'[%s] all accounts already has %d instances.' % (self.__name__, _nInstance))
			self.store_local_status(self.instances)
			return self.instances

		# create thread pool
		# Making new instances!! (in limited nInstances)
		print(u'[%s] Making working threads.....' % (self.__name__))
		for i in range(_nThreads):
			t = Thread(target=self.create_node_worker)
			t.daemon = True
			t.start()

		# waiting works done.
		self.work_queue.join()
		self.store_local_status(self.instances)

		time.sleep(60)  # delay

		# make server to fit for user application
		for user in self.instances.keys():
			for region in self.instances[user].keys():
				for instance in self.instances[user][region]:
					print(u'[%s] %s, %s :: IP %s assigned, starting to set it up...' % (self.__name__, user, REGIONS[region], instance['IP']))
					keypair =  os.path.join(self.KEY_PAIR_PATH, u'%s.pem' % instance['KeyName'])
					ret = self.server_application(user, REGIONS[region], instance['IP'],keypair)
					if ret is True:
						print(u'[%s] %s, %s :: %s server is prepared!' % (self.__name__, user, REGIONS[region], instance['IP']))
					else:
						print(u'[%s] %s, %s :: %s failed to setting as user application.' % (self.__name__, user, REGIONS[region], instance['IP'] ))

		# Save new InstInfo (InstInfo will be updated in threads.)
		self.store_local_status(self.instances)
		print(u'[%s] wrote data to local status'%(self.__name__))

		print(u'[%s] Completely Done.'% self.__name__)
		return self.instances

	def create_node_worker(self):
		'''
		Create a node with information in queue
		This function works in thread
		:return: None
		'''
		while True:
			user, region = self.work_queue.get()
			header = u'[%s] %s, %s ::'%(self.__name__, user, REGIONS[region])

			# create instance
			self.awsLock.acquire()
			res = self.utils.create_ec2(self.config.NODE_NAME,
										_user=user,
										_region=region,
										_os_type=self.config.OS_TYPE,
										_instance_type=self.config.INSTANCE_TYPE,
										_security_group=self.config.SECURITY_GROUP)
			if res['status'] == 'error':
				print(u'%s create instance Error!\n%s' % (header, res))
				return
			instance = res['instance']
			print(u'%s Created a instance ID(%s)!' % (header, instance['ID']))
			self.awsLock.release()

			# waiting server is ready
			print(u'%s Waiting server is ready...' % header)
			while True:
				time.sleep(10)
				self.awsLock.acquire()
				isPass = self.utils.check_ec2_ready(user, region, instance['ID'])
				self.awsLock.release()
				if isPass is True:
					break

			# changed information save
			self.awsLock.acquire()
			instance = self.utils.get_instance(user, region, instance['ID'])
			if region not in self.instances[user]:
				self.instances[user][region] = list()
			self.instances[user][region].append(instance)
			self.store_local_status(self.instances)
			self.awsLock.release()

			#change queue states.
			self.work_queue.task_done()
		return

	def reset_user_application(self, _serverIPs = None):
		'''
		Reset instances with user application
		If the instance is not working properly, you can execute this function
		If you don't designate server IPs, this function reset all instances
		:param _server_ips: list of server IP addr
		:return: None
		'''
		instances = self.load_local_status()
		if instances is None:
			print(u'[%s] There are no local status file. Please execute create!'%self.__name__)
			return

		works = []
		# make working list
		for user in instances.keys():
			for region in instances[user].keys():
				for inst in instances[user][region]:
					if _serverIPs is None:
						works.append({'IP': inst['IP'], 'Name': inst['KeyName']})
					else:
						for addr in _serverIPs:
							works.append({'IP': addr, 'KeyName': inst['KeyName']}) if inst['IP'] == addr else None

		# do works
		for item in works:
			print(u'WorkFor : %s, %s'%(item['IP'], item['KeyName']))
			obj.server_application(item['IP'], item['KeyName'])
		pass

	def server_application(self, _user, _region, _ipAddr, _keypairPath):
		'''
		This function should be overrided for your application
		Now, This function is noting
		:param _user: user identity to work instance
		:param _region: region name to work instance
		:param _ipAddr: IP address to work instance
		:param _keypairPath: local key pair file path stored in local KEY_PAIR_PATH
		:return:
		'''
		pass

	################################################################################
	# deleting part
	################################################################################
	def clear(self):
		'''
		Clear all instances using local instances status
		:return: None
		'''
		#load instances infomation
		instances = self.load_local_status()
		self.clear_worker(instances)
		pass

	def clear_with_remote(self):
		'''
		Clear all instances with remote instances information
		:return: None
		'''
		# collecting previous instance's information
		print(u'[%s] Checking previous state for all users...' % self.__name__)
		instances = self.load_remote_status(_filter_name=self.config.NODE_NAME, _filter_state='working',
												 _showProgress=True)
		print(u'[%s] Done.' % self.__name__)

		self.clear_worker(instances)
		pass

	def clear_worker(self, _instances):
		'''
		Clear all instances
		First, terminate all instances
		Second, delete key pair and security group after all instances terminated
		:param _instances: instance informations
		:return:
		'''
		# show statistics
		statistics = self.count_instances_each_user(_instances)
		statStr = u', '.join(u'%s(%d)' % (user, statistics[user]) for user in statistics.keys())
		print(u'[%s] statistics:: %s' % (self.__name__, statStr))

		# terminate all machines
		for user in _instances.keys():
			print(u'[%s] %s terminating instances...' % (self.__name__, user), end=u'')
			for region in _instances[user].keys():
				targets = [inst['ID'] for inst in _instances[user][region]]
				self.utils.delete_ec2(user, region, targets)
				print(u'%s(%d), ' % (region, len(targets)), end=u'')
			print(u' Done.')

		# delete key name and security group
		for user in _instances.keys():
			for region in _instances[user].keys():
				insts = self.utils.get_instances(user, region, self.config.NODE_NAME)
				flag = True
				for inst in insts:
					if inst['State'] != 'terminated':
						flag = False
				if flag is True:
					inst = _instances[user][region][0]
					self.utils.delete_security_group(user, region, inst['SecurityGroup'])
					self.utils.delete_key_pair(user, region, inst['KeyName'])
					print(u'[%s] security group and key pair deleted in %s %s.' % (self.__name__, user, region))
				else:
					print(u'[%s] waiting %s %s instances terminated...' % (self.__name__, user, region))
					time.sleep(60)
		print(u'[%s] Completely Deleted all instances.'% self.__name__)

		self.store_local_status({})
		pass

	def delete_instance(self, _instanceIDs):
		'''
		Delete instances corresponding _instanceIDs
		This function do not delete security group and key pair.
		:param _targets: the list of instance ID
		:return: None
		'''
		# load instances infomation
		instances = self.load_local_status()

		# find mapping information
		info = []
		for user in instances.keys():
			for region in instances[user].keys():
				for instance in instances[user][region]:
					for id in _instanceIDs:
						if id == instance['ID']:
							info.append({'user':user, 'region':region, 'id':id})

		for item in info:
			response = self.utils.delete_ec2(item['user'], item['region'], item['id'])
			print (u'[%s] %s terminated in %s %s'%(self.__name__, item['id'], item['user'], item['region']))
			print (u'[%s] response=%s'%(self.__name__, response))
		print(u'[%s] Deleted all instances.')
		pass

	def delete_all_key_pairs(self):
		'''

		:return:
		'''
		for user in self.config.ACCOUNTS.keys():
			print(u'[%s] %s removing key_pair...' % (self.__name__, user), end=u'')
			for region in REGIONS.keys():
				print(u'%s, ' % REGIONS[region], end=u'')
				#self.utils.delete_security_group()
				self.utils.delete_key_pair(user, region, user + u'-' + region)
			print(u'Done')
		pass

	def delete_all_security_groups(self):
		'''

		:return:
		'''
		for user in self.config.ACCOUNTS.keys():
			print(u'[%s] %s removing security_groups...' % (self.__name__, user), end=u'')
			for region in REGIONS.keys():
				print(u'%s, ' % REGIONS[region], end=u'')
				id_list = self.utils.search_security_group(user, region, self.config.SECURITY_GROUP['name'])
				for idstr in id_list:
					self.utils.delete_security_group(user, region, idstr)
			print(u'Done')
		pass

###############################################################################################################
###############################################################################################################
###############################################################################################################
if __name__ == '__main__':
	obj = EC2Controller(_settings=u'setting.py')


