#######################################################
#  OUTPUT PATH
OUTPUT_PATH = u'D:/works/#Amazon/'

#######################################################
#  OUTPUT PATH
NODE_NAME = u'proxy'

#######################################################
#  OUTPUT PATH
OS_TYPE = u'ubuntu'

#######################################################
# INSTANCE_TYPE
INSTANCE_TYPE=u't2.micro'

#######################################################
# SECURITY_GROUP: dictionary describing security_group
#		ex) {'name':'', 'desc':'', 'rules':[{'cidr':'0.0.0.0/0, 'protocol':'tcp', 'from_port':80, 'to_port':80}, ...]}
SECURITY_GROUP = {
	'name': u'proxy',
	'desc': u'EC2MultiController',
	'rules':[
		{'cidr': u'0.0.0.0/0', 'from_port': 22, 'to_port': 22, 'protocol': u'tcp'},
		{'cidr': u'0.0.0.0/0', 'from_port': 20160, 'to_port': 20160, 'protocol': u'tcp'},
	]
}

#######################################################
# ACCOUNTS
# please fill the access_key and secret_key
ACCOUNTS = {
	'User01': {'access_key': u'', 'secret_key': u''},
	'User02': {'access_key': u'', 'secret_key': u''},
}