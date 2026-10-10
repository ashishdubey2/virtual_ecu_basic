def test_engine_starts_when_rpm_or_throttle_is_nonzero(ecu):
    response = ecu.exchange(rpm=700, throttle=10)

    assert response.rpm == 700
    assert response.state == 1
    assert response.fault == 0


def test_engine_stays_off_with_zero_rpm_and_throttle(ecu):
    response = ecu.exchange(rpm=0, throttle=0)

    assert response.rpm == 0
    assert response.state == 0
    assert response.fault == 0
