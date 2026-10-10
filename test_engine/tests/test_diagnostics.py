def test_invalid_throttle_sets_throttle_diagnostic(ecu):
    response = ecu.exchange(rpm=2000, throttle=101)

    assert response.state == 2
    assert response.fault == 1 << 1


def test_multiple_diagnostics_are_reported_together(ecu):
    response = ecu.exchange(
        rpm=8001,
        throttle=101,
        coolant_temperature=111,
    )

    assert response.rpm == 0
    assert response.state == 2
    assert response.fault == (1 << 0) | (1 << 1) | (1 << 2)
