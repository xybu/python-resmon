#!/usr/bin/python3

"""
resmon.py

Resource monitor monitors system wide resource usage and availability. This script assumes that the number
of CPU cores does not change throughout the course.

NIC monitor component monitors the speed, in terms of Bps and Pkts/sec, and error and drop counts, of the specified NICs.

Process monitor component monitors resource usage of of a subset of living processes.
For example, if keyword "docker" is given, then it reports, every T seconds, the sum of resource
(CPU, RSS, IO, CtxSw, NThreads) usage of all processes whose name contains "docker" and their child processes.

@author	Xiangyu Bu <bu1@purdue.edu>
"""

import argparse
import os
import sched
import sys
import threading
import time
import psutil


class SystemMonitor:

    def __init__(self, outfile_name=None, flush=False):
        print('System monitor started.', file=sys.stderr)
        ncores = self.ncores = psutil.cpu_count()
        if outfile_name is None:
            self.outfile = sys.stdout
        else:
            self.outfile = open(outfile_name, 'w')
        self.flush = flush
        self.outfile.write(
            'Timestamp,  Uptime, NCPU, %CPU, ' + ', '.join(['%CPU' + str(i) for i in range(ncores)]) +
            ', %MEM, mem.total.KB, mem.used.KB, mem.avail.KB, mem.free.KB' +
            ', %SWAP, swap.total.KB, swap.used.KB, swap.free.KB' +
            ', io.read, io.write, io.read.KB, io.write.KB, io.read.ms, io.write.ms\n')
        self.prev_disk_stat = psutil.disk_io_counters()
        self.starttime = int(time.time())
        self.poll_stat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self, 'closed'):
            self.close()

    def close(self):
        if self.outfile is not sys.stdout:
            self.outfile.close()
        self.closed = True
        print('System monitor closed.', file=sys.stderr)

    def poll_stat(self):
        timestamp = int(time.time())
        uptime = timestamp - self.starttime
        total_cpu_percent = psutil.cpu_percent(percpu=False)
        percpu_percent = psutil.cpu_percent(percpu=True)
        mem_stat = psutil.virtual_memory()
        swap_stat = psutil.swap_memory()
        disk_stat = psutil.disk_io_counters()

        line = str(timestamp) + ', ' + str(uptime) + ', ' + \
            str(self.ncores) + ', ' + str(total_cpu_percent*self.ncores) + ', '
        line += ', '.join([str(i) for i in percpu_percent])
        line += ', ' + str(mem_stat.percent) + ', ' + str(mem_stat.total >> 10) + ', ' + str(
            mem_stat.used >> 10) + ', ' + str(mem_stat.available >> 10) + ', ' + str(mem_stat.free >> 10)
        line += ', ' + str(swap_stat.percent) + ', ' + str(swap_stat.total >> 10) + \
            ', ' + str(swap_stat.used >> 10) + ', ' + str(swap_stat.free >> 10)
        line += ', ' + str(disk_stat.read_count - self.prev_disk_stat.read_count) + ', ' + str(disk_stat.write_count - self.prev_disk_stat.write_count) + \
                ', ' + str((disk_stat.read_bytes - self.prev_disk_stat.read_bytes) >> 10) + ', ' + str((disk_stat.write_bytes - self.prev_disk_stat.write_bytes) >> 10) + \
                ', ' + str(disk_stat.read_time - self.prev_disk_stat.read_time) + \
            ', ' + str(disk_stat.write_time - self.prev_disk_stat.write_time)

        self.outfile.write(line + '\n')
        if self.flush:
            self.outfile.flush()
        self.prev_disk_stat = disk_stat


class NetworkInterfaceMonitor:

    def __init__(self, outfile_pattern='netstat.{nic}.csv', nics=[], flush=False):
        print('NIC monitor started.', file=sys.stderr)
        all_nics = psutil.net_if_stats()
        self.nic_files = dict()
        self.flush = flush
        for nic_name in nics:
            nic_name = nic_name.strip()
            if nic_name not in all_nics:
                print('Error: NIC "%s" does not exist. Skip.' %
                      nic_name, file=sys.stderr)
            else:
                self.nic_files[nic_name] = self.create_new_logfile(
                    outfile_pattern, nic_name)
        if len(self.nic_files) == 0:
            raise ValueError('No NIC to monitor.')
        self.prev_stat = dict()
        for nic, stat in psutil.net_io_counters(pernic=True).items():
            if nic in self.nic_files:
                self.prev_stat[nic] = stat
        self.starttime = int(time.time())
        self.poll_stat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self, 'closed'):
            self.close()

    def close(self):
        for f in self.nic_files.values():
            f.close()
        self.closed = True
        print('NIC monitor closed.', file=sys.stderr)

    def create_new_logfile(self, pattern, nic_name):
        f = open(pattern.format(nic=nic_name), 'w')
        f.write(
            'Timestamp,  Uptime, NIC, sent.B, recv.B, sent.pkts, recv.pkts, err.in, err.out, drop.in, drop.out\n')
        return f

    def poll_stat(self):
        timestamp = int(time.time())
        uptime = timestamp - self.starttime
        net_stat = psutil.net_io_counters(pernic=True)
        for nic, f in self.nic_files.items():
            stat = net_stat[nic]
            prevstat = self.prev_stat[nic]
            f.write(str(timestamp) + ', ' + str(uptime) + ', ' + nic + ', ' +
                    str(stat.bytes_sent-prevstat.bytes_sent) + ', ' + str(stat.bytes_recv-prevstat.bytes_recv) + ', ' +
                    str(stat.packets_sent-prevstat.packets_sent) + ', ' + str(stat.packets_recv-prevstat.packets_recv) + ', ' +
                    str(stat.errin-prevstat.errin) + ', ' + str(stat.errout-prevstat.errout) + ', ' + str(stat.dropin-prevstat.dropin) + ', ' + str(stat.dropout-prevstat.dropout) + '\n')
            if self.flush:
                f.flush()
        self.prev_stat = net_stat


class ProcessSetMonitor:

    BASE_STAT = {
        'io.read': 0,
        'io.write': 0,
        'io.read.KB': 0,
        'io.write.KB': 0,
        'mem.rss.KB': 0,
        '%MEM': 0,
        '%CPU': 0,
        'nctxsw': 0,
        'nthreads': 0
    }

    KEYS = sorted(BASE_STAT.keys())

    def __init__(self, keywords, pids, outfile_name, flush=False):
        print('ProcessSet monitor started.', file=sys.stderr)
        if outfile_name is None:
            self.outfile = sys.stdout
        else:
            self.outfile = open(outfile_name, 'w')
        self.pids = pids
        self.keywords = keywords
        self.flush = flush
        self.outfile.write('Timestamp, Uptime, ' + ', '.join(self.KEYS) + '\n')
        self.starttime = int(time.time())
        self.poll_stat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self, 'closed'):
            self.close()

    def close(self):
        if self.outfile is not sys.stdout:
            self.outfile.close()
        self.closed = True
        print('ProcessSet monitor closed.', file=sys.stderr)

    def _stat_proc(self, proc, stat, visited):
        """ Recursively stat a process and its child processes. """
        if proc.pid in visited:
            return
        visited.add(proc.pid)
        io = proc.io_counters()
        mem_rss = proc.memory_info().rss
        mem_percent = proc.memory_percent('rss')
        nctxsw = proc.num_ctx_switches()
        nctxsw = nctxsw.voluntary + nctxsw.involuntary
        nthreads = proc.num_threads()
        cpu_percent = proc.cpu_percent()
        stat['io.read'] += io.read_count
        stat['io.write'] += io.write_count
        stat['io.read.KB'] += io.read_bytes
        stat['io.write.KB'] += io.write_bytes
        stat['mem.rss.KB'] += mem_rss
        stat['%MEM'] += mem_percent
        stat['nctxsw'] += nctxsw
        stat['nthreads'] += nthreads
        stat['%CPU'] += cpu_percent
        for c in proc.children():
            self._stat_proc(c, stat, visited)

    def poll_stat(self):
        visited = set()
        curr_stat = dict(self.BASE_STAT)
        timestamp = int(time.time())
        uptime = timestamp - self.starttime
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'name'])
            except psutil.NoSuchProcess:
                pass
            else:
                if pinfo['pid'] not in visited:
                    if pinfo['pid'] in self.pids:
                        self._stat_proc(proc, curr_stat, visited)
                    else:
                        for k in self.keywords:
                            if k in pinfo['name'].lower():
                                self._stat_proc(proc, curr_stat, visited)
                                break  # for keyword
        curr_stat['%CPU'] = round(curr_stat['%CPU'], 3)
        curr_stat['%MEM'] = round(curr_stat['%MEM'], 3)
        curr_stat['io.read.KB'] >>= 10
        curr_stat['io.write.KB'] >>= 10
        curr_stat['mem.rss.KB'] >>= 10
        line = str(timestamp) + ', ' + str(uptime) + ', ' + \
            ', '.join([str(curr_stat[k]) for k in self.KEYS]) + '\n'
        self.outfile.write(line)
        if self.flush:
            self.outfile.flush()


def chprio(prio):
    try:
        psutil.Process(os.getpid()).nice(prio)
    except:
        print('Warning: failed to elevate priority!', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Monitor system-wide resource availability. Optionally monitor processes that match the specified criteria and their children.')
    parser.add_argument('--delay', '-d', type=int, default=1, help='Interval, in sec, to poll information.')
    parser.add_argument('--flush', '-f', default=False, action='store_true',
                        help='If present, flush the output files after each line is written.')
    parser.add_argument('--outfile', '-o', type=str, nargs='?', default=None,
                        required=False, help='Name of system monitor output file. If unset, print to stdout.')
    parser.add_argument('--nic', '-n', type=str, nargs='?', default=None, required=False,
                        help='Specify particular NICs, separated by a comma, to monitor. Default is none.')
    parser.add_argument('--nic-outfile', type=str, nargs='?',
                        default='netstat.{nic}.csv', help='Name of the NIC monitor output file. Use "{nic}" as placeholder for NIC name. Default: "netstat.{nic}.csv".')
    parser.add_argument('--enable-ps', '-p', default=False,
                        action='store_true', help='Enable process-keyword monitor.')
    parser.add_argument('--ps-keywords', type=str, nargs='*',
                        help='Include processes whose name contains the keyword and their children.')
    parser.add_argument('--ps-pids', type=int, nargs='*',
                        help='Include the specified PIDs and their children.')
    parser.add_argument('--ps-outfile', type=str, nargs='?', default='psstat.csv',
                        help='Name of the process monitor output file. Default: "psstat.csv".')
    args = parser.parse_args()
    if args.enable_ps and ((not args.ps_keywords or len(args.ps_keywords) == 0) and (not args.ps_pids or len(args.ps_pids) == 0)):
        parser.error('--enable-ps requires --ps-keywords or --ps-pids.')

    if args.ps_pids is None:
        args.ps_pids = set()
    else:
        args.ps_pids = set(args.ps_pids)

    if args.ps_keywords is None:
        args.ps_keywords = []
    else:
        # Convert to lowercase to achieve case IN-sensitiveness.
        args.ps_keywords = [k.lower() for k in args.ps_keywords]

    try:
        chprio(-20)
        scheduler = sched.scheduler(time.time, time.sleep)
        sm = SystemMonitor(args.outfile, args.flush)

        enable_nic_mon = args.nic is not None
        if enable_nic_mon:
            try:
                nm = NetworkInterfaceMonitor(
                    args.nic_outfile, args.nic.split(','), args.flush)
            except ValueError as e:
                print('Error: ' + str(e), file=sys.stderr)
                enable_nic_mon = False

        if args.enable_ps:
            pm = ProcessSetMonitor(
                args.ps_keywords, args.ps_pids, args.ps_outfile, args.flush)

        i = 1
        starttime = time.time()
        while True:
            scheduler.enterabs(
                time=starttime + i*args.delay, priority=2, action=SystemMonitor.poll_stat, argument=(sm, ))
            if enable_nic_mon:
                scheduler.enterabs(time=starttime + i*args.delay, priority=1,
                                   action=NetworkInterfaceMonitor.poll_stat, argument=(nm, ))
            if args.enable_ps:
                scheduler.enterabs(
                    time=starttime + i*args.delay, priority=0, action=ProcessSetMonitor.poll_stat, argument=(pm, ))
            scheduler.run()
            i += 1

    except KeyboardInterrupt:
        sm.close()
        if enable_nic_mon:
            nm.close()
        if args.enable_ps:
            pm.close()
        sys.exit(0)


if __name__ == '__main__':
    main()
