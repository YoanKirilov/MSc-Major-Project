"""Classify scanner failures without exposing arbitrary stderr or device banners."""


def process_failure(result):
    if result.cancelled:
        return "HOST_SCAN_CANCELLED"
    if result.overflow:
        return "HOST_OUTPUT_LIMIT"
    if result.timed_out:
        return "HOST_SCAN_TIMEOUT"
    if result.returncode:
        error = result.stderr[:8192].lower()
        if any(
            word in error
            for word in (
                b"requires root",
                b"require root",
                b"requires privileged",
                b"permission denied",
                b"administrator privileges",
            )
        ):
            return "HOST_PRIVILEGE_REQUIRED"
        if any(word in error for word in (b"npcap", b"winpcap", b"failed to open device")):
            return "HOST_DRIVER_UNAVAILABLE"
        return "HOST_SCAN_FAILED"
    return None


FAILURE_ADVICE = {
    "HOST_PRIVILEGE_REQUIRED": (
        "The scanner lacks permission for the selected checks. Check the Nmap setup; "
        "do not expose or run the web server as an administrator."
    ),
    "HOST_DRIVER_UNAVAILABLE": (
        "Nmap could not use its packet-capture driver or network adapter. "
        "Check Npcap and the selected adapter in Settings."
    ),
}
