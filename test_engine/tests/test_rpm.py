def test_engine_rpm(ecu):
    response = ecu.exchange(rpm=2000, throttle=40)

    assert response.rpm == 2000
    assert response.fault == 0


def test_rpm_above_limit_sets_diagnostic_fault(ecu):
    response = ecu.exchange(rpm=8001, throttle=40)

    assert response.rpm == 0
    assert response.state == 2
    assert response.fault & (1 << 2)
