#!/usr/bin/python3

import subprocess
import argparse
import sys
import requests
import json

f=None
out='out.json'

parser = argparse.ArgumentParser(description='openqa test data:display the  differences of Settings betwen 2 given tests IDs Or display the full data set of a single test ID')
parser.add_argument('--host', default='openqa.suse.de',help='Hostname; Default openqa.suse.de')
parser.add_argument('--jobids','-j', help='jobid1[,jobid2] # Enter 1[Full data] or 2[Differences] IDs')
parser.add_argument('--nossl','-n', action='store_true', help='http without ssl - Default https')
parser.add_argument('--comments','-c', action='store_true', help='to print job comments too - Default none')
parser.add_argument('--details','-d', action='store_true', help='to print also details of all result boxes; only allowed when jobid2 missing - Default none')
parser.add_argument('--skipfield','-s', default='NAME', help='F1[,F2,...] list of job.setting FiledNames to skip from diff. - Defult no skip - Default -s = NAME')
parser.add_argument('--file','-f', action='store', nargs='?', default='stdout', const=out, help='print json data to file out.json - Default stdout - Default -f = out.json')
args = parser.parse_args()

source_url=''
# Parameter list, to skip from diff.check default in argument parser
obvious_differs=args.skipfield.split(",")

if not (args.jobids):
    parser.print_help()
    exit(1) 

ids=args.jobids.split(",")

if args.nossl:
    source_url = 'http://'
else:
    source_url = 'https://'

# default host OSD set in argument parser
source_url += args.host + '/api/v1/jobs/'

if args.file == 'stdout':
    f=sys.stdout
else:
    if args.file != out:
        out=args.file
    f = open(out, 'w')

print(f'Result url:{source_url} - jobids:{ids}')

if len(ids) < 1:
    exit(1)
else:
    try:
        group_json1 = requests.get(source_url+ids[0]).json()
        if args.comments:
            group_json1_c = requests.get(source_url+ids[0]+'/comments').json()
        if args.details:
            if len(ids) > 1:
                raise SyntaxError
            else:
                group_json1_d = requests.get(source_url+ids[0]+'/details').json()
    except:
        print(f"ID {ids[0]} data not found or wrong query/option,check -host/-n/-d/")
        exit(1)

if len(ids) == 1:
    if args.details:
        print('\n',json.dumps(group_json1_d,indent=2),file=f)
    else:
        print('\n',json.dumps(group_json1,indent=2), file=f)

    if args.comments:
        print('\n',json.dumps(group_json1_c,indent=2), file=f)
else:
    try:
        group_json2 = requests.get(source_url+ids[1]).json()
        if args.comments:
            group_json2_c = requests.get(source_url+ids[1]+'/comments').json()
        if args.details:
            raise SyntaxError
    except:
        print(f"ID {ids[1]} data not found or wrong query/option")
        exit(1)

    diff_data1 = dict()
    diff_data2 = dict()
    common_data = dict()
    extra_first = dict()
    extra_second = dict()

    for key, value in group_json1['job']['settings'].items():
        if key in obvious_differs:
            continue
 
        # JOB 1+2 COMMON KEYS
        if key in group_json2['job']['settings']:
            value2 = group_json2['job']['settings'][key]
            if value != value2: 
                # SAME KEY DIFFERENT VALUES
                diff_data1.update({key:value})
                diff_data2.update({key:value2})
            else: 
                # SAME KEY SAME VALUE
                common_data.update({key:value})

    # job 1 only KEYS
    for key in group_json1['job']['settings'].keys():
        if key in obvious_differs:
            continue

        if key not in group_json2['job']['settings']:
            value=group_json1['job']['settings'][key]
            extra_first.update({key:value})

    # job 2 only KEYS
    for key in group_json2['job']['settings'].keys():
        if key in obvious_differs:
            continue

        if key not in group_json1['job']['settings']:
            value=group_json2['job']['settings'][key]
            extra_second.update({key:value})

    # Results:

    # All common key\val
    print(f'\n*** All common keys & values ', file=f)
    print(ids,json.dumps(common_data,indent=2), file=f)

    # Common keys, different values
    # job 1
    print(f'\n*** Common keys, different values:', file=f)
    print(ids[0],json.dumps(diff_data1,indent=2), file=f)
    # job 2
    #print(f'*** JOB:{ids[1]} - Common keys, different values')
    print(ids[1],json.dumps(diff_data2,indent=2), file=f)

    # Different Keys 
    # job 1
    print(f'\n*** Extra keys:', file=f)
    print(ids[0],json.dumps(extra_first,indent=2), file=f)

    # job 2
    #print(f'*** JOB {ids[1]} - Extra keys')
    print(ids[1],json.dumps(extra_second,indent=2), file=f)

    # Comments
    if args.comments:
        print(f'\n*** Comments:', file=f)
        print(ids[0], json.dumps(group_json1_c,indent=2), file=f)
        print(ids[1], json.dumps(group_json2_c,indent=2), file=f)

if args.file:
    print('Data stored in ',f.name)
    f.close()


