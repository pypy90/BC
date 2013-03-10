#!/usr/bin/python

import datetime,time
import os,sys
import subprocess
import ConfigParser
import re
from multiprocessing import Process
import Queue

JOINQ = Queue.Queue()

def logger(comment):
        try:
                lh = open("/tmp/mybc/bc.log","a")
        except:
                print('Log open failed!')
                sys.exit(-1)
        lh.write(comment)
        lh.close()

class BcMon(object):
        def __init__(self,sec):
                self.__hour = None
                self.__stat = InitStat()
                self.grp    = cf.get(sec,'class')
                self.node1  = cf.get(sec,'node1')
                self.node2  = cf.get(sec,'node2')
                self.proc   = cf.get(sec,'proc')
                self.script = cf.get(sec,'script')
                self.group  = cf.get(sec,'class')
                self.alert  = cf.get(sec,'alarm')
                self.sec    = sec

        def setHour(self,h):
                self.__hour = h
        def setStat(self,s):
                self.__stat = s
        def getHour(self):
                return self.__hour
        def run(self):
                self.__stat.StartMon(self)
                mypid = os.getpid()
                JOINQ.put(mypid)
        def getResult(self):
                state = [[0,0],[0,1]]
                code1 = self.getDBstat(self.node2,self.proc)
                code2 = self.getTabletime(self.script)
                for k,v in enumerate(state):
                        if [code1,code2] == v:
                                return k
                        else:
                                pass
        def getDBstat(self,host,proc):
                cmd = 'ssh -o ConnectTimeout=5 %s ps -ef | grep %s | grep -v grep | wc -l' % (host,proc)
                output = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
                res = output.stdout.read()
                if int(res) == 1:
                        return 0
                else:
                        return 1

        def getTabletime(self,script):
                cmd = "sh /app/pypy/BcMon/sbin/%s | grep -v '^$' | awk '{print $1}'" % script
                oo = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
                tt = subprocess.Popen('date +%Y-%m-%d',stdout=subprocess.PIPE,shell=True)
                t1 = oo.stdout.read()
                t2 = tt.stdout.read()
                if t1 == t2:
                        return 0
                else:
                        return 1

        def getLogcom(self):
                pass
        
        def voiceAlarm(self):
                cmd = "sh /app/pypy/BcMon/sbin/%s" % self.alert
                ww = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)

class State(object):
        def __init__(self):
                pass
        def StartMon(self,inst):
                pass

class InitStat(State,BcMon):
        def StartMon(self,inst):
                current = datetime.datetime.now()
                if inst.getHour() < 12 and inst.getHour() > 2:
                        if inst.getResult() == 0:
                                cont = '[%s] %s %s COPY OK!\n' % (current,inst.sec,inst.group)
                                logger(cont)
                        elif inst.getResult() == 1:     
                                '''daemon'''
                                return
                        else:
                                cont = '[%s] %s %s COPY ERROR!\n' % (current,inst.sec,inst.group)
                                logger(cont)
                                inst.voiceAlarm()
                else:
                        inst.setStat(PmStat())
                        inst.run()
        
class PmStat(State,BcMon):
        def StartMon(self,inst):
                current = datetime.datetime.now()
                if inst.getHour() < 18 and inst.getHour() >= 12:
                        if inst.getResult() == 0:
                                cont = '[%s] %s %s COPY OK!\n' % (current,inst.sec,inst.group)
                                logger(cont)
                        elif inst.getResult() == 1:
                                '''daemon'''
                                return
                        else:
                                cont = '[%s] %s %s COPY ERROR!\n' % (current,inst.sec,inst.group)
                                logger(cont)
                                inst.voiceAlarm()
                else:
                        inst.setStat(EveStat())
                        inst.run()

class EveStat(State,BcMon):
        def StartMon(self,inst):
                current = datetime.datetime.now()
                if inst.getHour() < 24 and inst.getHour() >= 18:
                        if inst.getResult() == 0:
                                cont = '[%s] %s %s COPY OK!\n' % (current,inst.sec,inst.group)
                                logger(cont)
                        elif inst.getResult() == 1:
                                '''daemon'''
                                return
                        else:
                                cont = '[%s] %s %s COPY ERROR!\n' % (current,inst.sec,inst.group)
                                logger(cont)
                                inst.voiceAlarm()
                else:
                        cont = '[%s] %s %s Sync Now!\n' % (current,inst.sec,inst.group)
                        logger(cont)
                        return

if __name__ == '__main__':
        os.chdir('/app/pypy/BcMon/bin')
        RUNQ = []
        cf = ConfigParser.ConfigParser()
        cfg_file = "/etc/mybc.conf"
        cf.read(cfg_file)
        sections = cf.sections()
        Hour = time.strftime("%H",time.localtime(time.time()))
        for sec in sections:
                enable = cf.get(sec,'enable')
                if enable == 'no': continue
                ob = BcMon(sec)
                ob.setHour(int(Hour))
                p = Process(target=ob.run,args=())
                RUNQ.append(p)
        
        for i in range(len(RUNQ)):
                RUNQ[i].start()
                
        JOINQ.put(-1)
        while True:
                joinpid = JOINQ.get()
                if joinpid == -1:
                        break
                else:
                        joinpid.join()
                        sys.exit(0)        
