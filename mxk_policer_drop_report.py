
"""
Module to retrieve transmit and recieve port discards for each port on a Zhone MXK819/319 and output a CSV file.
"""

import csv
import time
import getpass
from netmiko import ConnectHandler
import pprint
import collections

port_numbers = [1,2,3,4,5,6,7,8,9,10,1,12,13,14,15,16,17,18,19,20]

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
Connect to device using Netmiko and run commands to gather info. Use 'slots' to determine how many downlink modules are present. Loop over each port in each present slot and retrieve 'port stats'. Save info in 'stats_list'.
"""

device = ConnectHandler(device_type='cisco_ios', ip=host, username=username, password=password)
print ('Connected to OLT, gathering info.....')
print ('Please be patient, this may take up to 5 minutes.')
# disable pagination of OLT output
device.send_command('setline 0')
time.sleep(1)
full_slots = []
stats_list = []
slots = device.send_command('slots')
for i in slots.splitlines():
    if 'MXK 20 ACT ETH SS CSFP' in i:
        value = i.split(':')[0]
        value = value.split()
        full_slots.append(''.join(value))

for s in full_slots:
    for p in port_numbers:
        stats_list.append(device.send_command('port stats 1/{}/{}/0/eth'.format(s, p)))
        time.sleep(0.5)
    print ('Slot {} completed'.format(s))

device.disconnect()

print ('Disconnected from OLT, formulating report.....')

"""
Loop over stats list and extract the tarnsmit and receive drops. Save in ordered dictionary 'results'.
"""

results = collections.OrderedDict()

for entry in stats_list:
    thing = " ".join(entry.split())
    if ":" in thing.split(' ')[2]:
        short_name = thing.split(' ')[2]
        short_name = short_name.split(':')[1]
        results[short_name + ' Rx Drops'] = thing.split(' ')[37]
        results[short_name + ' Tx Drops'] = thing.split(' ')[47]
    else:
        results[thing.split(' ')[2] + ' Rx Drops'] = thing.split(' ')[37]
        results[thing.split(' ')[2] + ' Tx Drops'] = thing.split(' ')[47]

"""
write contents of results dictionary to csv file
"""

with open(host + '_policer_drop_report.csv', 'w') as new_file:
    csv_writer = csv.writer(new_file)
    for key, value in results.items():
        csv_writer.writerow([key, value])

print ('Completed')

