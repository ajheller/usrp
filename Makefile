all:
	echo all

probe:
	uhd_usrp_probe

kernel-vm-params:
	sudo sysctl -a |grep "vm\."


rec-15-900:
	sudo ./run_cap.sh -r 15e6 -f 1e9 -d 900 -o cap-15-c64.bin

rec-56-300:
	sudo ./run_cap.sh -r 56e6 -f 1e9 -d 300 -o cap-56-c64.bin

UHD_EXAMPLES=/usr/local/lib/uhd/examples

# ./tx_samples_from_file --help
# UHD TX samples from file Allowed options:
#   --help                         help message
#   --args arg                     multi uhd device address args
#   --file arg (=usrp_samples.dat) name of the file to read binary samples from
#   --type arg (=short)            sample type: double, float, or short
#   --spb arg (=10000)             samples per buffer
#   --rate arg                     rate of outgoing samples
#   --freq arg                     RF center frequency in Hz
#   --lo-offset arg (=0)           Offset for frontend LO in Hz (optional)
#   --gain arg                     gain for the RF chain
#   --ant arg                      antenna selection
#   --subdev arg                   subdevice specification
#   --bw arg                       analog frontend filter bandwidth in Hz
#   --ref arg (=internal)          reference source (internal, external, mimo)
#   --wirefmt arg (=sc16)          wire format (sc8 or sc16)
#   --delay arg (=0)               specify a delay between repeated transmission
#                                  of file (in seconds)
#   --channel arg (=0)             which channel to use
#   --repeat                       repeatedly transmit file
#   --int-n                        tune USRP with integer-n tuning
tx-15:
	sudo $(UHD_EXAMPLES)/tx_samples_from_file --file p-c64.bin --type float --rate 15e6 --freq 1e9 --args "num_send_frames=1979"


# sudo ./run_cap.sh --help
# /usr/local/lib/python3.8/site-packages/:
# compiling ...
# usage: usrp_rx_to_file_thread.py [-h] [--rx_center_frequency RX_CENTER_FREQUENCY] [--rx_sample_rate RX_SAMPLE_RATE] [--duration DURATION] [--output_path OUTPUT_PATH]
#                                  [--device_args DEVICE_ARGS] [--preallocate_file]

# optional arguments:
#   -h, --help            show this help message and exit
#   --rx_center_frequency RX_CENTER_FREQUENCY, -f RX_CENTER_FREQUENCY
#                         center frequency in Hz
#   --rx_sample_rate RX_SAMPLE_RATE, -r RX_SAMPLE_RATE
#                         samples per second
#   --duration DURATION, -d DURATION
#                         rx duration in seconds
#   --output_path OUTPUT_PATH, -o OUTPUT_PATH
#                         Output file name without extension
#   --device_args DEVICE_ARGS, -a DEVICE_ARGS
#                         USRP initialization arguments
#   --preallocate_file, -p
# heller@BB1-Precision-3460:~/usrp$ 

# heller@BB1-Precision-3460:~/usrp$ /usr/local/lib/uhd/examples/rx_samples_to_file --help
# UHD RX samples to file Allowed options:
#   --help                         help message
#   --args arg                     multi uhd device address args
#   --file arg (=usrp_samples.dat) name of the file to write binary samples to
#   --type arg (=short)            sample type: double, float, or short
#   --nsamps arg (=0)              total number of samples to receive
#   --duration arg (=0)            total number of seconds to receive
#   --spb arg (=10000)             samples per buffer
#   --rate arg (=1000000)          rate of incoming samples
#   --freq arg (=0)                RF center frequency in Hz
#   --lo-offset arg (=0)           Offset for frontend LO in Hz (optional)
#   --gain arg                     gain for the RF chain
#   --ant arg                      antenna selection
#   --subdev arg                   subdevice specification
#   --channels arg (=0)            which channel(s) to use (specify "0", "1", 
#                                  "0,1", etc)
#   --bw arg                       analog frontend filter bandwidth in Hz
#   --ref arg (=internal)          reference source (internal, external, mimo)
#   --wirefmt arg (=sc16)          wire format (sc8, sc16 or s16)
#   --setup arg (=1)               seconds of setup time
#   --progress                     periodically display short-term bandwidth
#   --stats                        show average bandwidth on exit
#   --sizemap                      track packet size and display breakdown on 
#                                  exit. Use with multi_streamer option if CPU 
#                                  limits stream rate.
#   --null                         run without writing to file
#   --continue                     don't abort on a bad packet
#   --skip-lo                      skip checking LO lock status
#   --int-n                        tune USRP with integer-N tuning
#   --multi_streamer               Create a separate streamer per channel.


rx-15:
	$(UHD_EXAMPLES)/rx_samples_to_file --channels 0 --freq 1000000000 --rate 15000000 --gain 20 --duration 10 --args "num_recv_frames=1979"
