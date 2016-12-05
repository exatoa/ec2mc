#-*- coding: utf-8 -*-
'''
Created on 2016. 12.05
@author: Zeck
'''
from AmazonUtils import AmazonUtils
from AmazonInfo import *
from EC2 import EC2
from EC2Controller import EC2Controller

__all__ = [
	'AmazonUtils',
	'REGIONS',
	'AMI',
	'INSTANCE_TYPE',
	'EC2',
	'EC2Controller',
]

__title__ = 'AWS EC2 Controller for multi accounts'
__version__ = '0.1'
__author__ = 'Zeck <exatoa@gmail.com>'
