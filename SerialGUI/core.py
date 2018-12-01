__author__ = 'jmorais'

try:
    from fase import Fase
except Exception as e:
    print('require module exception: %s' % e)
    exit(0)
"""
Starting Fase(...).execute() make possible the communication between the micro services.
simple: python core.py
"""
Fase(sender_endpoint='ipc:///tmp/sender', receiver_endpoint='ipc:///tmp/receiver').execute()
