#!/bin/bash

OUTPUT_FILE_INIT="/var/log/process_trace_init.log" 
ps -eo pid,ppid,comm > $OUTPUT_FILE_INIT

OUTPUT_FILE="/var/log/process_trace.log"
touch $OUTPUT_FILE

trace_processes(){
	execsnoop -t > $OUTPUT_FILE &
	TRACE_PID=$!
}

trace_processes

stop_tracing(){
	kill $TRACE_PID
}

trap stop_tracing EXIT

wait $TRACE_ID
