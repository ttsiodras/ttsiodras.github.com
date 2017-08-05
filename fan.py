#!/usr/bin/env python2
from __future__ import print_function
import os, sys, time

def printAndFlush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

#####################
# Parse configuration

CONFIG_FILE = "/etc/fan.conf"
DESIRED = 60
VERBOSE = "-v" in sys.argv

if os.path.exists(CONFIG_FILE):
    for line in open(CONFIG_FILE):
        if line.startswith('#'):
            continue
        try:
            data = line.split("=")
            varname = data[0].strip().lower()
            if varname == "temperature":
                DESIRED = int(data[1].strip())
            elif varname == "verbose":
                VERBOSE = bool(eval(data[1].strip()))
        except:
            pass

def info(*args, **kwargs):
    if VERBOSE:
        printAndFlush(*args, **kwargs)

if os.getenv("TZ") is None:
    os.putenv("TZ", open("/etc/timezone").read().strip())
printAndFlush("[-] Fan daemon started at", time.ctime())
printAndFlush("[-] Target temperature set at", str(DESIRED)+"C.")
printAndFlush("[-] Verbose logging: ", "enabled" if VERBOSE else "disabled")

###########
# Setup PWM

setup_is_needed = False
moduleLines = os.popen("/sbin/lsmod | grep 'p[w]m'").readlines()
if not moduleLines or not moduleLines[0].startswith('pwm_sunxi_opi0'):
    folder = os.path.dirname(os.path.realpath(__file__))
    try:
        os.chdir(folder)
    except OSError:
        printAndFlush("[x] Failed to chdir to folder with PWM module...")
        sys.exit(1)
    info("[-] Loading PWM module... (pwm-sunxi-opi0.ko)")
    if 0 != os.system("/sbin/insmod ./pwm-sunxi-opi0.ko"):
        printAndFlush("[x] Failed to load PWM module... Aborting.")
        sys.exit(1)
    setup_is_needed = True

try:
    PWM = "/sys/class/pwm-sunxi-opi0/pwm0"
    os.chdir(PWM)
except OSError:
    printAndFlush("[x] Failed to chdir to", PWM)
    sys.exit(1)

if setup_is_needed:
    info("[-] Setting up PWM scale from 0 to 100")
    open("run" , "w").write("1")
    open("polarity", "w").write("1")
    open("prescale", "w").write("2")
    open("entirecycles", "w").write("100")

###############
# PI controller

I = 0
while True:
    temp = int(open("/sys/class/thermal/thermal_zone0/temp").read())

    error = temp - DESIRED
    I = I + error
    I = min(I, 100)
    I = max(I, -100)
    PID_target = int(error * 4.0 + I * 0.4)

    if PID_target < 0:
        target = 0
    else:
        target = min(50+PID_target, 100)
    info("[-] Temp is %dC, setting fan at %d%% (I=%s)" % (
        temp, target, str(I)))
    open("activecycles", "w").write(str(target))
    time.sleep(4)
