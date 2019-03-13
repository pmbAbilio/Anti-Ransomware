import psutil
processes = []
history = {}
temp = {}
import time
import Finder
import os
import signal
N = 25
M = 15
W = 3
Y = N+M*2+W*3
class Process:
    def __init__(self, proc):
        self.id = proc.pid
        self.name = proc.name()
        self.childs = []
        self.dirs = []
        for p in proc.open_files():
            if p.path not in self.dirs: self.dirs.append(p.path)
        self.total_write = proc.io_counters()[3]
        self.total_read = proc.io_counters()[2]

    def getAllDirs(self):
        dirs = []
        for d in self.dirs: dirs.append(d)
        return dirs

    

    def getTotalRead(self):
        total = self.total_read
        for child in self.childs:
            total = total + child.getTotalRead()
        return total
    
    def getTotalWrite(self):
        total = self.total_write
        for child in self.childs:
            total = total + child.getTotalWrite()
        return total

    def findProcess(self, id):
        if self.id == id: return self
        for child in self.childs:
            if child.findProcess(id): return child
        return False
    

print "{} pids".format(len(psutil.pids()))
print "start collecting processes"
iteration = 0
x = 0
def suspendProcess(process):
    for p in psutil.process_iter():
        if p.name() == process.name():
            p.suspend()
def resumeProcess(process):
    print "Resuming"
    for p in psutil.process_iter():
        if p.name() == process.name():
            p.resume()
    
def kill_proc_tree(pid, sig, include_parent=True,
                   timeout=None, on_terminate=None):
    
    """Kill a process tree (including grandchildren) with signal
    "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callabck function which is
    called as soon as a child terminates.
    """
    if pid == os.getpid():
        raise RuntimeError("I refuse to kill myself")
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        p.send_signal(sig)
    gone, alive = psutil.wait_procs(children, timeout=timeout,
                                    callback=on_terminate)
    return (gone, alive)

while True:
    iteration = iteration + 1 
    for process in psutil.process_iter():
        #process = psutil.Process(process)
        x = x + 1
        #print "collecting process ", x, process.pid, len(processes)
        try:
            if len(processes) == 0:
                if process.ppid():
                    #print "first with parent"
                    parent = psutil.Process(process.ppid())
                    p = Process(parent)
                    p.childs.append(Process(process))
                    processes.append(p)
                    #processes[p.id] = p
                else:
                    #print "first without parent"
                    processes.append(Process(process))
            else:
                if process.ppid():#Se o processo tiver parent
                    inserted = False
                    for p in processes: #para cada processo no array processes
                        #print "Process with parent"
                        found = p.findProcess(process.ppid())
                        
                        if found:
                            #print "found", process.ppid(), process.pid
                            files = process.open_files()
                            for f in files:
                                if f.path not in found.dirs: found.dirs.append(f.path)
                            found.total_write = process.io_counters()[3]
                            found.total_read = process.io_counters()[2]
                            f = 1
                            inserted = True
                            break

                     
                    if not inserted:
                        parent = psutil.Process(process.ppid())
                        p = Process(parent)
                        p.childs.append(Process(process))
                        processes.append(p)
                        #print "processid {} has {} children".format(p.id, len(p.childs))
                            
                #print "not first", len(processes)
                f = 0
                for p in processes:
                    found = p.findProcess(process.pid)
                    if found:
                        files = process.open_files()
                        for f in files:
                            if f.path not in found.dirs: found.dirs.append(f.path)
                        found.total_write = process.io_counters()[3]
                        found.total_read = process.io_counters()[2]
                        f = 1
                        
                if f == 0: processes.append(Process(process))
                
        except Exception as e:
            pass #print e
        
    #print "{} processes collected".format(len(processes))
    x = 0
    for p in processes:
        x = x + 1
        total = p.getTotalWrite()
        if total > 100000:
            if p not in history: history[p] = [p.name, total, 0, 0, 0, 0, 1]
            else: history[p] = [p.name, total, history[p][1], history[p][2], history[p][3], history[p][4], 1]
            
    for h in history:
        
        if history[h][6] == 1:
            
            a = history[h]
            if iteration == 5 and a[1]-a[5] > 10000 and h.getAllDirs() > 10:
                length = len(h.getAllDirs())
                print h.name.ljust(N), "{}".format(a[1]-a[5]).ljust(M), "{}".format(a[1]).ljust(M), "{}".format(len(h.childs)).ljust(W), "{}".format(length).ljust(W), a[6]
                print length
                possible_warning = 0
                for f in h.getAllDirs():
                    possible_warning += Finder.start(f)
                if possible_warning > 0:
                    p = psutil.Process(h.id)
                    suspendProcess(p)
                    #p.suspend()
                    try:
                        print "We have notice {} odd files attached to a process named {}, Do you Trust it ?(S/N)\n".format(possible_warning, h.name)
                        response = raw_input()
                        print "Received ",response
                        if response == "N":
                            kill_proc_tree(h.id, signal.SIGTERM)
                        else:
                           resumeProcess(p) 
                    except:print("We could not stop process {} with the pid: {} please be carefull".format(h.name,h.id))
                      
            history[h][6] = 0
        else:
            history[h][1] = 0
            history[h][2] = history[h][1]
            history[h][3] = history[h][2]
            history[h][4] = history[h][3]
            history[h][5] = history[h][4]
            history[h][6] = 0
            
    if iteration == 5:
        print "#" * Y
        iteration = 0
    time.sleep(1)
                                               
        
