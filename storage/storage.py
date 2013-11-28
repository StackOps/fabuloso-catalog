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

from fabric.api import sudo, settings
from cuisine import package_ensure
from fabuloso import fabuloso


def stop():
    with settings(warn_only=True):
        sudo("nohup service nfs-kernel-server stop")


def start():
    stop()
    sudo("nohup service nfs-kernel-server start")


def restart():
    sudo("nohup service nfs-kernel-server start")


def configure_ubuntu_packages():
    """Configure rabbitmq ubuntu packages"""
    package_ensure('nfs-kernel-server')


def install(master_datastore='/exports/stackops'):
    """Creates an Internal NFS Server configuration
    for storage (volumes, instances and images)
    as default and as first candidate to operate"""
    configure_ubuntu_packages()
    sudo('mkdir -p %s/instances' % master_datastore)
    sudo('mkdir -p %s/volumes' % master_datastore)
    sudo('mkdir -p %s/images' % master_datastore)
    sudo('sed -i \'/stackops/d\' /etc/exports')
    sudo('echo \"%s *(rw,sync,fsid=0,no_root_squash,'
         'subtree_check)\" >> /etc/exports' % master_datastore)
    restart()


def validate(master_endpoint='localhost',
             master_datastore='/exports/stackops',
             master_storage_type='NFS',
             master_mount_parameters='defaults',
             master_hostname=None):
    print sudo('showmount -e %s' % master_endpoint)
    print '\n'

    sudo('cd /mnt/ && mkdir nfs_instances && mount -o soft,intr,rsize=8192,'
         'wsize=8192 %s:%s/instances /mnt/nfs_instances'
         % (master_endpoint, master_datastore))
    print sudo('cd /mnt/nfs_instances/ && mkdir test_instances_succesfully '
               '&& ls')
    print '\n'
    sudo('cd /mnt/nfs_instances/ && rm -r test_instances_succesfully')
    sudo('cd /mnt/ && umount nfs_instances/')
    sudo('cd /mnt/ && rm -r nfs_instances/')

    sudo('cd /mnt/ && mkdir nfs_volumes && mount -o soft,intr,rsize=8192,'
         'wsize=8192 %s:%s/volumes /mnt/nfs_volumes'
         % (master_endpoint, master_datastore))
    print sudo('cd /mnt/nfs_volumes/ && mkdir test_volumes_succesfully && ls')
    print '\n'
    sudo('cd /mnt/nfs_volumes/ && rm -r test_volumes_succesfully')
    sudo('cd /mnt/ && umount nfs_volumes/')
    sudo('cd /mnt/ && rm -r nfs_volumes/')

    sudo('cd /mnt/ && mkdir nfs_images && mount -o soft,intr,rsize=8192,'
         'wsize=8192 %s:%s/images /mnt/nfs_images'
         % (master_endpoint, master_datastore))
    print sudo('cd /mnt/nfs_images/ && mkdir test_images_succesfully && ls')
    print '\n'
    sudo('cd /mnt/nfs_images/ && rm -r test_images_succesfully')
    sudo('cd /mnt/ && umount nfs_images/')
    sudo('cd /mnt/ && rm -r nfs_images/')


def storage_instances(instances_endpoint='localhost',
                      instances_datastore='/exports/stackops/instances',
                      instances_storage_type='NFS',
                      instances_mount_parameters='defaults',
                      instances_hostname=None):
    """Here are defined just a set of properties to be used at the moment to
    do an 'attach' or 'detach' to a zone from the pool's datastore, and use
    them for instances. This properties are the match between the isolated
    datastores functionality and a zone.
    The default definition of these properties are given at the moment to do
    the install() method of this component showed above"""
    pass


def storage_volumes(volumes_endpoint='localhost',
                    volumes_datastore='/exports/stackops/volumes',
                    volumes_storage_type='NFS',
                    volumes_mount_parameters='defaults',
                    volumes_hostname=None):
    """Here are defined just a set of properties to be used at the moment to
    do an 'attach' or 'detach' to a zone from the pool's datastore, and use
    them for volumes. This properties are the match between the isolated
    datastores functionality and a zone.
    The default definition of these properties are given at the moment to do
    the install() method of this component showed above"""
    pass


def storage_images(images_endpoint='localhost',
                   images_datastore='/exports/stackops/images',
                   images_storage_type='NFS',
                   images_mount_parameters='defaults',
                   images_hostname=None):
    """Here are defined just a set of properties to be used at the moment to
    do an 'attach' or 'detach' to a zone from the pool's datastore, and use
    them for images. This properties are the match between the isolated
    datastores functionality and a zone.
    The default definition of these properties are given at the moment to do
    the install() method of this component showed above"""
    pass
