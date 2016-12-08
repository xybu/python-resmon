python-resmon
=============

# Intro

A resource monitor that records resource usage (e.g., CPU usage, RAM usage and free, disk I/O
count, NIC speed, etc.) and outputs the data in CSV format that is easy to post-process.

Compared to collecting and parsing the output of `top` and `atop`, this script incurs less overhead and the
CSV output is much easier to parse, making it handy for experiments that need resource monitoring
and processing of the generated data sets.

The script is written in Python 3 syntax and depends on [psutil](https://github.com/giampaolo/psutil).

# Installation

First make sure Python 3 interpreter and `pip` are installed.

```bash
# Install python3-dev on ubuntu because a dependency requires Python.h.
$ sudo apt install python3-dev

# Install pip.
$ wget -O- https://bootstrap.pypa.io/get-pip.py | sudo python3
```

Use `pip` to pull the repository and install:

```bash
# Install to user space. Remove "--user" to install system-wide.
$ pip install --user git+ssh://git@github.com/xybu/python-resmon.git
```

Or install from repository manually,

```bash
# Grab source code.
$ git clone git@github.com:xybu/python-resmon.git
$ cd python-resmon

# Install dependencies.
$ pip install -r requirements.txt # might need sudo

# Install python-resmon.
$ ./setup.py install --user
```

# Uninstallation

To uninstall the package,

```bash
$ pip uninstall python-resmon
```

# Usage

After installing, try with command `resmon --help` for more info:

```bash
xb@precision:[~/projects/python-resmon]: resmon --help
usage: resmon [-h] [--delay DELAY] [--flush] [--outfile [OUTFILE]]
              [--nic [NIC]] [--nic-outfile [NIC_OUTFILE]] [--enable-ps]
              [--ps-keywords [PS_KEYWORDS [PS_KEYWORDS ...]]]
              [--ps-pids [PS_PIDS [PS_PIDS ...]]] [--ps-outfile [PS_OUTFILE]]

Monitor system-wide resource availability. Optionally monitor processes that
match the specified criteria and their children.

optional arguments:
  -h, --help            show this help message and exit
  --delay DELAY, -d DELAY
                        Interval, in sec, to poll information.
  --flush, -f           If present, flush the output files after each line is
                        written.
  --outfile [OUTFILE], -o [OUTFILE]
                        Name of system monitor output file. If unset, print to
                        stdout.
  --nic [NIC], -n [NIC]
                        Specify particular NICs, separated by a comma, to
                        monitor. Default is none.
  --nic-outfile [NIC_OUTFILE]
                        Name of the NIC monitor output file. Use "{nic}" as
                        placeholder for NIC name. Default:
                        "netstat.{nic}.csv".
  --enable-ps, -p       Enable process-keyword monitor.
  --ps-keywords [PS_KEYWORDS [PS_KEYWORDS ...]]
                        Include processes whose name contains the keyword and
                        their children.
  --ps-pids [PS_PIDS [PS_PIDS ...]]
                        Include the specified PIDs and their children.
  --ps-outfile [PS_OUTFILE]
                        Name of the process monitor output file. Default:
                        "psstat.csv".
```

To terminate the monitor, send `SIGINT` or `SIGTERM` signal to the process.

# Example

Sample output of resource monitor (note that the operation of obtaining statistics is not atomic -- there is slight
time difference between obtaining sets of metrics; therefore a sum value (e.g., `%CPU` below) may not equal the sum
of individual values (e.g., `%CPUx`)):

```
Timestamp,  Uptime, NCPU, %CPU, %CPU0, %CPU1, %CPU2, %CPU3, %MEM, mem.total.KB, mem.used.KB, mem.avail.KB, mem.free.KB, %SWAP, swap.total.KB, swap.used.KB, swap.free.KB, io.read, io.write, io.read.KB, io.write.KB, io.read.ms, io.write.ms
1475022339, 0, 4, 400.0, 100.0, 0.0, 100.0, 0.0, 15.3, 4103824, 995080, 3475692, 3108744, 0.0, 4183036, 0, 4183036, 0, 0, 0, 0, 0, 0
1475022341, 2, 4, 158.0, 61.7, 41.2, 26.5, 28.2, 15.7, 4103824, 1019080, 3459788, 3084744, 0.0, 4183036, 0, 4183036, 532, 2, 8264, 12, 3432, 28
1475022343, 4, 4, 185.2, 36.3, 49.3, 29.9, 65.3, 17.1, 4103824, 1085820, 3402592, 3018004, 0.0, 4183036, 0, 4183036, 152, 31, 9492, 256, 816, 1376
1475022345, 6, 4, 222.8, 49.6, 36.3, 74.4, 58.2, 17.8, 4103824, 1120424, 3371292, 2983400, 0.0, 4183036, 0, 4183036, 46, 2, 3168, 24, 92, 24
1475022347, 8, 4, 226.4, 30.0, 35.3, 94.6, 36.6, 19.1, 4103824, 1174332, 3319400, 2929492, 0.0, 4183036, 0, 4183036, 30, 2, 1916, 12, 128, 24
1475022349, 10, 4, 173.6, 35.5, 27.5, 73.8, 22.9, 21.9, 4103824, 1287532, 3206692, 2816292, 0.0, 4183036, 0, 4183036, 4, 30, 304, 244, 12, 220
1475022351, 12, 4, 163.6, 36.0, 47.4, 41.2, 38.3, 21.9, 4103824, 1287932, 3206372, 2815892, 0.0, 4183036, 0, 4183036, 0, 3, 0, 16, 0, 52
1475022353, 14, 4, 218.8, 60.5, 55.2, 57.6, 45.1, 21.9, 4103824, 1290036, 3204276, 2813788, 0.0, 4183036, 0, 4183036, 0, 17, 0, 136, 0, 88
1475022355, 16, 4, 196.0, 55.2, 44.9, 43.5, 52.0, 21.9, 4103824, 1290416, 3203964, 2813408, 0.0, 4183036, 0, 4183036, 0, 1, 0, 4, 0, 0
...
```

Sample output of NIC monitor (the example was pasted from an output that monitored a NIC named `enp34s0`):

```
Timestamp,  Uptime, NIC, sent.B, recv.B, sent.pkts, recv.pkts, err.in, err.out, drop.in, drop.out
1475022339, 0, enp34s0, 0, 0, 0, 0, 0, 0, 0, 0
1475022341, 2, enp34s0, 0, 4272386, 0, 13394, 0, 0, 0, 0
1475022343, 4, enp34s0, 0, 7097273, 0, 20839, 0, 0, 0, 0
1475022345, 6, enp34s0, 0, 8107324, 0, 21161, 0, 0, 0, 0
1475022347, 8, enp34s0, 0, 12865759, 0, 24632, 0, 0, 0, 0
1475022349, 10, enp34s0, 0, 3188676, 0, 13986, 0, 0, 0, 0
1475022351, 12, enp34s0, 0, 3315832, 0, 14091, 0, 0, 0, 0
1475022353, 14, enp34s0, 0, 12910705, 0, 24074, 0, 0, 0, 0
1475022355, 16, enp34s0, 0, 6147833, 0, 17204, 0, 0, 0, 0
1475022357, 18, enp34s0, 0, 14606762, 0, 28263, 0, 0, 0, 0
1475022359, 20, enp34s0, 0, 5930482, 0, 19017, 0, 0, 0, 0
...
```

Sample output of process keyword-based monitor (in the example run, the keyword is set to `qemu`, meaning that the
resource usage printed is the sum of resource used by all processes containing keyword `qemu` and all their (direct
and indirect) child processes):

```
Timestamp, Uptime, %CPU, %MEM, io.read, io.read.KB, io.write, io.write.KB, mem.rss.KB, nctxsw, nthreads
1475022339, 0, 0.0, 11.789, 19269, 168236, 11619, 592, 483808, 11414, 23
1475022341, 2, 61.9, 11.789, 19326, 168960, 11638, 592, 483808, 11452, 23
1475022343, 4, 118.0, 13.139, 19821, 178452, 11846, 868, 539184, 11778, 23
1475022345, 6, 169.6, 13.937, 19998, 181620, 11905, 868, 571952, 11896, 23
1475022347, 8, 174.0, 15.185, 20090, 183536, 11942, 912, 623152, 11957, 23
1475022349, 10, 131.4, 17.934, 20119, 183840, 11958, 1000, 735992, 11982, 23
1475022351, 12, 130.0, 17.934, 20119, 183840, 11958, 1000, 735992, 11985, 23
1475022353, 14, 168.5, 17.984, 20124, 183840, 11975, 1124, 738040, 11992, 23
1475022355, 16, 153.9, 17.984, 20134, 183840, 11984, 1128, 738040, 12004, 23
1475022357, 18, 191.5, 17.94, 20134, 183840, 11984, 1128, 736232, 12007, 21
1475022359, 20, 172.6, 17.943, 20149, 183840, 12005, 1300, 736356, 12022, 16
...
```

# Support

Contribute to the code base or report bugs by committing to the repository (https://github.com/xybu/python-resmon) or creating issues.
