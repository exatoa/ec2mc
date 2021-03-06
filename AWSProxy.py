#-*- coding: utf-8 -*-
'''
Created on 2016. 12. 03
Updated on 2016. 12. 06
This class is for example of using MultiEC2Controller
@author: Zeck
'''
from __future__ import print_function
import os
import codecs
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

		self.remote_command(_executeCmd='sudo apt-get -y install squid',
		                    _verifyCmd='service squid view',
		                    _assertText='Usage: /etc/init.d/squid')
		print(u'%s installed squid' % header)

		self.remote_command(_executeCmd='sudo wget %s -O /etc/squid/squid.conf' % self.squidSettingURL,
		                    _verifyCmd='cat /etc/squid/squid.conf | grep "^http_port"',
		                    _assertText='http_port %d' % self.squidPort)
		print(u'%s copied squid config file.' % header)

		self.remote_command(_executeCmd='sudo service squid restart',
		                    _verifyCmd='netstat -nat tcp | grep %d | grep LISTEN' % self.squidPort,
		                    _assertText='tcp')
		print(u'%s squid service restarted.' % header)
		return True


	def remote_command(self, _executeCmd, _verifyCmd, _assertText):
		'''
		fabric을 이용해서 원격서버에 명령을 수행
		:param _executeCmd: 실행하고자 하는 명령문
		:param _verifyCmd: 실행결과를 확인하기 위해 사용할 검증 명령문, 없으면 None
							만약 이 명령이 없으면 _assertText는 _executeCmd의 결과와 비교
		:param _assertText: 실행이 잘 되었는지 확인하는 문장, _assertText가 없으면 확인없이 종료
		:return:
		'''
		while True:
			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run(_executeCmd)

			if _verifyCmd is not None:
				with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
					res = run(_verifyCmd)

			if _assertText is not None:
				if res.startswith(_assertText) is True:
					break
			else:
				break
			time.sleep(5)
		pass

	def creates(self, _nInstances, _nThreads):
		'''
		Overwrite clear method
		:return:
		'''
		super(AWSProxy, self).creates(_nInstances, _nThreads)
		self.store_proxy_list(self.instances)
		print(u'[%s] wrote data to %s' % (self.__name__, self.OutputFileName))
		pass

	def clear(self):
		'''
		Overwrite clear method
		:return:
		'''
		super(AWSProxy, self).clear()
		self.store_proxy_list(dict())
		print(u'[%s] wrote data to %s' % (self.__name__, self.OutputFileName))
		pass

	def clear_with_remote(self):
		'''
		Overwrite clear method
		:return:
		'''
		super(AWSProxy, self).clear_with_remote()
		self.store_proxy_list(dict())
		print(u'[%s] wrote data to %s' % (self.__name__, self.OutputFileName))
		pass

	def store_proxy_list(self, _instances):
		f = codecs.open(self.OutputFileName, 'w', 'utf-8')
		f.write(self.convert_instances_to_proxylist(_instances))
		f.close()
		pass

	def convert_instances_to_proxylist(self, _instances):
		hostStr = u''
		for user in _instances.keys():
			for region in _instances[user].keys():
				for node in _instances[user][region]:
					if node['IP'] is None or node['IP'] == u'': continue
					hostStr += u"\t{'http':'http://%s:%d', 'https':'http://%s:%d'},\n" \
								% (node['IP'], self.squidPort, node['IP'], self.squidPort)
		# make final text
		if hostStr.endswith(u',\n') is True:
			hostStr = hostStr[:-2]
		result = u'#-*- coding: utf-8 -*-\nproxies = [\n' + hostStr + u'\n]'
		return result

	def start_watcher(self):
		'''
		Start AWSWatcher
		:return:
		'''
		from utils.AWSWatcher import AWSWatcher
		instances = self.load_local_status()
		obj = AWSWatcher(120, 15, os.path.join(self.config.OUTPUT_PATH, u'logs'), self.KEY_PAIR_PATH)
		obj.run(instances)
		pass

	def clear_remote_logs(self):
		'''
		Start AWSWatcher clear log
		:return:
		'''
		from utils.AWSWatcher import AWSWatcher
		instances = self.load_local_status()
		obj = AWSWatcher(120, 15, os.path.join(self.config.OUTPUT_PATH, u'logs'), self.KEY_PAIR_PATH)
		obj.initialize_remote_log(instances)
		pass


###############################################################################################################
###############################################################################################################
###############################################################################################################
def getargs():
	import argparse
	parser = argparse.ArgumentParser(description='Mulit Account AWS Proxy server Management Program')
	parser.add_argument('-s', dest='server', default='', help='server command\n(create / local_status / remote_status / clear / clear_force) ')
	parser.add_argument('-l', dest='log', default='', help='log commands ( watch / clear )')
	parser.add_argument('-n', dest='nInstances', type=int, default=2, help='the number of instances will be created each account')
	parser.add_argument('-t', dest='nThreads', type=int, default=5, help='the number of thread will be used for working')
	args = parser.parse_args()

	if ((args.server == '') ^ (args.log == '') ) == False :
		parser.print_help()
		return None, None
	return parser, args

if __name__ == '__main__':
	parser, args = getargs()
	if args is None:
		exit(1)

	obj = AWSProxy(_settings=u'sample/AWSsettings.py')
	if args.server == 'create':
		obj.creates(_nInstances=args.nInstances, _nThreads=args.nThreads)

	elif args.server == 'local_status':
		obj.show_local_status()

	elif args.server == 'remote_status':
		obj.show_remote_status()

	elif args.server == 'clear':
		obj.clear()

	elif args.server == 'clear_force':
		obj.clear_with_remote()

	elif args.log == 'watch':
		obj.start_watcher()

	elif args.log == 'clear':
		obj.clear_remote_logs()

	else:
		print ('   wrong command!!!')
		parser.print_help()