#---------------------------------------------------------------------------------------------------
# Python Module File to describe processing request
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import os
from scheduler import Scheduler
from sample import Sample

DEBUG = 0

#---------------------------------------------------------------------------------------------------
"""
Class:  Request(scheduler=None,sample=None,config='filefi',version='046',py='data')
A request will have to specify the configuration, version and python configuration file to be
applied to the also given a scheduler and a sample.
"""
#---------------------------------------------------------------------------------------------------
class Request:
    "Description of a request for a specific sample processing."

    #-----------------------------------------------------------------------------------------------
    # constructor
    #-----------------------------------------------------------------------------------------------
    def __init__(self,scheduler=None,sample=None,config='filefi',version='046',py='data'):
        
        self.base = os.getenv('KRAKEN_SE_BASE')

        self.scheduler = scheduler
        self.sample = sample
        self.config = config
        self.version = version
        self.py = py

        self.loadQueuedJobs()
        self.loadHeldJobs()
        self.loadCompletedJobs()
        self.sample.createMissingJobs()

    #-----------------------------------------------------------------------------------------------
    # load all jobs so far completed relevant to this task
    #-----------------------------------------------------------------------------------------------
    def loadCompletedJobs(self):

        # initialize from scratch
        path = self.base + '/' + self.config + '/' + self.version + '/' \
            + self.sample.dataset
        # first fully checked files
        cmd = 'list ' + path + '  2> /dev/null | grep root'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split()
            file = (f[1].split("/")).pop()
            self.sample.addCompletedJob(file)
        # now also look at the temporary files (not yet cataloged)
        cmd = 'list ' + path + '/' + os.getenv('KRAKEN_TMP_PREFIX') \
            + '*/  2> /dev/null | grep _tmp.root'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split()
            file = (f[1].split("/")).pop()
            file = file.replace('_tmp','')
            self.sample.addNoCatalogJob(file)
        if DEBUG > 0:
            print ' NOCATAL - Jobs: %6d'%(len(self.sample.noCatalogJobs))
            print ' DONE    - Jobs: %6d'%(len(self.sample.completedJobs))

    #-----------------------------------------------------------------------------------------------
    # load all jobs that are presently queued
    #-----------------------------------------------------------------------------------------------
    def loadQueuedJobs(self):

        # initialize from scratch
        self.sample.resetQueuedJobs()

        path = self.base + '/' + self.config + '/' + self.version + '/' + self.sample.dataset
        pattern = "%s %s %s %s"%(self.config,self.version,self.py,self.sample.dataset)
        cmd = 'condor_q ' + self.scheduler.user \
            + ' -constraint JobStatus!=5 -format \'%s\n\' Args 2> /dev/null|grep \'' + pattern + '\''

        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
                + ' \"' + cmd + '\"'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split(' ')
            file = f[5] + '.root'
            self.sample.addQueuedJob(file)
        if DEBUG > 0:
            print ' QUEUED  - Jobs: %6d'%(len(self.sample.queuedJobs))

    #-----------------------------------------------------------------------------------------------
    # load all jobs that are presently queued but in held state
    #-----------------------------------------------------------------------------------------------
    def loadHeldJobs(self):

        # initialize from scratch
        self.sample.resetHeldJobs()

        path = self.base + '/' + self.config + '/' + self.version + '/' \
            + self.sample.dataset
        pattern = "%s %s %s %s"%(self.config,self.version,self.py,self.sample.dataset)
        cmd = 'condor_q ' + self.scheduler.user \
            + ' -constraint JobStatus==5 -format \'%s\n\' Args 2> /dev/null|grep \'' + pattern + '\''

        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
                + ' \"' + cmd + '\"'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split(' ')
            file = f[5] + '.root'
            self.sample.addHeldJob(file)

        if DEBUG > 0:
            print ' HELD    - Jobs: %6d'%(len(self.sample.heldJobs))
