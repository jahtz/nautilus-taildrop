# Nautilus Admin - Extension for Nautilus to do administrative operations
# Copyright (C) 2024 Janik Haitz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from urllib.parse import unquote, urlparse
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pathlib import Path
import multiprocessing
import subprocess
import json

from gi import require_version
require_version('Notify', '0.7')
try:
    require_version('Nautilus', '4.0')
    require_version('Gtk', '4.0')
except:
    require_version('Nautilus', '3.0')
    require_version('Gtk', '3.0')
from gi.repository import GObject, Nautilus, Notify


class ProcessType(Enum):
    IDLE = 0
    SEND = 1
    RECEIVE = 2


@dataclass
class Device:
    dns_name: str
    display_name: str
    online: bool


class NautilusTaildrop(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()
        Notify.init('NautilusTaildropNotifier')

        self.devices: list[Device] = []
        self.update_devices(None)
        self.queue: multiprocessing.Queue = multiprocessing.Queue()
        self.process: Optional[multiprocessing.Process] = None
        self.process_type: ProcessType = ProcessType.IDLE

    @staticmethod
    def send_notification(header: str, body: str, error: bool):
        notification = Notify.Notification.new(header, body, "dialog-error" if error else "dialog-ok")
        notification.show()

    @staticmethod
    def send_files(selected_files: list[Nautilus.FileInfo], device: Device, queue: multiprocessing.Queue) -> None:
        for file in selected_files:
            fp = Path(unquote(urlparse(file.get_uri()).path))
            process = subprocess.Popen(
                ['tailscale', 'file', 'cp', fp.as_posix(), f'{device.dns_name}:'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                body = f'Error sending "{fp.name}" to "{device.display_name}": {stderr.decode().strip()}.'
                queue.put(('Taildrop', body, True))
                print(f'Taildrop: {body}')
                break
        body = f'Successfully sent {len(selected_files)} file{"s" if len(selected_files) > 1 else ""} to "{device.display_name}".'
        queue.put(('Taildrop', body, False))
        print(f'Taildrop: {body}')

    @staticmethod
    def receive_files(current_directory: Nautilus.FileInfo, queue: multiprocessing.Queue) -> None:
        directory = Path(unquote(urlparse(current_directory.get_uri()).path))
        process = subprocess.Popen(
            ['tailscale', 'file', 'get', directory.as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            body = f'Error receiving files: {stderr.decode().strip()}.'
            queue.put(('Taildrop', body, True))
            print(f'Taildrop: {body}')
        else:
            body = f'Successfully received file(s).'
            queue.put(('Taildrop', body, False))
            print(f'Taildrop: {body}')

    def update_devices(self, _menu) -> None:
        process = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, check=False)
        tailnet_status = json.loads(process.stdout)
        user_id: int = tailnet_status['Self']['UserID']  # fetch current user id
        self.devices.clear()
        for _, device_info in tailnet_status['Peer'].items():
            if device_info['UserID'] == user_id:
                device_dns_name = device_info['DNSName']
                if device_dns_name.endswith('.'):
                    device_dns_name = device_dns_name[:-1]
                self.devices.append(Device(device_dns_name, device_dns_name.split('.')[0], device_info['Online']))

    def background_process(self, _menu, pt: ProcessType, args: tuple = None) -> None:
        if self.process_type == ProcessType.RECEIVE and self.process:
            self.process.terminate()
            self.process = None
            self.process_type = ProcessType.IDLE
        if self.process_type != ProcessType.IDLE or self.process:
            print('Taildrop: Background process already running')
            return

        self.queue = multiprocessing.Queue()  # reset queue
        match pt:
            case ProcessType.SEND:
                self.process = multiprocessing.Process(target=self.send_files, args=args + (self.queue,))
                print('Taildrop: Sending files...')
            case ProcessType.RECEIVE:
                self.process = multiprocessing.Process(target=self.receive_files, args=args + (self.queue,))
                print('Taildrop: Receiving files...')
            case _:
                print('Taildrop: Unknown process type')
                return
        self.process_type = pt
        self.process.start()
        GObject.timeout_add(100, self.queue_watcher)

    def queue_watcher(self) -> bool:
        if not self.queue.empty():
            header, body, error = self.queue.get()
            print(header, body)
            self.send_notification(header, body, error)
            self.process = None
            self.process_type = ProcessType.IDLE
            return False
        if self.process and not self.process.is_alive():  # cleanup process if it is done
            self.process = None
            self.process_type = ProcessType.IDLE
            return False
        return True

    def get_file_items(self, selected_files: list[Nautilus.FileInfo]) -> Optional[list[Nautilus.MenuItem]]:
        if any(file.is_directory() for file in selected_files):
            return  # Taildrop only supports files
        send_menu = Nautilus.MenuItem(name='TaildropExtension::Devices',
                                      label='Taildrop Send',
                                      tip='Send selected files.')
        device_menu = Nautilus.Menu()
        send_menu.set_submenu(device_menu)
        for idx, device in enumerate(self.devices):
            device_item = Nautilus.MenuItem(name=f'TaildropExtension::Device{idx}',
                                            label=device.display_name,
                                            tip=f'Send selected files to {device.display_name}.',
                                            sensitive=device.online)
            device_item.connect('activate', self.background_process, ProcessType.SEND, (selected_files, device))
            device_menu.append_item(device_item)
        update_item = Nautilus.MenuItem(name='TaildropExtension::DevicesUpdate',
                                        label='Update devices',
                                        tip='Update device list.')
        update_item.connect('activate', self.update_devices)
        device_menu.append_item(update_item)
        return [send_menu]

    def get_background_items(self, current_directory: Nautilus.FileInfo) -> Optional[list[Nautilus.MenuItem]]:
        receive_item = Nautilus.MenuItem(name='TaildropExtension::Receive',
                                         label='Taildrop Receive',
                                         tip='Receive files here.',
                                         sensitive=self.process_type != ProcessType.SEND)
        receive_item.connect('activate', self.background_process, ProcessType.RECEIVE, (current_directory,))
        return [receive_item]
