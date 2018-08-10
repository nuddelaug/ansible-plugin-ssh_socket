#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
        lookup: ssh_socket
        author: Michaela Lang <Michaela.Lang@ctbto.org>
        version_added: "2.3"
        short_description: looking up an active SSH_socket to be used
        description:
            - This lookup returns an active SSH_socket path if found from the basepath provided
        options:
            _path:
                description: start of path to search for ssh sockets (*/ssh)
                required: True
            _keyname:
                description: ssh agents with multiple keys to ensure you'll find the right one
                required: False
        notes:
            - there's no recursion happening on finding a socket called 'ssh' it's meant that the base follows EL7 specific implementation
"""

EXAMPLES = """
- debug:
    msg: "the socket found is {{ lookup('ssh_socket', '/run/user/{{ ansible_user_uid }}/*/ssh') }}"
    
- debug # pub key complete, or starting/ending part use as much as comfortable to ensure the right one is found
    msg: "key found in socket {{ lookup('ssh_socket', '/run/user/{{ ansible_user_uid }}/*/ssh', keyname='....==') }}"

- name: updating crontab to be able to use ssh-agent for connecting to remote hosts
  cron:
    name: "SSH_AUTH_SOCK"
    env: yes
    value: "{{ lookup('ssh_socket', '/run/user/{{ ansible_user_uid }}/*/ssh', keyname='....==') }}"
    state: present

"""

RETURN = """
    _raw:
        description:
            - ssh socket path
            - exception raised if none is found or key isn't found 
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase

import glob
import paramiko
import os
from itertools import chain

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()
    
class LookupModule(LookupBase):
    def run(self, basepath, variables=None, **kwargs):
        for ssh_soc in chain.from_iterable(map(lambda x: glob.glob(x), basepath)):
            os.environ['SSH_AUTH_SOCK'] = ssh_soc
            display.vvvvv('searching for socket in %s' % os.environ['SSH_AUTH_SOCK'])
            a = paramiko.Agent()
            display.vv('keys found in socket %s: %s' % (os.environ['SSH_AUTH_SOCK'], a.get_keys()))
            if a.get_keys() != ():
                if kwargs.has_key('keyname'):
                    keyname = kwargs['keyname']
                    keys    = map(lambda x: x.get_base64(), a.get_keys())
                    display.vvvvv('checking for key %s' % keyname)
                    display.vvvvv('available keys:\n\t%s' % '\n\t'.join(keys))
                    if any([keyname in keys,
                            keyname in map(lambda x: x[:len(keyname)], keys),
                            keyname in map(lambda x: x[len(x) - len(keyname):], keys),]):
                        display.vv('key %s found' % keyname)
                        return [ ssh_soc ]
                else:
                    display.vv('socket %s found' % ssh_soc)
                    return [ ssh_soc ]
        raise AnsibleError('couldnt find any ssh Agent socket in path %s' % basepath)
