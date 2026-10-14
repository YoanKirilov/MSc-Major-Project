"""Reviewed equivalents, bound to exact source sentences.

Ollama selects wording; it cannot invent factual claims or device instructions.
An unrecognised/changed source has no approved alternative and stays unchanged.
These pairs are editorial choices, not an automated readability score.
Changes to approved alternatives require a PROMPT_VERSION bump to invalidate cached AI wording.
"""

REVIEWED_WORDING = {
    "Telnet service identified": "Older remote control found (Telnet)",
    "FTP service identified": "File transfer found (FTP)",
    "HTTP service identified": "Device web page found (HTTP)",
    "Remote desktop service reachable locally": "Remote desktop answered on your local network",
    "File-sharing service reachable locally": "File sharing answered on your local network",
    "MQTT service reachable locally": "Smart-home messaging found (MQTT)",
    "Service found; review its purpose": "Check what this connection is used for",
    ("This device offers an older remote-control service called Telnet on your local network."): (
        "This device has a feature called Telnet. It is an older way to "
        "control the device from another computer on your local network."
    ),
    ("This device offers an FTP service for moving files across your local network."): (
        "This device has a feature called FTP for sending and receiving "
        "files on your local network."
    ),
    "This device offers a web page over HTTP on your local network.": (
        "This device has a web page you can reach from your local network. "
        "It answered using HTTP, a type of web connection."
    ),
    ("A remote-control connection for this device answered on your local network."): (
        "This device answered a request to its remote-control feature on "
        "your local network. Remote control lets someone use a device from "
        "another computer."
    ),
    ("This device offers a file-sharing connection on your local network."): (
        "This device has a feature for sharing files with other devices on your local network."
    ),
    ("This device offers a messaging service that smart-home devices may use."): (
        "This device has a messaging feature that smart-home devices may "
        "use to communicate with each other."
    ),
    (
        "A connection on this device answered. No specific security "
        "assessment is available for this service."
    ): (
        "The device replied to this check. This tool does not test the "
        "security of this feature, so its safety is unknown."
    ),
    (
        "Telnet normally sends management information without encryption. "
        "This scan did not try to sign in or check who can use it."
    ): (
        "Telnet normally sends control information without scrambling it "
        "for protection. This scan did not try signing in or check who can "
        "use it."
    ),
    (
        "Basic FTP may send file contents or sign-in details without "
        "encryption. This scan did not check whether a protected "
        "alternative is available."
    ): (
        "Basic FTP may send files or sign-in details without scrambling "
        "them for protection. This scan did not check for a protected "
        "alternative."
    ),
    (
        "HTTP itself does not encrypt traffic. The scan did not check "
        "whether the page redirects to a protected HTTPS connection."
    ): (
        "HTTP does not scramble information for protection. This scan did "
        "not check whether the page switches to a protected HTTPS "
        "connection."
    ),
    (
        "HTTP itself does not encrypt traffic. Device details show any optional "
        "redirect check recorded for this port. A redirect alone does not "
        "establish that every page uses HTTPS."
    ): (
        "HTTP does not scramble information to protect it while it travels. "
        "Any saved check for a switch to HTTPS concerns only the starting page, "
        "not all pages."
    ),
    (
        "Someone with permission may be able to control the device from "
        "another computer. This scan did not test sign-in or access rules."
    ): (
        "Someone with permission may control this device from another "
        "computer. This scan did not test signing in or who is allowed to "
        "connect."
    ),
    (
        "Shared folders can be useful, but they should be available only "
        "to the people you choose. This scan did not check folder "
        "permissions."
    ): (
        "Shared folders can be useful. Only people you choose should have "
        "access. This scan did not check who is allowed to open them."
    ),
    (
        "The service lets devices exchange messages. This scan did not "
        "check who may connect or whether those messages are protected."
    ): (
        "Devices use this service to exchange messages. This scan did not "
        "check who may connect or whether the messages are protected."
    ),
    (
        "This may be normal for the device. Check what the connection is "
        "for before deciding whether it needs a change."
    ): (
        "This may be ordinary behaviour for the device. Find out what the "
        "feature does before changing any settings."
    ),
    (
        "This is a local observation from the selected service profile only."
    ): "Only the selected checks on your local network were used.",
    "No credentials or login attempts were performed.": (
        "The scan did not try any sign-in details or attempt to sign in."
    ),
    "The scan did not validate encrypted transfer support.": (
        "The scan did not check whether protected file transfer is supported."
    ),
    "The scan did not test HTTPS redirection or page purpose.": (
        "The scan did not check whether the page switches to HTTPS or what it is for."
    ),
    (
        "Any recorded redirect check covers only the root page at scan time. "
        "The scan did not establish the page's purpose or protection of other pages."
    ): (
        "Any saved check for a switch to HTTPS covers only the starting page when scanned. "
        "The scan did not confirm what the page is for or whether other pages are protected."
    ),
    ("This scan did not test credentials, exposure, or user permissions."): (
        "This scan did not test sign-in details, wider access to the "
        "service, or who is allowed to use it."
    ),
    "SMB version and permissions were not established by this scan.": (
        "The scan did not establish which version of SMB file sharing is "
        "used, or who is allowed to use it."
    ),
    "Shared-folder permissions and Internet exposure were not established by this scan.": (
        "The scan did not check who can open shared folders or whether the service "
        "can be reached from the Internet."
    ),
    "The scan did not verify authentication or encryption settings.": (
        "The scan did not check sign-in requirements or settings for protecting messages."
    ),
    "An open connection alone does not establish a security weakness.": (
        "A connection answering does not, by itself, mean there is a security problem."
    ),
    ("Check the device's settings or manual to see whether Telnet is needed."): (
        "Check the settings or manual to find out whether this device needs Telnet."
    ),
    ("If you need remote control, look for a protected option recommended by the manufacturer."): (
        "If you need remote control, look for a protected option recommended by the device maker."
    ),
    ("If you do not use it, ask the owner or manufacturer how to turn it off safely."): (
        "If you do not use it, ask the owner or device maker how to turn it off safely."
    ),
    "Confirm that option works before disabling the old one.": (
        "Check that the new option works before turning off the old one."
    ),
    ("If you still need file transfer, look for a protected option supported by the device."): (
        "If you still need to move files, look for a protected option the device supports."
    ),
    "Confirm the new option works before removing the old one.": (
        "Check that the new option works before removing the old one."
    ),
    ("Look for https:// at the start of the address; ask the manufacturer if you are unsure."): (
        "Look for https:// at the start of the address. Ask the device maker if you are unsure."
    ),
    "Review the feature's access settings or manufacturer guidance.": (
        "Check who can use this feature in its settings or the device maker's instructions."
    ),
    "Ask the manufacturer or installer if the setting is unclear.": (
        "Ask the device maker or installer if you are unsure about this setting."
    ),
    ("Ask the manufacturer or someone who manages the device if you are unsure."): (
        "Ask the device maker or the person who manages it if you are unsure."
    ),
    "Check whether you still use this device to move files by FTP.": (
        "Check whether you use FTP, the file-transfer feature, on this device."
    ),
    ("If not, check its settings or manual for a safe way to turn that feature off."): (
        "If you do not use it, look in the device settings or manual for how to turn it off safely."
    ),
    ("Open the device's web page and check whether its address changes to HTTPS."): (
        "Open the device's web page. Check whether the address starts with "
        "https://, which indicates a protected web connection."
    ),
    ("Check whether this device is meant to offer a web page on your home network."): (
        "Check whether this device is supposed to have a web page available on your home network."
    ),
    ("Use the device's manual or settings to confirm what the page is for."): (
        "Look in the device manual or settings to find out what the page does."
    ),
    ("Check whether anyone in your household is meant to control this device remotely."): (
        "Check whether anyone in your household needs to use this device from another computer."
    ),
    ("If not, check the device's settings for a safe way to turn remote access off."): (
        "If nobody needs this feature, check the device settings for how "
        "to turn remote control off safely."
    ),
    "If remote access is needed, limit it to people you trust.": (
        "If you need remote control, allow only people you trust to use it."
    ),
    "Check the device's account and access settings with its owner.": (
        "With the device owner, check which accounts are allowed to connect."
    ),
    "Check which folders this device is set up to share.": (
        "Check which folders this device makes available to other devices."
    ),
    "Compare them with the folders you intended to share.": (
        "Make sure these are the folders you meant to share."
    ),
    "Limit shared-folder access to people who need it.": (
        "Allow only the people who need the shared folders to open them."
    ),
    "Review the sharing settings with the device's owner.": (
        "Ask the device owner to check the file-sharing settings with you."
    ),
    ("Check which smart-home devices are allowed to use this messaging feature."): (
        "Check which smart-home devices have permission to use this feature to exchange messages."
    ),
    "Check whether the feature offers a protected connection.": (
        "Check whether this feature has an option to protect the information it sends."
    ),
    "Check whether this connection is expected for the device.": (
        "Check whether the device is supposed to offer this connection."
    ),
    "Compare it with the device's manual or ask its owner.": (
        "Look for the feature in the device manual, or ask the owner whether it is needed."
    ),
    (
        "Find out which feature uses the connection before changing settings."
    ): "Find out what this connection does before changing any settings.",
}

REVIEWED_WORDING.update(
    {
        "Older SMBv1 file sharing is supported": "Older file sharing answered (SMBv1)",
        (
            "This device accepted SMBv1, an older file-sharing protocol, during this local check."
        ): "This device answered using SMBv1, an older way to share files on your local network.",
        (
            "SMBv1 lacks protections available in newer file-sharing versions. This scan did not "
            "test whether any weakness can be exploited or which devices still use it."
        ): (
            "SMBv1 lacks protections found in newer ways to share files. The scan did not "
            "test whether a weakness could be used or which devices still need it."
        ),
        (
            "Support was observed at scan time on the associated local connection; this does "
            "not establish Internet exposure."
        ): (
            "This result describes the local connection when scanned. It does not tell us "
            "whether the feature can be reached from the Internet."
        ),
        (
            "The check negotiated a protocol only; it did not sign in, inspect files, "
            "or test an exploit."
        ): (
            "The check only asked which file-sharing version the device accepts. It did not "
            "sign in, read files, or try to use a security weakness."
        ),
        "An incomplete or absent SMB result cannot establish that SMBv1 is disabled.": (
            "If this check is missing or unfinished, it cannot tell us that SMBv1 is turned off."
        ),
        ("Check the device's manual or ask its owner whether older devices still require SMBv1."): (
            "Check the manual or ask the owner whether any older device still needs "
            "SMBv1 file sharing."
        ),
        ("Confirm those devices can use a newer file-sharing version before changing settings."): (
            "Check that those devices can share files using a newer version "
            "before changing settings."
        ),
        (
            "Ask the owner or device maker how to turn off SMBv1 while keeping "
            "newer file sharing available."
        ): (
            "Ask the owner or device maker how to turn off SMBv1 "
            "and keep newer file sharing working."
        ),
        (
            "After an authorised change, run another Deep check; a missing response "
            "does not prove the setting changed."
        ): (
            "After a change approved by the owner, repeat the Deep check. A device not replying "
            "does not prove that its setting changed."
        ),
        "SMB message signing is not required": (
            "File sharing does not require message signing (SMB)"
        ),
        (
            "During this check, the device did not require message signing "
            "for the negotiated SMB version."
        ): (
            "For the SMB file-sharing version used in this check, the device did not require "
            "messages to be signed."
        ),
        (
            "Signing helps detect changes to file-sharing messages. A server that does not "
            "require it may accept unsigned connections; this scan did not establish "
            "whether ordinary connections are signed."
        ): (
            "Message signing helps detect changes to file-sharing messages. This device may "
            "accept unsigned connections; the scan did not check whether the connections "
            "you normally use are signed."
        ),
        (
            "Only the negotiated SMB version was checked; other versions and client "
            "settings were not established."
        ): (
            "Only the SMB version used in this check was assessed. Other versions and the "
            "settings on connecting computers were not checked."
        ),
        "Signing concerns message integrity, not encryption or shared-folder permissions.": (
            "Signing helps detect changed messages. It does not scramble file contents "
            "or decide who can open shared folders."
        ),
        (
            "This was a local negotiation check; no tampering, credential relay, "
            "or Internet exposure was tested."
        ): (
            "This check stayed on your local network. It did not try changing messages, "
            "misusing sign-in details, or reaching the device from the Internet."
        ),
        (
            "Check the file-sharing settings or ask the device maker whether "
            "SMB signing can be required."
        ): (
            "Check the settings or ask the device maker whether file sharing "
            "can require SMB signing."
        ),
        (
            "Check that the computers using the shared folders support signing "
            "before changing this setting."
        ): (
            "Before changing this setting, check that the computers using your shared "
            "folders can sign messages."
        ),
        (
            "Ask the owner to enable required signing using the device maker's "
            "instructions if supported."
        ): (
            "If the device supports it, ask the owner to require message signing "
            "by following the device maker's instructions."
        ),
        (
            "After an authorised change, confirm file sharing still works "
            "and repeat the Deep check."
        ): (
            "After a change approved by the owner, check that file sharing still works "
            "and run the Deep check again."
        ),
    }
)


def wording_choices(original: str) -> list[str]:
    alternative = REVIEWED_WORDING.get(original)
    return [original, alternative] if alternative else [original]
