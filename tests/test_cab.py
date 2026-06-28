"""Lock the host<->CAB protocol shape against the mock bench (docs/CAB-PROTOCOL.md)."""

from canopy.hal.cab import MockCABLink, make_cab_link
from canopy.profiles.generate import build_profile
from canopy.profiles.schema import ModuleProfile


def test_mock_handshake_and_safe_defaults():
    cab = MockCABLink()
    hello = cab.hello()
    assert hello["protocol"] == "1.0"
    assert "CAB-PWR-IGN" in hello["cards"]
    # safe by default: nothing armed, rails down
    status = cab.status()
    assert status["armed"] == []
    assert status["rails"]["vbat"] == 0.0


def test_mock_arm_read_disarm_cycle():
    cab = MockCABLink()
    cab.set_channel("CAB-PWR-IGN", "VBAT", "vbat", {"voltage_v": 13.5, "current_limit_a": 1.0})
    cab.arm("CAB-PWR-IGN")
    assert "CAB-PWR-IGN" in cab.status()["armed"]
    q = cab.read("CAB-PWR-IGN", "VBAT")["readback"]
    assert "current_a" in q
    cab.estop()
    assert cab.status()["armed"] == []


def test_mock_rejects_absent_card():
    cab = MockCABLink(cards=["CAB-PWR-IGN"])
    try:
        cab.arm("CAB-LOAD-16")
        raise AssertionError("expected CABError")
    except Exception as e:
        assert "not present" in str(e)


def test_make_cab_link_defaults_to_mock():
    assert isinstance(make_cab_link(), MockCABLink)


def test_profile_active_cards_present_on_bench(tmp_path):
    # a generated profile's active cards should all exist on the (mock) bench
    from canopy.vision.store import Store
    s = Store(str(tmp_path / "t.db"))
    vid = s.create_vehicle(label="GM TCM")["id"]
    s.add_tag(vid, "TCM")
    s.merge_pinouts(vid, None, 0, [
        {"connector": "C1", "pin": "6", "signal": "HS CAN +", "function": "CAN High"},
        {"connector": "C1", "pin": "30", "signal": "Battery +", "function": "KL30"},
    ])
    prof = build_profile(s, vid)
    assert isinstance(prof, ModuleProfile)
    bench = set(MockCABLink().cards)
    assert set(prof.active_cards) <= bench
