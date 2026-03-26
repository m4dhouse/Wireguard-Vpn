#!/usr/bin/env python3
# script created by madhouse

import sys
import os
import subprocess
import urllib.request


class C:
	RESET = "\033[0m"
	BOLD = "\033[1m"
	GREEN = "\033[92m"
	YELLOW = "\033[93m"
	RED = "\033[91m"
	CYAN = "\033[96m"
	WHITE = "\033[97m"


def run(cmd, check=True, capture=False):
	return subprocess.run(cmd, shell=True, check=check, capture_output=capture, text=True)

def run_out(cmd):
	result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
	return result.stdout.strip()

def check_kernel_version():
	print(f"{C.CYAN}[WireGuard VPN] Checking kernel version...{C.RESET}")
	required = (3, 10)
	raw = run_out("uname -r")
	parts = raw.split(".")
	current = (int(parts[0]), int(parts[1]))
	if current >= required:
		print(f"{C.GREEN}[WireGuard VPN] Kernel version check passed: {raw}{C.RESET}")
	else:
		print(f"{C.RED}[WireGuard VPN] Kernel version ({'.'.join(str(x) for x in current)}) is less than {'.'.join(str(x) for x in required)}.{C.RESET}")
		print(f"{C.RED}[WireGuard VPN] Installation aborted.{C.RESET}")
		sys.exit(1)

def check_internet_connection():
	print(f"{C.CYAN}[WireGuard VPN] Checking Internet connection...{C.RESET}")
	result = run("ping -c 1 8.8.8.8 > /dev/null 2>&1", check=False)
	if result.returncode == 0:
		print(f"{C.GREEN}[WireGuard VPN] Internet connection is OK.{C.RESET}")
	else:
		print(f"{C.RED}[WireGuard VPN] No Internet connection. Please check your network.{C.RESET}")
		sys.exit(1)

def get_python_minor():
	return sys.version_info.minor

def get_architecture():
	return run_out("uname -m")

def get_chipset_info():
	path = "/proc/stb/info/chipset"
	if os.path.isfile(path):
		with open(path) as f:
			return f.read().strip()
	return "unknown"

def get_distro_feed():
	result = run_out("awk '{ print $2 }' /etc/opkg/all-feed.conf | cut -d'-' -f1")
	return result

BRANCH_MAP = {
	14: "python-3.14",
	13: "python-3.13",
	12: "python-3.12",
	9:  "python-3.9",
}

SUPPORTED_DISTROS = {"egami", "openatv", "openvix", "openbh", "openhdf", "pure2", "opendroid", "openspa"}


def install_dependencies():
	print(f"{C.BOLD}{C.CYAN}====================================={C.RESET}")
	print(f"{C.BOLD}{C.CYAN}  Installing necessary dependencies  {C.RESET}")
	print(f"{C.BOLD}{C.CYAN}====================================={C.RESET}")
	packages = [
		"wireguard-tools",
		"wireguard-tools-bash-completion",
		"kernel-module-wireguard",
		"openresolv",
		"alsa-utils",
		"iptables",
		"python3-pillow",
	]
	run("opkg update", check=False)
	for pkg in packages:
		result = run(f"opkg install {pkg}", check=False)
		if result.returncode != 0:
			print(f"{C.YELLOW}[WireGuard VPN] Failed to install: {pkg} (skipping){C.RESET}")

	print(f"{C.GREEN}[WireGuard VPN] Dependencies installed successfully.{C.RESET}")


def check_existing_plugin():
	plugin_dir = "/usr/lib/enigma2/python/Plugins/Extensions/Wireguard"
	if os.path.isdir(plugin_dir):
		print(f"{C.YELLOW}[WireGuard VPN] WireGuard VPN plugin is already installed.{C.RESET}")
		with open("/dev/tty") as tty:
			sys.stdout.write(f"{C.WHITE}[WireGuard VPN] Do you want to reinstall it? [y/N]: {C.RESET}")
			sys.stdout.flush()
			answer = tty.readline().strip().lower()
		if answer != "y":
			print(f"{C.RED}[WireGuard VPN] Installation cancelled.{C.RESET}")
			sys.exit(0)


def main():
	check_kernel_version()
	check_internet_connection()

	python_minor = get_python_minor()
	architecture = get_architecture()
	chipset = get_chipset_info()

	base_branch = BRANCH_MAP.get(python_minor)
	if not base_branch:
		print(f"{C.RED}[WireGuard VPN] Unsupported Python version: 3.{python_minor}{C.RESET}")
		sys.exit(1)

	version_url = f"https://raw.githubusercontent.com/m4dhouse/Wireguard-Vpn/{base_branch}/version"
	version = urllib.request.urlopen(version_url).read().decode().strip()

	if architecture.startswith("arm"):
		if chipset == "hi3716mv430":
			ipk_filename = f"enigma2-plugin-extensions-wireguard-vpn-h82h_{version}_all.ipk"
		else:
			ipk_filename = f"enigma2-plugin-extensions-wireguard-vpn_{version}_all.ipk"
	elif architecture.startswith("mips"):
		ipk_filename = f"enigma2-plugin-extensions-wireguard-vpn-mips_{version}_all.ipk"
	elif architecture.startswith("aarch"):
		ipk_filename = f"enigma2-plugin-extensions-wireguard-vpn-aarch64_{version}_all.ipk"
	else:
		print(f"{C.RED}[WireGuard VPN] Unsupported architecture: {architecture}{C.RESET}")
		sys.exit(1)

	url_ipk = f"https://raw.githubusercontent.com/m4dhouse/Wireguard-Vpn/{base_branch}/{ipk_filename}"

	distro_feed = get_distro_feed()
	if distro_feed in SUPPORTED_DISTROS:
		install_dependencies()

	check_existing_plugin()

	print(f"{C.BOLD}{C.GREEN}====================================={C.RESET}")
	print(f"{C.BOLD}{C.GREEN}   I install WireGuard VPN plugin    {C.RESET}")
	print(f"{C.BOLD}{C.GREEN}        Written by Madhouse          {C.RESET}")
	print(f"{C.BOLD}{C.GREEN}====================================={C.RESET}")
	run(f"opkg --force-reinstall --force-overwrite --force-depends install {url_ipk}")
	print()
	print(f"{C.BOLD}{C.CYAN}===================================={C.RESET}")
	print(f"{C.BOLD}{C.CYAN}         Restarting enigma2         {C.RESET}")
	print(f"{C.BOLD}{C.CYAN}===================================={C.RESET}")
	run("init 4")
	run("init 3")

if __name__ == "__main__":
	main()
