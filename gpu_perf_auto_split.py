#!/usr/bin/env python
# -*- coding: UTF-8 -*-
###################################################################################
#Copyright 2018 NXP                                                               #
#
##The code contained herein is licensed under the GNU General Public
#License. You may obtain a copy of the GNU General Public License
#Version 2 or later at the following locations:
#
##http://www.opensource.org/licenses/gpl-license.html
#http://www.gnu.org/copyleft/gpl.html
###################################################################################
# Revision History:                                                               #
#                      Modification     Tracking                                  #
# Author                   Date          Number    Description of Changes         #
#-------------------   ------------    ----------  ---------------------          #
# Tim Huang              1/1/2018        n/a          Initial ver.                #
###################################################################################


import sys
import os
import re
import string 

def writetofile(wholelog,casename,tfile):
    global caselogcontent
    try:
        fd=open(wholelog,'r')
    except IOError:
        print('open logfile failed')
        sys.exit(1)
    else:
        logcontent=fd.read()
        fd.close()
    split_flag_front='Hook: case Name:  '+casename+' Start'
    split_flag_back='Hook: case '+casename+' Finish'
    case_num=len(logcontent.split(split_flag_front))
    for i in range(case_num,0,-1):
        logcontent=logcontent.split(split_flag_front)[i-1]
        if  re.search(split_flag_back,logcontent,re.S) != None:
            caselogcontent=logcontent.split(split_flag_back)[0]
            break
    fd=open(tfile,'a')
    #print('================')
    #print(tfile)
    #print('================')
    fd.write(caselogcontent)
    fd.close()

def applycaselist(caselistfile):
    case_list=[]
    try:
        fd=open(caselistfile,'r')
    except IOError:
        print('open caselist file failed')
        sys.exit(1)
    else:
        caselist=fd.readlines()
        fd.close()
    for i in caselist:
        case_list.append(str(i).strip())
    return case_list

def splitlogfile(wholelogfile,caselistfile):
    full_case_list=[]
    case_name_old=""
    logcontent=""
    full_case_list=applycaselist(caselistfile)
    try:
        fd=open(wholelogfile,'r')
    except IOError:
        print('open logfile failed')
        sys.exit(1)
    else:
        logcontent=fd.readlines()
        fd.close()
    j=0
    tempfile=wholelogfile+'.temp'
    #print('===============')
    #print(full_case_list)
    #print('===============')
    for case_name in full_case_list: 
        for line in logcontent:
            case_id='Hook: case Name:  '+case_name+' Start'
            if line.find(case_id) != -1:
                if case_name_old is case_name:
                    print('ERROR: case %s has been found at least twice in logfile, please check'%case_name)
                    sys.exit(1)
                else:
                    case_name_old=case_name
                    writetofile(wholelogfile,case_name,tempfile)
                    j=j+1
    #print('============')
    #os.system("ls ../automation_log/log/")
    #print('============')
    try:
        fd=open(tempfile,'r')
    except IOError:
        print('open txt temp file failed')
        sys.exit(1)
    else:
        #remove redundant strings in logfile
        logcontent=fd.read()
        fd.close()
        logcontent=re.sub(r'\[\s*[0-9]+.[0-9]+\]\s*contiguous mapping is too small\s*[0-9]+\/[0-9]+\n','',logcontent)
        logcontent=re.sub(r'\[\s*[0-9]+.[0-9]+\]\s*watchdog: watchdog0: watchdog did not stop!\n','',logcontent)
        logcontent=re.sub(r'\[\s*[0-9]+.[0-9]+\]\s*random: crng init done\n','',logcontent)
        logcontent=re.sub(r'\[\s*[0-9]+.[0-9]+\]\s*alloc_contig_range:\s*\[[0-9]*[a-z]*[0-9]*,\s*[0-9]*[a-z]*[0-9]*\)\s*PFNs busy\n','',logcontent)
        logcontent=re.sub(r'\[\s*[0-9]+.[0-9]+\]\s*alloc_contig_range:\s*[0-9]*\s*callbacks suppressed\n','',logcontent)
        os.system('rm -rf %s'%tempfile)
        fd=open(tempfile,'w')
        fd.write(logcontent)
        fd.close()

def usage():
    name=sys.argv[0]
    print("\nUsage: python %s -f logfile -c case_list_xx\n"%name)
    sys.exit(1)

if __name__ == '__main__':
    argc=len(sys.argv)
    inputlist=sys.argv
    logfile=''
    caselist=''
    it=1
    if argc != 5:
        usage()
    while it < argc:
        if re.search('^(-F|--FILE)$',inputlist[it].upper()):
            logfile=sys.argv[it+1]
            it+=2
        elif re.search('^(-C|--CASELIST)$',inputlist[it].upper()):
            caselist=sys.argv[it+1]
            it+=2
        else:
            usage()
    if logfile == '' or caselist == '':
        print "ERROR: failed to get arguments,please check your cmdline"
        usage()
    splitlogfile(logfile,caselist)
