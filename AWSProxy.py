#-*- coding: utf-8 -*-
'''
Created on 2016. 12. 03
Updated on 2016. 12. 03
This class is for example of using EC2MultiController
@author: Zeck
'''
from __future__ import print_function
import os
import codecs
import threading
import time
from fabric.api import env, run, settings, hide
from ec2mc import EC2Controller

import warnings
warnings.filterwarnings("ignore", category=UnicodeWarning)


class AWSProxy(EC2Controller):
	'''
	This class is example of making multi proxy server
	This class need to install fabric :: pip install fabric
	if you want to test this file,
	upload squid.conf in same directory to some web server change squidSettingURL property
	'''
	__name__ = u'AWSProxy'
	squidSettingURL = u'http://52.78.230.52/squid.conf'
	squidPort = 20160
	OutputFileName = 'data/ProxyList.py'

	appLock = None
	def __init__(self, _settings):
		super(AWSProxy, self).__init__(_settings)

		self.appLock = threading.Lock()
		pass

	def server_application(self, _user, _region, _ipAddr, _keypairPath):
		'''
		this function meke a instance as a proxy server using squid
		1. install squid
		2. change setting file
		3. service restart
		:param _user:
		:param _region:
		:param _ipAddr:
		:param _keypairPath:
		:return:
		'''
		header = u'[%s] %s, %s ::' % (self.__name__, _user, _region)
		env.host_string = 'ubuntu@%s' % _ipAddr
		env.key_filename = [_keypairPath]  #os.path.join(self.config.KEY_PAIR_PATH, '%s.pem' % _keyName),]

		while True:
			self.appLock.acquire()
			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run('sudo apt-get -y install squid')

			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run('service	squid view')
			if res.startswith('Usage: /etc/init.d/squid') is True:
				self.appLock.release()
				break
			self.appLock.release()
			time.sleep(5)
		print(u'%s installed squid' % header)

		while True:
			self.appLock.acquire()
			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run('sudo wget %s -O /etc/squid/squid.conf' % self.squidSettingURL)

			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run('cat /etc/squid/squid.conf | grep "^http_port"')

			if res.startswith('http_port %d' % self.squidPort) is True:
				self.appLock.release()
				break
			self.appLock.release()
			time.sleep(5)
		print(u'%s copied squid config file.' % header)

		while True:
			self.appLock.acquire()
			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run('sudo service squid restart')

			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run('netstat -nat tcp | grep %d | grep LISTEN' % self.squidPort)

			if res.startswith('tcp') is True:
				self.appLock.release()
				break
			self.appLock.release()
			time.sleep(5)
		print(u'%s squid service restarted.' % header)
		return True

	def creates(self, _nInstances, _nThreads):

		super(AWSProxy, self).creates(_nInstances, _nThreads)

		self.store_proxy_list(self.instances)
		print(u'[%s] wrote data to ProxyList.py' % self.__name__)
		return

	def store_proxy_list(self, _instances):
		# if os.path.exists(self.config.OUTPUT_PATH) is False:
		# 	os.makedirs(self.config.OUTPUT_PATH)

		#filepath = os.path.join(self.config.OUTPUT_PATH, self.OutputFileName)
		f = codecs.open(self.OutputFileName, 'w', 'utf-8')
		f.write(self.convert_instances_to_proxylist(_instances))
		f.close()
		pass

	def convert_instances_to_proxylist(self, _instances):
		hostStr = u''
		for user in _instances.keys():
			for region in _instances[user].keys():
				for machine in _instances[user][region]:
					if machine['IP'] is None or machine['IP'] == u'': continue
					hostStr += u"\t{'http':'http://%s:%d', 'https':'http://%s:%d'},\n" % (machine['IP'],
																						  self.squidPort,
																						  machine['IP'],
																						  self.squidPort)
		# make final text
		if hostStr.endswith(u',\n') is True:
			hostStr = hostStr[:-2]
		result = u'#-*- coding: utf-8 -*-\nproxies = [\n' + hostStr + u'\n]'
		return result

	def start_watcher(self):
		from AWSWatcher import AWSWatcher
		obj = AWSWatcher(120, 15, os.path.join(self.config.OUTPUT_PATH, u'logs'), self.KEY_PAIR_PATH)
		obj.run()
		pass

	def clear_remote_logs(self):
		from AWSWatcher import AWSWatcher
		obj = AWSWatcher(120, 15, os.path.join(self.config.OUTPUT_PATH, u'logs'), self.KEY_PAIR_PATH)
		obj.initialize_remote_log()
		pass


###############################################################################################################
###############################################################################################################
###############################################################################################################
def getargs():
	import argparse
	parser = argparse.ArgumentParser(description='')
	parser.add_argument('-s', dest='server', default='', help='server command   (create / local / remote / clear / clear_force) ')
	parser.add_argument('-l', dest='log', default='', help='log commands ( watch / clear )')
	args = parser.parse_args()

	if ((args.server == '') ^ (args.log == '') ) == False :
		parser.print_help()
		return None
	return args

if __name__ == '__main__':
	args = getargs()
	if args is None:
		exit(1)

	obj = AWSProxy(_settings=u'AWSsettings.py')
	if args.command == 'create':
		obj.creates(_nInstances=2, _nThreads=5)

	elif args.command == 'local':
		obj.show_local_status()

	elif args.command == 'remote':
		obj.show_remote_status()

	elif args.command == 'clear':
		obj.clear()

	elif args.command == 'clear_force':
		obj.clear_with_remote()

	elif args.logs == 'watch':
		obj.start_watcher()

	elif args.command == 'clear':
		obj.clear_remote_logs()

	# save proxy
	# instaces = obj.load_local_status()
	# obj.store_proxy_list(instaces)

	# 보조 작업들
	# [u'i-0988f737e76564dc5', u'i-0265af93a235874a6']
	# obj.delete_instance(_instanceIDs=[])

	# obj.reset_user_application(_serverIPs=[u' 35.154.71.132', u'52.78.64.253'])
	# obj.delete_all_key_pairs()
	# obj.delete_all_security_groups()

