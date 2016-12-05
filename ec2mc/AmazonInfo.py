#-*- coding: utf-8 -*-
'''
Created on 2016. 12.05
@author: Zeck
'''
AMI = {
	u'ubuntu':{
		u'us-east-1': u'ami-40d28157',
		u'us-east-2': u'ami-153e6470',
		u'us-west-1': u'ami-6e165d0e',
		u'us-west-2': u'ami-a9d276c9',
		u'eu-west-1': u'ami-0d77397e',
		u'eu-central-1': u'ami-8504fdea',
		u'ap-northeast-1': u'ami-0567c164',
		u'ap-northeast-2': u'ami-8fed39e1',
		u'ap-southeast-1': u'ami-a1288ec2',
		u'ap-southeast-2': u'ami-4d3b062e',
		u'ap-south-1': u'ami-0355216c',
		u'sa-east-1': u'ami-e93da085',
	}
}

REGIONS = {
	u'us-east-1': u'N.Virginia',
	u'us-east-2': u'Ohio',
	u'us-west-1': u'N.California',
	u'us-west-2': u'Oregon',
	u'eu-west-1': u'Ireland',
	u'eu-central-1': u'Frankfrut',
	u'ap-northeast-1': u'Tokyo',
	u'ap-northeast-2': u'Seoul',
	u'ap-southeast-1': u'Singapore',
	u'ap-southeast-2': u'Sydney',
	u'ap-south-1': u'Mumbai',
	u'sa-east-1': u'SaoPaulo',
}

INSTANCE_TYPE = [
	u't2.nano', u't2.micro', u't2.small', u't2.medium', u't2.large', u't2.xlarge', u't2.2xlarge',
	u'm4.large', u'm4.xlarge', u'm4.2xlarge', u'm4.4xlarge', u'm4.10xlarge', u'm4.16xlarge',
	u'c4.large', u'c4.xlarge', u'c4.2xlarge', u'c4.4xlarge', u'c4.8xlarge',
	u'r3.large', u'r3.xlarge', u'r3.2xlarge', u'r3.4xlarge', u'r3.8xlarge',
	u'x1.16xlarge', u'x1.32xlarge',
	u'd2.xlarge', u'd2.2xlarge', u'd2.4xlarge', u'd2.8xlarge',
	u'i2.xlarge', u'i2.2xlarge', u'i2.4xlarge', u'i2.8xlarge'
]