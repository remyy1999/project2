# confundo/common.py

MTU = 512
MAX_SEQNO = 102401
RETX_TIME = 0.5
FIN_WAIT_TIME = 2.0
SYN_WAIT_TIME = 10.0

INIT_SSTHRESH = 10000

GLOBAL_TIMEOUT = 10.0

# Parameters for congestion control
MAX_WINDOW_SIZE = 10000
INIT_CWND_SIZE = 10
CC_TIMEOUT = 1.0  # Timeout value for congestion control
