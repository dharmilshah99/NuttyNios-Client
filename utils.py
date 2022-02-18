import threading
from subprocess import Popen, PIPE

class AccelerometerStream(object):
    """Gets chats in a dedicated thread."""
    def __init__(self):
        """Initialize Thread."""
        self.events = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        
    def run(self):
        """Continually get messages from a NIOS."""
        with Popen("nios2-terminal", shell=True, executable='/bin/bash', stdout=PIPE) as p:
            for line in p.stdout: # line is encoded string from the stdout
                string_1 = line.decode().strip()
                try:
                    y_val = float(string_1)
                except:
                    y_val = 0
                self.msg = y_val
                self.events.set()
            
    def get(self):
        """Get messages."""
        self.events.clear()
        return self.msg