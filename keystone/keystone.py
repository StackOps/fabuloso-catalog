#   Copyright 2012-2013 STACKOPS TECHNOLOGIES S.L.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.from fabric.api import *
import MySQLdb

from fabric.api import settings, sudo, put, local, puts
from cuisine import package_ensure, package_clean
from fabuloso import fabuloso
from keystoneclient.v2_0 import client


def stop():
    with settings(warn_only=True):
        sudo("service keystone stop")


def start():
    stop()
    sudo("service keystone start")


def uninstall():
    """Uninstall keystone packages"""
    package_clean('keystone')
    package_clean('python-keystone')
    package_clean('python-keystoneclient')


def install(cluster=False):
    """Generate keystone configuration. Execute on both servers"""
    package_ensure('keystone')
    package_ensure('python-keystone')
    package_ensure('python-keystoneclient')
    package_ensure('python-mysqldb')
    if cluster:
        stop()
        sudo('echo "manual" >> /etc/init/keystone.override')
        sudo('mkdir -p /usr/lib/ocf/resource.d/openstack')
        put('./ocf/keystone', '/usr/lib/ocf/resource.d/openstack/keystone',
            use_sudo=True)
        sudo('chmod +x /usr/lib/ocf/resource.d/openstack/keystone')


def _get_id(str):
    stdout = local("echo '%s' | awk '/ id / { print $4 }'" % str, capture=True)
    puts(stdout)
    return stdout.replace('\n', '')


def _sql_connect_string(host, password, port, schema, username):
    sql_connection = 'mysql://%s:%s@%s:%s/%s' % (username, password, host,
                                                 port, schema)
    return sql_connection


def set_config_file(admin_token='password', mysql_username='keystone',
                    mysql_password='stackops', mysql_host='127.0.0.1',
                    mysql_port='3306', mysql_schema='keystone'):
    """Configure keystone to use the database and set the default
    admin token password"""
    bind_host = '0.0.0.0'
    public_port = '5000'
    admin_port = '35357'
    sudo("sed -i 's/^.*admin_token =.*$/admin_token = %s/g' "
         "/etc/keystone/keystone.conf" % admin_token)
    sudo("sed -i 's/^# bind_host =.*$/bind_host = %s/g' "
         "/etc/keystone/keystone.conf" % bind_host)
    sudo("sed -i 's/^# public_port =.*$/public_port = %s/g' "
         "/etc/keystone/keystone.conf" % public_port)
    sudo("sed -i 's/^# admin_port =.*$/admin_port = %s/g' "
         "/etc/keystone/keystone.conf" % admin_port)
    sudo("sed -i 's#connection.*$#connection = %s#g' "
         "/etc/keystone/keystone.conf" %
         _sql_connect_string(mysql_host, mysql_password, mysql_port,
                             mysql_schema, mysql_username))
    sudo("service keystone restart")
    sudo("keystone-manage db_sync")


def _link_user_role(endpoint, admin_token, quantum_user, admin_role,
                    service_tenant):
    sudo('keystone --endpoint %s --token %s user-role-add --user-id %s '
         '--role-id %s --tenant-id %s' % (endpoint, admin_token, quantum_user,
                                          admin_role, service_tenant))


def _create_role(endpoint, admin_token, role):
    stdout = sudo('keystone --endpoint %s --token %s role-create --name=%s'
                  % (endpoint, admin_token, role))
    return _get_id(stdout)


def _create_user(endpoint, admin_token, name, password, tenant):
    stdout = sudo(
        'keystone --endpoint %s --token %s user-create --name=%s --pass=%s '
        '--tenant-id %s --email=%s@domain.com' % (endpoint, admin_token, name,
                                                  password, tenant, name))
    return _get_id(stdout)


def _create_tenant(endpoint, admin_token, name):
    stdout = sudo('keystone --endpoint %s --token %s tenant-create --name=%s'
                  % (endpoint, admin_token, name))
    return _get_id(stdout)


def _get_tenant_id(endpoint, admin_token, name):
    stdout = sudo("keystone --endpoint %s --token %s tenant-list | grep '%s' |"
                  " awk '/ | / { print $2 }'" % (endpoint, admin_token, name))
    puts(stdout)
    return stdout.replace('\n', '')


def _get_role_id(endpoint, admin_token, name):
    stdout = sudo("keystone --endpoint %s --token %s role-list | grep '%s' |"
                  " awk '/ | / { print $2 }'" % (endpoint, admin_token, name))
    puts(stdout)
    return stdout.replace('\n', '')


def _create_user_for_service(endpoint, service_user_name, admin_token,
                             service_user_pass, tenant):
    """Configure component user and service"""
    service_tenant = _get_tenant_id(endpoint, admin_token, tenant)
    admin_role = _get_role_id(endpoint, admin_token, 'admin')
    service_user = _create_user(endpoint, admin_token, service_user_name,
                                service_user_pass, service_tenant)
    _link_user_role(endpoint, admin_token, service_user, admin_role,
                    service_tenant)


def configure_users(endpoint="'http://localhost:35357/v2.0'",
                    admin_token="password", admin_pass="stackops"):
    """Configure basic service users/roles"""
    admin_tenant = _create_tenant(endpoint, admin_token, 'admin')
    head_tenant = _create_tenant(endpoint, admin_token, 'head')
    _create_tenant(endpoint, admin_token, 'service')
    admin_role = _create_role(endpoint, admin_token, 'admin')
    member_role = _create_role(endpoint, admin_token, 'Member')
    keystone_admin_role = _create_role(endpoint, admin_token, 'KeystoneAdmin')
    keystone_service_admin_role = _create_role(endpoint, admin_token,
                                               'KeystoneServiceAdmin')
    portal_admin_role = _create_role(endpoint, admin_token,
                                     'ROLE_PORTAL_ADMIN')
    portal_user_role = _create_role(endpoint, admin_token, 'ROLE_PORTAL_USER')
    activity_admin_role = _create_role(endpoint, admin_token,
                                       'ROLE_ACTIVITY_ADMIN')
    activity_user_role = _create_role(endpoint, admin_token,
                                      'ROLE_ACTIVITY_USER')
    chargeback_admin_role = _create_role(endpoint, admin_token,
                                         'ROLE_CHARGEBACK_ADMIN')
    chargeback_user_role = _create_role(endpoint, admin_token,
                                        'ROLE_CHARGEBACK_USER')
    accounting_user_role = _create_role(endpoint, admin_token,
                                        'ROLE_ACCOUNTING')
    automation_user_role = _create_role(endpoint, admin_token,
                                        'ROLE_HEAD_ADMIN')
    admin_user = _create_user(endpoint, admin_token, 'admin', admin_pass,
                              admin_tenant)
    head_user = _create_user(endpoint, admin_token, 'head', admin_pass,
                             head_tenant)
    _link_user_role(endpoint, admin_token, admin_user, keystone_admin_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, head_user, keystone_admin_role,
                    head_tenant)
    _link_user_role(endpoint, admin_token, admin_user,
                    keystone_service_admin_role, admin_tenant)
    _link_user_role(endpoint, admin_token, head_user,
                    keystone_service_admin_role, head_tenant)
    _link_user_role(endpoint, admin_token, admin_user, admin_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, member_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, portal_admin_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, portal_user_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, head_user, portal_admin_role,
                    head_tenant)
    _link_user_role(endpoint, admin_token, head_user, portal_user_role,
                    head_tenant)
    _link_user_role(endpoint, admin_token, admin_user, activity_admin_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, activity_user_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, chargeback_admin_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, chargeback_user_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, accounting_user_role,
                    admin_tenant)
    _link_user_role(endpoint, admin_token, admin_user, automation_user_role,
                    head_tenant)


def _create_service(admin_token, service_name, service_type, description,
                    region, endpoint, public_url, internal_url, admin_url):
    """Create a new service"""
    stdout = sudo("keystone --endpoint %s --token %s service-create --name=%s"
                  " --type=%s --description='%s' " % (endpoint, admin_token,
                                                      service_name,
                                                      service_type,
                                                      description))
    service_id = _get_id(stdout)
    sudo("keystone --endpoint %s --token %s endpoint-create --region %s "
         "--service-id %s --publicurl '%s' --adminurl '%s' --internalurl '%s' "
         % (endpoint, admin_token, region, service_id, public_url, admin_url,
            internal_url))


def define_keystone_service(admin_token='password', region='RegionOne',
                            endpoint="'http://localhost:35357/v2.0'",
                            ks_public_url="'http://localhost:35357/"
                                          "keystone/v2.0'",
                            ks_internal_url="'http://localhost:5000/v2.0'",
                            ks_admin_url="'http://localhost:35357/v2.0'",
                            ks_user='keystone',
                            ks_password='stackops'):
    _create_service(admin_token, 'keystone', 'identity', 'Keystone Identity '
                    'Service', region, endpoint, ks_public_url,
                    ks_internal_url, ks_admin_url)
    _create_user_for_service(endpoint, ks_user, admin_token,
                             ks_password, 'service')


def define_nova_service(admin_token='password', region='RegionOne',
                        endpoint="'http://localhost:35357/v2.0'",
                        nova_public_url="'http://localhost/compute/v1.1/"
                                        "$(tenant_id)s'",
                        nova_internal_url="'http://localhost:8774/v1.1/"
                                          "$(tenant_id)s'",
                        nova_admin_url="'http://localhost:8774/v1.1/"
                                       "$(tenant_id)s'",
                        nova_user='nova',
                        nova_password='stackops'):
    _create_service(admin_token, 'nova', 'compute', 'OpenStack Computer '
                    'Service', region, endpoint, nova_public_url,
                    nova_internal_url, nova_admin_url)
    _create_user_for_service(endpoint, nova_user, admin_token,
                             nova_password, 'service')


def define_ec2_service(admin_token='password', region='RegionOne',
                       endpoint="'http://localhost:35357/v2.0'",
                       ec2_public_url="'http://localhost/services/Cloud'",
                       ec2_internal_url="''http://localhost/services/Cloud'",
                       ec2_admin_url="'http://localhost/services/Admin'"):
    _create_service(admin_token, 'ec2', 'ec2', 'EC2 Compatibility '
                    'Service', region, endpoint, ec2_public_url,
                    ec2_internal_url, ec2_admin_url)


def define_glance_service(admin_token='password', region='RegionOne',
                          endpoint="'http://localhost:35357/v2.0'",
                          glance_public_url="'http://localhost/glance/v1'",
                          glance_internal_url="'http://localhost:9292/v1'",
                          glance_admin_url="'http://localhost:9292/v1'",
                          glance_user='glance',
                          glance_password='stackops'):
    _create_service(admin_token, 'glance', 'image', 'Glance Image '
                    'Service', region, endpoint, glance_public_url,
                    glance_internal_url, glance_admin_url)
    _create_user_for_service(endpoint, glance_user, admin_token,
                             glance_password, 'service')


def define_quantum_service(admin_token='password', region='RegionOne',
                           endpoint="'http://localhost:35357/v2.0'",
                           quantum_public_url="'http://localhost/network",
                           quantum_internal_url="'http://localhost:9696'",
                           quantum_admin_url="'http://localhost:9696'",
                           quantum_user='quantum',
                           quantum_password='stackops'):
    _create_service(admin_token, 'quantum', 'network', 'Network '
                    'Service', region, endpoint, quantum_public_url,
                    quantum_internal_url, quantum_admin_url)
    _create_user_for_service(endpoint, quantum_user, admin_token,
                             quantum_password, 'service')


def define_cinder_service(admin_token='password', region='RegionOne',
                          endpoint="'http://localhost:35357/v2.0'",
                          cinder_public_url="'http://localhost/volume/v1/"
                                            "$(tenant_id)s'",
                          cinder_internal_url="'http://localhost:8776/v1/"
                                              "$(tenant_id)s'",
                          cinder_admin_url="'http://localhost:8776/v1/"
                                           "$(tenant_id)s'",
                          cinder_user='cinder',
                          cinder_password='stackops'):
    _create_service(admin_token, 'cinder', 'volume', 'OpenStack Volume '
                    'Service', region, endpoint, cinder_public_url,
                    cinder_internal_url, cinder_admin_url)
    _create_user_for_service(endpoint, cinder_user, admin_token,
                             cinder_password, 'service')


def define_portal_service(admin_token='password', region='RegionOne',
                          endpoint="'http://localhost:35357/v2.0'",
                          portal_public_url="'http://localhost/portal'",
                          portal_internal_url="'http://localhost:8080/portal'",
                          portal_admin_url="'http://localhost:8080/portal'",
                          portal_user='portal',
                          portal_password='stackops'):
    _create_service(admin_token, 'portal', 'portal', 'StackOps Portal '
                    'Service', region, endpoint, portal_public_url,
                    portal_internal_url, portal_admin_url)
    _create_user_for_service(endpoint, portal_user, admin_token,
                             portal_password, 'service')


def define_accounting_service(admin_token='password', region='RegionOne',
                              endpoint="'http://localhost:35357/v2.0'",
                              accounting_public_url="'http://localhost/"
                                                    "activity'",
                              accounting_internal_url="'http://localhost:8080/"
                                                      "activity'",
                              accounting_admin_url="'http://localhost:8080/"
                                                   "activity'",
                              accounting_user='activity',
                              accounting_password='stackops'):
    _create_service(admin_token, 'accounting', 'accounting',
                    'StackOps accounting '
                    'service', region, endpoint, accounting_public_url,
                    accounting_internal_url, accounting_admin_url)
    _create_service(admin_token, 'activity', 'activity', 'stackops activity '
                    'service', region, endpoint, accounting_public_url,
                    accounting_internal_url, accounting_admin_url)
    _create_user_for_service(endpoint, accounting_user, admin_token,
                             accounting_password, 'service')


def define_automation_service(admin_token='password', region='RegionOne',
                              endpoint="'http://localhost:35357/v2.0'",
                              automation_public_url="'http://localhost:8089/"
                                                    "automation'",
                              automation_internal_url="'http://localhost:8089/"
                                                      "v1.1'",
                              automation_admin_url="'http://localhost:8089/"
                                                   "v1.1'",
                              automation_user='automation',
                              automation_password='stackops'):
    _create_service(admin_token, 'automation', 'automation',
                    'Stackops Automation '
                    'service', region, endpoint, automation_public_url,
                    automation_internal_url, automation_admin_url)
    _create_user_for_service(endpoint, automation_user, admin_token,
                             automation_password, 'service')


def define_swift_service(admin_token='password', region='RegionOne',
                         endpoint="'http://localhost:35357/v2.0'",
                         swift_public_url="''http://localhost:8888/v1/"
                                          "AUTH_%(tenant_id)s'",
                         swift_internal_url="'http://localhost:8888/v1/"
                                            "AUTH_%(tenant_id)s'",
                         swift_admin_url="'http://localhost:8888/v1'",
                         swift_user='swift', swift_password='stackops'):

    _create_service(
        admin_token, 'swift', 'object-store',
        'OpenStack Object-Store service', region, endpoint,
        swift_public_url, swift_internal_url, swift_admin_url)

    _create_user_for_service(endpoint, swift_user, admin_token,
                             swift_password, 'service')


def configure_services(admin_token="password", public_ip='127.0.0.1',
                       public_port='80', internal_ip='127.0.0.1',
                       region='RegionOne'):
    """Configure services and endpoints"""
    endpoint = "'http://localhost:35357/v2.0'"
    _create_service(endpoint, admin_token, 'keystone', 'identity',
                    'Keystone Identity Service', region,
                    'http://%s:%s/keystone/v2.0' % (public_ip, public_port),
                    'http://%s:$(admin_port)s/v2.0' % internal_ip,
                    'http://%s:$(public_port)s/v2.0' % internal_ip)
    _create_service(endpoint, admin_token, 'nova', 'compute',
                    'Openstack Compute Service', region,
                    'http://%s:%s/compute/v1.1/$(tenant_id)s' % (public_ip,
                                                                 public_port),
                    'http://%s:$(compute_port)s/v1.1/$(tenant_id)s'
                    % internal_ip,
                    'http://%s:$(compute_port)s/v1.1/$(tenant_id)s'
                    % internal_ip)
    _create_service(endpoint, admin_token, 'ec2', 'ec2',
                    'EC2 Compatibility Layer', region,
                    'http://%s:%s/services/Cloud' % (public_ip, public_port),
                    'http://%s:8773/services/Admin' % internal_ip,
                    'http://%s:8773/services/Cloud' % internal_ip)
    _create_service(endpoint, admin_token, 'glance', 'image',
                    'Glance Image Service', region,
                    'http://%s:9292/v1' % public_ip,
                    'http://%s:9292/v1' % internal_ip,
                    'http://%s:9292/v1' % internal_ip)
    _create_service(endpoint, admin_token, 'cinder', 'volume',
                    'Openstack Volume Service', region,
                    'http://%s:%s/volume/v1/$(tenant_id)s' % (public_ip,
                                                              public_port),
                    'http://%s:8776/v1/$(tenant_id)s' % internal_ip,
                    'http://%s:8776/v1/$(tenant_id)s' % internal_ip)
    _create_service(endpoint, admin_token, 'quantum', 'network',
                    'Quantum Service', region,
                    'http://%s:%s/network' % (public_ip, public_port),
                    'http://%s:9696' % internal_ip,
                    'http://%s:9696' % internal_ip)


def validate_requirements(admin_token, auth_protocol, auth_host, auth_port,
                          auth_version, admin_tenant, automation_tenant,
                          admin_user, automation_user, portal_user,
                          activity_user, admin_role, keystone_admin_role,
                          keystone_service_admin_role, member_role,
                          activity_user_role, accounting_role,
                          portal_admin_role, chargeback_user_role,
                          portal_user_role, activity_admin_role,
                          head_admin_role, chargeback_admin_role,
                          service_type, auth_context=None):
    try:
        admin_token = str(admin_token)
        if auth_context is None:
            endpoint = '%s://%s:%s/%s' % (auth_protocol, auth_host, auth_port,
                                          auth_version)
        else:
            endpoint = '%s://%s:%s/%s/%s' % (auth_protocol, auth_host,
                                             auth_port, auth_context,
                                             auth_version)

        keystone = client.Client(token=admin_token, endpoint=endpoint)

        #Getting tenant list
        tenant_list = 0
        admin_tenant_id = 0
        automation_tenant_id = 0
        tenants_on_keystone = keystone.tenants.list()
        if tenants_on_keystone is not None:
            if len(tenants_on_keystone) > 0:
                for tenant in tenants_on_keystone:
                    if tenant.name == admin_tenant:
                        tenant_list += 1
                        admin_tenant_id = tenant.id
                    if tenant.name == automation_tenant:
                        tenant_list += 1
                        automation_tenant_id = tenant.id

        #logging.debug(tenant_list)
        if tenant_list < 2:
            #logging.error('Keystone has not the minimum tenants to operate..
            # .Please check....')
            raise Exception('Keystone has not the minimum tenants to operate'
                            '...Please check....')

        #Gettting user-list to validate 'admin','automation', 'activity'
        #and 'portal' users as minimum
        user_list = 0
        admin_user_id = 0
        automation_user_id = 0
        portal_user_id = 0
        activity_user_id = 0
        users_on_keystone = keystone.users.list()
        if users_on_keystone is not None:
            if len(users_on_keystone) > 0:
                for user in users_on_keystone:
                    if user.name == str(admin_user):
                        user_list += 1
                        admin_user_id = user.id
                    if user.name == str(automation_user):
                        user_list += 1
                        automation_user_id = user.id
                    if user.name == str(portal_user):
                        user_list += 1
                        portal_user_id = user.id
                    if user.name == str(activity_user):
                        user_list += 1
                        activity_user_id = user.id

        #logging.debug(user_list)
        if user_list < 4:
            #logging.error('Keystone has the minimum tenants but it has not
            # the minimum users to operate...Please check....')
            raise Exception('Keystone has the minimum tenants but it has not '
                            'the minimum users to operate...Please check....')

        #Gettting role-list to validate 'admin','KeystoneAdmin',
        #'KeystoneServiceAdmin','Member', 'ROLE_ACTIVITY_USER,
        #'ROLE_ACCOUNTING','ROLE_PORTAL_ADMIN','ROLE_CHARGEBACK_USER',
        #'ROLE_PORTAL_USER', 'ROLE_ACTIVITY_ADMIN', 'ROLE_HEAD_ADMIN'
        #'ROLE_CHARGEBACK_ADMIN' roles as minimum
        sum_roles = 0
        roles_on_keystone = keystone.roles.list()
        if roles_on_keystone is not None:
            if len(roles_on_keystone) > 0:
                for rol in roles_on_keystone:
                    if rol.name in (admin_role, keystone_admin_role,
                                    keystone_service_admin_role, member_role,
                                    activity_user_role, accounting_role,
                                    portal_admin_role, chargeback_user_role,
                                    portal_user_role, activity_admin_role,
                                    head_admin_role, chargeback_admin_role):
                        if rol.name == admin_role:
                            sum_roles += 1
                        if rol.name == keystone_admin_role:
                            sum_roles += 1
                        if rol.name == keystone_service_admin_role:
                            sum_roles += 1
                        if rol.name == member_role:
                            sum_roles += 1
                        if rol.name == activity_user_role:
                            sum_roles += 1
                        if rol.name == accounting_role:
                            sum_roles += 1
                        if rol.name == portal_admin_role:
                            sum_roles += 1
                        if rol.name == chargeback_user_role:
                            sum_roles += 1
                        if rol.name == portal_user_role:
                            sum_roles += 1
                        if rol.name == activity_admin_role:
                            sum_roles += 1
                        if rol.name == head_admin_role:
                            sum_roles += 1
                        if rol.name == chargeback_admin_role:
                            sum_roles += 1

        #logging.debug(sum_roles)
        if sum_roles < 12:
            #logging.error('Keystone has the minimum users and tenants but it
            # has not the minimum roles to operate'...Please check....')
            raise Exception('Keystone has the minimum users and tenants but '
                            'it has not the minimum roles to operate...'
                            'Please check....')

        if tenant_list == 2 and user_list == 4 and sum_roles == 12:
            #logging.debug("The users 'admin' and 'automation' ,
            # the roles 'admin', 'KeystoneAdmin', 'KeystoneServiceAdmin
            # and 'Member', and tenants 'admin' and 'service' exists
            # in Keystone. Prepare to verify dependencies between them.....")

            #Getting roles by user on a tenant
            #Roles on admin tenant with admin user
            complete_verification = 0
            roles_by_user_on_tenant = keystone.roles.\
                roles_for_user(tenant=admin_tenant_id,
                               user=admin_user_id)

            if roles_by_user_on_tenant is not None:
                if len(roles_by_user_on_tenant) > 0:
                    for rol in roles_by_user_on_tenant:
                        if rol.name in (admin_role, keystone_admin_role,
                                        keystone_service_admin_role,
                                        member_role):
                            if rol.name == admin_role:
                                complete_verification += 1

                            if rol.name == keystone_admin_role:
                                complete_verification += 1

                            if rol.name == keystone_service_admin_role:
                                complete_verification += 1

                            if rol.name == member_role:
                                complete_verification += 1

            #Roles on service tenant with automation user
            rol_by_user_automation_on_tenant = keystone.roles.\
                roles_for_user(tenant=automation_tenant_id,
                               user=automation_user_id)

            if rol_by_user_automation_on_tenant is not None:
                if len(rol_by_user_automation_on_tenant) > 0:
                    for rol in rol_by_user_automation_on_tenant:
                        if rol.name in admin_role:
                            if rol.name == admin_role:
                                complete_verification += 1

            #Roles on service tenant with portal user
            rol_by_user_portal_on_tenant = keystone.roles.\
                roles_for_user(tenant=automation_tenant_id,
                               user=portal_user_id)

            if rol_by_user_portal_on_tenant is not None:
                if len(rol_by_user_portal_on_tenant) > 0:
                    for rol in rol_by_user_portal_on_tenant:
                        if rol.name in admin_role:
                            if rol.name == admin_role:
                                complete_verification += 1

            #Roles on service tenant with activity user
            rol_by_user_activity_on_tenant = keystone.roles.\
                roles_for_user(tenant=automation_tenant_id,
                               user=activity_user_id)

            if rol_by_user_activity_on_tenant is not None:
                if len(rol_by_user_activity_on_tenant) > 0:
                    for rol in rol_by_user_activity_on_tenant:
                        if rol.name in admin_role:
                            if rol.name == admin_role:
                                complete_verification += 1

        #logging.debug(complete_verification)
        if complete_verification < 7:
            #logging.error('Keystone has the minimum requirements to operate
            # (tenants, users and roles) but it has not relationships between
            # them... Please check....')
            raise Exception('Keystone has the minimum requirements to operate '
                            '(tenants, users and roles) but it has not '
                            'relationships between them...Please check....')

        #Getting service-list
        service_list = 0
        services = keystone.services.list()
        if services is not None:
            if len(services) > 0:
                for service in services:
                    if service.type == service_type:
                        service_id = service.id
                        service_list = 1

        #logging.debug(service_list)
        if service_list < 1:
            #logging.error('Keystone has the minimum requirements to operate
            # (users, roles, tenants and relationships) but it has not the
            # minimum service identity...Please check....')
            raise Exception('Keystone has the minimum requirements to operate '
                            '(users, roles, tenants and relationships but it '
                            'has not the minimum service Identity'
                            '...Please check....')

        #Getting endpoint of the identity service
        endpoint_list = 0
        endpoints = keystone.endpoints.list()
        if endpoints is not None:
            if len(endpoints) > 0:
                for endpoint in endpoints:
                    if endpoint.service_id == service_id:
                        endpoint_list = 1

        #logging.debug(endpoint_list)
        if endpoint_list < 1:
            #logging.error('Keystone has the minimum requirements to operate '
            #              '(users, roles, tenants and relationships, also the'
            #              ' Identity Service but has not the endpoint'
            #              '...Please check....')
            raise Exception('Keystone has the minimum requirements to operate '
                            '(users, roles, tenants and relationships, also '
                            'the Identity Service, but it has not the '
                            'endpoint of the identity service created...'
                            'Please check....')

        print 'Validation of keystone finished successfully...'
    except Exception, e:
        import traceback
        print traceback.format_exc()
        #logging.error(traceback.format_exc())
        #logging.error("Error at the moment to Create %s tenant. %s" %
        # (tenant, e))
        raise Exception('Error at the moment to validate Keystone Service. '
                        'Please check log... %s' % e)


def repair_requirements(admin_token, auth_protocol, auth_host, auth_port,
                        auth_version, public_port, services_port, auth_region,
                        admin_tenant, automation_tenant,
                        admin_tenant_description,
                        automation_tenant_description,
                        admin_user, automation_user, portal_user,
                        activity_user, admin_user_password,
                        automation_user_password, portal_user_password,
                        activity_user_password, admin_user_email,
                        automation_user_email, portal_user_email,
                        activity_user_email, admin_role, keystone_admin_role,
                        keystone_service_admin_role, member_role,
                        activity_user_role, accounting_role,
                        portal_admin_role, chargeback_user_role,
                        portal_user_role, activity_admin_role,
                        head_admin_role, chargeback_admin_role, service_name,
                        service_type, service_description, auth_context=None):
    try:
        fix = True
        admin_token = admin_token
        if auth_context is None:
            endpoint = '%s://%s:%s/%s' % (auth_protocol, auth_host, auth_port,
                                          auth_version)
        else:
            endpoint = '%s://%s:%s/%s/%s' % (auth_protocol, auth_host,
                                             auth_port, auth_context,
                                             auth_version)

        keystone = client.Client(token=admin_token, endpoint=endpoint)

        #Getting tenant list
        tenant_list = 0
        admin_tenant_id = 0
        automation_tenant_id = 0
        tenants_on_keystone = keystone.tenants.list()
        if tenants_on_keystone is not None:
            if len(tenants_on_keystone) > 0:
                for tenant in tenants_on_keystone:
                    if tenant.name == admin_tenant:
                        tenant_list += 1
                        admin_tenant_id = tenant.id
                    if tenant.name == automation_tenant:
                        tenant_list += 1
                        automation_tenant_id = tenant.id

            if tenant_list < 2 and fix:
                if admin_tenant_id == 0:
                    tenantAdmin = keystone.tenants.\
                        create(tenant_name=admin_tenant,
                               description=admin_tenant_description,
                               enabled=True)
                    if tenantAdmin is not None:
                        admin_tenant_id = tenantAdmin.id
                        tenant_list += 1

                if automation_tenant_id == 0:
                    tenantHead = keystone.tenants.\
                        create(tenant_name=automation_tenant,
                               description=automation_tenant_description,
                               enabled=True)
                    if tenantHead is not None:
                        automation_tenant_id = tenantHead.id
                        tenant_list += 1
        #logging.debug(tenant_list)
        if tenant_list < 2:
            #logging.error('Keystone has not the minimum tenants to operate...
            # Please check....')
            raise Exception('Keystone has not the minimum tenants to operate'
                            '...Please check....')

        #Gettting user-list to validate 'admin' and 'automation'
        # users as minimum
        user_list = 0
        admin_user_id = 0
        automation_user_id = 0
        portal_user_id = 0
        activity_user_id = 0
        users_on_keystone = keystone.users.list()
        if users_on_keystone is not None:
            if len(users_on_keystone) > 0:
                for user in users_on_keystone:
                    if user.name == str(admin_user):
                        user_list += 1
                        admin_user_id = user.id
                    if user.name == str(automation_user):
                        user_list += 1
                        automation_user_id = user.id
                    if user.name == str(portal_user):
                        user_list += 1
                        portal_user_id = user.id
                    if user.name == str(activity_user):
                        user_list += 1
                        activity_user_id = user.id

            if user_list < 4 and fix:
                if admin_user_id == 0:
                    userAdmin = keystone.users.\
                        create(name=admin_user,
                               password=admin_user_password,
                               email=admin_user_email,
                               tenant_id=admin_tenant_id)
                    if userAdmin is not None:
                        admin_user_id = userAdmin.id
                        user_list += 1
                if automation_user_id == 0:
                    userAutomation = keystone.users.\
                        create(name=automation_user,
                               password=automation_user_password,
                               email=automation_user_email,
                               tenant_id=automation_tenant_id)
                    if userAutomation is not None:
                        automation_user_id = userAutomation.id
                        user_list += 1
                if portal_user_id == 0:
                    userPortal = keystone.users.\
                        create(name=portal_user,
                               password=portal_user_password,
                               email=portal_user_email,
                               tenant_id=automation_tenant_id)
                    if userPortal is not None:
                        portal_user_id = userPortal.id
                        user_list += 1
                if activity_user_id == 0:
                    userActivity = keystone.users.\
                        create(name=activity_user,
                               password=activity_user_password,
                               email=activity_user_email,
                               tenant_id=automation_tenant_id)
                    if userActivity is not None:
                        activity_user_id = userActivity.id
                        user_list += 1
        #logging.debug(user_list)
        if user_list < 4:
            #logging.error('Keystone has the minimum tenants but it
            # has not the minimum users to operate...'
            #              'Please check....')
            raise Exception('Keystone has the minimum tenants but it '
                            'has not the minimum users to operate...'
                            'Please check....')

        #Gettting role-list to validate 'admin','KeystoneAdmin',
        # 'KeystoneServiceAdmin', 'Member', 'ROLE_ACTIVITY_USER,
        #'ROLE_ACCOUNTING','ROLE_PORTAL_ADMIN','ROLE_CHARGEBACK_USER',
        #'ROLE_PORTAL_USER', 'ROLE_ACTIVITY_ADMIN', 'ROLE_HEAD_ADMIN'
        #'ROLE_CHARGEBACK_ADMIN' roles as minimum
        sum_roles = 0
        _admin_role = False
        _keystone_admin_role = False
        _keystone_service_admin_role = False
        _member_role = False
        _activity_user_role = False
        _accounting_role = False
        _portal_admin_role = False
        _chargeback_user_role = False
        _portal_user_role = False
        _activity_admin_role = False
        _head_admin_role = False
        _chargeback_admin_role = False

        admin_rol_id = 0
        keystone_admin_role_id = 0
        member_role_id = 0
        keystone_service_admin_role_id = 0
        activity_user_rol_id = 0
        accounting_rol_id = 0
        portal_admin_rol_id = 0
        chargeback_user_rol_id = 0
        portal_user_rol_id = 0
        activity_admin_rol_id = 0
        head_admin_rol_id = 0
        chargeback_admin_rol_id = 0

        roles_on_keystone = keystone.roles.list()
        if roles_on_keystone is not None:
            if len(roles_on_keystone) > 0:
                for rol in roles_on_keystone:
                    if rol.name in (admin_role, keystone_admin_role,
                                    keystone_service_admin_role, member_role,
                                    activity_user_role, accounting_role,
                                    portal_admin_role,
                                    chargeback_user_role,
                                    portal_user_role, activity_admin_role,
                                    head_admin_role, chargeback_admin_role):
                        if rol.name == admin_role:
                            _admin_role = True
                            admin_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == keystone_admin_role:
                            _keystone_admin_role = True
                            keystone_admin_role_id = rol.id
                            sum_roles += 1
                        if rol.name == keystone_service_admin_role:
                            _keystone_service_admin_role = True
                            keystone_service_admin_role_id = rol.id
                            sum_roles += 1
                        if rol.name == member_role:
                            _member_role = True
                            member_role_id = rol.id
                            sum_roles += 1
                        if rol.name == activity_user_role:
                            _activity_user_role = True
                            activity_user_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == accounting_role:
                            _accounting_role = True
                            accounting_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == portal_admin_role:
                            _portal_admin_role = True
                            portal_admin_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == chargeback_user_role:
                            _chargeback_user_role = True
                            chargeback_user_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == portal_user_role:
                            _portal_user_role = True
                            portal_user_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == activity_admin_role:
                            _activity_admin_role = True
                            activity_admin_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == head_admin_role:
                            _head_admin_role = True
                            head_admin_rol_id = rol.id
                            sum_roles += 1
                        if rol.name == chargeback_admin_role:
                            _chargeback_admin_role = True
                            chargeback_admin_rol_id = rol.id
                            sum_roles += 1

            if fix:
                if not _admin_role:
                    adminRole = keystone.roles.create(name=admin_role)
                    if adminRole is not None:
                        admin_rol_id = adminRole.id
                        sum_roles += 1
                if not _keystone_admin_role:
                    keystoneAdminRole = keystone.roles.\
                        create(name=keystone_admin_role)
                    if keystoneAdminRole is not None:
                        keystone_admin_role_id = keystoneAdminRole.id
                        sum_roles += 1
                if not _keystone_service_admin_role:
                    keystoneServiceAdminRole = keystone.roles.\
                        create(name=keystone_service_admin_role)
                    if keystoneServiceAdminRole is not None:
                        keystone_service_admin_role_id = \
                            keystoneServiceAdminRole.id
                        sum_roles += 1
                if not _member_role:
                    memberRole = keystone.roles.create(name=member_role)
                    if memberRole is not None:
                        member_role_id = memberRole.id
                        sum_roles += 1
                if not _activity_user_role:
                    activityUserRole = keystone.roles.create(
                        name=activity_user_role)
                    if activityUserRole is not None:
                        activity_user_rol_id = activityUserRole.id
                        sum_roles += 1
                if not _accounting_role:
                    accountingRole = keystone.roles.create(
                        name=accounting_role)
                    if accountingRole is not None:
                        accounting_rol_id = accountingRole.id
                        sum_roles += 1
                if not _portal_admin_role:
                    portalAdminRole = keystone.roles.create(
                        name=portal_admin_role)
                    if portalAdminRole is not None:
                        portal_admin_rol_id = portalAdminRole.id
                        sum_roles += 1
                if not _chargeback_user_role:
                    chargebackUserRole = keystone.roles.create(
                        name=chargeback_user_role)
                    if chargebackUserRole is not None:
                        chargeback_user_rol_id = chargebackUserRole.id
                        sum_roles += 1
                if not _portal_user_role:
                    portalUserRole = keystone.roles.create(
                        name=portal_user_role)
                    if portalUserRole is not None:
                        portal_user_rol_id = portalUserRole.id
                        sum_roles += 1
                if not _activity_admin_role:
                    activityAdminRole = keystone.roles.create(
                        name=activity_admin_role)
                    if activityAdminRole is not None:
                        activity_admin_rol_id = activityAdminRole.id
                        sum_roles += 1
                if not _head_admin_role:
                    headAdminRole = keystone.roles.create(
                        name=head_admin_role)
                    if headAdminRole is not None:
                        head_admin_rol_id = headAdminRole.id
                        sum_roles += 1
                if not _chargeback_admin_role:
                    chargebackAdminRole = keystone.roles.create(
                        name=chargeback_admin_role)
                    if chargebackAdminRole is not None:
                        chargeback_admin_rol_id = chargebackAdminRole.id
                        sum_roles += 1

        #logging.debug(sum_roles)
        if sum_roles < 12:
            #logging.error('Keystone has the minimum users and tenants but it
            # has not the minimum roles to operate...Please check....')
            raise Exception('Keystone has the minimum users and tenants but '
                            'it has not the minimum roles to operate...'
                            'Please check....')

        if tenant_list == 2 and user_list == 4 and sum_roles == 12:
            #logging.debug("The users 'admin' and 'head/automation' , the roles
            # 'admin', 'KeystoneAdmin', 'KeystoneServiceAdmin and 'Member', and
            # tenants 'admin' and 'service' exists in Keystone. Prepare to
            # verify dependencies between them.....")

            #Getting roles by user on a tenant
            complete_verification = 0

            #Roles on admin tenant with admin user
            _admin_role_on_tenant = False
            _keystone_admin_role_on_tenant = False
            _keystone_service_admin_role_on_tenant = False
            _member_role_on_tenant = False

            roles_by_user_on_tenant = keystone.roles.roles_for_user(
                tenant=admin_tenant_id, user=admin_user_id)
            if roles_by_user_on_tenant is not None:
                if len(roles_by_user_on_tenant) > 0:
                    for rol in roles_by_user_on_tenant:
                        if rol.name in (admin_role,
                                        keystone_admin_role,
                                        keystone_service_admin_role,
                                        member_role):
                            if rol.name == admin_role:
                                _admin_role_on_tenant = True
                                complete_verification += 1

                            if rol.name == keystone_admin_role:
                                _keystone_admin_role_on_tenant = True
                                complete_verification += 1

                            if rol.name == keystone_service_admin_role:
                                _keystone_service_admin_role_on_tenant = True
                                complete_verification += 1

                            if rol.name == member_role:
                                _member_role_on_tenant = True
                                complete_verification += 1

                if fix:
                    if not _admin_role_on_tenant:
                        adminRoleOnTenant = keystone.roles.\
                            add_user_role(user=admin_user_id,
                                          role=admin_rol_id,
                                          tenant=admin_tenant_id)
                        if adminRoleOnTenant is not None:
                            complete_verification += 1

                    if not _keystone_admin_role_on_tenant:
                        keystoneAdminRoleOnTenant = keystone.roles.\
                            add_user_role(user=admin_user_id,
                                          role=keystone_admin_role_id,
                                          tenant=admin_tenant_id)
                        if keystoneAdminRoleOnTenant is not None:
                            complete_verification += 1

                    if not _keystone_service_admin_role_on_tenant:
                        keystoneServiceAdminRoleOnTenant = keystone.roles.\
                            add_user_role(user=admin_user_id,
                                          role=
                                          keystone_service_admin_role_id,
                                          tenant=admin_tenant_id)
                        if keystoneServiceAdminRoleOnTenant is not None:
                            complete_verification += 1

                    if not _member_role_on_tenant:
                        memberRoleOnTenant = keystone.roles.\
                            add_user_role(user=admin_user_id,
                                          role=member_role_id,
                                          tenant=admin_tenant_id)
                        if memberRoleOnTenant is not None:
                            complete_verification += 1

            #Roles on service tenant with automation user
            _admin_role_on_tenant = False
            rol_by_user_automation_on_tenant = keystone.roles.roles_for_user(
                tenant=automation_tenant_id, user=automation_user_id)
            if rol_by_user_automation_on_tenant is not None:
                if len(rol_by_user_automation_on_tenant) > 0:
                    for rol in rol_by_user_automation_on_tenant:
                        if rol.name in admin_role:
                            if rol.name == admin_role:
                                _admin_role_on_tenant = True
                                complete_verification += 1

                if fix:
                    if not _admin_role_on_tenant:
                        adminRoleOnTenant = keystone.roles.\
                            add_user_role(user=automation_user_id,
                                          role=admin_rol_id,
                                          tenant=automation_tenant_id)
                        if adminRoleOnTenant is not None:
                            complete_verification += 1

            #Roles on service tenant with portal user
            _admin_role_on_tenant = False
            rol_by_user_portal_on_tenant = keystone.roles.\
                roles_for_user(tenant=automation_tenant_id,
                               user=portal_user_id)

            if rol_by_user_portal_on_tenant is not None:
                if len(rol_by_user_portal_on_tenant) > 0:
                    for rol in rol_by_user_portal_on_tenant:
                        if rol.name in admin_role:
                            if rol.name == admin_role:
                                _admin_role_on_tenant = True
                                complete_verification += 1

                if fix:
                    if not _admin_role_on_tenant:
                        adminRoleOnTenant = keystone.roles.\
                            add_user_role(user=portal_user_id,
                                          role=admin_rol_id,
                                          tenant=automation_tenant_id)
                        if adminRoleOnTenant is not None:
                            complete_verification += 1

            #Roles on service tenant with activity user
            _admin_role_on_tenant = False
            rol_by_user_activity_on_tenant = keystone.roles.\
                roles_for_user(tenant=automation_tenant_id,
                               user=activity_user_id)

            if rol_by_user_activity_on_tenant is not None:
                if len(rol_by_user_activity_on_tenant) > 0:
                    for rol in rol_by_user_activity_on_tenant:
                        if rol.name in admin_role:
                            if rol.name == admin_role:
                                _admin_role_on_tenant = True
                                complete_verification += 1

                if fix:
                    if not _admin_role_on_tenant:
                        adminRoleOnTenant = keystone.roles.\
                            add_user_role(user=activity_user_id,
                                          role=admin_rol_id,
                                          tenant=automation_tenant_id)
                        if adminRoleOnTenant is not None:
                            complete_verification += 1

        #logging.debug(complete_verification)
        if complete_verification < 7:
            #logging.error('Keystone has the minimum requirements to operate
            # (tenants, users and roles) but it has not relationships between
            # them...Please check....')
            raise Exception('Keystone has the minimum requirements to operate '
                            '(tenants, users and roles) but it has not '
                            'relationships between them...Please check....')

        #Getting service-list
        service_list = 0
        endpoint_list = 0
        service_id = 0
        services = keystone.services.list()
        if services is not None:
            if len(services) > 0:
                for service in services:
                    if service.type == service_type:
                        service_id = service.id
                        service_list = 1

            #logging.debug(service_list)

            if auth_context is None:
                public_url = '%s://%s:%s/%s' % (auth_protocol,
                                                auth_host,
                                                public_port,
                                                auth_version)
                admin_url = '%s://%s:%s/%s' % (auth_protocol,
                                               auth_host,
                                               auth_port,
                                               auth_version)
                internal_url = '%s://%s:%s/%s' % (auth_protocol,
                                                  auth_host,
                                                  services_port,
                                                  auth_version)
            else:
                public_url = '%s://%s:%s/%s/%s' % (auth_protocol,
                                                   auth_host,
                                                   public_port,
                                                   auth_context,
                                                   auth_version)
                admin_url = '%s://%s:%s/%s/%s' % (auth_protocol,
                                                  auth_host,
                                                  auth_port,
                                                  auth_context,
                                                  auth_version)
                internal_url = '%s://%s:%s/%s/%s' % (auth_protocol,
                                                     auth_host,
                                                     services_port,
                                                     auth_context,
                                                     auth_version)

            if service_list == 0 and fix:
                service_new, endpoint_new = add_service(admin_token,
                                                        endpoint,
                                                        service_name,
                                                        service_type,
                                                        service_description,
                                                        auth_region,
                                                        public_url,
                                                        admin_url,
                                                        internal_url)
                service_id = service_new.id
                endpoint_list = 1
                service_list = 1

        if service_list < 1:
            #logging.error('Keystone has the minimum requirements to operate
            # (users, roles, tenants and relationships) but it has not the
            # minimum endpoint or service identity...Please check....')
            raise Exception('Keystone has the minimum requirements to operate '
                            '(users, roles, tenants and relationships) but it '
                            'has not the minimum endpoint or service Identity'
                            '...Please check....')

        #Getting endpoint of the identity service
        if endpoint_list < 1:
            endpoints = keystone.endpoints.list()
            if endpoints is not None:
                if len(endpoints) > 0:
                    for endpoint_check in endpoints:
                        if endpoint_check.service_id == service_id:
                            endpoint_list = 1

                if endpoint_list == 0 and fix:
                    endpoint_new = _add_endpoint(admin_token,
                                                 endpoint,
                                                 service_id,
                                                 admin_url,
                                                 internal_url,
                                                 public_url,
                                                 auth_region)
                    endpoint_list = 1

        if endpoint_list < 1:
            #logging.error('Keystone has the minimum requirements to operate '
            #              '(users, roles, tenants and relationships, also the'
            #              ' Identity Service but has not the endpoint'
            #              '...Please check....')
            raise Exception('Keystone has the minimum requirements to operate '
                            '(users, roles, tenants and relationships, also '
                            'the Identity Service, but it has not the '
                            'endpoint of the identity service created...'
                            'Please check....')

        print'Validation and fixed of keystone finished successfully...'

    except Exception, e:
        import traceback
        print traceback.format_exc()
        #logging.error(traceback.format_exc())
        #logging.error("Error at the moment to Create %s tenant. %s" %
        # (tenant, e))
        raise Exception('Error at the moment to validate and fix '
                        'Keystone Service. Please check log... %s' % e)


def add_service(admin_token, endpoint, service_name, service_type,
                service_description, service_region, service_public_url,
                service_admin_url, service_internal_url):
    try:
        keystone = client.Client(token=admin_token, endpoint=endpoint)
        services = keystone.services.list()
        if services is not None:
            if len(services) > 0:
                for service_row in services:
                    if service_row.type == service_type:
                        #logging.debug('Service Type %s specified already
                        # exists on Keystone '
                        #              'identity as %s.' % (service,
                        # service_type_keystone))
                        raise Exception('Service Type %s specified already '
                                        'exists on Keystone as %s.' %
                                        (service_name, service_type))

        service_new = keystone.services.create(name=service_name,
                                               service_type=service_type,
                                               description=service_description)
        if service_new is not None:
            service_id = service_new.id
            endpoint = _add_endpoint(admin_token, endpoint, service_id,
                                     service_admin_url, service_internal_url,
                                     service_public_url, service_region)
            return service_new, endpoint

    except Exception, e:
        #logging.error("Error at the moment to add a Service. %s" % e)
        raise Exception('Error at the moment to add a Service. '
                        'Please check log %s' % e)


def validate_credentials(user, password, tenant, endpoint, admin_token):
    try:
        keystone = client.Client(token=admin_token, endpoint=endpoint)
        token = keystone.tokens.authenticate(username=user,
                                             tenant_name=tenant,
                                             password=password)
        if token is not None:
                print 'Validation of credentials for %s user in ' \
                      'tenant %s was successful..' % (user, tenant)

    except Exception, e:
        #logging.error("Error at the moment to add a Service. %s" % e)
        raise Exception('Error at the moment to Validate Credentials '
                        'on Keystone for user %s. Please check log %s'
                        % (user, e))


def _add_endpoint(admin_token, endpoint, service_id, service_admin_url,
                  service_internal_url, service_public_url, service_region):
    try:
        keystone = client.Client(token=admin_token, endpoint=endpoint)
        endpoint = keystone.endpoints.\
            create(service_id=service_id,
                   adminurl=service_admin_url,
                   internalurl=service_internal_url,
                   publicurl=service_public_url,
                   region=service_region)
        if endpoint is not None:
            return endpoint
    except Exception, e:
        #logging.error("Error at the moment to add a Service. %s" % e)
        raise Exception('Error at the moment to add an endpoint. '
                        'Please check log %s' % e)


def validate_database(database_type, username, password, host, port,
                      schema, drop_schema=None, install_database=None):
    fab = fabuloso.Fabuloso()
    fab.validate_database(database_type, username, password, host, port,
                          schema, drop_schema, install_database)


def validate_credentials(user, password, tenant, endpoint, admin_token):
    fab = fabuloso.Fabuloso()
    fab.validate_credentials(user, password, tenant, endpoint, admin_token)
