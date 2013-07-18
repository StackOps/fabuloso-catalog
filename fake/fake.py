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
import time


def tear_down(fake_tear_down_time):
    print "Start : %s" % time.ctime()
    time.sleep(fake_tear_down_time)
    print "End : %s" % time.ctime()


def setup(fake_setup_time):
    print "Start : %s" % time.ctime()
    time.sleep(fake_setup_time)
    print "End : %s" % time.ctime()


def install(fake_install_time):
    print "Start : %s" % time.ctime()
    time.sleep(fake_install_time)
    print "End : %s" % time.ctime()


def verify(fake_verify_time):
    print "Start : %s" % time.ctime()
    time.sleep(fake_verify_time)
    print "End : %s" % time.ctime()
