RULESET_VERSION = "1.3.0"

RULE_CATALOGUE = {
    "R01": {
        "title": "Telnet service identified",
        "meaning": (
            "This device offers an older remote-control service called Telnet "
            "on your local network."
        ),
        "why_it_matters": (
            "Telnet normally sends management information without encryption. "
            "This scan did not try to sign in or check who can use it."
        ),
        "severity": "high",
        "confidence": "medium",
        "limitations": [
            "This is a local observation from the selected service profile only.",
            "No credentials or login attempts were performed.",
        ],
        "actions": [
            {
                "action_id": "review_service_need",
                "text": "Check the device's settings or manual to see whether Telnet is needed.",
                "verification": (
                    "If you do not use it, ask the owner or manufacturer how to turn it off safely."
                ),
            },
            {
                "action_id": "use_secure_alternative",
                "text": (
                    "If you need remote control, look for a protected option "
                    "recommended by the manufacturer."
                ),
                "verification": "Confirm that option works before disabling the old one.",
            },
        ],
        "references": [
            {
                "title": "CISA guidance on unused and plaintext services",
                "url": "https://www.cisa.gov/resources-tools/resources/enhanced-visibility-and-hardening-guidance-communications-infrastructure",
            }
        ],
        "version": "1.1.0",
        "rule_id": "R01",
    },
    "R02": {
        "title": "FTP service identified",
        "meaning": "This device offers an FTP service for moving files across your local network.",
        "why_it_matters": (
            "Basic FTP may send file contents or sign-in details without "
            "encryption. This scan did not check whether a protected "
            "alternative is available."
        ),
        "severity": "medium",
        "confidence": "medium",
        "limitations": ["The scan did not validate encrypted transfer support."],
        "actions": [
            {
                "action_id": "review_service_need",
                "text": "Check whether you still use this device to move files by FTP.",
                "verification": (
                    "If not, check its settings or manual for a safe way to turn that feature off."
                ),
            },
            {
                "action_id": "prefer_encrypted_transfer",
                "text": (
                    "If you still need file transfer, look for a protected option "
                    "supported by the device."
                ),
                "verification": "Confirm the new option works before removing the old one.",
            },
        ],
        "references": [
            {
                "title": "CISA guidance on unused and plaintext services",
                "url": "https://www.cisa.gov/resources-tools/resources/enhanced-visibility-and-hardening-guidance-communications-infrastructure",
            }
        ],
        "version": "1.1.0",
        "rule_id": "R02",
    },
    "R03": {
        "title": "HTTP service identified",
        "meaning": "This device offers a web page over HTTP on your local network.",
        "why_it_matters": (
            "HTTP itself does not encrypt traffic. Device details show any optional "
            "redirect check recorded for this port. A redirect alone does not "
            "establish that every page uses HTTPS."
        ),
        "severity": "low",
        "confidence": "medium",
        "limitations": [
            "Any recorded redirect check covers only the root page at scan time. "
            "The scan did not establish the page's purpose or protection of other pages."
        ],
        "actions": [
            {
                "action_id": "check_https",
                "text": (
                    "Open the device's web page and check whether its address changes to HTTPS."
                ),
                "verification": (
                    "Look for https:// at the start of the address; ask the "
                    "manufacturer if you are unsure."
                ),
            },
            {
                "action_id": "review_web_exposure",
                "text": (
                    "Check whether this device is meant to offer a web page on your home network."
                ),
                "verification": (
                    "Use the device's manual or settings to confirm what the page is for."
                ),
            },
        ],
        "references": [
            {
                "title": "MDN explanation of HTTP and HTTPS",
                "url": "https://developer.mozilla.org/en-US/docs/Glossary/HTTP",
            }
        ],
        "version": "1.1.1",
        "rule_id": "R03",
    },
    "R04": {
        "title": "Remote desktop service reachable locally",
        "meaning": "A remote-control connection for this device answered on your local network.",
        "why_it_matters": (
            "Someone with permission may be able to control the device from "
            "another computer. This scan did not test sign-in or access rules."
        ),
        "severity": "medium",
        "confidence": "medium",
        "limitations": ["This scan did not test credentials, exposure, or user permissions."],
        "actions": [
            {
                "action_id": "review_service_need",
                "text": (
                    "Check whether anyone in your household is meant to control this "
                    "device remotely."
                ),
                "verification": (
                    "If not, check the device's settings for a safe way to turn remote access off."
                ),
            },
            {
                "action_id": "restrict_access",
                "text": "If remote access is needed, limit it to people you trust.",
                "verification": "Check the device's account and access settings with its owner.",
            },
        ],
        "references": [
            {
                "title": "Microsoft Remote Desktop access guidance",
                "url": "https://learn.microsoft.com/windows-server/remote/remote-desktop-services/remotepc/remote-desktop-allow-access",
            }
        ],
        "version": "1.1.0",
        "rule_id": "R04",
    },
    "R05": {
        "title": "File-sharing service reachable locally",
        "meaning": "This device offers a file-sharing connection on your local network.",
        "why_it_matters": (
            "Shared folders can be useful, but they should be available only "
            "to the people you choose. This scan did not check folder "
            "permissions."
        ),
        "severity": "medium",
        "confidence": "medium",
        "limitations": [
            "Shared-folder permissions and Internet exposure were not established by this scan."
        ],
        "actions": [
            {
                "action_id": "review_sharing",
                "text": "Check which folders this device is set up to share.",
                "verification": "Compare them with the folders you intended to share.",
            },
            {
                "action_id": "check_permissions",
                "text": "Limit shared-folder access to people who need it.",
                "verification": "Review the sharing settings with the device's owner.",
            },
        ],
        "references": [
            {
                "title": "Microsoft guidance on secure file sharing",
                "url": "https://learn.microsoft.com/en-us/windows-server/storage/file-server/smb-secure-traffic",
            }
        ],
        "version": "1.1.1",
        "rule_id": "R05",
    },
    "R06": {
        "title": "MQTT service reachable locally",
        "meaning": "This device offers a messaging service that smart-home devices may use.",
        "why_it_matters": (
            "The service lets devices exchange messages. This scan did not "
            "check who may connect or whether those messages are protected."
        ),
        "severity": "medium",
        "confidence": "medium",
        "limitations": ["The scan did not verify authentication or encryption settings."],
        "actions": [
            {
                "action_id": "verify_auth",
                "text": "Check which smart-home devices are allowed to use this messaging feature.",
                "verification": "Review the feature's access settings or manufacturer guidance.",
            },
            {
                "action_id": "check_encryption",
                "text": "Check whether the feature offers a protected connection.",
                "verification": "Ask the manufacturer or installer if the setting is unclear.",
            },
        ],
        "references": [{"title": "MQTT security overview", "url": "https://mqtt.org/"}],
        "version": "1.1.0",
        "rule_id": "R06",
    },
    "R07": {
        "title": "Service found; review its purpose",
        "meaning": (
            "A connection on this device answered. No specific security "
            "assessment is available for this service."
        ),
        "why_it_matters": (
            "This may be normal for the device. Check what the connection is "
            "for before deciding whether it needs a change."
        ),
        "severity": "informational",
        "confidence": "low",
        "limitations": ["An open connection alone does not establish a security weakness."],
        "actions": [
            {
                "action_id": "review_service_need",
                "text": "Check whether this connection is expected for the device.",
                "verification": "Compare it with the device's manual or ask its owner.",
            },
            {
                "action_id": "verify_service_identity",
                "text": "Find out which feature uses the connection before changing settings.",
                "verification": (
                    "Ask the manufacturer or someone who manages the device if you are unsure."
                ),
            },
        ],
        "references": [
            {
                "title": "CISA guidance on unnecessary ports and services",
                "url": "https://www.cisa.gov/news-events/alerts/2022/01/11/understanding-and-mitigating-russian-state-sponsored-cyber-threats-us-critical-infrastructure",
            }
        ],
        "version": "1.2.0",
        "rule_id": "R07",
    },
    "R08": {
        "title": "Older SMBv1 file sharing is supported",
        "meaning": (
            "This device accepted SMBv1, an older file-sharing protocol, during this local check."
        ),
        "why_it_matters": (
            "SMBv1 lacks protections available in newer file-sharing versions. This scan did not "
            "test whether any weakness can be exploited or which devices still use it."
        ),
        "severity": "high",
        "confidence": "medium",
        "limitations": [
            "Support was observed at scan time on the associated local connection; this does "
            "not establish Internet exposure.",
            "The check negotiated a protocol only; it did not sign in, inspect files, "
            "or test an exploit.",
            "An incomplete or absent SMB result cannot establish that SMBv1 is disabled.",
        ],
        "actions": [
            {
                "action_id": "check_smb1_dependencies",
                "text": (
                    "Check the device's manual or ask its owner whether older devices "
                    "still require SMBv1."
                ),
                "verification": (
                    "Confirm those devices can use a newer file-sharing version "
                    "before changing settings."
                ),
            },
            {
                "action_id": "review_smb1_retirement",
                "text": (
                    "Ask the owner or device maker how to turn off SMBv1 while keeping "
                    "newer file sharing available."
                ),
                "verification": (
                    "After an authorised change, run another Deep check; a missing response "
                    "does not prove the setting changed."
                ),
            },
        ],
        "references": [
            {
                "title": "Nmap SMB protocol negotiation check",
                "url": "https://nmap.org/nsedoc/scripts/smb-protocols.html",
            },
            {
                "title": "Microsoft guidance on retiring SMBv1",
                "url": "https://learn.microsoft.com/en-us/windows-server/storage/file-server/troubleshoot/detect-enable-and-disable-smbv1-v2-v3",
            },
        ],
        "version": "1.0.0",
        "rule_id": "R08",
    },
    "R09": {
        "title": "SMB message signing is not required",
        "meaning": (
            "During this check, the device did not require message signing "
            "for the negotiated SMB version."
        ),
        "why_it_matters": (
            "Signing helps detect changes to file-sharing messages. A server that does not "
            "require it may accept unsigned connections; this scan did not establish "
            "whether ordinary connections are signed."
        ),
        "severity": "medium",
        "confidence": "medium",
        "limitations": [
            "Only the negotiated SMB version was checked; other versions and client "
            "settings were not established.",
            "Signing concerns message integrity, not encryption or shared-folder permissions.",
            "This was a local negotiation check; no tampering, credential relay, "
            "or Internet exposure was tested.",
        ],
        "actions": [
            {
                "action_id": "review_smb_signing",
                "text": (
                    "Check the file-sharing settings or ask the device maker whether "
                    "SMB signing can be required."
                ),
                "verification": (
                    "Check that the computers using the shared folders support signing "
                    "before changing this setting."
                ),
            },
            {
                "action_id": "require_smb_signing_if_supported",
                "text": (
                    "Ask the owner to enable required signing using the device maker's "
                    "instructions if supported."
                ),
                "verification": (
                    "After an authorised change, confirm file sharing still works "
                    "and repeat the Deep check."
                ),
            },
        ],
        "references": [
            {
                "title": "Nmap SMB signing negotiation check",
                "url": "https://nmap.org/nsedoc/scripts/smb2-security-mode.html",
            },
            {
                "title": "Microsoft guidance on SMB signing",
                "url": "https://learn.microsoft.com/en-us/windows-server/storage/file-server/smb-signing",
            },
        ],
        "version": "1.0.0",
        "rule_id": "R09",
    },
}
