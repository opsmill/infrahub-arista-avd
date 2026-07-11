from __future__ import annotations

from solution_arista_avd.structural_parity import compare_configs, normalize_config


def test_normalize_config_masks_literal_values_but_preserves_shape() -> None:
    config_a = """
hostname ih-dc1-leaf1a
interface Ethernet49/1
   description P2P_ih-dc1-spine1_Ethernet1/1
   ip address 10.250.3.1/31
router bgp 65101
   neighbor 10.250.1.1 remote-as 65100
   vlan 11
      route-target both 10011:10011
"""
    config_b = """
hostname other-leaf
interface Ethernet50
   description P2P_other_Ethernet4
   ip address 192.0.2.1/31
router bgp 65299
   neighbor 203.0.113.10 remote-as 65200
   vlan 19
      route-target both 10019:10019
"""

    assert normalize_config(config_a) == normalize_config(config_b)


def test_compare_configs_reports_missing_structural_commands() -> None:
    generated = """
router bgp 65101
   address-family evpn
      neighbor EVPN-OVERLAY-PEERS activate
"""
    intended = """
router bgp 65201
   address-family evpn
      route export ethernet-segment ip mass-withdraw
      neighbor EVPN-OVERLAY-PEERS activate
"""

    result = compare_configs("leaf.cfg", generated, intended)

    assert not result.ok
    assert any("route export ethernet-segment ip mass-withdraw" in shape for shape in result.missing)
