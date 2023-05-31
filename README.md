# usrp

Streaming RF captures from an Ettus USRP SDR to disk at full bandwidth -- 56 MSa/sec in the case of a B210.

Modern computers with multiple cores and high-bandwidth SSDs appear to be overspeced for this by an order of magnitude, yet still struggle to do it without dropping samples.  