"""Network interface auto-detection for robot communication."""

from __future__ import annotations

import fcntl
import os
import socket
import struct

# Known robot subnets: (network_prefix, robot_description)
_KNOWN_SUBNETS: dict[str, str] = {
    "192.168.123.": "Unitree G1/H1",
    "192.168.10.": "Booster T1",
}

# Interface name prefixes to skip during auto-detection
_SKIP_PREFIXES = ("lo", "wl", "docker", "br-", "veth", "virbr", "vnet", "tun", "tap")

# ioctl constant for getting interface address
_SIOCGIFADDR = 0x8915


def _get_ipv4_address(ifname: str) -> str | None:
    """Get the IPv4 address of a network interface using ioctl.

    Args:
        ifname: Network interface name (e.g., "eth0").

    Returns:
        IPv4 address string, or None if the interface has no IPv4 address.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        result = fcntl.ioctl(
            sock.fileno(),
            _SIOCGIFADDR,
            struct.pack("256s", ifname.encode("utf-8")[:15]),
        )
        return socket.inet_ntoa(result[20:24])
    except OSError:
        return None
    finally:
        sock.close()


def _is_interface_up(ifname: str) -> bool:
    """Check if a network interface is operationally up.

    Args:
        ifname: Network interface name.

    Returns:
        True if the interface operstate is "up".
    """
    operstate_path = f"/sys/class/net/{ifname}/operstate"
    try:
        with open(operstate_path) as f:
            return f.read().strip().lower() == "up"
    except OSError:
        return False


def _should_skip(ifname: str) -> bool:
    """Check if an interface should be skipped during auto-detection.

    Args:
        ifname: Network interface name.

    Returns:
        True if the interface matches a skip prefix.
    """
    return any(ifname.startswith(prefix) for prefix in _SKIP_PREFIXES)


def _match_subnet(ip_addr: str) -> str | None:
    """Match an IP address against known robot subnets.

    Args:
        ip_addr: IPv4 address string.

    Returns:
        Robot description string if matched, None otherwise.
    """
    for prefix, description in _KNOWN_SUBNETS.items():
        if ip_addr.startswith(prefix):
            return description
    return None


def detect_robot_interface(robot_type: str | None = None) -> str:
    """Auto-detect the network interface connected to a robot.

    Scans wired network interfaces that are operationally UP and have an
    IPv4 address. Uses known robot subnets to identify the correct interface.

    Known subnets:
        - ``192.168.123.x`` → Unitree G1/H1
        - ``192.168.10.x``  → Booster T1

    Args:
        robot_type: Optional robot type hint (e.g., "g1", "t1") used to
            prefer a specific subnet when multiple candidates exist.

    Returns:
        Network interface name (e.g., ``"eth0"``, ``"enp132s0"``).

    Raises:
        RuntimeError: If no suitable interface is found or the result is
            ambiguous (multiple candidates with no way to disambiguate).
    """
    # Map robot types to expected subnet prefixes
    robot_subnet_hint: dict[str, str] = {
        "g1": "192.168.123.",
        "h1": "192.168.123.",
        "h1_2": "192.168.123.",
        "go2": "192.168.123.",
        "t1": "192.168.10.",
    }

    try:
        all_interfaces = os.listdir("/sys/class/net/")
    except OSError as e:
        raise RuntimeError(f"Cannot list network interfaces: {e}") from e

    # Collect candidate interfaces: (name, ip_address, subnet_match_description)
    candidates: list[tuple[str, str, str | None]] = []

    for ifname in sorted(all_interfaces):
        if _should_skip(ifname):
            continue
        if not _is_interface_up(ifname):
            continue
        ip_addr = _get_ipv4_address(ifname)
        if ip_addr is None:
            continue
        subnet_match = _match_subnet(ip_addr)
        candidates.append((ifname, ip_addr, subnet_match))

    if not candidates:
        raise RuntimeError(
            "No suitable wired network interface found. "
            "Ensure a wired NIC is UP and has an IPv4 address, "
            "or specify the interface explicitly (e.g., --interface eth0)."
        )

    # Filter by robot type hint if provided
    if robot_type is not None:
        hint_prefix = robot_subnet_hint.get(robot_type.lower())
        if hint_prefix:
            hinted = [c for c in candidates if c[1].startswith(hint_prefix)]
            if hinted:
                chosen = hinted[0]
                print(
                    f"[network] Auto-detected interface '{chosen[0]}' "
                    f"(ip={chosen[1]}, subnet={chosen[2]}) "
                    f"for robot_type='{robot_type}'"
                )
                return chosen[0]

    # Filter to candidates on known robot subnets
    on_robot_subnet = [c for c in candidates if c[2] is not None]

    if len(on_robot_subnet) == 1:
        chosen = on_robot_subnet[0]
        print(
            f"[network] Auto-detected interface '{chosen[0]}' "
            f"(ip={chosen[1]}, subnet={chosen[2]})"
        )
        return chosen[0]

    if len(on_robot_subnet) > 1:
        details = ", ".join(f"{c[0]}={c[1]} ({c[2]})" for c in on_robot_subnet)
        raise RuntimeError(
            f"Multiple interfaces on known robot subnets: {details}. "
            f"Specify the interface explicitly (e.g., --interface eth0) "
            f"or provide robot_type to disambiguate."
        )

    # No known subnet match — fall back to single wired NIC heuristic
    if len(candidates) == 1:
        chosen = candidates[0]
        print(
            f"[network] Auto-detected interface '{chosen[0]}' "
            f"(ip={chosen[1]}, no known robot subnet match — only wired NIC found)"
        )
        return chosen[0]

    # Multiple candidates, none on known subnets
    details = ", ".join(f"{c[0]}={c[1]}" for c in candidates)
    raise RuntimeError(
        f"Multiple wired interfaces found but none on a known robot subnet: {details}. "
        f"Specify the interface explicitly (e.g., --interface eth0)."
    )
