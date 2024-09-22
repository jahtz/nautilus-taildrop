# Nautilus Taildrop
Nautilus extension for sending and receiving files with [Taildrop](https://tailscale.com/taildrop) (Tailscale)

>[!IMPORTANT]
> Taildrop can't transfer files to devices of other users or devices that are tagged:
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
> Modifications require Nautilus to be reloaded:
> Run `nautilus -q`
### Show full DNS names
If you want to show full DNS names (e.g. _yourdevice.your-tailnet.ts.net_) instead of device names (e.g. _yourdevice_), 
you can set `SHOW_DNS_NAME` to `True` (`~/.local/share/nautilus-python/extensions/nautilus-taildrop.py`, line 28).