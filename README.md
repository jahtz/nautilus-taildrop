# Nautilus Taildrop
Nautilus extension for sending and receiving files with [Taildrop](https://tailscale.com/taildrop) (Tailscale)

>[!IMPORTANT]
> Taildrop can't transfer files to devices of other users or devices that are tagged:<br>
> https://tailscale.com/kb/1106/taildrop#send-files-with-taildrop
## Setup
### Tailscale
Run Tailscale with
```shell
tailscale up --operator $USER
```
### Requirements
Ubuntu/Debian/Mint: `sudo apt install python3-nautilus python3-gi`

RHEL/Fedora: `sudo dnf install nautilus-python python3-gobject`

Arch: `sudo pacman -S python-nautilus python-gobject`

### Install extension
 ```shell
git clone https://github.com/jahtz/nautilus-taildrop.git
cd nautilus-taildrop
make install
````

### Remove extension
```shell
make uninstall
```

## Modification
>[!NOTE]
> File to modify: `~/.local/share/nautilus-python/extensions/nautilus-taildrop.py`<br>
> Modifications require Nautilus to be reloaded: `nautilus -q`
### Show full DNS names
If you want to show full DNS names (e.g. _yourdevice.your-tailnet.ts.net_) instead of device names (e.g. _yourdevice_), 
you can set `SHOW_FULL_DNS_NAME` to `True` (line 35).

### Hide offline devices
If you want to hide offline devices from the device list, set `HIDE_OFFLINE` to `True` (line 37)
