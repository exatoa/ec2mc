#-*- coding: utf-8 -*-
'''
Created on 2016. 12. 03
Updated on 2016. 12. 05
@author: Zeck
'''
from __future__ import print_function

import codecs
import datetime
import os
import threading
import time
from fabric.api import env, run, settings, hide
from fabric.exceptions import NetworkError
from data.ProxyContext import proxy_contexts

import warnings
warnings.filterwarnings("ignore", category=UnicodeWarning)


class AWSWatcher(object):
	'''
	request Log들을 모아줌
	'''
	savePath = u''
	keypairPath =  u''
	AccessLogPath = u'/var/log/squid/access.log'

	infos = {}
	period_data = 120
	period_view = 10
	status_worker = False

	check_count = 0
	def __init__(self, _period_data, _period_view, _cachePath, _keypairPath):
		self.savePath = _cachePath
		self.keypairPath = _keypairPath
		self.period_view = _period_view
		self.period_data  = _period_data
		self.cmd = u'w'
		self.working_count = 0
		self.node_count = 0
		pass

	def watcher(self):
		'''
		주기적을 화면을 갱신하여 출력
		:param period:
		:return:
		'''
		while True:
			os.system('cls')
			print (u'Refresh every %4d seconds\t\t\t\t%s (refreshed:%5d)'%(self.period_view, datetime.datetime.now(), self.check_count))
			print (u'----------------------------------------------* Logs *----------------------------------------------\n')
			users = self.infos.keys()
			users.sort()
			for user in users:
				regionStrs = {}
				for region in self.infos[user].keys():
					regionStrs[region] = u', '.join([u'%15s%s(%5d)'%(ip,
					                                                u'*' if  self.infos[user][region][ip]['status'] is True else u' ',
					                                                self.infos[user][region][ip]['cnt'])
					                                 for ip in self.infos[user][region].keys()]
					                                )
				userStr = u', '.join([u'[%15s: %s]'%(key, regionStrs[key]) for key in regionStrs.keys()])
				print(u'%10s:: %s'%(user, userStr))
			print (u'\n----------------------------------------------------------------------------------------------------')
			if self.status_worker is True:
				print(u'log checker is working (%d/%d)...'%(self.working_count, self.node_count))
			time.sleep(self.period_view)

	####################################################
	# unit command
	####################################################
	def init_log(self, _ip, _key):
		'''
		특정 machine의 log를 초기화
		:param _ip:
		:param _key:
		:return:
		'''
		env.host_string = 'ubuntu@%s' % _ip
		env.key_filename = [self.keypairPath + '%s.pem' % _key]

		with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
			res = run('sudo truncate -s 0 %s ' % (self.AccessLogPath))
		return True if res ==u'' else False

	def get_remote_log(self, _user, _region, _ip, _key):
		'''
		copy remote logs and return result lines
		:param _user:
		:param _region:
		:param _ip:
		:param _key:
		:return:
		'''
		#setting environment
		env.host_string = 'ubuntu@%s' % _ip
		env.key_filename = [self.keypairPath + '%s.pem' % _key]

		# load remote log file
		res = u''
		try:
			with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
				res = run('sudo cat %s'%self.AccessLogPath)
		except NetworkError, e:
			print (e)
			return False

		#save log
		res = res.strip()
		if res==u'' or res.startswith(u'cat: /var/log'):
			lines = []
		else:
			lines = res.split(u'\n')
			writer = codecs.open(os.path.join(self.savePath, u'%s.log'%_ip), 'w', 'utf-8')
			for line in lines:
				writer.write(u'%s\t%s\t%s\t%s\n'%(_user, _region, _ip, line))
				writer.flush()
			writer.close()
		return len(lines)

	####################################################
	# group command
	####################################################
	def instances_iterator(self):
		users = proxy_contexts.keys()
		users.sort()
		for user in users:
			for region in proxy_contexts[user].keys():
				for instance in proxy_contexts[user][region]:
					yield user, region, instance
		pass

	def initialize_remote_log(self):
		'''
		clear log for remote logs
		:return:
		'''
		print(u'[AWSWatcher] initialize_remote_log')
		#initialize logs
		for user, region, instance in self.instances_iterator():
			if self.cmd == u'x':return
			if self.init_log(instance['IP'], instance['KEY']):
				print(u'%s\t%s\t%s\t%s\t success.' % (user, region, instance['ID'], instance['IP']))
			else:
				print(u'%s\t%s\t%s\t%s\t Error.' % (user, region, instance['ID'], instance['IP']))
		print(u'[AWSWatcher] initialize_remote_log done.')
		pass

	def get_check_states(self):
		'''
		works in thread checking worker log states
		:return:
		'''
		while True:
			self.status_worker = True
			self.working_count = 0
			for user, region, instance in self.instances_iterator():
				self.working_count += 1
				self.infos[user][region][instance['IP']]['status'] = True

				cnt = self.get_remote_log(user, region, instance['IP'], instance['KEY'])
				self.infos[user][region][instance['IP']]['cnt'] = cnt
				self.infos[user][region][instance['IP']]['status'] = False
			self.check_count += 1
			self.status_worker = False
			time.sleep(self.period_data)
		return

	####################################################
	# main command
	####################################################
	def run(self):
		'''
		스레드들을 생성하고 명령에 따라 프로그램 수행하도록 함
		:return:
		'''
		threads = []
		if os.path.exists(self.savePath) is False:
			os.makedirs(self.savePath)

		# 설정
		for user, region, instance in self.instances_iterator():
			if user not in self.infos:
				self.infos[user] = {}
			if region not in self.infos[user]:
				self.infos[user][region] = {}
			self.infos[user][region][instance['IP']] = {'cnt':0,'status':False}
			self.node_count += 1

		# copy logs (각자 적절한 주기로 데이터 갱신함)
		t = threading.Thread(target=self.get_check_states())
		t.setDaemon(True)
		t.start()
		threads.append(t)

		# watcher 실행
		t = threading.Thread(target=self.watcher)
		t.setDaemon(True)
		t.start()
		threads.append(t)

		#print(u'waiting for quitting thread...')
		for t in threads:
			t.join()
		print(u'Done. Bye!')

###############################################################################################################
###############################################################################################################
###############################################################################################################

if __name__ == '__main__':
	obj = AWSWatcher(120, 15, u'D:/works/#Amazon/logs/', u'D:/works/#Amazon/key_pairs/')
	obj.run()
	pass




