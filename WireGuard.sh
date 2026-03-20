#!/bin/sh
# shell created by madhouse

check_kernel_version() {
  echo "[WireGuard] Checking kernel version..."
  required_version="3.10"
  current_version=$(uname -r | cut -d. -f1-2)

  compare_versions() {
    local v1=$(echo "$1" | awk -F. '{printf("%d%03d\n", $1, $2)}')
    local v2=$(echo "$2" | awk -F. '{printf("%d%03d\n", $1, $2)}')

    if [ "$v1" -ge "$v2" ]; then
      return 0
    else
      return 1
    fi
  }

  if compare_versions "$current_version" "$required_version"; then
    echo "[WireGuard] Kernel version check passed: $current_version"
  else
    echo "[WireGuard] Kernel version ($current_version) is less than $required_version."
    echo "[WireGuard] Installation aborted."
    exit 1
  fi
}

check_internet_connection() {
  echo "Checking Internet connection..."
  if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "Internet connection is OK."
  else
    echo "No Internet connection. Please check your network."
    exit 1
  fi
}

check_kernel_version

check_internet_connection

PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info.minor)")
ARCHITECTURE=$(uname -m)

case $PYTHON_VERSION in
  14)
    BASE_BRANCH='python-3.14'
    ;;
  13)
    BASE_BRANCH='python-3.13'
    ;;
  12)
    BASE_BRANCH='python-3.12'
    ;;
  9)
    BASE_BRANCH='python-3.9'
    ;;
  *)
    echo "Unsupported Python version: $PYTHON_VERSION"
    exit 1
    ;;
esac

get_chipset_info() {
  if [ -f "/proc/stb/info/chipset" ]; then
    cat /proc/stb/info/chipset
  else
    echo "unknown"
  fi
}

install_dependencies() {
  echo '====================================='
  echo '  Installing necessary dependencies  '
  echo '====================================='
  opkg update
  opkg install wireguard-tools
  opkg install wireguard-tools-bash-completion
  opkg install kernel-module-wireguard
  opkg install openresolv
  opkg install alsa-utils
  opkg install iptables
  opkg install python3-pillow
  if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    exit 1
  fi
  echo "Dependencies installed successfully."
}

CHIPSET=$(get_chipset_info)

RAW_URL_VERSION="https://raw.githubusercontent.com/m4dhouse/Wireguard-Vpn/$BASE_BRANCH/version"
VERSION=$(python3 -c "import urllib.request; print(urllib.request.urlopen('$RAW_URL_VERSION').read().decode())")

case $ARCHITECTURE in
  arm*)
    if [ "$CHIPSET" == "hi3716mv430" ]; then
      URL_IPK="https://raw.githubusercontent.com/m4dhouse/Wireguard-Vpn/$BASE_BRANCH/enigma2-plugin-extensions-wireguard-vpn-h82h_${VERSION}_all.ipk"
    else
      URL_IPK="https://raw.githubusercontent.com/m4dhouse/Wireguard-Vpn/$BASE_BRANCH/enigma2-plugin-extensions-wireguard-vpn_${VERSION}_all.ipk"
    fi
    ;;
  mips*)
    URL_IPK="https://raw.githubusercontent.com/m4dhouse/Wireguard-Vpn/$BASE_BRANCH/enigma2-plugin-extensions-wireguard-vpn-mips_${VERSION}_all.ipk"
    ;;
  aarch*)
    URL_IPK="https://raw.githubusercontent.com/m4dhouse/Wireguard-Vpn/$BASE_BRANCH/enigma2-plugin-extensions-wireguard-vpn-aarch64_${VERSION}_all.ipk"
    ;;
  *)
    echo "Unsupported architecture: $ARCHITECTURE"
    exit 1
    ;;
esac

DISTRO_FEED=$(awk '{ print $2 }' /etc/opkg/all-feed.conf | cut -d'-' -f1)
SUPPORTED_DISTRO=("egami" "openatv" "openvix" "openbh" "openhdf" "pure2" "opendroid" "openspa")

if [[ " ${SUPPORTED_DISTRO[@]} " =~ " ${DISTRO_FEED} " ]]; then
  install_dependencies
fi

echo '====================================='
echo '   I install WireGuard VPN plugin    '
echo '        Written by Madhouse          '
echo '====================================='
opkg --force-reinstall --force-overwrite --force-depends install $URL_IPK
echo ''
echo '===================================='
echo '         Restarting enigma2         '
echo '===================================='
init 4
init 3
exit 0
