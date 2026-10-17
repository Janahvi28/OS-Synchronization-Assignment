"""
common/shared_resource.py
A shared integer that can DETECT synchronization bugs.
 - A write is deliberately split: read value -> sleep -> write value+1.
   If two writers ever overlap, one update is lost (classic race condition).
 - Every overlap (writer+writer or writer+reader) is counted as a violation.
"""
import threading
import time


class SharedResource:
    def __init__(self):
        self.value = 0
        self._meta = threading.Lock()      # only protects the counters below
        self.readers_inside = 0
        self.writers_inside = 0
        self.max_readers = 0
        self.violations = 0

    def read(self, pause):
        with self._meta:
            self.readers_inside += 1
            self.max_readers = max(self.max_readers, self.readers_inside)
            if self.writers_inside:
                self.violations += 1
        seen = self.value
        time.sleep(pause)
        with self._meta:
            self.readers_inside -= 1
        return seen

    def write(self, pause):
        with self._meta:
            self.writers_inside += 1
            if self.writers_inside > 1 or self.readers_inside:
                self.violations += 1
        temp = self.value          # step 1: read
        time.sleep(pause)          # step 2: window where another writer could sneak in
        self.value = temp + 1      # step 3: write back
        with self._meta:
            self.writers_inside -= 1
        return self.value
