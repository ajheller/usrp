import argparse
import uhd
import logging
import numpy as np
import os
import time
from datetime import datetime, timedelta
import tqdm

# Author: Aaron Heller aaron.heller@sri.com 24-May-2023

# References:
#   https://kb.ettus.com/UHD_Python_API
#   https://files.ettus.com/manual/classuhd_1_1usrp_1_1multi__usrp.html
#   https://pysdr.org/content/usrp.html#usrp-chapter
#   https://files.ettus.com/manual/page_usrp_b200.html
#   https://github.com/EttusResearch/uhd
#   https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q0000019mApCAI&l=en-US
#
# Examples:
#   https://github.com/EttusResearch/uhd/tree/master/host/examples
#   https://ewf-engineering.com/a-deeper-look-into-the-ettus-usrp-b200/
#
# -------------------------------------------------------------------------------------

# config variables
UHD_USRP_ARGS = "num_recv_frames=1024"  # default is 32, which is way to small
# UHD_USRP_ARGS += ", type=b200, serial=xxxxxxx" # to find a specific Ettus

RX_SAMPLES_PER_SECOND = 25e6
RX_DURATION_SECONDS = 300
RX_CENTER_FREQUENCY_HZ = 1.0e9

PREALLOCATE_OUTPUT_FILE = True

parser = argparse.ArgumentParser()
parser.add_argument(
    "--rx_center_frequency",
    "-f",
    type=float,
    default=RX_CENTER_FREQUENCY_HZ,
    help="center frequency in Hz",
)
parser.add_argument(
    "--rx_sample_rate",
    "-r",
    type=float,
    default=RX_SAMPLES_PER_SECOND,
    help="samples per second",
)
parser.add_argument(
    "--duration",
    "-d",
    type=float,
    default=RX_DURATION_SECONDS,
    help="rx duration in seconds",
)
parser.add_argument("--preallocate_file", "-p", action="store_true", default=False)
args = parser.parse_args()


class LogFormatter(logging.Formatter):
    """Log formatter which prints the timestamp with fractional seconds"""

    @staticmethod
    def pp_now():
        """Returns a formatted string containing the time of day"""
        now = datetime.now()
        return "{:%H:%M}:{:05.2f}".format(now, now.second + now.microsecond / 1e6)
        # return "{:%H:%M:%S}".format(now)

    def formatTime(self, record, datefmt=None):
        converter = self.converter(record.created)
        if datefmt:
            formatted_date = converter.strftime(datefmt)
        else:
            formatted_date = LogFormatter.pp_now()
        return formatted_date


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
logger.addHandler(console)
formatter = LogFormatter(
    fmt="[%(asctime)s] [%(levelname)s] (%(threadName)-10s) %(message)s"
)
console.setFormatter(formatter)

# To estimate the number of dropped samples in an overflow situation, we need the following
#   . On the first overflow, set had_an_overflow and record the time
#   . On the next ERROR_CODE_NONE, calculate how long its been since the recorded time, and use the
#     tick rate to estimate the number of dropped samples. Also, reset the tracking variables.
had_an_overflow = False
last_overflow = uhd.types.TimeSpec(0)
# Setup the statistic counters
num_rx_samps = 0
num_rx_dropped = 0
num_rx_overruns = 0
num_rx_seqerr = 0
num_rx_timeouts = 0
num_rx_late = 0


def process_metadata(usrp, metadata):
    global had_an_overflow, last_overflow
    global num_rx_samps, num_rx_dropped, num_rx_overruns, num_rx_seqerr, num_rx_timeouts, num_rx_late

    rate = usrp.get_rx_rate()
    # Handle the error codes
    if metadata.error_code == uhd.types.RXMetadataErrorCode.none:
        # Reset the overflow flag
        if had_an_overflow:
            had_an_overflow = False
            num_rx_dropped_here = (metadata.time_spec - last_overflow).to_ticks(rate)
            num_rx_dropped += num_rx_dropped_here
            if True:
                logger.warning(f"{num_rx_dropped_here} samples dropped!")
    elif metadata.error_code == uhd.types.RXMetadataErrorCode.overflow:
        had_an_overflow = True
        # Need to make sure that last_overflow is a new TimeSpec object, not
        # a reference to metadata.time_spec, or it would not be useful
        # further up.
        last_overflow = uhd.types.TimeSpec(
            metadata.time_spec.get_full_secs(), metadata.time_spec.get_frac_secs()
        )
        # If we had a sequence error, record it
        if metadata.out_of_sequence:
            num_rx_seqerr += 1
        # Otherwise just count the overrun
        else:
            num_rx_overruns += 1
    elif metadata.error_code == uhd.types.RXMetadataErrorCode.late:
        logger.warning(
            "Receiver error: %s, restarting streaming...", metadata.strerror()
        )
        num_rx_late += 1
        # Radio core will be in the idle state. Issue stream command to restart streaming.
        stream_cmd.time_spec = uhd.types.TimeSpec(
            usrp.get_time_now().get_real_secs() + INIT_DELAY
        )
        # stream_cmd.stream_now = num_channels == 1
        # rx_streamer.issue_stream_cmd(stream_cmd)
    elif metadata.error_code == uhd.types.RXMetadataErrorCode.timeout:
        logger.warning("Receiver error: %s, continuing...", metadata.strerror())
        num_rx_timeouts += 1
    else:
        logger.error("Receiver error: %s", metadata.strerror())
        logger.error("Unexpected error on receive, continuing...")


def preallocate_output_file(samples, len_recv_buffer):
    logger.info(f"preallocating output file ({samples.size*samples.itemsize/1e6} MB)")
    if samples.dtype == np.int16:
        increment = len_recv_buffer * 2
    else:
        increment = len_recv_buffer
    t0 = time.time()
    for i in tqdm.trange(0, len(samples), increment):
        samples[i : (i + increment)] = 0
    os.sync()
    write_time_seconds = time.time() - t0
    write_speed_samples_per_second = samples.size / write_time_seconds
    logger.info(
        f"Done! Write speed is {write_speed_samples_per_second/1e6:5.1f} MSa/sec;"
        f" required {sample_rate/1e6:5.1f} MSa/sec"
    )
    if write_speed_samples_per_second < sample_rate:
        logger.error("Disk write speed not adquate for sample rate")


usrp = uhd.usrp.MultiUSRP("num_recv_frames=1024")

dev_rx_channels = usrp.get_rx_num_channels()
dev_tx_channels = usrp.get_tx_num_channels()

print(f"#rx_ch={dev_rx_channels}, #tx_ch = {dev_tx_channels}")

center_freq = args.rx_center_frequency  # Hz
sample_rate = args.rx_sample_rate  # Hz
agc = True
gain = 50  # dB

# file_format = np.complex64
file_format = np.int16

num_samps_min = int(sample_rate * args.duration)  # minimum number of samples received

usrp.set_rx_rate(sample_rate, 0)
usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), 0)

if agc:
    usrp.set_rx_agc(agc, 0)  # 0 for channel 0, i.e. the first channel of the USRP
else:
    usrp.set_rx_gain(gain, 0)

# Set up the stream and receive buffer
st_args = uhd.usrp.StreamArgs("fc32", "sc16")
st_args.channels = [0]
metadata = uhd.types.RXMetadata()
streamer = usrp.get_rx_stream(st_args)

# allocate receive buffer
len_recv_buffer = streamer.get_max_num_samps()
num_recv_buffers = int(np.ceil(num_samps_min / len_recv_buffer))
# rounded up to integer number of buffers
num_samps = num_recv_buffers * len_recv_buffer

recv_buffer = np.zeros((len(st_args.channels), len_recv_buffer), dtype=np.complex64)
print("buffer size = ", len_recv_buffer)

float_to_int16_scale = np.iinfo(np.int16).max

# os.nice(-20)

# Receive Samples
# samples = np.zeros(num_samps, dtype=np.complex64)
# samples = np.memmap("test-mmap-c64.bin", dtype=np.complex64, mode='write', shape=num_samps)
if file_format == np.int16:
    samples = np.memmap(
        "test-mmap-i16i.bin", dtype=np.int16, mode="write", shape=num_samps * 2
    )
else:
    samples = np.memmap(
        "test-mmap-c64.bin", dtype=np.complex64, mode="write", shape=num_samps
    )

# Preallocate output file
print(samples.dtype, samples.shape)
if args.preallocate_file:
    preallocate_output_file(samples, len_recv_buffer)

logger.info(
    f"Recording for {num_samps/usrp.get_rx_rate()} seconds ({num_samps} samples)"
    f" at {usrp.get_rx_rate()/1e6} MSa/s"
    f" at {usrp.get_rx_freq()/1e6} MHz"
    f" on {streamer.get_num_channels()} channels"
    f" with {len_recv_buffer} samples per buffer"
)

# Start Stream
stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
stream_cmd.stream_now = True
streamer.issue_stream_cmd(stream_cmd)

try:
    if file_format == np.int16:
        recv_buffer_int16 = np.zeros(2 * len_recv_buffer, dtype=np.int16)
        bl = len(recv_buffer_int16)
        for i in tqdm.trange(num_samps // len_recv_buffer):
            streamer.recv(recv_buffer, metadata)
            recv_buffer[:] *= float_to_int16_scale
            recv_buffer_int16[:] = recv_buffer[0].view(np.float32).astype(np.int16)
            samples[i * bl : (i + 1) * bl] = recv_buffer_int16
            if metadata.error_code == uhd.types.RXMetadataErrorCode.none:
                pass
            else:
                print("!", flush=True)
    elif file_format == np.complex64:
        bl = len(recv_buffer[0])
        for i in tqdm.trange(num_samps // len_recv_buffer):
            streamer.recv(recv_buffer, metadata)
            samples[i * bl : (i + 1) * bl] = recv_buffer[0]
            # process_metadata(usrp, metadata)
    else:
        raise TypeError(
            f"file format must be np.int16 or np.complex64, not {file_format}"
        )

except KeyboardInterrupt as ki:
    logger.info(f"Recording interrupted by user after {i * len_recv_buffer} samples.")

except RuntimeError as re:
    logger.error(re)

# make sure everything is written to disk
samples.flush()

# Stop Stream
stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
streamer.issue_stream_cmd(stream_cmd)

# once more with feeling
samples.flush()

print(len(samples))
print(samples[0:100])
