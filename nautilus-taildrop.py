# Copyright 2024 Janik Haitz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import subprocess
from urllib.parse import unquote, urlparse
from pathlib import Path

import gi

pygi_version = '3.0' if gi.version_info[1] < 40 else '4.0'
gi.require_version('Nautilus', pygi_version)
from gi.repository import GObject, Nautilus


### Settings
SHOW_DNS_NAME = False


class Tailscale:
    @staticmethod
    def get_devices() -> list[tuple[str, bool]]:
        """
        Load a list of devices that are connected to tailscale.
        Only use devices that are by the current user, are not tagged.
        -> https://tailscale.com/kb/1106/taildrop#send-files-with-taildrop

        :return: list of tailscale DNSNames and their online state.
        """
        process = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, check=False)
        tailnet_status = json.loads(process.stdout)
        peers = tailnet_status['Peer']
        users = tailnet_status['User']
        self_id: int = tailnet_status['Self']['UserID']

        devices: list[tuple[str, bool]] = []
        for _, device_info in peers.items():
            if device_info['UserID'] == self_id:
                device_dns_name = device_info['DNSName']
                if device_dns_name.endswith('.'):
                    device_dns_name = device_dns_name[:-1]
                devices.append((device_dns_name, device_info['Online']))
        return sorted(devices, key=lambda d: d[0])

    @staticmethod
    def taildrop_send(fp: Path, dns_name: str):
        """
        Send a file with Taildrop.

        :param fp: File to send.
        :param dns_name: Target device DNS name.
        """
        subprocess.Popen(['tailscale', 'file', 'cp', fp.as_posix(), dns_name + ':'])

    @staticmethod
    def taildrop_receive(fp: Path):
        """
        Receive file(s) with Taildrop.

        :param fp: Directory where file(s) should be downloaded to.
        """
        subprocess.Popen(['tailscale', 'file', 'get', fp])


class TaildropExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass

    @staticmethod
    def callback_send(_menu, files: list[Nautilus.FileInfo], dns_name: str):
        """
        Callback handler for sending files to a device in your Tailnet.

        :param _menu: Nautilus menu object.
        :param files: list of files to send.
        :param dns_name: DNS name of target device.
        """
        for fp in files:
            fp = Path(unquote(urlparse(fp.get_uri()).path))
            Tailscale.taildrop_send(fp, dns_name)

    @staticmethod
    def callback_receive(_menu, current_folder: Nautilus.FileInfo):
        """
        Callback handler for receiving files from a device in your Tailnet.

        :param _menu: Nautilus menu object.
        :param current_folder: Target directory to save received file in.
        """
        fp = Path(unquote(urlparse(current_folder.get_uri()).path))
        Tailscale.taildrop_receive(fp)
    def get_file_items(self, files: list[Nautilus.FileInfo]):
        """
        Executed when a file is selected.
        Create a menu entry for sending files with Taildrop and a submenu containing all available devices.

        :param files: list of selected files.
        """
        send_files_menu = Nautilus.MenuItem(name='TaildropExtension::Devices',
                                            label='Taildrop Send',
                                            tip='Send selected files.')
        device_list_menu = Nautilus.Menu()
        send_files_menu.set_submenu(device_list_menu)

        for idx, device in enumerate(Tailscale.get_devices()):
            label = device[0] if SHOW_DNS_NAME else device[0].split('.')[0]
            device_item = Nautilus.MenuItem(name=f'TaildropExtension::Device{idx}',
                                            label=label,
                                            tip=f'Send selected files to {device[0]}.',
                                            sensitive=device[1])
            device_item.connect('activate', self.callback_send, files, device[0])
            device_list_menu.append_item(device_item)
        return (send_files_menu, )

    def get_background_items(self, current_folder: Nautilus.FileInfo):
        """
        Executed when no file is selected.
        Creates a menu entry for receiving files from Taildrop.
        :param current_folder: Current directory.
        """
        receive_item = Nautilus.MenuItem(name='TaildropExtension::Receive',
                                         label='Taildrop Receive',
                                         tip='Receive files here.')
        receive_item.connect('activate', self.callback_receive, current_folder)
        return (receive_item, )
