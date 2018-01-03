
"""
Module to retrieve transmit and recieve port discards for each port on a Zhone MXK819/319 and output a CSV file.
"""

import csv
import time
import getpass
from netmiko import ConnectHandler
import pprint
import collections

port_numbers = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
#port_numbers = [2]

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
print ('Please be patient, this may take up to 15 minutes.')
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
        time.sleep(1)
        device.send_command('port stats clear 1/{}/{}/0/eth'.format(s, p))
        time.sleep(1)
    print ('Slot {} completed'.format(s))

device.disconnect()

print ('Disconnected from OLT, formulating report.....')

"""
Loop over stats list and extract the transmit and receive drops. Save in ordered dictionary 'results'.
"""

results = collections.OrderedDict()

for entry in stats_list:
    thing = " ".join(entry.split())
    print thing.split(' ')
    try:
        if ":" in thing.split(' ')[2]:
            short_name = thing.split(' ')[2]
            short_name = short_name.split(':')[1]
            results[short_name + ' Tx Packets'] = thing.split(' ')[26]
            results[short_name + ' Tx Drops'] = thing.split(' ')[47]
        else:
            print thing.split(' ')
            results[thing.split(' ')[2] + ' Tx Packets'] = thing.split(' ')[26]
            results[thing.split(' ')[2] + ' Tx Drops'] = thing.split(' ')[47]
    except Exception as e:
        print e

"""
write contents of results dictionary to csv file
"""
datenow = time.strftime("%b-%d")

with open(host + '_policer_drop_report_' + datenow +'.csv', 'w') as new_file:
    csv_writer = csv.writer(new_file)
    for key, value in results.items():
        csv_writer.writerow([key, value])

print ('Completed')

