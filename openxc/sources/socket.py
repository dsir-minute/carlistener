from __future__ import absolute_import

from .base import BytestreamDataSource, DataSourceError

# TODO can we get rid of this?
import socket


class SocketDataSource(BytestreamDataSource):
    def read(self):
        try:
            line = ""
            while '\x00' not in line:
                # TODO this is fairly inefficient
                line += self.socket.recv(1)
        except (OSError, socket.error, IOError) as e:
            raise DataSourceError("Unable to read from socket connection")
                
        if not line:
            raise DataSourceError("Unable to read from socket connection")
            
        return line

    def write_bytes(self, data):
        return self.socket.send(data)
