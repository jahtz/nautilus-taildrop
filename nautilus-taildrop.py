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

import json
import subprocess
from urllib.parse import unquote, urlparse
from pathlib import Path

from gi import require_version
try:
	require_version('Nautilus', '4.0')
	require_version('Gtk', '4.0')
except:
    require_version('Nautilus', '3.0')
    require_version('Gtk', '3.0')
from gi.repository import GObject, Nautilus


### Settings ###
# If enabled, show devices as `yourdevice.yourtailnet.ts.net`, else `yourdevice`
SHOW_FULL_DNS_NAME = False
# If enabled, hide offline devices, else show them grayed out
HIDE_OFFLINE = False


class NautilusTaildrop(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        self.devices: list[tuple[str, bool]] = []
        self._update_devices()

    def get_file_items(self, selected_files: list[Nautilus.FileInfo]):
        send_files_menu = Nautilus.MenuItem(name='TaildropExtension::Devices',
                                            label='Taildrop Send',
                                            tip='Send selected files.')
        device_list_menu = Nautilus.Menu()
        send_files_menu.set_submenu(device_list_menu)
        for idx, device in enumerate(self.devices):
            device_item = Nautilus.MenuItem(name=f'TaildropExtension::Device{idx}',
                                            label=device[0] if SHOW_FULL_DNS_NAME else device[0].split('.')[0],
                                            tip=f'Send selected files to {device[0]}.',
                                            sensitive=device[1])
            device_item.connect('activate', self._taildrop_send, selected_files, device[0])
            device_list_menu.append_item(device_item)
        
        update_item = Nautilus.MenuItem(name='TaildropExtension::DevicesUpdate',
                                            label='Update devices',
                                            tip='Update device list.')
        update_item.connect('activate', self._update_devices)
        device_list_menu.append_item(update_item)

        return (send_files_menu, )

    def get_background_items(self, current_directory: Nautilus.FileInfo):
        receive_item = Nautilus.MenuItem(name='TaildropExtension::Receive',
                                         label='Taildrop Receive',
                                         tip='Receive files here.')
        receive_item.connect('activate', self._taildrop_receive, current_directory)
        return (receive_item, )

    def _update_devices(self, _menu = None):
        """ Update devices """
        process = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, check=False)
        tailnet_status = json.loads(process.stdout)

        user_id: int = tailnet_status['Self']['UserID']
        devices: list[tuple[str, bool]] = []
        for _, device_info in tailnet_status['Peer'].items():
            if HIDE_OFFLINE and not device_info['Online']:
                continue
            if device_info['UserID'] == user_id:
                device_dns_name = device_info['DNSName']
                if device_dns_name.endswith('.'):
                    device_dns_name = device_dns_name[:-1]
                devices.append((device_dns_name, device_info['Online']))
        self.devices = devices
    
    @staticmethod
    def _taildrop_send(_menu, selected_files: list[Nautilus.FileInfo], dns_name: str):
        valid_files: list[Path] = []
        for file in selected_files:
            if not file.get_uri_scheme() == "file": # must be a local file/directory
                continue
            fp = Path(unquote(urlparse(file.get_uri()).path))
            if fp.is_dir():  # expand directories (not natively supported)
                valid_files.extend([f for f in fp.glob('*') if f.is_file()])
            else:
                valid_files.append(fp)
        for file in valid_files:
            subprocess.Popen(['tailscale', 'file', 'cp', file.as_posix(), f'{dns_name}:'])

    @staticmethod   
    def _taildrop_receive(_menu, current_directory: Nautilus.FileInfo):
        file = Path(unquote(urlparse(current_directory.get_uri()).path))
        subprocess.Popen(['tailscale', 'file', 'get', file])
