Sample rate is 56 MSa/sec.  Each sample is an np.complex64 -- 8 bytes so the the data rate is 448 MB/sec.  An alternative would be np.uint16's, so 4 bytes and 224 MB/sec.

Each buffer is about 2000 samples long, so 2040/56e6 = ~36.4 usec

I use the RT scheduler.  I also use memory-mapped I/O, tho Linus says it won't help.  The code is here

   https://github.com/ajheller/usrp/blob/main/usrp_rx_to_file_mp.py

three processes:

- RT priority loop to read sample buffers from the SDR and put them into the shared array, pushes indices onto queue
- RT priority loop to read indices from queue, get samples from shared array, write to memory-mapped output array
- regular priority process that runs once per second and calls sync()

It all runs perfectly except for a single glitch about 2 minutes in.  You can watch it playout with htop, the processes run at 20-50% CPU.  But the kernel is doing delayed writes, so it's buffering up the file writes... you can watch this happen with htop. When the 64GB memory is exhausted, the kernel processes the delayed writes and the first process is suspended for ~100 usec and drops a few buffers.   After that it functions perfectly for hours, until the disk fills up.  So I simply want it to start doing the delayed writes earlier, so they're done in smaller increments.  I thought the periodic calls to sync() would do that, but apparently not. 

Here's the funny thing.  At one point, I was running an rsync backup to our NAS and it didn't glitch, so rsync was forcing enough I/O buffer churn, that it was doing the delayed writes earlier.  So loading the machine improved the performance.  The machine is a 24 core, SFF Dell, with a M2 SSD, so well overspec'ed for the task. 

I need to try sequential writes vs. memory-mapped. 

Marc Lavalée says:

Is your computer running with a RT kernel? It could help.

Kernel 6.1 seem to have capabilities for realtime scheduling, but 
there's also a PREMPT_RT version of kernel 6.1, I don't know if it'd be 
better.

>> I need to try sequential writes vs. memory-mapped.
>
> I suspect it'd be better to write without much delay using a small 
> buffer.

Instead of SCHED_RR, why not using  SCHED_FIFO? They're similar, but 
maybe one is working better than the other.

There's a mention of the realtime kernel in the sched man page :

https://www.man7.org/linux/man-pages/man7/sched.7.html

I replied:

I like the realtime kernel idea... looks pretty easy to do.  Tuning parameters on a stock kernel would be specific to a particular machine, how much memory, disk. speeds.  RT kernel is a more disciplined approach

   - https://ubuntu.com/blog/real-time-ubuntu-released
   - https://ubuntu.com/blog/real-time-kernel-technical

I remember Nando used to compile the RT kernels for the Planet CCRMA distro himself, using patches from a physician in Australia.

Key feature:

    “The scheduler of the real-time Ubuntu beta can preempt threads in the kernel, including in critical sections, interrupt handlers, and interrupt-disable code sequences, guaranteeing bounded responses.”
