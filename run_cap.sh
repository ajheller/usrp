#! /bin/bash
#
# Typical invocation:
#   sudo ./run_cap.sh --rx_sample_rate 56e6 -d 300 -o p 
#
# set CPUs for performance
#  https://kb.ettus.com/USRP_Host_Performance_Tuning_Tips_and_Tricks
#  https://www.cyberciti.biz/faq/howto-set-real-time-scheduling-priority-process/
#  sudo cpufreq-info -g # shows possible governors  -l shows min and max frequency 

# set all processors for performance
for ((i=0;i<$(nproc --all);i++)); do sudo cpufreq-set -c $i -r -g performance; done

export PYTHONPATH=/usr/local/lib/python3.8/site-packages/:$PYTHONPATH
echo $PYTHONPATH

export TARGET=./usrp_rx_to_file_thread.py
echo compiling ...
/usr/bin/python3 -m py_compile $TARGET

# https://stackoverflow.com/questions/8887531/which-real-time-priority-is-the-highest-priority-in-linux
# run with rt scheduler and high priority
# chrt --rr 20 /usr/bin/python3 $TARGET "$@"
# chrt --fifo 20 /usr/bin/python3 $TARGET "$@"
# chrt  20 /usr/bin/python3 $TARGET "$@"
/usr/bin/python3 $TARGET "$@"