def test_normal_coolant_temperature_has_no_fault(ecu):
    response = ecu.exchange(rpm=2000, throttle=40, coolant_temperature=85)

    assert response.rpm == 2000
    assert response.fault == 0


def test_coolant_temperature_above_limit_sets_fault(ecu):
    response = ecu.exchange(rpm=2000, throttle=40, coolant_temperature=111)

    assert response.rpm == 0
    assert response.state == 2
    assert response.fault & (1 << 0)
