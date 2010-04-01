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
LOCK_ALREADY_ACQUIRED = 'LOCK_ALREADY_ACQUIRED\r\n'
LOCK_NEVER_ACQUIRED = 'LOCK_NEVER_ACQUIRED\r\n'
LOCK_NOT_RELEASED = 'LOCK_NOT_RELEASED\r\n'
QUIT = 'QUIT\r\n'

"""Daemon states"""
LOCKED, UNLOCKED, DONE = [_ for _ in range(3)]

key_locked_status = {}


def sock_write(sockfd, msg):
    """
    Function which flushes the internal buffer so that the message appears on 
    the stream immediately
    """
    sockfd.write(msg)
    sockfd.flush()

def handle_state(client_conn_fd, client_msg, daemon_state):
    """Manages the state of the daemon according to the request"""
    if client_msg.startswith('LOCK'):
        if daemon_state == LOCKED:
            sock_write(client_conn_fd, LOCK_ALREADY_ACQUIRED)
            return LOCKED
        elif daemon_state == UNLOCKED:
            key = client_msg.split()[1]
            if key_locked_status.has_key(key) and key_locked_status[key]:
                sock_write(client_conn_fd, LOCK_EXISTS)
                return UNLOCKED
            else:
                key_locked_status[key] = True
                sock_write(client_conn_fd, "LOCKED %s\r\n" %(key))
                return LOCKED
    elif client_msg.startswith('UNLOCK'):
        key = client_msg.split()[1]
        if daemon_state == LOCKED:
            key_locked_status[key] = False
            sock_write(client_conn_fd, "UNLOCKED %s\r\n" %(key))
            return UNLOCKED
        elif daemon_state == UNLOCKED:
            sock_write(client_conn_fd, LOCK_NEVER_ACQUIRED)
            return UNLOCKED
    elif client_msg.startswith('QUIT'):
        if daemon_state == LOCKED:
            sock_write(client_conn_fd, LOCK_NOT_RELEASED)
            return LOCKED
        elif daemon_state == UNLOCKED:
            sock_write(client_conn_fd, QUIT)
            return DONE

def conn_handler(sock, addr):
    """Handles connections made by requesting clients"""
    sockfd = sock.makefile('rw')
    state = UNLOCKED
    while True:
        line = sockfd.readline().rstrip()
        state = handle_state(sockfd, line, state)
        if state == DONE:
            break

eventlet.serve(eventlet.listen((HOST, PORT)), conn_handler)
