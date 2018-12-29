#!/usr/bin/python
#############################################################################
#copyright (C) 2012 Freescale Semiconductor, Inc. All Rights Reserved.      #
#                                                                           #
#The code contained herein is licensed under the GNU General Public         #
#License. You may obtain a copy of the GNU General Public License           #
#Version 2 or later at the following locations:                             #
#                                                                           #
#http://www.opensource.org/licenses/gpl-license.html                        #
#http://www.gnu.org/copyleft/gpl.html                                       #
#                                                                           #
# Revision History:                                                         #
#                      Modification     Tracking                            #
# Author                   Date          Number    Description of Changes   #
#-------------------   ------------    ----------  ---------------------    #
# Jared Hu              13/06/2014         n/a          Initial ver.        #
# Adam  Du              26/08/2014         n/a               V1.1           #
# Adam  Du              18/09/2014         n/a               V2.1           #
# Tim Huang             1/1/2018           n/a               v2.2           #
#############################################################################
import sys
import os
import re
import xlrd
import xlwt
import time
import string
import fcntl
from xlutils.copy import copy

# define the case name map
# left is in excel while right in logFile
silence = 0
casenamemap={'MM06':'mm06 test',
             'MM07':'mm07 test',
             'MM06_NOAA':'mm06 NOAA test',
             'MM06_FSAA':'mm06 FSAA test',
             'MM07_NOAA':'mm07 NOAA test',
             'MM07_FSAA':'mm07 FSAA test',
             'MIRADA':'Mirada',
             'MIRADA NOAA':'Mirada NOAA test',
             'BASEMARK_V2':'basemark_v2 test',
             'VGMARK_GC355':'VGmark_gc355 test',
             'VGMARK_GC355\n(RGB888)':'VGmark_gc355 test',
             'VGMARK_GC2000':'VGmark10_gc2000 test',
             'VGMARK11_GC2000':'VGmark11_gc2000 test',
             'VGMARK_GC2000\n(8880)':'VGmark10_gc2000 test',
             'GTK-PERF':'gtkperf test',
             'GTKPERF':'gtkperf test',
             'DF_DOK':'df_dok test',
             'GPUBENCH':'gpubench test',
             'EGL/GLES':'SPECIAL',
             'GL':'SPECIAL',
             'OPENCL TEST':'OpenCL Test',
             'CLPEAK':'clpeak test',
             'GEMM':'GEMM test',
             'HEVC_CL':'hevc_cl_test test',
             'OCL':'SPECIAL',
             'SOFTISP':'SoftISP test',
             'WEBGL':'WebGL performance test',
             'MOTIONMARK':'MotionMark Test',
             'WEBGL3.0':'WebGL3.0 Test',
             'G2D':'G2d performance test',
             'XACC':'acceleration test',
             'KPA':'KPA performance test',
             'GRAPHIC_CBM_ID_4A_FLUSH':'Graphic_CBM_ID_4A_flush test',
             'GRAPHIC_CBM_ID_4B_FLUSH&SWAP':'Graphic_CBM_ID_4B_flushswap test',
             'GRAPHIC_CBM_ID_4C_FINISH&SWAP':'Graphic_CBM_ID_4C_finishswap test',
             'GRAPHIC_CBM_ID_4_FINISH':'Graphic_CBM_ID_4_finish test',
             'GRAPHIC_CBM_ID_5A_FLUSH':'Graphic_CBM_ID_5A_flush test',
             'GRAPHIC_CBM_ID_5B_FLUSH&SWAP':'Graphic_CBM_ID_5B_flushswap test',
             'GRAPHIC_CBM_ID_5C_FINISH&SWAP':'Graphic_CBM_ID_5C_finishswap test',
             'GRAPHIC_CBM_ID_5_FINISH':'Graphic_CBM_ID_5_finish test',
             'GRAPHIC_CBM_ID_6A_FLUSH':'Graphic_CBM_ID_6A_flush test',
             'GRAPHIC_CBM_ID_6B_FLUSH&SWAP':'Graphic_CBM_ID_6B_flushswap test',
             'GRAPHIC_CBM_ID_6C_FINISH&SWAP':'Graphic_CBM_ID_6C_finishswap test',
             'GRAPHIC_CBM_ID_6_FINISH':'Graphic_CBM_ID_6_finish test',
             'GRAPHIC_CBM_ID_99_FINISH&SWAP':'Graphic_CBM_ID_99_finishswap test'
             }

############################################################
#
# description: a class for lock file by using fcntl
#
############################################################
class Lock(object):
    def __init__(self,filename):
        self.fobj=open(filename, 'w')
        self.handle=self.fobj.fileno()
    
    def acquire(self):
        try:
            fcntl.flock(self.handle, fcntl.LOCK_EX)
            print('Locking on block file, please wait')
            time.sleep(10)
        except:
            print('Block file was locked, please try again later')

    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        print('Unlock block file successfully')

    def __del__(self):
        self.fobj.close()
        os.system('rm block.txt')

############################################################
#   description: get checkitem data                        #
#                python has no switch statement             #
#                the following def just like switch        #
#   parm: logfragment - logfile fragment                   #
#         checkitem - checkitem in the logfile             #
#   ret : return the checkitem data                        #
############################################################

def getcheckitemdata(logfragment,casename,checkitem):
    checkitem = checkitem.strip()
    if '_L_' in checkitem:
        stepList = checkitem.split('_L_')
        ch0 = stepList[0].strip()
        ch1 = stepList[1].strip()
        var = ch0+'.*?'+ch1+' *\d+\.*\d'
        if 'colorseg_demo' in checkitem:
            return colorseg_demo(logfragment,checkitem,casename)
        elif 'CLPEAK' in casename:
            return clpeak(logfragment,checkitem)
        else:
            return handle_gap(logfragment, checkitem, casename, var)
    else:
        if 'GRAPHIC_CBM' in casename:
            return graphics_contibenchmark(logfragment,checkitem)
        fundict={'G2D':g2d,'WEBGL':webgl,'MM06':mm06,'MM07':mm07,'MIRADA':Mirada,'MIRADA NOAA':Mirada,
                'BASEMARK_V2':basemark_v2,'VGMARK_GC2000':vgmark_gc2000,'VGMARK_GC355':vgmark_gc355,
                'GTK-PERF':gtkperf,'GTKPERF':gtkperf,'DF_DOK':df_dok,'GPUBENCH':gpubench,'MM07_NOAA':MM07_NOAA,
                'MM07_FSAA':MM07_FSAA,'MM06_NOAA':MM06_NOAA,'MM06_FSAA':MM06_FSAA,'XACC':XACC,'HEVC_CL':hevc_cl,
                'CLPEAK':clpeak,'KPA':kpa,'VGMARK11_GC2000':vgmark11_gc2000}
        return fundict[casename](logfragment,checkitem)

def getcheckitemdataspecial(logfragment,checkitemname,checkitem):
    funcdict = {'GLMARK2-ES2FULLSCREEN(SCORE)':glmark_score,
                'GLMARK2-ES2-WAYLANDFULLSCREEN(SCORE)':glmark_score,
                'SIMPLE_DRAW(FPS)':noName,
                'TUTORIAL6_ES20(FPS)':normal_get,
                'ES2GEARS(FPS)': gears_max,
                'GLXGEARSFULLSCREEN(FPS)': gears_max,
                'GLMARK2FULLSCREEN(SCORE)':glmark_score,
                'TOTALRUNNINGTIME(S)':ocl}
    return funcdict[checkitemname](logfragment, checkitem, checkitemname)

def glmark_score(logfragment, checkitem, checkitemname='glmark_score'):
    stepList = checkitem.split('_L_')
    ch0 = stepList[0].strip()
    ch1 = stepList[-1].strip()
    chSp = 'OpenGL ES'
    var = ch0+'.*?'+ch1+'.*?\d+'
    stepList = checkitem.split('_L_')
    pattern = re.compile(var, re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        #print checkitem+match[-1].split()[-1]
        if len(stepList) ==3: # for openGL ES
            if chSp in match[0]:
                return match[0].split()[-1]
            elif len(match) == 1: # to forbid invalid call to match[1]
                print 'missed in '+checkitem+' \tin\t '+checkitemname
            elif chSp in match[1]:
                return match[1].split()[-1]
            else:
                print 'missed in '+checkitem+' \tin\t '+checkitemname
        else:
            if  not chSp in match[0]:
                return match[0].split()[-1]
            elif len(match) == 1: # to forbid invalid call to match[1]
                print 'missed in '+checkitem+' \tin\t '+checkitemname
            elif not chSp in match[1]:
                return match[1].split()[-1]
            else:
                print 'missed in '+checkitem+' \tin\t '+checkitemname

def gears_max(logfragment, checkitem, checkitemname='gears_max'):
    stepList = checkitem.split('_L_')
    ch0 = stepList[0].strip()
    ch1 = stepList[1].strip()
    ch2 = stepList[2].strip()
    chTag = '=========================='
    var = ch0+'.*?'+chTag+'.*?'+chTag
    pattern = re.compile(var, re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        if re.search(ch0, logfragment[-1])!=None:
            match = []
        else:
            print 'missed in '+checkitem+' \tin\t '+checkitemname
            return None
    var = ch1+'.*?'+ch2+' *?\d+\.\d+'
    pattern = re.compile(var, re.S)
    match = pattern.findall(match[-1])
    max = 0
    for matchCase in match:
        dataTemp = matchCase.split()[-1]
        if string.atof(dataTemp) > max:
            max = string.atof ( dataTemp )
    return str( max )

def normal_get(logfragment, checkitem, checkitemname='normal_get'):
    stepList = checkitem.split('_L_')
    ch0 = stepList[0].strip()
    ch1 = stepList[-1].strip()
    var = ch0+'.*?'+ch1+' *\d+\.\d+'
    return handle_gap(logfragment, checkitem, checkitemname, var)

def noName(logfragment, checkitem, checkitemname):
    return -1
def gpubench(logfragment, checkitem, checkitemname='gpubench'):
    checkitem = checkitem.strip()
    pattern=re.compile('[^ ]'+checkitem+'.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' in the func '+checkitemname
    else:
        #print checkitem+match[-1].split()[-1]
        return match[0].split()[-1]

def df_dok(logfragment, checkitem, checkitemname='df_dok'):
    checkitem = checkitem.strip()
    pattern=re.compile('[^ ]'+checkitem+' *\d+\.\d+.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' in the func '+checkitemname
    else:
        #print checkitem+match[-1].split()[-1]
        return match[-1].split()[-1]

def MM06_NOAA(logfragment, checkitem):
    return mm06(logfragment,checkitem, 'MM06_NOAA')
def MM06_FSAA(logfragment, checkitem):
    return mm06(logfragment, checkitem, 'MM06_FSAA')
def mm06(logfragment,checkitem, checkitemname='MM06'):
    pattern=re.compile(checkitem+'.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        return match[0].split()[-1]

def MM07_NOAA(logfragment, checkitem):
    return mm07(logfragment, checkitem,'MM07_NOAA')
def MM07_FSAA(logfragment, checkitem):
    return mm07(logfragment, checkitem, 'MM07_FSAA')
def mm07(logfragment,checkitem, checkitemname='MM07'):
    pattern=re.compile(checkitem+'.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        if checkitem == 'unified shader - Completed':
            return match[0].split()[-1]
        return match[0].split()[-1]

def webgl(logfragment,checkitem, checkitemname='WEBGL'):
    pattern=re.compile(checkitem+'\s+'+':'+'\s+\d+',re.S)
    pattern=re.compile(checkitem+':'+'\s+\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        return match[0].split()[-1]

def graphics_contibenchmark(logfragment,checkitem, checkitemname='ContiBenchmark'):
    pattern=re.compile(checkitem+'\s+'+':'+'\s+\d+\.\d+',re.S)
    match=re.findall(pattern,logfragment[-1])
    logid=len(logfragment)-2
    while len(match)==0 and logid>=0:
        match=pattern.findall(logfragment[logid])
        logid-=1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
        writeToCheckItemMiss(checkitemname, checkitem)
    else:
        return match[0].split()[-1]

def g2d(logfragment,checkitem,checkitemname='G2D'):
    pattern=re.compile(checkitem+'.*?\d+us,.*?\d+fps,.*?\d+Mpixel/s',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid >= 0:
        match=pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        value=match[0].split(',')[-1]
        value=value.split('Mpixel/s')[0]
        return value

def XACC(logfragment,checkitem,checkitemname='XACC'):
    pattern=re.compile('\s*\d+\strep\s@\s+\d+\.\d+\smsec\s\(\s*\d+\.\d\/sec\):\s'+checkitem,re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid >= 0:
        match=pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        value=match[0].split('msec')[0]
        value=value.split('@')[-1]
        return value

def Mirada(logfragment,checkitem,checkitemname='Mirada'):
    pattern=re.compile(checkitem+'.*?cut avg fps.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        #print checkitem+match[0].split()[-1]
        return match[0].split()[-1]

def basemark_v2(logfragment,checkitem, checkitemname='basemark_v2'):
    pattern=re.compile(checkitem+'.*?Average fps.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)!=2 and logid>=0: # expect exact 2 match as high and normal
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==2:
        return match[0].split()[-1],match[1].split()[-1]
    else:
        print 'basemark need two mode:High Q and Normal Q\n'
        print 'please make sure there are two mode in the log\n'

def vgmark_gc2000(logfragment,checkitem,checkitemname='vgmark_gc2000'):
    if 'Image quality' in checkitem:
        pattern=re.compile(checkitem+'.*?Score.*?\d+\.\d+',re.S)
    else:
        pattern=re.compile(checkitem+'.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        return match[-1].split()[-1]

def vgmark_gc355(logfragment,checkitem,checkitemname='vgmark_gc355'):
    if 'Image quality' in checkitem:
        pattern=re.compile(checkitem+'.*?Score.*?\d+\.\d+',re.S)
    else:
        pattern=re.compile(checkitem+'.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        return match[-1].split()[-1]

def vgmark11_gc2000(logfragment,checkitem,checkitemname='vgmark11_gc2000'):
    pattern=re.compile('FPS total: '+'\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    #match shoube like ['FPS total: 17.475', 'FPS total: 17.040']
    if len(match) != 2:
        print 'missed in'+checkitem+' \tin\t '+checkitemname
    if 'RGB565' in checkitem:
        return match[0].split()[-1]
    elif 'RGB888' in checkitem:
        return match[-1].split()[-1]
    else:
        print 'can not find RGB565 or RGB888 in checkitem'

def gtkperf(logfragment,checkitem, checkitemname='gtkperf'):
    pattern=re.compile(checkitem+'.*?\d+\.\d+',re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        return match[-1].split()[-1]

def clpeak(logfragment,checkitem, checkitemname='clpeak'):
    stepList = checkitem.split('_L_')
    if len(stepList) == 3:
        ch0 = stepList[0].strip()
        ch1 = stepList[-1].strip()
        pattern_item=re.compile(ch0, re.S)
        if pattern_item.findall(logfragment[-1]):
            logfragment=logfragment[-1].split(ch0)[1]
            logfragment=logfragment.split(ch1)[0]
            currentItem = stepList[1].strip()
            var=currentItem+'.*?\d+\.\d+'
            pattern = re.compile(var, re.S)
            match=pattern.findall(logfragment)
        else:
            print 'missed in '+checkitem+' \tin\t '+checkitemname
            match = []
    else:
        pattern = re.compile(checkitem+'.*?\d+\.\d+',re.S)
        match=pattern.findall(logfragment[-1])
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
    else:
        # do result check, wether extract not exact value
        checkString='\r\n'
        checkPattern=re.compile(checkString,re.S)
        checkMatch=checkPattern.findall(match[0])
        if len(checkMatch) != 0:
            print 'missed in '+checkitem+' \tin\t '+checkitemname
        else:
            return match[0].split()[-1]

def hevc_cl(logfragment, checkitem, checkitemname='hevc_cl'):
    stepList = checkitem.split('_L_')
    var = checkitem+' *\d+'
    return handle_gap(logfragment, checkitem, checkitemname, var)

def ocl(logfragment, checkitem, checkitemname='ocl'):
    stepList = checkitem.split('_L_')
    ch0 = stepList[0].strip()
    ch1 = stepList[-1].strip()
    var = ch0+'.*?'+ch1+'*\d+\.\d+'
    data = handle_gap(logfragment, checkitem, checkitemname, var)
    if data is not None:
        dataStep = data.split('is')
        data = dataStep[-1]
        return data

def handle_gap(logfragment, checkitem, casename, var):
    stepList = checkitem.split('_L_')
    pattern = re.compile(var, re.S)
    match=pattern.findall(logfragment[-1])
    logid = len(logfragment)-2
    while len(match)==0 and logid>=0:
        match = pattern.findall(logfragment[logid])
        logid -= 1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+casename
    else:
        #print checkitem+match[-1].split()[-1]
        data = match[-1].split()[-1]
        # change the data to suit the unit
        if len(stepList) == 3 and re.search('^[kmKM]$',stepList[2])!=None:
            daTmp = data.split('.')
            if re.search('^[kK]', stepList[1])== None and re.search('^[mM]$',stepList[2])!=None:
                data = daTmp[0][0:-6]+'.'+daTmp[0][-6:]+daTmp[1]
            else:
                data = daTmp[0][0:-3]+'.'+daTmp[0][-3:]+daTmp[1]
        return data
def colorseg_demo(logfragment,checkitem,casename,checkitemname='colorseg_demo'):
    stepList = checkitem.split('_L_')
    ch0=stepList[0].strip()
    ch1=stepList[1].strip()
    
    chTag='==========================='
    
    var=ch0+'.*?'+chTag+'.*?'+chTag
    pattern = re.compile(var,re.S)
    match = pattern.findall(logfragment[-1])
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
        return None
      
    var1='\r\n'+ch1+' \d+'
    pattern=re.compile(var1,re.S)
    match=pattern.findall(match[-1])
    min=100000
    for matchcase in match:
        datatemp=matchcase.split()[-1]
        if string.atof(datatemp) < min:
            min=string.atof(datatemp)
    return str(min)

def kpa(logfragment,checkitem,checkitemname='kpa'):
    pattern=re.compile(checkitem+'\s+'+':'+'\s+\d+',re.S)
    match=re.findall(pattern,logfragment[-1])
    logid=len(logfragment)-2
    while len(match)==0 and logid>=0:
        match=pattern.findall(logfragment[logid])
        logid-=1
    if len(match)==0:
        print 'missed in '+checkitem+' \tin\t '+checkitemname
        writeToCheckItemMiss(checkitemname, checkitem)
    else:
        return match[0].split()[-1]

############################################################
#   description: check if path exit                       #
#   parm: path - the log file path                         #
#   ret : no return value                                  #
############################################################
def checkpath(path):
    if not os.path.exists(path):
        print("GPUPmdata_grab.py can't grab data in the provide logfile\n")
        print("Please make sure the file path and name is OK and try again\n")
        sys.exit(1)
    print 'check path OK'

############################################################
#   description: list the log file name                    #
#                in the given path                         #
#   parm: path - the log file path                         #
#   ret : no return value                                  #
############################################################
def listfile(path):
    filelist=os.listdir(path)
    return filelist

############################################################
#   description: read the dictionary file to               #
#                get checkitem map from excel to logfile   #
#   parm: no parm                                          #
#   ret : return the map dict from excel to logfile        #
############################################################
def mapcheckitem():
    testitemdic={}
    try:
        dictionary = open('dictionary.txt','r')
    except IOError:
        print("dictionary.txt can not be opened!")
        print("Please make sure it exists.")
        sys.exit(1)
    for tmpline in dictionary:
        if tmpline.strip()=='' or re.search('^#', tmpline):
            continue
        tmpStr = tmpline.split('|')[0].upper().strip()
        testitemdic[tmpStr.replace(' ','')]=tmpline.split('|')[1].strip('\r\n')
    return testitemdic

############################################################
#   description: analysis the file name to get              #
#                boardname backend and kernelver           #
#   parm: filename - log file name                         #
#   ret : return boardname backend and kernelver           #
############################################################
def analysisfilename(filename):
    tmplist = filename.split('_L_')
    broad = tmplist[0].split('_')
    if len(broad)==3:
        if broad[1]=='EVK':
            boardname=tmplist[0]
        boardname=broad[0]+'_'+broad[2]
        print 'The broad and backend is '+boardname
    backend = broad[-1]
    kernelver = 'L' + tmplist[1].strip('(.txt|.TXT)')
    return boardname, backend, kernelver

############################################################
#   description: split the logfile into several part       #
#                by testcase                               #
#   parm: logline - the string of the whole logfile        #
#         testcaselist - testcase list get from excel      #
#   ret : return logfile fragment                          #
############################################################
def logstringsplit(logline,testcaselist):
    logfragment={}
    index=[]
    indexdic={}
    indexdicSpe=[]
    for testcase in testcaselist:
        casename=casenamemap[testcase]
        noMatch = 1
        if casename!='SPECIAL':
            # to normal one
            pattern=re.compile(casename,re.S)
            match=pattern.finditer(logline)
            for matchIt in match:
                noMatch = 0
                index.append(matchIt.start())
                indexdic[matchIt.start()] = testcase
                logfragment[testcase] = []
            if noMatch == 1:
                print 'Missed testcase in logfile: ' + testcase
        else:
            indexdicSpe.append(testcase)
    index.sort()
    if len(index)==0:
        print "Can't get data from the logfile!"
        sys.exit(1)
    for i in range(len(index)-1):
        logfragment[indexdic[index[i]]].append(logline[index[i]:index[i+1]])
    logfragment[indexdic[index[-1]]].append(logline[index[-1]:len(logline)])
    # if the keyword in excel has no contact in log, just use the whold log file
    if indexdicSpe!=[]:
        for testcaseIt in indexdicSpe:
            logfragment[testcaseIt] = [logline]
    return logfragment

############################################################
#   description: get testcase list from excel              #
#   parm: sheetfile - the sheet file in the excel          #
#   ret : return testcase list                             #
############################################################
def gettestcaselist(sheetfile):
    testcaselist=[]
    for i in range(1,sheetfile.nrows):
        casename = sheetfile.cell_value(i, 0)
        if casename!='':
            testcaselist.append(str(casename).upper().strip())
    return testcaselist

def getTestCheckItemCol(sheetfile):
    gloHead = sheetfile.row_values(0)
    if 'ITEM' in gloHead[2].upper():
        return 2
    else:
        return 1

############################################################
#   description: analysis the data to know how much        #
#                it change by percent                      #
#   parm: checkitem - checkitem name                       #
#         newdata - the data grab just now                 #
#         olddata - the data in the history                #
#   ret : no return value                                  #
############################################################
def generatereport(checkitem,newdata,olddata):
    percentage=0
    fdata=float(newdata)
    try:
        olddataEncode = olddata.encode()
    except:
        olddataEncode = ''
    if olddata!='' and not 'sec' in olddataEncode:
        folddata=float(olddata)
        if folddata!=0:
            percentage=(fdata-folddata)/folddata*100
            print "Data analysis: %-45s %.0f%%"%(checkitem,percentage)
            #percentage_intabs=abs(int(percentage))
        else:
            print "Data analysis: %-45s %s"%(checkitem,'Zero of ori data')
    else:
        print checkitem+" no data in history"
    return percentage

############################################################
#   description: get the exact col or row number of the    #
#                sheet, useful to get rid of blank cell     #
#   parm: sheetfile - the sheet file in the excel          #
#   ret : return the col or row number of the sheet        #
############################################################
def getvalidcol(sheet):
    col = sheet.ncols
    while sheet.cell_value(0, col-1) == '':
        col-=1
    return col
def getvalidrow(sheet):
    validcol = getTestCheckItemCol(sheet)
    row = sheet.nrows
    while sheet.cell_value(row-1, validcol) == '':
        row-=1
    return row

############################################################
#   description: grab performance data and write           #
#                into our excel file by checkitem          #
#   parm: logfile - logfile name                           #
#         path - logfile path                              #
#   ret : no return value                                  #
############################################################
def grabperformance(logfile, path, excelfile):
    Fail_item=[]
    Fail_case=[]
    Fail_olddata=[]
    Fail_newdata=[]
    try:
        logfilep = open(path+logfile,'r')
    except IOError:
        print "%s can not be opened!"%logfile
        print "Please make sure it exists."
        sys.exit(1)
    lines = logfilep.read()
    logfilep.close()
    print '%-45s %9s'%('Reading logfile','[OK]')

    boardname,backend,kernelver=analysisfilename(logfile)
    print '%-45s %9s'%('Analysis file name','[OK]')

    oldexcelfile = xlrd.open_workbook(excelfile, formatting_info=True)
    newexcelfile = copy(oldexcelfile)
    oldsheet = oldexcelfile.sheet_by_name(unicode( boardname ))
    sheetName = oldexcelfile.sheet_names()
    newsheet = newexcelfile.get_sheet(sheetName.index(unicode( boardname )))
    ncols = getvalidcol(oldsheet)
    nrows = getvalidrow(oldsheet)
    print '%-45s %9s'%('Openning excel','[OK]')

    # add new colour to palette and set RGB colour value
    xlwt.add_palette_colour("custom_colour", 0x21)
    newexcelfile.set_colour_RGB(0x21, 255, 153, 0)
    #add title_style data_style
    tittle_style = xlwt.easyxf('''font: height 220, name Calibri, colour_index black, bold on;
                                align: wrap on, vert centre, horiz left;
                                pattern: pattern SOLID_PATTERN, pattern_fore_colour 0x21;
                                borders: right THIN,top THIN,bottom THIN,left THIN;'''
                                )
    data_style = xlwt.easyxf('''font: height 220, name Calibri, colour_index black;
                                align: wrap on, vert centre, horiz left;
                                borders: right THIN,top THIN,bottom THIN,left THIN;'''
                                )
    row_datas=oldsheet.row_values(0)
    ncols_original=ncols
    for j in range(0,ncols):
        if row_datas[j] == kernelver:
            print '%-45s %9s'%('overwrite a title '+kernelver,'[OK]')
            ncols=j
            break
    if ncols == ncols_original:
        print '%-45s %9s'%('insert a title '+kernelver,'[OK]')
    if not silence:
        newsheet.write(0,ncols,kernelver,tittle_style)
        print 'writting the performance data to excel'
    i = 1
    missing=0
    testcaselist=gettestcaselist(oldsheet)
    logfragment=logstringsplit(lines,testcaselist)
    checkitemmap=mapcheckitem()
    checkItemCol = getTestCheckItemCol(oldsheet)
    while i!=nrows:
        casename=str(oldsheet.cell_value(i , 0)).upper().strip()
        if casename!='' and casename in testcaselist and casename in logfragment:
            fragmentline=logfragment[casename]
        else:
            i=i+1
            print 'missed one: '+casename+' in logfragment'
            missing=missing+1   # missing info has been loaded in logstringsplit()
            continue
        print '\n'
        print '================================='
        print 'Grab data of '+casename
        print '================================='
        while i!=nrows and (oldsheet.cell_value(i,0).upper().strip()==casename or oldsheet.cell_value(i,0)==''):
            checkitemname=str(oldsheet.cell_value(i , checkItemCol)).upper().strip()
            checkitemname=checkitemname.replace(' ','')
            if checkitemname == '':
                i+=1
                continue
            try:
                checkitem=checkitemmap[checkitemname]
            except:
                checkitem = None
                data = None
                print 'cannot find the item in dict:  '+checkitemname
            if checkitem!=None:
                if casenamemap[casename] !='SPECIAL':
                    data=getcheckitemdata(fragmentline,casename,checkitem) # main match func
                else:
                    data=getcheckitemdataspecial(fragmentline, checkitemname, checkitem)
            if data==None:
                missing=missing+1
                print 'Get the data of None, something missing!\n '
            elif type(data)==str:
                if not silence:
                    newsheet.write(i,ncols, string.atof(data), data_style)
                    print  ' \t[ '+str(i+1)+',  '+str(ncols+1)+' ] <<<--- data: '+data
                olddata=oldsheet.cell_value(i , ncols-1)
                try:
                    float(olddata);
                except(ValueError):
                    print 'the olddata is not an integer'
                else:
                    per_absint=generatereport(checkitemname,data,olddata)
                    if abs(int(per_absint)) >= 5:
                        Fail_item.append(checkitemname)
                        #casename=''.join(casename.split('\n'))
                        Fail_case.append(casename)
                        Fail_olddata.append(olddata)
                        Fail_newdata.append(data)
            elif type(data)==tuple and len(data)==2:
                if '[High Q]' in str(oldsheet.cell_value(i , checkItemCol )):
                    if not silence:
                        newsheet.write(i,ncols, string.atof(data[0]), data_style)
                        print  ' \t[ '+str(i+1)+',  '+str(ncols+1)+' ] <<<--- data: '+data[0]
                    olddata=oldsheet.cell_value(i , ncols-1)
                    try:
                        float(olddata);
                    except(ValueError):
                        print 'the olddata is not an integer'
                    else:
                        per_absint=generatereport(checkitemname,data[0],olddata)
                        if abs(int(per_absint)) >= 5:
                            Fail_item.append(checkitemname)
                            #casename=''.join(casename.split('\n'))
                            Fail_case.append(casename)
                            Fail_olddata.append(olddata)
                            Fail_newdata.append(data[0])
                if '[Normal Q]' in str(oldsheet.cell_value(i , checkItemCol)):
                    if not silence:
                        print  ' \t[ '+str(i+1)+',  '+str(ncols+1)+' ] <<<--- data: '+data[1]
                        newsheet.write(i,ncols, string.atof(data[1]), data_style)
                    olddata=oldsheet.cell_value(i , ncols-1)
                    try:
                        float(olddata);
                    except(ValueError):
                        print 'the olddata is not an integer'
                    else:
                        per_absint=generatereport(checkitemname,data[1],olddata)
                        if abs(int(per_absint)) >= 5:
                            Fail_item.append(checkitemname)
                            #casename=''.join(casename.split('\n'))
                            Fail_case.append(casename)
                            Fail_olddata.append(olddata)
                            Fail_newdata.append(data[1])
            else:
                missing=missing+1
                print checkitem+' miss grab error, the log file maybe wrong\n'
            i=i+1
    print '------------------GPU Performance auto grab done!--------------------\n'
    if missing!=0:
        print '\n'
        print('Totally %d case item missed listed above!'%missing)
    itemnum=1
    print('------------------list items changed over 5%-------------------------')
    FailNum=len(Fail_item)
    if FailNum != 0:
        print('%-2s %-50.50s %-60.60s %-15s %-15s'%('Number','Case_Name','Case_Item','Old_Data','New_Data'))
        print('%-2s %-50.50s %-60.60s %-15s %-15s'%('------','---------','---------','--------','--------'))
        for i in range(0,len(Fail_item)):
            Fail_case[i]=''.join(Fail_case[i].split('\n'))
            print('Num %-2d: %-50.50s %-60.60s %-15s %-15s'%(i,Fail_case[i],Fail_item[i],Fail_olddata[i],Fail_newdata[i]))
            itemnum=itemnum+1
    else:
        print('>>> No item changed over 5% by comparing with previous <<<')
    print('---------------------------------------------------------------------\n')
    newexcelfile.save(excelfile)
    return missing,FailNum

def reArrangeFile(excelfile):
    cmdstr = 'cp '+excelfile+' '+re.split('.xl',excelfile)[-2]+'_'+time.strftime("%Y-%m-%d")+'bak.xls'
    os.system(cmdstr)
    print 'backup the old excel'

def usage():
    name = sys.argv[0]
    print("\nUsage: python %s -f excelfile -l logfile\n"%name)
    print("Note: add abs path to both excelfile and logfile")
    sys.exit(1)

if __name__=='__main__':
    argc=len(sys.argv)
    inputlist=sys.argv
    it=1
    gloMissing=0
    logfile=''
    excelfile=''
    while it < argc:
        if re.search('^(--HELP|-H)$',inputlist[it].upper()):
            usage()
        elif re.search('^(-F|--FILE)$',inputlist[it].upper()):
            excelfile = inputlist[it+1]
            it+=2
        elif re.search('^(-L|--LOGFILE)$',inputlist[it].upper()):
            logfile = inputlist[it+1]
            it+=2
        elif re.search('^(-S|--SILENCE)$',inputlist[it].upper()):
            silence = 1
            it+=1
        else:
            usage()
    if logfile == '' or excelfile == '':
        print "failed to get arguments"
        usage()
    logpath=os.path.dirname(logfile)
    logname=os.path.basename(logfile)
    if logpath[-1] != '/':
        logpath=logpath+'/'
    #lock on a file so that only one process can work at a time
    try:
        locker=Lock('block.txt')
        locker.acquire()
        gloMissing,FailItemNum = grabperformance(logname, logpath, excelfile)
    finally:
        locker.release()
    print "Performance auto grab done."
