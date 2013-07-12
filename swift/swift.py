# -*- coding: utf-8 -*-

import os.path
import functools

from fabric.api import cd, get, put, settings
from cuisine import *

CONF_DIR = '/etc/swift'
CONF_FILE = 'swift.conf'
PROXY_CONF = 'proxy-server.conf'
NODE_DIR = '/srv/node'
RSYNC_CONF = '/etc/rsyncd.conf'
OWNER = {
    'owner': 'swift',
    'group': 'swift'
}


# Common Swift stuff

def install_common_packages():
    """Installs common packages used by a Swift installation"""

    repository_ensure_apt('ppa:openstack-ubuntu-testing/folsom-trunk-testing')
    package_update()

    package_ensure('swift')
    package_ensure('python-swift')


def install_config():
    """Creates the Swift config directory and the swift.conf file"""

    with mode_sudo():
        dir_ensure(CONF_DIR)

        with cd(CONF_DIR):
            file_write(CONF_FILE, _get_config('swift.conf'))


def post_install_config():
    """Runs post installation configuration commands"""

    with mode_sudo():
        dir_attribs(CONF_DIR, recursive=True, **OWNER)


# Swift proxy node stuff

def install_proxy():
    """Installs the Swift proxy node packages"""

    # TODO: Extract the memcached install to another component
    package_ensure('memcached')
    package_ensure('swift-proxy')


def install_proxy_config(auth_port, auth_host, auth_protocol, auth_uri,
                         admin_tenant_name, admin_user, admin_password,
                         keystone_signing_dir):

    """Installs the Swift proxy configuration"""

    data = dict(
        auth_port=auth_port,
        auth_host=auth_host,
        auth_protocol=auth_protocol,
        auth_uri=auth_uri,
        admin_tenant_name=admin_tenant_name,
        admin_user=admin_user,
        admin_password=admin_password,
        keystone_signing_dir=keystone_signing_dir
    )

    config = _template('proxy-server.conf', data)

    with cd(CONF_DIR):
        with mode_sudo():
            file_write(PROXY_CONF, config)


def install_proxy_cert():
    """Installs a self-signed SSL certificate for proxy https support"""

    with cd(CONF_DIR):
        sudo('openssl req -new -x509 -nodes -out cert.crt -keyout cert.key '
             '-subj "/C=US/ST=TX/L=Austin/O=STACKOPS TECHNOLOGIES '
             'INC./OU=STACKOPS 360/CN=127.0.0.1"')


def install_keystone_signing_dir(keystone_signing_dir):
    with mode_sudo():
        dir_ensure(keystone_signing_dir, recursive=True, **OWNER)


def start_proxy():
    """Starts the Swift proxy services"""

    sudo('swift-init proxy start')


def build_rings(zones, part_power, replicas, min_part_hours):
    """Builds the Swift account, container and object rings"""

    with cd(CONF_DIR):
        _create_ring('account.builder', part_power, replicas, min_part_hours)
        _create_ring('container.builder', part_power, replicas, min_part_hours)
        _create_ring('object.builder', part_power, replicas, min_part_hours)

        # Add storage devices for each node
        for zone in zones:
            for node in zone['nodes']:
                for device in node['devices']:
                    _add_device_to_ring(
                        'account.builder', zone['id'], node['ip'], 6002,
                        device['id'], device['weight'])

                    _add_device_to_ring(
                        'container.builder', zone['id'], node['ip'], 6001,
                        device['id'], device['weight'])

                    _add_device_to_ring(
                        'object.builder', zone['id'], node['ip'], 6000,
                        device['id'], device['weight'])

        _rebalance_ring('account.builder')
        _rebalance_ring('container.builder')
        _rebalance_ring('object.builder')

        _validate_ring('account.builder')
        _validate_ring('container.builder')
        _validate_ring('object.builder')


def deploy_rings(zones):
    """Deploys built rings into each storage node"""

    with mode_local():
        dir_remove('rings')
        dir_ensure('rings')

    # Download the built rings from the proxy node
    with cd(CONF_DIR):
        get('*.ring.gz', 'rings')

    # Upload rings to each storage node
    for node in __flat_nodes(zones):
        with settings(host_string=node['ip']):
            put('rings/*.ring.gz', CONF_DIR, use_sudo=True)
            post_install_config()


def _create_ring(name, part_power, replicas, min_part_hours):
    sudo(__swift_ring_builder(name, 'create', part_power,
                              replicas, min_part_hours))


def _add_device_to_ring(name, zone, ip, port, device, weight):
    sudo(__swift_ring_builder(name, 'add', 'z{}-{}:{}/{} {}'.format(
        zone, ip, port, device, weight)))


def _validate_ring(name):
    sudo(__swift_ring_builder(name, 'validate'))


def _rebalance_ring(name):
    sudo(__swift_ring_builder(name, 'rebalance'))


def __swift_ring_builder(*args):
    command = [str(arg) for arg in args]
    command.insert(0, 'swift-ring-builder')

    return ' '.join(command)


# Swift storage node stuff

def install_storage(recon_cache):
    """Installs the Swift storage node packages"""

    package_ensure('swift-account')
    package_ensure('swift-container')
    package_ensure('swift-object')
    package_ensure('python-swiftclient')

    with mode_sudo():
        dir_ensure(NODE_DIR, recursive=True, **OWNER)
        dir_ensure(recon_cache, recursive=True, **OWNER)


def install_storage_config():
    """Installs custom Swift storage configuration"""

    with cd(CONF_DIR):
        with mode_sudo():
            for config in ('account-server.conf', 'container-server.conf',
                           'object-server.conf'):
                file_write(config, _get_config(config))


def install_storage_devices(devices):
    """Installs all the node storage devices and ensures that are mounted"""

    with cd(NODE_DIR):
        for device in devices:
            with mode_sudo():
                dir_ensure(device)

            mount_ensure('/dev/' + device, device)

    with mode_sudo():
        dir_attribs(NODE_DIR, recursive=True, **OWNER)


def install_rsync():
    """Installs and configures rsync"""

    with mode_sudo():
        file_write(RSYNC_CONF, _get_config('rsyncd.conf'))

    sudo("sed -ie 's/RSYNC_ENABLE=false/RSYNC_ENABLE=true/' "
         "/etc/default/rsync")

    sudo('service rsync start')


def start_storage():
    """Starts all the Swift storage services"""

    sudo('swift-init all start')


# Common utilities

def mount_ensure(device, location):
    """Ensures the given `device` is mounted. If not mounted then mounts
    it in the given `location`.

    """

    if not run('mount | grep {} ; true'.format(device)):
        sudo('mount {} {}'.format(device, location))


def _template(name, data):
    return _get_config(name).format(**data)


def _get_config(name):
    path = os.path.join(os.path.dirname(__file__), 'config', name)

    with open(path) as f:
        return f.read()


def __flat_nodes(zones):
    for zone in zones:
        for node in zone['nodes']:
            yield node


# Proxy tests

from expects import expect


def test_config():
    _test_dir_exists(CONF_DIR)
    _test_owner(CONF_DIR, OWNER)

    with cd(CONF_DIR):
        _test_file_exists(CONF_FILE)
        _test_owner(CONF_FILE, OWNER)


def test_proxy_config():
    with cd(CONF_DIR):
        _test_file_exists(PROXY_CONF)
        _test_owner(PROXY_CONF, OWNER)


def test_proxy_cert():
    with cd(CONF_DIR):
        for path in ('cert.crt', 'cert.key'):
            _test_file_exists(path)
            _test_owner(path, OWNER)


def test_keystone_signing_dir(keystone_signing_dir):
    _test_dir_exists(keystone_signing_dir)
    _test_owner(keystone_signing_dir, OWNER)


def test_built_rings():
    _test_rings()


def test_deployed_rings(zones):
    for node in __flat_nodes(zones):
        with settings(host_string=node['ip']):
            _test_rings()


def _test_rings():
    with cd(CONF_DIR):
        for ring in ('account.ring.gz', 'container.ring.gz',
                     'object.ring.gz'):

            _test_file_exists(ring)
            _test_owner(ring, OWNER)


def test_start_proxy():
    # I don't know why, but the `ps -A` command run in the `process_find`
    # function truncates the processes names so I can't match the entire
    # process name 'swift-proxy-server'.

    expect(process_find('swift-proxy')).not_to.be.empty


# Storage tests

def test_storage_config():
    with cd(CONF_DIR):
        for path in ('account-server.conf', 'container-server.conf',
                     'object-server.conf'):

            _test_file_exists(path)
            _test_owner(path, OWNER)


def test_storage(recon_cache):
    _test_dir_exists(NODE_DIR)
    _test_owner(NODE_DIR, OWNER)

    _test_dir_exists(recon_cache)
    _test_owner(recon_cache, OWNER)


def test_storage_devices(devices):
    with cd(NODE_DIR):
        for device in devices:
            _test_dir_exists(device)
            _test_owner(device, OWNER)


def test_rsync():
    _test_file_exists(RSYNC_CONF)

    expect(process_find('rsync')).not_to.be.empty


def test_start_storage():
    expect(process_find('swift-account')).not_to.be.empty
    expect(process_find('swift-container')).not_to.be.empty
    expect(process_find('swift-object')).not_to.be.empty


# Test utilities

def _test_file_exists(path):
    expect(file_exists(path)).to.be.true


def _test_dir_exists(path):
    expect(dir_exists(path)).to.be.true


def _test_owner(path, owner):
    attribs = file_attribs_get(path)

    expect(attribs).to.have.keys(owner)
