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


def install(master_datastore):
    """Generate Internal NFS Server for storage
    (volumes, instances and images) configuration. """
    configure_ubuntu_packages()
    sudo('mkdir -p %s/instances' % master_datastore)
    sudo('mkdir -p %s/volumes' % master_datastore)
    sudo('mkdir -p %s/images' % master_datastore)
    sudo('sed -i \'/stackops/d\' /etc/exports')
    sudo('echo \"%s *(rw,sync,fsid=0,no_root_squash,'
         'subtree_check)\" >> /etc/exports' % master_datastore)
    restart()


def validate(master_endpoint, master_datastore, master_storage_type,
             master_mount_parameters, master_hostname=None):
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


def storage_instances(instances_endpoint, instances_datastore,
                      instances_storage_type, instances_mount_parameters,
                      instances_hostname=None):
    pass


def storage_volumes(volumes_endpoint, volumes_datastore, volumes_storage_type,
                    volumes_mount_parameters, volumes_hostname=None):
    pass


def storage_images(images_endpoint, images_datastore, images_storage_type,
                   images_mount_parameters, images_hostname=None):
    pass
