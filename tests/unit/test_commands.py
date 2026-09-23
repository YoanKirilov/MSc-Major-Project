from app.scanner.commands import (
    DEEP_PROFILE,
    DEEP_SAFE_SCRIPTS,
    DEEP_UDP_PORTS,
    LIGHT_SAFE_SCRIPTS,
    PORTS,
    UDP_PORTS,
    discovery_command,
    host_command,
)


def test_commands_are_fixed_argument_lists():
    assert discovery_command("/usr/bin/nmap", "192.168.56.0/24") == [
        "/usr/bin/nmap", "-sn", "-n", "-oX", "-", "192.168.56.0/24"
    ]
    command = host_command("/usr/bin/nmap", "192.168.56.10")
    assert command[0] == "/usr/bin/nmap"
    assert "-sT" in command
    assert "-sU" in command
    assert command[command.index("--script") + 1] == LIGHT_SAFE_SCRIPTS
    light_ports = f"T:{','.join(str(port) for port in PORTS)},U:{','.join(str(port) for port in UDP_PORTS)}"
    assert command[command.index("-p") + 1] == light_ports
    assert command[-1] == "192.168.56.10"
    assert len(PORTS) == 12
    assert len(UDP_PORTS) == 3
    assert {53, 161, 1900}.issubset(UDP_PORTS)
    deep_command = host_command("/usr/bin/nmap", "192.168.56.10", DEEP_PROFILE)
    assert "-sT" in deep_command and "-sU" in deep_command
    deep_ports = f"T:1-65535,U:{','.join(str(port) for port in DEEP_UDP_PORTS)}"
    assert deep_command[deep_command.index("-p") + 1] == deep_ports
    assert "--version-all" in deep_command
    assert deep_command[deep_command.index("--script") + 1] == DEEP_SAFE_SCRIPTS
    assert "broadcast" not in DEEP_SAFE_SCRIPTS

    discovery_with_interface = discovery_command(
        "/usr/bin/nmap", "192.168.56.0/24", "eth0"
    )
    assert discovery_with_interface[-5:] == [
        "-e", "eth0", "-oX", "-", "192.168.56.0/24"
    ]
    host_with_interface = host_command(
        "/usr/bin/nmap", "192.168.56.10", interface="eth0"
    )
    assert host_with_interface[host_with_interface.index("-e") + 1] == "eth0"
