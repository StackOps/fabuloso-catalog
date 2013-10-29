#   Copyright 2012-2013 STACKOPS TECHNOLOGIES S.L.
from fabric.api import settings, sudo
from cuisine import package_ensure, package_clean


def stop():
    with settings(warn_only=True):
        sudo("nohup service tomcat7 stop")


def start():
    stop()
    sudo("nohup service tomcat7 start")


def configure_ubuntu_packages():
    """Configure java, tomcat and mysql client packages"""
    package_ensure('openjdk-7-jdk')
    package_ensure('tomcat7')
    package_ensure('mysql-client')


def uninstall_ubuntu_packages():
    """Uninstall accounting and chargeback packages"""
    package_clean('stackops-chargeback-portal-plugin')
    package_clean('stackops-chargeback')
    package_clean('stackops-activity-portal-plugin')
    package_clean('stackops-activity')


def configure_activity(mysql_activity_username='activity',
                       mysql_activity_password='stackops',
                       mysql_activity_host='localhost',
                       mysql_activity_port='3306',
                       mysql_activity_schema='activity',
                       mysql_activity_root_password='stackops',
                       service_activity_user='activity',
                       service_activity_pass='stackops',
                       rabbit_username='guest',
                       rabbit_password='guest',
                       rabbit_host='localhost',
                       rabbit_port='5672',
                       admin_token='password',
                       auth_host='127.0.0.1',
                       auth_port='35357',
                       auth_protocol='http',
                       auth_uri='/v2.0',
                       license_token="SUhIsoHOLNFjt6Drz7W26NrNs"):
    """Generate activity configuration. Execute on both servers"""
    sudo('echo stackops-activity stackops-activity/mysql-usr string '
         '%s | debconf-set-selections' % mysql_activity_username)
    sudo('echo stackops-activity stackops-activity/mysql-password password %s '
         '| debconf-set-selections' % mysql_activity_password)
    sudo('echo stackops-activity stackops-activity/mysql-schema string %s '
         '| debconf-set-selections' % mysql_activity_schema)
    sudo('echo stackops-activity stackops-activity/mysql-host string %s '
         '| debconf-set-selections' % mysql_activity_host)
    sudo('echo stackops-activity stackops-activity/mysql-port string %s '
         '| debconf-set-selections' % mysql_activity_port)
    sudo('echo stackops-activity stackops-activity/mysql-admin-password '
         'password %s | debconf-set-selections' % mysql_activity_root_password)
    sudo('echo stackops-activity stackops-activity/mysql-purgedb boolean true '
         '| debconf-set-selections')
    sudo('echo stackops-activity stackops-activity/present-stackops-license '
         'boolean true | debconf-set-selections')
    sudo('echo stackops-activity stackops-activity/rabbit-usr string %s '
         '| debconf-set-selections' % rabbit_username)
    sudo('echo stackops-activity stackops-activity/rabbit-password password '
         '%s | debconf-set-selections' % rabbit_password)
    sudo('echo stackops-activity stackops-activity/rabbit-host string %s '
         '| debconf-set-selections' % rabbit_host)
    sudo('echo stackops-activity stackops-activity/rabbit-port string %s '
         '| debconf-set-selections' % rabbit_port)
    sudo('echo stackops-activity stackops-activity/keystone-usr string %s '
         '| debconf-set-selections' % service_activity_user)
    sudo('echo stackops-activity stackops-activity/keystone-password password '
         '%s | debconf-set-selections' % service_activity_pass)
    sudo('echo stackops-activity stackops-activity/keystone-url string '
         '%s://%s:%s%s | debconf-set-selections' % (auth_protocol,
                                                    auth_host,
                                                    auth_port, auth_uri))
    sudo('echo stackops-activity stackops-activity/keystone-admin-token '
         'string %s | debconf-set-selections' % admin_token)
    package_ensure('stackops-activity')
    sudo('''mysql -h%s -u%s --password=%s %s -e "UPDATE
    ACT_SETTINGS SET PROPERTY_VALUE='%s' WHERE
    PROPERTY_KEE='license.manager.token';"''' %
         (mysql_activity_host, mysql_activity_username,
          mysql_activity_password, mysql_activity_schema, license_token))
    package_ensure('stackops-activity-portal-plugin')


def configure_chargeback(mysql_chargeback_username='chargeback',
                         mysql_chargeback_password='stackops',
                         mysql_chargeback_host='localhost',
                         mysql_chargeback_port='3306',
                         mysql_chargeback_schema='chargeback',
                         mysql_activity_schema='activity',
                         mysql_chargeback_root_password='stackops',
                         service_chargeback_user='chargeback',
                         service_chargeback_password='stackops',
                         admin_token='password',
                         auth_host='127.0.0.1',
                         auth_port='35357',
                         auth_protocol='http',
                         auth_uri='/v2.0'):
    """Generate chargeback configuration. Execute on both servers"""
    sudo('echo stackops-chargeback stackops-chargeback/mysql-usr string '
         '%s | debconf-set-selections' % mysql_chargeback_username)
    sudo('echo stackops-chargeback stackops-chargeback/mysql-password '
         'password %s | debconf-set-selections' % mysql_chargeback_password)
    sudo('echo stackops-chargeback stackops-chargeback/mysql-schema string '
         '%s | debconf-set-selections' % mysql_chargeback_schema)
    sudo('echo stackops-chargeback stackops-chargeback/mysql-activity-schema '
         'string %s | debconf-set-selections' % mysql_activity_schema)
    sudo('echo stackops-chargeback stackops-chargeback/mysql-host string %s '
         '| debconf-set-selections' % mysql_chargeback_host)
    sudo('echo stackops-chargeback stackops-chargeback/mysql-port string %s '
         '| debconf-set-selections' % mysql_chargeback_port)
    sudo('echo stackops-chargeback stackops-chargeback/mysql-admin-password '
         'password %s | debconf-set-selections' %
         mysql_chargeback_root_password)
    sudo('echo stackops-chargeback stackops-chargeback/mysql-purgedb boolean '
         'true | debconf-set-selections')
    sudo('echo stackops-chargeback stackops-chargeback/'
         'present-stackops-license boolean true | debconf-set-selections')
    sudo('echo stackops-chargeback stackops-chargeback/keystone-usr string %s '
         '| debconf-set-selections' % service_chargeback_user)
    sudo('echo stackops-chargeback stackops-chargeback/keystone-password '
         'password %s | debconf-set-selections' % service_chargeback_password)
    sudo('echo stackops-chargeback stackops-chargeback/keystone-url string '
         '%s://%s:%s%s | debconf-set-selections' % (auth_protocol,
                                                    auth_host,
                                                    auth_port, auth_uri))
    sudo('echo stackops-chargeback stackops-chargeback/keystone-admin-token '
         'string %s | debconf-set-selections' % admin_token)
    package_ensure('stackops-chargeback')
    package_ensure('stackops-chargeback-portal-plugin')
