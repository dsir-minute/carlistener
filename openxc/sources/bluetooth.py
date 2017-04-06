"""A Bluetooth data source."""
from __future__ import absolute_import

import logging

from openxc.controllers.base import Controller
from .socket import SocketDataSource
from .base import DataSourceError
import socket

import time

LOG = logging.getLogger(__name__)

try:
    import bluetooth
except ImportError:
    LOG.debug("pybluez library not installed, can't use bluetooth interface")
    bluetooth = None


class BluetoothVehicleInterface(SocketDataSource, Controller):
    """A data source reading from a bluetooth device.
    """

    OPENXC_DEVICE_NAME_PREFIX = "OpenXC-VI-"

    def __init__(self, address=None, **kwargs):
        """Initialize a connection to the bluetooth device.

        Raises:
            DataSourceError if the bluetooth device cannot be opened.
        """
        super(BluetoothVehicleInterface, self).__init__(**kwargs)
        self.address = address

        if bluetooth is None:
            raise DataSourceError("pybluez library is not available")

        # DARIO: New procedure for connection: If the user passes an invalid
        # address the first attemp will fail and at the next cycle the address
        # will be reset in order to perform a scan cycle again. With the old
        # code if the user passes a wrong address the connection will never
        # occur
        connected = False
        while not connected:
            while self.address is None:
                self.scan_for_bluetooth_device()

            # 4 connection tentatives before resetting the address
            i=0
            while i<4:
                connected = self.connect()
                if not connected:
                    time.sleep(1)
                    i=i+1
                else:
                    break

            if not connected:
                self.address = None

    def connect(self):
        # DARIO: Refactored method because the old one will hang forever if
        # bluetooth address is wrong
        port = 1
        connected = False
        
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        try:
            self.socket.connect((self.address, port))
        except IOError as e:
            LOG.warn("Unable to connect to %s" % self.address, e)
        else:
            LOG.info("Opened bluetooth device at %s", port)
            connected = True

        return connected

    # DARIO: Addendum to force the closure of connection on dongle
    def disconnect(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def scan_for_bluetooth_device(self):
        nearby_devices = bluetooth.discover_devices()

        self.address = None
        device_name = None
        for address in nearby_devices:
            device_name = bluetooth.lookup_name(address)
            if (device_name is not None and
                    device_name.startswith(self.OPENXC_DEVICE_NAME_PREFIX)):
                self.address = address
                break

        if self.address is not None:
            LOG.info("Discovered OpenXC VI %s (%s)" % (device_name, self.address))
        else:
            LOG.info("No OpenXC VI devices discovered")
