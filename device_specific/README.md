# Device specific configuration

## Gigabyte Aero 15x (v8)

### Fan control

[Nbfc-linux](https://github.com/nbfc-linux/nbfc-linux) works well on linux. But the original nbfc also works.
On windows I had some issues with bluescreens. I don't know why, but I think it was related to the fan control.
The configuration file is in the is available for both projects.
The fan curve is very quiet until a high temperature is reached, then it ramps up quickly.
When the load is removed, it cools down quickly without ramping down the fan speed until cool.
This reduces quiet constant noise when doing light tasks.
Install and enable nbfc-linux. Copy the json file to /usr/share/nbfc/configs (or /usr/local/share/nbfc/configs).
Run `sudo nbfc config -a "Gigabyte Aero15x v8"` to apply the config.

### Nvidia Optimus on Linux

[Asus supergfxctl](https://gitlab.com/asus-linux/supergfxctl) works well for me.
The [GNOME Extension](https://gitlab.com/asus-linux/supergfxctl-gex) also works well.
Both are preinstalled on Nobora Project. This requires a logout to apply the changes, but reliably works.
(Remember running `flatpak update` to install nvidia drivers. Without them, the nvidia card is not detected inside flatpak apps.)

<details>
<summary>Old experimental stuff</summary>
I had limited sucess with this method. It sometimes even allowed me to enable and disable the nvidia card
without logging out. But it was not reliable.

Install switcheroo-control (for gnome). Nvidia driver.
Use the following script to enable the nvidia card (save as nvidia-on):
```
#!/bin/env bash
tee /sys/bus/pci/devices/0000:00:01.0/rescan <<<1 &&
modprobe nvidia nvidia_uvm nvidia_modeset nvidia_drm &&
tee /sys/bus/pci/devices/0000:00:01.0/power/control <<<on
```

Use the following script to disable the nvidia card (save as nvidia-off):
```
#!/bin/env bash
sudo modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia &&
sudo tee /sys/bus/pci/devices/0000:01:00.0/remove <<<1 &&
sudo tee /sys/bus/pci/devices/0000:01:00.1/remove <<<1 &&
sudo tee /sys/bus/pci/devices/0000:00:01.0/power/control <<<auto
```

Disable nvidia card on boot by adding /etc/systemd/system/nvidia-off-on-boot.service:
```
[Unit]
Description="Remove Nvidia GPU from kernel."

[Service]
Type=oneshot
ExecStart=/bin/bash -c '/usr/bin/nvidia-off'

[Install]
WantedBy=multi-user.target
```
And enable it with `systemctl enable nvidia-off-on-boot.service`.

Disable nouveau driver by adding /etc/modprobe.d/blacklist-nouveau.conf:
```
blacklist nouveau
```

</details>

### CPU power management

To reduce power consumption, undervolt the CPU. On linux [intel-undervolt](https://github.com/kitsunyan/intel-undervolt) works well.
Copy "intel-undervolt.conf" to /etc/intel-undervolt.conf. Enable it with `systemctl enable intel-undervolt.service`.
These settings are only valid for my CPU.
On Arch install (and enable) power-profiles-daemon for gnome unlocks the power management options in quick settings.
On Windows, use Throttlestop to undervolt the CPU. Compare the values with the ones in the config file for linux.
To apply automatically, add a task to Task Scheduler. (Don't forget to disable the options which disable the task on battery. Throttlestop admin rights)
