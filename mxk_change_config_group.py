
"""
Module to change config group from old_grp to new_grp for all ports on a MXK.
"""

import time
import getpass
from netmiko import ConnectHandler

"""
Gather connection information
"""

host = raw_input('Enter hostname of OLT: ')
username = raw_input('Enter username for OLT: ')
password = getpass.getpass('Enter password for OLT: ')
old_grp = raw_input('Enter old config group number: ')
new_grp = raw_input('Enter new config group number: ')
# no handler type for zhone but 'cisco-ios' seems to work
platform = 'cisco_ios'
print ('Connecting....')

"""
Connect to device using Netmiko and run commands to gather info. Use 'cpe-mgr show config member' to gather info on all ports assigned to config groups.
"""

device = ConnectHandler(device_type='cisco_ios', ip=host, username=username, password=password)
print ('Connected to OLT, gathering info.....')
# disable pagination of OLT output
device.send_command('setline 0')
time.sleep(1)

members = device.send_command('cpe-mgr show config member')
time.sleep(3)

"""
'members' is a multi-line unicode string where each line is a port assigned to a config group.
Use splitlines() to convert members into a list of strings, where
each string is a line from members.
Loop over each line and use split to split each line into a list of strings.
Use filter to remove all spaces.
Find each line that has group old_grp assigned and add the port details to list 'members_to_change'.
"""
members_to_change = []

for i in members.splitlines():
    member = i.split(' ')
    member = filter(None, member)
    try:
        if member[1] == old_grp:
            port = member[0]
            try:
                port = port.split(':')[1]
                members_to_change.append(port)
            except:
                port = member[0]
                members_to_change.append(port)
    except Exception as e:
        print e

print 'Ports to be changed:'
print members_to_change
print 'Changing config group of ports......'

"""
Loop over the ports in members_to_change and change the config group from old_grp to new_grp
"""
for i in members_to_change:
    try:
        device.send_command('cpe-mgr delete config member {}'.format(i))
        time.sleep(1)
        device.send_command('cpe-mgr add config member {} group {}'.format(i, new_grp))
        time.sleep(1)
    except:
        print 'Error'


print ('Completed')
