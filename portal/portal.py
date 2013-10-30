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
#   limitations under the License.
from fabric.api import settings, sudo
from cuisine import package_ensure, package_clean


def stop():
    with settings(warn_only=True):
        sudo("nohup service tomcat7 stop")


def start():
    stop()
    sudo("nohup service tomcat7 start")


def configure_ubuntu_packages():
    """Configure portal packages"""
    package_ensure('openjdk-7-jdk')
    package_ensure('tomcat7')
    package_ensure('stackops-portal')
    package_ensure('mysql-client')
    package_ensure('stackops-documentation-portal-plugin')
    package_ensure('stackops-glance-portal-plugin')
    package_ensure('stackops-instances-portal-plugin')
    package_ensure('stackops-zendesk-portal-plugin')
    package_ensure('stackops-accounting-portal-plugin')
    package_ensure('stackops-cinder-portal-plugin')
    package_ensure('stackops-security-portal-plugin')
    package_ensure('stackops-quotas-portal-plugin')
    package_ensure('stackops-flavors-portal-plugin')
    package_ensure('stackops-networking-portal-plugin')
    package_ensure('stackops-hostsmanager-portal-plugin')


def uninstall_ubuntu_packages():
    """Uninstall portal packages"""
    package_clean('stackops-hostsmanager-portal-plugin')
    package_clean('stackops-networking-portal-plugin')
    package_clean('stackops-flavors-portal-plugin')
    package_clean('stackops-quotas-portal-plugin')
    package_clean('stackops-security-portal-plugin')
    package_clean('stackops-cinder-portal-plugin')
    package_clean('stackops-accounting-portal-plugin')
    package_clean('stackops-documentation-portal-plugin')
    package_clean('stackops-glance-portal-plugin')
    package_clean('stackops-instances-portal-plugin')
    package_clean('stackops-zendesk-portal-plugin')
    package_clean('stackops-portal')
    package_clean('tomcat7')
    package_clean('openjdk-7-jdk')
    package_clean('mysql-client')


def configure(mysql_username='portal',
              mysql_password='stackops',
              admin_token='password',
              mysql_admin_password='stackops',
              keystone_url='http://localhost:5000/v2.0',
              keystone_admin_url='http://localhost:35357/v2.0',
              mysql_host='127.0.0.1',
              mysql_port='3306',
              mysql_schema='portal',
              automation_license_token='vs0QiaN9TA6lIIe3uPSfiG3fs',
              activity_license_token='SUhIsoHOLNFjt6Drz7W26NrNs'):
    """Generate portal configuration. Execute on both servers"""
    sudo('echo stackops-portal stackops-portal/mysql-usr string %s | '
         'debconf-set-selections' % mysql_username)
    sudo('echo stackops-portal stackops-portal/mysql-password password %s '
         '| debconf-set-selections' % mysql_password)
    sudo('echo stackops-portal stackops-portal/mysql-schema string %s '
         '| debconf-set-selections' % mysql_schema)
    sudo('echo stackops-portal stackops-portal/mysql-host string %s '
         '| debconf-set-selections' % mysql_host)
    sudo('echo stackops-portal stackops-portal/mysql-port string %s |'
         'debconf-set-selections' % mysql_port)
    sudo('echo stackops-portal stackops-portal/mysql-admin-password password '
         '%s | debconf-set-selections' % mysql_admin_password)
    sudo('echo stackops-portal stackops-portal/mysql-purgedb boolean true '
         '| debconf-set-selections')
    sudo('echo stackops-portal stackops-portal/present-stackops-license '
         'boolean true | debconf-set-selections')
    sudo('echo stackops-portal stackops-portal/keystone-url string %s '
         '| debconf-set-selections' % keystone_url)
    sudo('echo stackops-portal stackops-portal/keystone-admin-url string %s '
         '| debconf-set-selections' % keystone_admin_url)
    sudo('echo stackops-portal stackops-portal/keystone-admin-token string %s '
         '| debconf-set-selections' % admin_token)
    configure_ubuntu_packages()
    configure_automation_license(automation_license_token,
                                 mysql_admin_password)
    configure_activity_license(activity_license_token,
                               mysql_admin_password)


def _configure_token_license(app_id, license_token, root_pass):
        sudo("""mysql -uroot -p%(root_pass)s -e "INSERT INTO
        PORTAL_LICENSING_TOKEN (APP_ID,TOKEN) VALUES ('%(app_id)s',
        '%(lic_token)s');" portal""" % {'root_pass': root_pass,
                                        'app_id': app_id,
                                        'lic_token': license_token})


def configure_automation_license(license_token=None, root_pass="stackops"):
    _configure_token_license('automation', license_token, root_pass)


def configure_activity_license(license_token=None, root_pass="stackops"):
    _configure_token_license('activity', license_token, root_pass)
