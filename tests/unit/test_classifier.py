from app.profiling.classifier import classify_device
from app.schemas.scan import Device, Service


def test_classifier_uses_distinct_hostname_and_service_evidence():
    device = Device(
        device_id="device-1",
        scan_id="11111111-1111-4111-8111-111111111111",
        ip="192.168.0.2",
        hostname="front-camera",
    )
    service = Service(
        service_id="service-1",
        device_id=device.device_id,
        port=554,
        state="open",
        name="rtsp",
    )

    result = classify_device(device, [service])

    assert result["category"] == "camera"
    assert result["confidence"] == "medium"
    assert result["conflict"] is False
