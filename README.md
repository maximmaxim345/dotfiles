# Dotfiles

Collection of my personal dotfiles.

## Installation

To install the majority of the dotfiles, use the Terminal GUI by starting "./dotfiles.py". There the
specific dotfiles can be selected for installation. This will however will not install software and
system wide configurations. When launching for the first time, it will download the required
dependencies automatically. The dependencies used are listed in ./requirements.txt.

## Uninstallation

To uninstall the dotfiles, use the Terminal GUI by starting "./dotfiles.py" and just remove the
dotfiles that were installed. This will revert the changes made by the dotfiles and leave the system
in the same state as before the installation. Since it does not install software, it will not remove
any software as well. ./config.json contains the configuration of theses dotfiles, it is required to
correctly uninstall the dotfiles.

## Software

Software I use regularly. The software on this list is available on linux, but some is also compatible with windows.

### GUI

- adw-gtk-theme: GTK3 theme with libadwaita look
- appimagelauncher: Integrate AppImages into the system
- mpv: media player
- moserial: serial monitor
- neovide: neovim gui with animations
- kitty: terminal emulator
- timeshift: btrfs snapshot manager
- Gnome Tweaks: more gnome settings
- Rnote: note taking app
- Flatseal: manage flatpak permissions
- Extension Manager: manage gnome extensions
- Black Box: terminal emulator
- Bottles: wine manager
- Inkscape: vector graphics editor
- Prusaslicer: 3d printer slicer
- Firefox: web browser
- Brave: web browser (chromium based)
- Kicad: schematic and pcb design
- Easyeffects: audio effects
- Vlc: media player
- Libreoffice: office suite
- Pikabackup: backup manager
- Qalculate (GTK): calculator
- File Roller: archive manager (GNOME)
- Ark: archive manager (KDE), more powerful than file roller
- REW: room acoustics measurement
- Joplin: text based note taking app
- Audacity: Basic audio editor
- Blender: 3d modeling and animation

### CLI

- bat: cat clone with syntax highlighting
- ripgrep: grep clone with better visuals and usability
- htop: interactive process viewer
- btop: htop clone with better visuals
- aria2: download manager
- exa: ls clone with better visuals
- fd: find clone with better visuals and usability
- fzf: fuzzy finder
- neofetch: system info
- ncdu: disk usage analyzer
- nvtop: (nvidia) gpu monitor
- powertop: power consumption monitor
- stress: basic stress test
- tldr: better man pages
- tmux: terminal multiplexer
- tokei: code statistics

### Development

- ninja: build system
- cmake: build system generator
- nodejs/npm: javascript runtime and package manager
- docker: containerization
- docker-compose: container orchestration
- rustup: up to date rust toolchain
- openocd: embedded debugging
- clang: c/c++ compiler
- stlink: stlink debugger
- stcubeide: stm microcontroller ide
- etcher: flash images to sd cards
- flutter: mobile app development
- esp-idf: esp32 development
- avrdude: avr programmer

### Windows

- winget: windows package manager
- scoop: windows package manager (does not require admin rights, more developer tools, remember to add buckets)
- WingetUI: GUI for windows package managers
- 7zip: archive manager
- teracopy: replace windows copy
- notepad++: text editor
- MusicBee: music player with good replaygain calculation
- mp3tag: tag editor
- windirstat: disk usage analyzer

## VSCode Plugins

- C/C++: C/C++ language support from Microsoft
- Material Theme: Material Theme for VSCode
- Copilot: AI code completion
- Matieral Icon Theme: Material Design Icons for Visual Studio Code
- rust extension pack: rust language support
- git graph: Display a git graph of your repository
- todo tree: Show TODO, FIXME, etc. comment tags of a project

## Device Specific

See [device_specific](/device_specific/README.md) for device specific configurations and notes for my personal devices.

## Notes (Linux)

To set environment variables for a user on X11, write them to ~/.profile with the following format:
```
export VAR=value
```
This will not work for wayland with gnome.
write them to ~/.config/environment.d/envvars.conf with the following format:
```
VAR=value
```
When using flatpak apps, just add the environment variables via Flatseal.

### Environment variables

For Firefox (and I think Thunderbird), set the following environment variables for wayland support:
```
MOZ_USE_XINPUT2=1
MOZ_ENABLE_WAYLAND=1
```

For neovide, set the following environment variables:
```
NEOVIDE_MULTIGRID=true
```

For development of GObject Introspection based libraries, set the following environment variables
(maybe use ~/.local/lib...?):
```
GI_TYPELIB_PATH=/usr/local/lib/girepository-1.0
```

For flutter development, set the following environment variables to not use Chrome (flatpak webbrowsers are as far as I know not supported):
```
CHROME_EXECUTABLE=brave
```

Maybe also set if using pyopengl (works on my intel integrated gpu):
```
PYOPENGL_PLATFORM=osmesa
```

## Awesome WM

I no longer use Awesome WM, but on very old systems it still works better than gnome. The configuration is not exactly
finished (especially the app picker), but it works.
It requres following software (some is optional): nm-applet, [Jonaburg's picom](https://github.com/jonaburg/picom), light-locker (with lightdm), unclutter, copyq, mate-volume-control-status-icon, blueman-applet, touchegg, polkit-gnome-authentication-agent-1, acpi
Maybe some more, but I don't remember.
