#!/usr/bin/env python
import sys
import eventlet

if len(sys.argv) < 3:
    print 'Usage: python guard.py <host> <port>'
    sys.exit(1)

HOST = sys.argv[1]
try:
    PORT = int(sys.argv[2]) 
except ValueError:
    print 'Specify a valid port number'
    sys.exit(1)

pool = eventlet.GreenPool()

"""Constant responses"""
BAD_MESSAGE = 'BAD_MESSAGE\r\n'
LOCK_EXISTS = 'LOCK_EXISTS\r\n'
QUIT = 'QUIT\r\n'

key_locked_status = {}


def sock_write(sockfd, msg):
    """
    Function which flushes the internal buffer so that the message appears on 
    the stream immediately
    """
    sockfd.write(msg)
    sockfd.flush()

def conn_handler(sock, addr):
    """Handles connections made by requesting clients"""
    sockfd = sock.makefile('rw')
    line = sockfd.readline().rstrip()
    print 'Received: ', line
    if not line.startswith('LOCK'):
        if not line.startswith('QUIT'):
            sock_write(sockfd, BAD_MESSAGE)
        sockfd.close()
        return
    cmd, key = line.split()
    if key_locked_status.has_key(key) and key_locked_status[key]:
        sock_write(sockfd, LOCK_EXISTS)
    else:
        key_locked_status[key] = True
        sock_write(sockfd, "LOCKED %s\r\n" %(key))
    line = sockfd.readline().rstrip()
    print 'Received: ', line
    if not line.startswith('UNLOCK') and not line.startswith('QUIT'):
        sock_write(sockfd, BAD_MESSAGE)
    key_locked_status[key] = False
    sock_write(sockfd, QUIT)
    sockfd.close()

eventlet.serve(eventlet.listen((HOST, PORT)), conn_handler)
