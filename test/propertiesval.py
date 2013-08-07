# Component properties
#########################################
## DEPLOYTIME VALUES
########################################
singlenode = {
    # Public IP address to reach the host
    'host': '192.168.1.149'
}

##########################################
# COMPONENT VALUES
#########################################
keystone = {
    'admin_token': 'stackops_admin',
    'auth_protocol': 'http',
    'auth_host': singlenode['host'],
    'auth_port': '35357',
    'auth_version': 'v2.0',
    'public_port': '80',
    'services_port': '5000',
    'auth_region': 'RegionOne',
    'admin_tenant': 'admin',
    'automation_tenant': 'service',
    'admin_tenant_description': 'Admin tenant',
    'automation_tenant_description': 'Automation tenant',
    'admin_user': 'admin',
    'automation_user': 'automation',
    'portal_user': 'portal',
    'activity_user': 'activity',
    'admin_user_password': 'stackops',
    'automation_user_password': 'stackops',
    'portal_user_password': 'stackops',
    'activity_user_password': 'stackops',
    'admin_user_email': 'admin@stackops.com',
    'automation_user_email': 'automation@stackops.com',
    'portal_user_email': 'portal@stackops.com',
    'activity_user_email': 'activity@stackops.com',
    'admin_role': 'admin',
    'keystone_admin_role': 'KeystoneAdmin',
    'keystone_service_admin_role': 'KeystoneServiceAdmin',
    'member_role': 'Member',
    'activity_user_role': 'ROLE_ACTIVITY_USER',
    'accounting_role': 'ROLE_ACCOUNTING',
    'portal_admin_role': 'ROLE_PORTAL_ADMIN',
    'chargeback_user_role': 'ROLE_CHARGEBACK_USER',
    'portal_user_role': 'ROLE_PORTAL_USER',
    'activity_admin_role': 'ROLE_ACTIVITY_ADMIN',
    'head_admin_role': 'ROLE_HEAD_ADMIN',
    'chargeback_admin_role': 'ROLE_CHARGEBACK_ADMIN',
    'service_type': 'identity',
    'service_name': 'keystone',
    'service_description': 'Keystone Identity Service',
    'user': 'keystone',
    'password': 'stackops',
    'tenant': 'service',
    'endpoint': 'http://'+singlenode['host']+':35357/v2.0',
    'database_type': 'mysql',
    'username': 'keystone',
    'password': 'stackops',
    'host': singlenode['host'],
    'port': '3306',
    'schema': 'keystone'
}

keystone_add = {
    'admin_token': 'stackops_admin',
    'service_name': 'other',
    'service_type': 'other',
    'service_description': 'Other Service',
    'endpoint': 'http://'+singlenode['host']+':35357/v2.0',
    'service_region': 'RegionOne',
    'service_public_url': 'http://localhost/v2.0/other',
    'service_admin_url': 'http://localhost/v2.0/other',
    'service_internal_url': 'http://localhost/v2.0/other'
}

mysql = {
    'database_type': 'mysql',
    'username': 'root',
    'password': 'stackops',
    'host': singlenode['host'],
    'port': '3306',
    'schema': 'mysql'
}

glance = {
    'database_type': 'mysql',
    'username': 'glance',
    'password': 'stackops',
    'host': singlenode['host'],
    'port': '3306',
    'schema': 'glance',
    'admin_token': 'stackops_admin',
    'user': 'glance',
    'password': 'stackops',
    'tenant': 'service',
    'endpoint': 'http://'+singlenode['host']+':35357/v2.0',
}

cinder = {
    'database_type': 'mysql',
    'username': 'cinder',
    'password': 'stackops',
    'host': singlenode['host'],
    'port': '3306',
    'schema': 'cinder',
    'admin_token': 'stackops_admin',
    'user': 'cinder',
    'password': 'stackops',
    'tenant': 'service',
    'endpoint': 'http://'+singlenode['host']+':35357/v2.0',
    'service_type': 'cinder',
    'rport': '5672',
    'ruser': 'guest',
    'rpassword': 'guest',
    'virtual_host': '/'
}

nova = {
    'database_type': 'mysql',
    'username': 'nova',
    'password': 'stackops',
    'host': singlenode['host'],
    'port': '3306',
    'schema': 'nova',
    'admin_token': 'stackops_admin',
    'user': 'nova',
    'password': 'stackops',
    'tenant': 'service',
    'endpoint': 'http://'+singlenode['host']+':35357/v2.0',
    'service_type': 'nova',
    'rport': '5672',
    'ruser': 'guest',
    'rpassword': 'guest',
    'virtual_host': '/'
}

quantum = {
    'database_type': 'mysql',
    'username': 'quantum',
    'password': 'stackops',
    'host': singlenode['host'],
    'port': '3306',
    'schema': 'quantum',
    'admin_token': 'stackops_admin',
    'user': 'quantum',
    'password': 'stackops',
    'tenant': 'service',
    'endpoint': 'http://'+singlenode['host']+':35357/v2.0',
    'service_type': 'quantum',
    'rport': '5672',
    'ruser': 'guest',
    'rpassword': 'guest',
    'virtual_host': '/'
}

rabbitmq = {
    'service_type': 'rabbitmq',
    'host': singlenode['host'],
    'rport': '5672',
    'ruser': 'guest',
    'rpassword': 'guest',
    'virtual_host': '/'
}

storage = {
    'master_storage_type': 'NFS',
    'master_endpoint': singlenode['host'],
    'master_hostname': '',
    'master_datastore': '/exports/stackops',
    'master_mount_parameters': 'defaults',
    'volumes_storage_type': 'NFS',
    'volumes_endpoint': singlenode['host'],
    'volumes_hostname': '',
    'volumes_datastore': '/exports/stackops/volumes',
    'volumes_mount_parameters': 'defaults',
    'images_storage_type': 'NFS',
    'images_endpoint': singlenode['host'],
    'images_hostname': '',
    'images_datastore': '/exports/stackops/images',
    'images_mount_parameters': 'defaults',
    'instances_storage_type': 'NFS',
    'instances_endpoint': singlenode['host'],
    'instances_hostname': '',
    'instances_datastore': '/exports/stackops/images',
    'instances_mount_parameters': 'defaults'
}
