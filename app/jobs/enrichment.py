"""Optional device enrichment orchestration, separate from the scan job lifecycle."""

import asyncio

from app.profiling.classifier import classify_device


async def enrich_details(
    store,
    scan_id,
    cancel_event,
    *,
    nmap_path,
    process_runner,
    host_capacity,
    detail_capacity,
    timeout_s=30,
):
    from app.profiling.history import compare_history
    from app.scanner.details import netbios_name, network_details
    from app.scanner.mdns import MAX_ADVERTISEMENTS, MAX_UNIQUE_HOSTS
    from app.scanner.observations import detail, existing_details

    document = await store.load_scan(scan_id)
    if not document.policy.get("extra_details_enabled") or cancel_event.is_set():
        return
    devices = [d.model_copy(deep=True) for d in document.devices]
    mdns_limit_reached = (
        len(document.observations) >= MAX_ADVERTISEMENTS
        or len({item.ip for item in document.observations}) >= MAX_UNIQUE_HOSTS
    )
    finished = set()
    failed = set()

    def record_error(device, label, kind="web"):
        failed.add(device.device_id)
        detail(
            device,
            kind,
            label,
            "This optional information could not be collected because the check failed.",
            "Bounded extra checks",
            "unavailable",
        )

    async def enrich(device):
        services = [s for s in document.services if s.device_id == device.device_id]
        try:
            existing_details(device, services, document.observations)
        except Exception:
            record_error(device, "Saved observation details")
        async with detail_capacity:
            if cancel_event.is_set():
                return
            try:
                await network_details(device, services, document.policy["allowed_network"])
            except Exception:
                record_error(device, "Web and device description details")
            if cancel_event.is_set():
                return
            try:
                async with host_capacity:
                    await netbios_name(
                        device,
                        services,
                        nmap_path,
                        process_runner,
                        cancel_event,
                        document.policy.get("interface"),
                    )
            except Exception:
                record_error(device, "Computer name", "netbios")
            finished.add(device.device_id)

    tasks = [asyncio.create_task(enrich(d)) for d in devices]
    cancellation = asyncio.create_task(cancel_event.wait())
    group = asyncio.gather(*tasks)
    try:
        await asyncio.wait(
            {group, cancellation},
            timeout=timeout_s,
            return_when=asyncio.FIRST_COMPLETED,
        )
    finally:
        for task in [*tasks, cancellation]:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, cancellation, return_exceptions=True)
        await asyncio.gather(group, return_exceptions=True)
    for device in devices:
        if device.device_id not in finished:
            detail(
                device,
                "web",
                "Extra information",
                "Some optional checks ran out of time or were cancelled.",
                "Bounded extra checks",
                "not_checked",
            )
        services = [s for s in document.services if s.device_id == device.device_id]
        device.profile = device.profile.model_validate(classify_device(device, services))
    comparison = document.model_copy(update={"devices": devices})
    history_warning = None
    try:
        async with asyncio.timeout(5):
            page = await store.list_scans(source="live", offset=0, limit=11)
            previous = []
            for entry in page["items"]:
                if entry["scan_id"] != scan_id and entry.get("storage_status") == "ok":
                    try:
                        previous.append(await store.load_scan(entry["scan_id"]))
                    except (OSError, ValueError):
                        continue
            compare_history(comparison, previous[:10])
    except Exception:
        history_warning = {
            "code": "HISTORY_COMPARISON_UNAVAILABLE",
            "message": "History comparison could not finish; scan facts remain available.",
        }
    await store.update_scan(
        scan_id,
        lambda current: current.model_copy(
            update={
                "devices": devices,
                "warnings": [
                    *current.warnings,
                    *([history_warning] if history_warning else []),
                    *(
                        [
                            {
                                "code": "MDNS_LIMIT_REACHED",
                                "message": "The announcement limit was reached; additional "
                                "device names or features may not have been collected.",
                            }
                        ]
                        if mdns_limit_reached
                        else []
                    ),
                    *(
                        [
                            {
                                "code": "EXTRA_DETAILS_INCOMPLETE",
                                "message": "Some extra details were unavailable or unfinished; "
                                "see device details.",
                            }
                        ]
                        if failed or len(finished) != len(devices)
                        else []
                    ),
                ],
            }
        ),
    )
