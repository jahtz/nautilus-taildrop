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
#### Ubuntu/Debian/Mint
```shell
sudo apt install python3-nautilus python3-gi
```

#### RHEL/Fedora
```shell
sudo dnf install nautilus-python python3-gobject
```

#### Arch
```shell
sudo pacman -S python-nautilus python-gobject
```

### Install extension
 ```shell
git clone https://github.com/jahtz/nautilus-taildrop.git
 ```

#### Method 1: make
```shell
cd nautilus-taildrop
make install
```

####  Method 2: manual
```shell
mkdir -p ~/.local/share/nautilus-python/extensions
cp nautilus-taildrop/nautilus-taildrop.py ~/.local/share/nautilus-python/extensions
```

### Remove extension
#### Method 1: make
```shell
make uninstall
```

#### Method 2: manual
```shell
rm ~/.local/share/nautilus-python/extensions/nautilus-taildrop.py
```

## Modification
>[!NOTE]
> Modifications require Nautilus to be reloaded:
> Run `nautilus -q`
### Show full DNS names
If you want to show full DNS names (e.g. _yourdevice.your-tailnet.ts.net_) instead of device names (e.g. _yourdevice_), 
you can set `SHOW_DNS_NAME` to `True` (`~/.local/share/nautilus-python/extensions/nautilus-taildrop.py`, line 28).