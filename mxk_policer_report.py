

"""
Module to retrieve port and policer information from a Zhone MXK819/319,
massage the data and output a CSV file containing a mapping of port to
policer value.
"""

import csv
import time
import getpass
from netmiko import ConnectHandler

"""
Function used to format strings
"""
def changer(s):
    s = s.split('-')
    s.pop()
    s.pop()
    s = '-'.join(s)
    s = s + '/eth'
    return s

"""
Gather connection information
"""
host = raw_input('Enter hostname of OLT: ')
username = raw_input('Enter username for OLT: ')
password = getpass.getpass('Enter password for OLT: ')
# no handler type for zhone but 'cisco-ios' seems to work
platform = 'cisco_ios'
print ('Connecting....')



"""
Connect to device using Netmiko and run commands to gather info. Save
info in 'ports' and 'rules' variables.
"""
device = ConnectHandler(device_type=platform, ip=host, username=username, password=password)
print ('Connected to OLT, gathering info.....')
# disable pagination of OLT output
device.send_command('setline 0')
time.sleep(1)
ports = device.send_command('rule showuser')
time.sleep(2)
rules = device.send_command('rule show')
time.sleep(2)
device.disconnect()
print ('Disconnected from OLT, formulating report.....')

"""
'rules' is a multi-line unicode string where each line is an OLT policer
policy.
Use splitlines() to convert rules into a list of strings, where
each string is a line from rules.
Loop over these lines and use split to split each line into
a list of strings.
Loop over each inner list and look for 'ratelimitdiscard'. If
'ratelimitdiscard' is present then retrieve rate limiter ID and
and rate limiter value using their index and insert into policers
dictionary.
Note - 2 different sets of indexes are required because some OLTs
output contains the required info in different positions in the output
string, probably because of code version.

"""
policers = {}

for i in rules.splitlines():
    for l in i.split(' '):
        if 'ratelimitdiscard' in l:
            if '/' in i.split(' ')[27]:
                policers[i.split(' ')[27]] = i.split(' ')[45]
            if '/' in i.split(' ')[28]:
                policers[i.split(' ')[28]] = i.split(' ')[46]
"""
Loop through policers dictionary and change actual policer
values to human readable values. This loop will have to be
modified based on the values used.
"""
for k, v in policers.items():
    if v == '27000kbps' or v == '25000kbps':
        policers[k] = '25'
    if v == '54000kbps' or v == '50000kbps':
        policers[k] = '50'
    if v == '108000kbps' or v == '100000kbps':
        policers[k] = '100'
    if v == '580000kbps' or v == '540000kbps':
        policers[k] = '500'

"""
'ports' is a multi-line unicode string where each line contains a
port and it's coresponding policy ID.
Use splitlines() to convert ports into a list of strings, where
each string is a line from rules.
Loop over these lines and use split to split each line into
a list of strings.
Loop over each inner list and look for 'ratelimitdiscard'. If
'ratelimitdiscard' is present then retrieve rate limiter ID and
and port info using their index and insert into results
dictionary. Use the rate limiter ID as a key into policers dictionary
to insert actual policer value into results dictionary.
Note - 3 different sets of indexes are required because some OLTs
output contains the required info in different positions in the output
string.

"""

results = {}

for i in ports.splitlines():
    for l in i.split(' '):
        if 'ratelimitdiscard' in l:
            if '/' in i.split(' ')[29] and '/br' in i.split(' ')[52]:
                results[i.split(' ')[52]] = policers[i.split(' ')[29]]
            if '/' in i.split(' ')[29] and '/br' in i.split(' ')[51]:
                results[i.split(' ')[51]] = policers[i.split(' ')[29]]
            if '/' in i.split(' ')[28] and '/br' in i.split(' ')[50]:
                results[i.split(' ')[50]] = policers[i.split(' ')[28]]

"""
1Gbps services are unpoliced so do not have a ratelimiter applied. They
just have an option 82 insertion policy applied on input. So to identify
1Gbps services we look at all option 82 policies, find the port details
and check if that port is already in the results dictionary. If it is not
then the port must be a 1Gbps service port so we add it to the results
dictionary as a 1Gbps port.
"""
for i in ports.splitlines():
    for l in i.split(' '):
        if 'bridgeinsertoption82' in l:
            if '/br' in i.split(' ')[-2] and i.split(' ')[-2] not in results.keys():
                results[i.split(' ')[-2]] = '1000'


"""
Use changer function to clean up the keys in results dict
"""
results = {changer(key) : value for key, value in results.items()}

"""
write contents of results dictionary to csv file
"""
with open(host + '_policer_report.csv', 'w') as new_file:
    csv_writer = csv.writer(new_file)
    for key, value in results.items():
        csv_writer.writerow([key, value])

print ('Completed')

