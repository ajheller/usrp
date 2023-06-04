import os
import time

if True:
    print(f"{os.sched_getscheduler(0)}, {os.getpriority(os.PRIO_PROCESS, 0)}")
    time.sleep(4)

    os.setpriority(os.PRIO_PROCESS, 0, -20)
    print(f"{os.sched_getscheduler(0)}, {os.getpriority(os.PRIO_PROCESS, 0)}")
    for i in range(4000):
        time.sleep(1e-3)

    os.setpriority(os.PRIO_PROCESS, 0, 0)
    print(f"{os.sched_getscheduler(0)}, {os.getpriority(os.PRIO_PROCESS, 0)}")
    time.sleep(4)


# os.setpriority(which, who, priority)
""" 
# Set program scheduling priority. The value which is one of PRIO_PROCESS, PRIO_PGRP, or PRIO_USER, and who is interpreted relative to which (a process identifier for PRIO_PROCESS, process group identifier for PRIO_PGRP, and a user ID for PRIO_USER). A zero value for who denotes (respectively) the calling process, the process group of the calling process, or the real user ID of the calling process. priority is a value in the range -20 to 19. The default priority is 0; lower priorities cause more favorable scheduling. 
# """

for s in (
    os.SCHED_OTHER,
    os.SCHED_BATCH,
    os.SCHED_IDLE,
    # os.SCHED_SPORADIC,
    os.SCHED_FIFO,
    os.SCHED_RR,
    # os.SCHED_RESET_ON_FORK,
):
    print(s, os.sched_get_priority_min(s), os.sched_get_priority_max(s))
    print(os.sched_rr_get_interval(0))
