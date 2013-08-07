#!/usr/bin/env python
import os
import fabuloso
import propertiesval

currentdir = os.path.dirname(os.path.abspath(__file__))

env = {
    'host': '127.0.0.1',
    'port': 2223,
    'username': 'stackops',
    'ssh_key_file': '~/.ssh/nonsecureid_rsa',
}

# Loads the default catalog
fab = fabuloso.Fabuloso()
print fab.catalog

# Validate Mysql component
print '\nStarting mysql component validation\n'
mysql = fab.init_component("mysql", propertiesval.mysql, env)
mysql.validate()

# Validate RabbitMQ component
print '\nStarting rabbitmq component validation\n'
rabbitmq = fab.init_component("rabbitmq", propertiesval.rabbitmq, env)
rabbitmq.validate()

# Validate Keystone component
print '\nStarting keystone component validation\n'
keystone = fab.init_component("keystone", propertiesval.keystone, env)
keystone.validate()
keystone.repair()

#Add service in keystone (keystone component)
#keystone_add = fab.init_component("keystone", propertiesval.keystone_add, env)
#keystone_add.add_service()


# Validate Glance component
print '\nStarting glance component validation\n'
glance = fab.init_component("glance", propertiesval.glance, env)
glance.validate()

# Validate Cinder component
print '\nStarting cinder component validation\n'
cinder = fab.init_component("cinder", propertiesval.cinder, env)
cinder.validate()

# Validate Nova component
print '\nStarting nova component validation\n'
nova = fab.init_component("nova", propertiesval.nova, env)
nova.validate()

# Validate Quantum component
print '\nStarting quantum component validation\n'
quantum = fab.init_component("nova", propertiesval.quantum, env)
quantum.validate()

#Install and configure
print '\nInstalling and configuring server-nfs-internal\n'
storage = fab.init_component("storage", propertiesval.storage, env)
storage.install()
print '\nStarting storage component validation\n'
storage.validate()
