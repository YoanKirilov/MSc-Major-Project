from app.scanner.commands import discovery_command, host_command


def test_commands_are_fixed_argument_lists():
    assert discovery_command("/usr/bin/nmap", "192.168.56.0/24") == ["/usr/bin/nmap", "-sn", "-n", "-oX", "-", "192.168.56.0/24"]
    command = host_command("/usr/bin/nmap", "192.168.56.10")
    assert command[0] == "/usr/bin/nmap"
    assert "-sT" in command
    assert "-sU" not in command
    assert "--script" not in command
    assert command[-1] == "192.168.56.10"
