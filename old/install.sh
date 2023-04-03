#!/usr/bin/env bash

set -e

sudo -v

install_themes() {
    # make sure ~/.profile exists
    if [ ! -f ~/.profile ]; then
        touch ~/.profile
    fi

    # add fontconfig
    mkdir -p ~/.config/fontconfig
    rm -rf ~/.config/fontconfig/fonts.conf
    ln -sf "$(realpath ./themes/fonts.conf)" ~/.config/fontconfig/fonts.conf

    # select qt4 theme
    rm -rf ~/.config/Trolltech.conf
    ln -sf "$(realpath ./themes/Trolltech.conf)" ~/.config/Trolltech.conf

    # select qt5 theme
    rm -rf ~/.config/qt5ct
    ln -sf "$(realpath ./themes/qt5ct)" ~/.config/qt5ct
    mkdir -p ~/.config/qt5ct/colors
    mkdir -p ~/.config/qt5ct/qss
    if ! grep -q "export QT_QPA_PLATFORMTHEME=qt5ct" ~/.profile; then
        echo "export QT_QPA_PLATFORMTHEME=qt5ct" >> ~/.profile
    fi
    kvantummanager --set MateriaLight

    # select gtk2 theme
    rm -rf ~/.gtkrc-2.0
    ln -sf "$(realpath ./themes/gtkrc-2.0)" ~/.gtkrc-2.0

    # select gtk3 theme
    mkdir -p ~/.config/gtk-3.0
    rm -rf ~/.config/gtk-3.0/settings.ini
    ln -sf "$(realpath ./themes/gtk-3.0-settings.ini)" ~/.config/gtk-3.0/settings.ini
    gsettings set org.gnome.desktop.interface gtk-theme "Materia-Light"
    gsettings set org.gnome.desktop.interface icon-theme "Papirus"
    gsettings set org.gnome.desktop.interface font-name 'Inter 11'
    gsettings set org.gnome.desktop.interface document-font-name 'Inter 11'
    gsettings set org.gnome.desktop.interface monospace-font-name 'MesloLGS NF 10'
}

install_lightdm_theme() {
    sudo cp -f ./themes/lightdm-bg.png /etc/lightdm/bg.png
    sudo chmod 644 /etc/lightdm/bg.png
    sudo cp -f ./themes/lightdm-gtk-greeter.conf /etc/lightdm/lightdm-gtk-greeter.conf
    sudo chmod 644 /etc/lightdm/lightdm-gtk-greeter.conf
    # todo add "greeter-session=lightdm-gtk-greeter"
}

install_picom() {
    rm -rf picom-git
    git clone --depth=1 https://github.com/jonaburg/picom picom-git
    cd picom-git
    meson --buildtype=release . build
    ninja -C build
    sudo ninja -C build install
    cd -
    rm -rf picom-git
}

case "$(uname -s)" in
  Darwin)
    echo "macOS is not supported"
    exit
    ;;
  Linux)
    if [ -f /etc/os-release ]; then
      . /etc/os-release
      case "$ID" in 
        debian | ubuntu | raspbian)
          OS="debian"
          ;;
        arch | archarm)
          OS="arch"
          ;;
        *)
          echo "Unsupported linux distro"
          exit
          ;;
      esac
    else
      echo "Unsupported linux distro"
      exit
    fi
    ;;
  *)
    echo "Unsupported OS"
    exit
    ;;
esac

print_help() {
    echo "Install dotfiles for the current system"
    echo "Options:"
    echo "  install [type] - installs all dotfiles to the system"
    echo "  basic-install - installs all dotfiles to the system, but without installing packages"
    echo "  update [type] - updates the system"
    echo "Installation types:"
    echo "  gui-legacy"
    echo "  gui"
    echo "  tui"
}
if [[ $# -ne 2 ]]; then
    print_help
    exit
fi
case "$1" in
    install | update)
        ;;
    *)
        print_help
        exit
esac
case "$2" in
    gui | tui | gui-legacy)
        TYPE="$2"
        ;;
    *)
        print_help
        exit
esac

if [[ "$1" == "install" ]]; then
    if [[ "$OS" == "debian" ]]; then
        echo "Installing packages for debian/ubuntu"

        sudo apt-get update
        sudo apt-get upgrade -y
        sudo apt-get install -y build-essential git curl wget gnupg
        sudo apt-get install -y clang lldb llvm neofetch nodejs npm python3 python3-pip zsh
        sudo apt-get install -y make ninja-build gettext libtool libtool-bin autoconf automake cmake g++ pkg-config unzip
        sudo apt-get install -y tmux ripgrep meson
        # todo install pamixer, pipewire, pipewire-pulse, light
        # themes, icons, fonts
        if [[ "$TYPE" == "gui" ]]; then
            sudo apt-get install -y xmonad libghc-xmonad-contrib-dev suckless-tools xmobar
        fi
        install_nvim
    elif [[ "$OS" == "arch" ]]; then
        echo "Installing packages for arch"

        sudo pacman -Syu --noconfirm
        sudo pacman -S --needed --noconfirm git base-devel curl wget gnupg
        sudo pacman -S --needed --noconfirm clang lldb llvm neofetch nodejs npm python python-pip zsh
        sudo pacman -S --needed --noconfirm make base-devel cmake unzip ninja tree-sitter
        sudo pacman -S --needed --noconfirm tmux ripgrep go tokei
        sudo pacman -S --needed --noconfirm neovim meson fzf htop acpi openssh
        which yay > /dev/null && echo "yay is allready installed" || install_yay
        if [[ "$TYPE" == "gui" || "$TYPE" == "gui-legacy" ]]; then
            sudo pacman -S --needed --noconfirm xorg xclip
            # backlight
            sudo pacman -S --needed --noconfirm light
            # install audio packages
            sudo pacman -S --needed --noconfirm pamixer pipewire pipewire-pulse wireplumber
            # picom make dependencies
            sudo pacman -S --needed --noconfirm libev uthash libconfig
            # fonts and themes
            sudo pacman -S --needed --noconfirm inter-font papirus-icon-theme
            # qt theming
            sudo pacman -S --needed --noconfirm kvantum-qt5 kvantum-theme-materia qt5ct
            # gtk theming
            sudo pacman -S --needed --noconfirm gsettings-desktop-schemas materia-gtk-theme
            # display manager
            sudo pacman -S --needed --noconfirm lightdm lightdm-gtk-greeter light-locker unclutter polkit-gnome
            # install packages for better touchscreen support
            sudo pacman -S --needed --noconfirm onboard iio-sensor-proxy
            # software
            sudo pacman -S --needed --noconfirm nemo nemo-preview nemo-share nemo-fileroller mpv evolution
            # applets
            sudo pacman -S --needed --noconfirm copyq mate-media blueman
        fi
        if [[ "$TYPE" == "gui-legacy" ]]; then
            sudo pacman -S --needed --noconfirm xterm
        fi
        if [[ "$TYPE" == "gui" ]]; then
            sudo pacman -S --needed --noconfirm kitty
        fi
    fi

    mkdir -p ~/.config

    [ -d $HOME/.oh-my-zsh ] && echo "oh-my-zsh is allready installed" || install_oh_my_zsh
    [ -d ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k ] && echo "powerlevel10k is allready installed" || install_p10k

    config_git
    config_nvim
    config_zsh
    config_tmux
    config_kitty
    config_starship

    if [[ "$TYPE" == "gui" || "$TYPE" == "gui-legacy" ]]; then
        config_onboard
        config_touchegg
        config_awesome
        config_xterm
        install_fonts
        # install_themes
        install_picom
        # install_lightdm_theme
    fi
    if [[ "$TYPE" == "gui-legacy" ]]; then
        config_picom_legacy
    fi
    if [[ "$TYPE" == "gui" ]]; then
        config_picom
    fi
elif [[ "$1" == "basic-install" ]]; then
    config_nvim
    config_zsh
    config_tmux
    config_kitty
    config_starship
    echo "This script will not install packages, manually install following packages:"
    echo "git clang neofetch npm nodejs python python-pip zsh cmake ninja tmux neovim meson htop btop fzf kitty"
    echo "Cargo packages: ripgrep, tokei, bat, starship, neovide"
elif [[ "$1" == "update" ]]; then
    if [[ "$OS" == "debian" ]]; then
        echo "Updating packages for debian/ubuntu"

        sudo apt-get update
        sudo apt-get upgrade -y
        install_nvim
    elif [[ "$OS" == "arch" ]]; then
        echo "Updating packages for arch"

        sudo pacman -Syu --noconfirm
    fi

    update_oh_my_zsh
    config_nvim
fi
# TODO:
# add user to video group for light
# install xf86-video-intel for intel graphics
# enable lightdm

