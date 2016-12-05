#-*- coding: utf-8 -*-
'''
Created on 2016. 12. 03
Updated on 2016. 12. 03
@author: Zeck
'''
from __future__ import print_function
import boto3
import os
from botocore.exceptions import ClientError
from EC2 import EC2
from AmazonInfo import *

class AmazonUtils:
	'''
	Amazon Web Service control utilities
	This class works in boto3
	'''
	accounts = None
	keypairPath = None

	def __init__(self, _accounts, _keyset):
		self.accounts = _accounts
		self.keypairPath = _keyset

		if os.path.exists(self.keypairPath) is False:
			os.makedirs(self.keypairPath)
		pass

	def get_session(self, _user, _region):
		session = boto3.session.Session(
			aws_access_key_id=self.accounts[_user]['access_key'],
			aws_secret_access_key=self.accounts[_user]['secret_key'],
			region_name=_region
		)
		return session

	#################################################################
	# security_group
	#################################################################
	def create_security_group(self, _user, _region, _security_group):
		'''
		Create security_group in amazon account at specific region
		:param _user: account identity existing in settings.py
		:param _region: region that specified by user
		:param _security_group: dictionary describing security_group
				ex) {'name':'', 'desc':'', 'rules':[
							{'cidr':'0.0.0.0/0, 'protocol':'tcp', 'from_port':80, 'to_port':80},
							...
						]
					}
		:return:
		'''
		#Check already exists Security Group
		session = self.get_session(_user, _region)
		ec2_client = session.client('ec2')
		response = ec2_client.describe_security_groups()
		groups = response['SecurityGroups']
		for remote_group in groups:
			if _security_group['name'] == remote_group['GroupName']:
				return remote_group['GroupId']

		#make new SGID
		response = ec2_client.create_security_group(GroupName=_security_group['name'],
													Description=_security_group['desc'])
		for rule in _security_group['rules']:
			ec2_client.authorize_security_group_ingress(GroupId=response['GroupId'],
														IpProtocol=rule['protocol'],
														CidrIp=rule['cidr'],
														FromPort=rule['from_port'],
														ToPort=rule['to_port'])
		return response['GroupId']

	def update_security_group(self, _user, _region, _security_group):
		'''
		update security_group
		:param _user: account identity existing in settings.py
		:param _region: region that specified by user
		:param _security_group: dictionary describing security_group
				ex) {'name':'', 'desc':'', 'rules':[
							{'cidr':'0.0.0.0/0, 'protocol':'tcp', 'from_port':80, 'to_port':80},
							...
						]
					}
		:return: security group ID
		'''

		# Check already exists Security Group
		session = self.get_session(_user, _region)
		ec2_client = session.client('ec2')
		result = ec2_client.describe_security_groups(GroupNames=[_security_group['name'],])
		if len(result['SecurityGroups'])==0:
			return False
		response = result['SecurityGroups'][0]

		# delete previous rules
		ec2_client.revoke_security_group_ingress(IpPermissions=response['IpPermissions'])

		# create new rules
		for rule in _security_group['rules']:
			ec2_client.authorize_security_group_ingress(GroupId=response['GroupId'],
														IpProtocol=rule['protocol'],
														CidrIp=rule['cidr'],
														FromPort=rule['from_port'],
														ToPort=rule['to_port'])
		return response['GroupId']

	def delete_security_group(self, _user, _region, _groupID):
		'''
		Delete a specific security_group
		:param _user: account identity existing in settings.py
		:param _region: region that specified by user
		:param _groupID: security group ID
		:return: None
		'''
		session = self.get_session(_user, _region)
		ec2 = session.client('ec2')
		ec2.delete_security_group(GroupId=_groupID)
		pass

	def search_security_group(self, _user, _region, _security_group_nme):
		IDs = []
		session = self.get_session(_user, _region)
		ec2_client = session.client('ec2')
		try:
			response = ec2_client.describe_security_groups(GroupNames=[_security_group_nme])
			for group in response['SecurityGroups']:
				IDs.append(group['GroupId'])
		except ClientError, e:
			return IDs
		return IDs

	#################################################################
	# key_pair
	#################################################################
	def create_key_pair(self, _user, _region, _keyName):
		'''
		Create new key pair in specific region in user
		If the key pair is exists, returns exist key name.
		:param _user: Account identity existing in settings.py
		:param _region: Region that specified by user
		:param _keyName: key pair name
		:return:
		'''
		flag = False
		session = self.get_session(_user, _region)
		ec2_client = session.client('ec2')
		response = ec2_client.describe_key_pairs()
		key_pairs = response['KeyPairs']
		for key_pair in key_pairs:
			if _keyName == key_pair['KeyName']:
				flag = True

		if flag is False:
			response = ec2_client.create_key_pair(KeyName=_keyName)
			_keyName = response['KeyName']

			f = open(os.path.join(self.keypairPath, _keyName + '.pem'), 'w')
			f.write(response['KeyMaterial'])
			f.close()
		return _keyName

	def delete_key_pair(self, _user, _region, _keyName):
		'''
		Delete key pair amazon server and local
		:param _user:
		:param _region:
		:param _keyName:
		:return:
		'''
		session = self.get_session(_user, _region)
		ec2_client = session.client('ec2')
		ret = ec2_client.delete_key_pair(KeyName=_keyName) #_user + u'-' + _region + u'.pem')
		if ret['ResponseMetadata']['HTTPStatusCode']==200:
			#delete file also
			fname = os.path.join(self.keypairPath, _keyName + '.pem')
			if os.path.exists(fname) is True:
				os.remove(fname)
		else:
			return False
		return True

	#################################################################
	# ec2 manage
	#################################################################
	def check_ec2_ready(self, _user, _region, _instanceID):
		'''
		After the instance created, check the instance's state whether it is ready to connect or not
		:param _user: user account identity existing in settings.py
		:param _region: region name
		:param _instanceID: specific instance's ID
		:return: boolean
		'''
		session = self.get_session(_user, _region)
		ec2 = session.resource('ec2')

		for status in ec2.meta.client.describe_instance_status()['InstanceStatuses']:
			if status['InstanceId'] != _instanceID: continue
			if (status['InstanceStatus']['Status']=='ok' and
				status['SystemStatus']['Status']=='ok' and
				status['InstanceState']['Name'] == 'running'):
				return True
		return False

	def check_ec2_terminated(self, _user, _region, _instanceID):
		'''
		After the instance created, check the instance's state whether it is ready to connect or not
		:param _user: user account identity existing in settings.py
		:param _region: region name
		:param _instanceID: specific instance's ID
		:return: boolean
		'''
		session = self.get_session(_user, _region)
		ec2 = session.resource('ec2')

		for status in ec2.meta.client.describe_instance_status()['InstanceStatuses']:
			if status['InstanceId'] != _instanceID: continue
			if status['InstanceState']['Name'] == 'terminated':
				return True
		return False

	def get_instances(self, _user, _region, _name):
		'''
		Returns instances matching instance name
		:param _user: user account identity existing in settings.py
		:param _region: region name
		:param _name: specific instance's name tag
		:return: the list of EC2() objects
		'''
		session = self.get_session(_user, _region)
		ec2 = session.resource('ec2')

		filters = [
			{'Name': 'tag-value', 'Values': [_name]},
			#{'Name': 'instance-state-name', 'Values': ['running']}
		]
		instances = ec2.instances.filter(Filters=filters)
		results = []
		for instance in instances:
			results.append(EC2(instance))
		return results

	def get_instance(self, _user, _region, _instanceID):
		'''
		Returns instance corresponding instance ID
		:param _user: user account identity existing in settings.py
		:param _region: region name
		:param _instanceID: specific instance's ID
		:return: EC2() object
		'''
		session = self.get_session(_user, _region)
		ec2 = session.resource('ec2')
		return EC2(ec2.Instance(_instanceID))

	def get_all_instances(self, _user, _region):
		'''
		Returns EC2 objects corresponding user and region
		:param _user: user account identity existing in settings.py
		:param _region: region name
		:return: EC2() object
		'''
		session = self.get_session(_user, _region)
		ec2 = session.resource('ec2')

		results = []
		for inst in ec2.instances.all():
			results.append(EC2(inst))
		return results

	def get_instance_counts(self, _user, _onlyWorking=False):
		'''
		Returns all instances count corresponding user in any regions
		:param _user: user account identity existing in settings.py
		:return: the number of count (int)
		'''
		count = 0
		for region in REGIONS.keys():
			session = self.get_session(_user, region)
			ec2 = session.resource('ec2')
			for instance in ec2.instances.all():
				if _onlyWorking is True:
					if instance.state['Name'] == 'terminated': continue
				count += 1
		return count

	def get_instances_state(self, _user, _region, _filter_name=None, _filter_state=None):
		'''
		Getting infomations in specific user, region, and filters
		:param _user: account identity existing in settings.py
		:param _region: region that specified by user
		:param _filter_name: instance name tag to filter
		:param _filter_state: instance state to filter ['running', 'terminated', 'working', ...]
			'working' means not 'terminated' appended by me, this state is not in amazon
		:return: the list of EC2() objects
		'''
		session = self.get_session(_user, _region)
		ec2 = session.resource('ec2')

		filters = []
		if _filter_name is not None:
			filters.append({'Name':'tag:Name', 'Values':[_filter_name]})
		if _filter_state is not None:
			if _filter_state == 'working':
				values = ['pending','running','shutting-down','stopping','stopped']
			else: values = [_filter_state]
			filters.append({'Name':'instance-state-name', 'Values':values})

		#getting instances
		results = []
		instances = ec2.instances.filter(Filters=filters)
		for instance in instances:
			results.append(EC2(instance))
		return results



	#################################################################
	# ec2 command
	#################################################################
	def create_ec2(self, _name, _user, _region, _os_type=u'ubuntu', _instance_type=None, _security_group=None):
		'''
		Create EC2 instance in amazon account at specific region
		:param _name: Instance name
		:param _user: user account identity existing in settings.py
		:param _region: Region that specified by user
		:param _os_type: OS type be installed in instance
		:param _instance_type: instance type, 't2.micro' is default.
		:param _security_group: dictionary describing security_group
								ex) {'name':'', 'desc':'', 'rules':[
											{'cidr':'0.0.0.0/0, 'protocol':'tcp', 'from_port':80, 'to_port':80},
											...
										]
									}
		:return: the dictionary of results
				{"status": "error" or "success",
				 "message":"description of status",
				 "instance": EC2() object if this function success}
		'''
		if _os_type not in AMI:
			return {"status": "error", "message": u'Unknown OS Type.'}

		if _instance_type is not None and _instance_type not in INSTANCE_TYPE:
			return {"status": "error", "message": u'Unknown Instance Type.'}

		targetAMI = AMI[_os_type][_region]
		instanceType = _instance_type if _instance_type is not None else 't2.micro'
		SGID = self.create_security_group(_user, _region, _security_group)
		keyName = self.create_key_pair(_user, _region, _keyName=_user + u'-' + _region)

		try:
			session = self.get_session(_user, _region)
			ec2 = session.resource('ec2')
			data = ec2.create_instances(ImageId=targetAMI,
										MinCount=1,
										MaxCount=1,
										InstanceType=instanceType,
										SecurityGroupIds=[SGID],
										KeyName=keyName)

			if data is None or len(data) ==0:
				return {"status": "error", "message": u'Unknown error! There is no result!'}

			# set tag name
			ec2.create_tags(Resources=[data[0].id], Tags=[{'Key': 'Name', 'Value': _name}])
			instance = EC2(data[0])
			instance.Name = _name

		except ClientError as e:
			return {"status":"error", "message": e.message}

		return {"status": "success", "message": "Created instance", "instance": instance}

	def delete_ec2(self, _user, _region, _instances):
		'''
		Terminate EC2 instances correspoding specific user, region
		:param _user: user account identity existing in settings.py
		:param _region: region name
		:param _instances: the list of instances ID
		:return: the number of count of terminated instances
		'''
		if len(_instances)<=0: return None

		session = self.get_session(_user, _region)
		ec2_client = session.client('ec2')
		response = ec2_client.terminate_instances(InstanceIds=_instances)
		return len(response['TerminatingInstances'])







