from __future__ import print_function
import socket
import json
import os
import logging
import threading
import Queue

CONFIG_FILE = "kernel-config.json"
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONFIG_FILE)
config = json.load(open(CONFIG_FILE_PATH, "r"))

HOST = config["host"]              # Symbolic name meaning all available interfaces
PORT = config["port"]              # Arbitrary non-privileged port

class SpringConnector(threading.Thread):
    def executeLua(self, msg):
        self.logger.info('Asked to execute code')
        # Add the task
        self.tasks.put(msg)
        self.logger.info('Waiting on results')
        # Wait until results are ready
        return self.results.get(True, 60)

    def _handleTasks(self):
        self.logger.info('Waiting on code')
        # Wait until there are tasks to do
        task = self.tasks.get(True)
        self.logger.info('Send code for execution')
        jsonData = None
        data = None
        try:
            self.conn.sendall(json.dumps(task))
            data = self.conn.recv(20971520)
            jsonData = json.loads(data)
            self.logger.info('Received data: {0}'.format(jsonData))
        except ValueError as ex:
            self.logger.error("Failed parsing spring data as json: {}".format(ex))
            self.logger.error("data: {}\njsonData: {}".format(data, jsonData))
            self.results.put({})
            return
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            self.logger.error(message)
            self.results.put({})
            raise ex
        if not jsonData:
            self.results.put({})
            raise
        else:
            # Give the results back
            self.results.put(jsonData)

    def run(self):
        self.logger = logging.getLogger(__name__)

        self.logger.info('Starting SpringConnector server')

        self.tasks = Queue.Queue(1)
        self.results = Queue.Queue(1)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((HOST, PORT))
        self.s.listen(1)
        while True:
            self.conn, addr = self.s.accept()
            self.logger.info('Connected by {}')
            self.logger.info('Connected by {}'.format(addr))
            while True:
                try:
                    self._handleTasks()
                except Exception as e:
                    self.logger.warning(e)
                    break
            self.conn.close()
            self.logger.info('Connection closed')
