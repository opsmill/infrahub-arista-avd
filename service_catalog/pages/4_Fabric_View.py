"""Infrahub Service Catalog - Fabric Visualization.

Displays the fabric design topology and expected AVD output summary.
"""

from typing import Any

import streamlit as st  # type: ignore[import-untyped]
from utils import (
    INFRAHUB_ADDRESS,
    INFRAHUB_API_TOKEN,
    INFRAHUB_UI_URL,
    InfrahubClient,
    display_error,
    display_success,
)
from utils.api import InfrahubAPIError, InfrahubConnectionError, InfrahubGraphQLError

if "infrahub_url" not in st.session_state:
    st.session_state.infrahub_url = INFRAHUB_ADDRESS

# Persist branch in query params
if "branch" in st.query_params:
    st.session_state.fabric_view_branch = st.query_params["branch"]
elif "fabric_view_branch" not in st.session_state:
    st.session_state.fabric_view_branch = "main"


def _fetch_fabric_topology(client: InfrahubClient, fabric_name: str, branch: str) -> dict[str, Any]:
    """Fetch complete fabric topology data."""
    query = """
    query($name: String!) {
      NetworkFabric(name__value: $name) {
        edges { node {
          id
          name { value }
          virtual_router_mac { value }
          underlay_routing_protocol { value }
          overlay_routing_protocol { value }
          p2p_uplinks_mtu { value }
          spanning_tree_mode { value }
          spanning_tree_priority { value }
          amount_of_super_spines { value }
          children {
            edges { node {
              ... on NetworkPod {
                name { value }
                role { value }
                amount_of_spines { value }
                loopback_ipv4_offset { value }
                devices { count }
                racks {
                  edges { node {
                    name { value }
                    rack_type { value }
                    amount_of_leafs { value }
                    amount_of_l2leafs { value }
                    devices {
                      edges { node {
                        ... on DcimDevice {
                          name { value }
                          role { value }
                        }
                      } }
                    }
                  } }
                }
              }
            } }
          }
        } }
      }
      EvpnTenant(fabrics__name__value: $name) {
        edges { node {
          name { value }
          mac_vrf_vni_base { value }
          vrfs {
            edges { node {
              name { value }
              vrf_vni { value }
              svis { count }
            } }
          }
          l2vlans { count }
        } }
      }
      MlagDomain {
        count
      }
    }
    """
    return client.execute_graphql(query, {"name": fabric_name}, branch=branch)


def _make_node(nid: str, x: int, y: int, label: str, color: str, w: int = 100) -> "StreamlitFlowNode":
    """Create a compact styled node."""
    from streamlit_flow.elements import StreamlitFlowNode

    return StreamlitFlowNode(
        id=nid,
        pos=(x, y),
        data={"content": label},
        node_type="default",
        style={
            "background": color,
            "color": "#fff",
            "padding": "4px 8px",
            "borderRadius": "6px",
            "fontSize": "11px",
            "textAlign": "center",
            "width": w,
            "minHeight": "30px",
            "border": f"1px solid {color}",
        },
    )


def _render_topology(data: dict[str, Any]) -> None:
    """Render fabric design topology."""
    from streamlit_flow import streamlit_flow
    from streamlit_flow.elements import StreamlitFlowEdge
    from streamlit_flow.state import StreamlitFlowState

    fabric = data["NetworkFabric"]["edges"][0]["node"]
    fabric_name = fabric["name"]["value"]
    ss_count = fabric.get("amount_of_super_spines", {}).get("value", 0)

    nodes = []
    edges = []

    W = 110  # node width
    GAP = 20
    SLOT = W + GAP
    Y_FABRIC = 0
    Y_POD = 100
    Y_RACK = 200
    Y_L2 = 300

    # Collect pod info
    all_pods = fabric["children"]["edges"]
    pod_infos = []
    total_slots = 0
    for pe in all_pods:
        p = pe["node"]
        rc = len(p.get("racks", {}).get("edges", []))
        w = max(rc, 1)
        pod_infos.append({"pod": p, "rc": rc, "w": w})
        total_slots += w

    cx = (total_slots * SLOT) // 2

    # Fabric
    nodes.append(_make_node("fabric", cx, Y_FABRIC, fabric_name, "#2563eb", 120))

    cursor = 0
    for pi in pod_infos:
        p = pi["pod"]
        pn = p["name"]["value"]
        pid = pn.replace("-", "_")
        role = p.get("role", {}).get("value", "")
        spines = p.get("amount_of_spines", {}).get("value", 0)
        pcx = (cursor * SLOT) + (pi["w"] * SLOT) // 2

        if role == "fabric":
            nodes.append(_make_node(pid, pcx, Y_POD, f"{pn}\n{ss_count} SS", "#7c3aed", W))
        else:
            nodes.append(_make_node(pid, pcx, Y_POD, f"{pn}\n{spines} spines", "#059669", W))

        edges.append(
            StreamlitFlowEdge(
                id=f"f-{pid}",
                source="fabric",
                target=pid,
                animated=True,
                style={"stroke": "#64748b"},
            )
        )

        for ri, re in enumerate(p.get("racks", {}).get("edges", [])):
            r = re["node"]
            rn = r["name"]["value"]
            rid = rn.replace("-", "_")
            rt = r.get("rack_type", {}).get("value", "")
            lc = r.get("amount_of_leafs", {}).get("value", 0)
            l2c = r.get("amount_of_l2leafs", {}).get("value", 0)
            rx = (cursor + ri) * SLOT

            devs = r.get("devices", {}).get("edges", [])
            leafs = [d["node"]["name"]["value"] for d in devs if d["node"].get("role", {}).get("value") == "leaf"]
            l2s = [d["node"]["name"]["value"] for d in devs if d["node"].get("role", {}).get("value") == "l2leaf"]

            tag = f"{lc}L3" + (f"+{l2c}L2" if l2c else "")
            rc = {"compute": "#b45309", "storage": "#b91c1c"}.get(rt, "#4b5563")
            nodes.append(_make_node(rid, rx, Y_RACK, f"{rn}\n{rt} | {tag}", rc, W))
            edges.append(
                StreamlitFlowEdge(
                    id=f"{pid}-{rid}",
                    source=pid,
                    target=rid,
                    style={"stroke": "#64748b"},
                )
            )

            for l2 in l2s:
                l2id = l2.replace("-", "_")
                nodes.append(_make_node(l2id, rx, Y_L2, f"{l2}\nL2 leaf", "#4b5563", W))
                edges.append(
                    StreamlitFlowEdge(
                        id=f"{rid}-{l2id}",
                        source=rid,
                        target=l2id,
                        style={"stroke": "#6b7280", "strokeDasharray": "4"},
                    )
                )

        cursor += pi["w"]

    cache_key = f"design_{fabric_name}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = StreamlitFlowState(nodes=nodes, edges=edges)

    streamlit_flow(
        "fabric_topology",
        st.session_state[cache_key],
        fit_view=True,
        height=500,
        get_node_on_click=False,
        get_edge_on_click=False,
        pan_on_drag=True,
        allow_zoom=True,
        enable_node_menu=False,
        enable_edge_menu=False,
        enable_pane_menu=False,
        hide_watermark=True,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_cabling_data(_client: InfrahubClient, fabric_name: str, branch: str) -> list[dict[str, Any]]:
    """Fetch all network links with endpoint details for a fabric."""
    # First get all link IDs from the fabric
    query = """
    query($name: String!) {
      NetworkFabric(name__value: $name) {
        edges { node { children { edges { node {
          ... on NetworkPod {
            devices { edges { node {
              __typename
              ... on DcimDevice { interfaces { edges { node {
                ... on InterfacePhysical { connector { node { id } } }
              } } } }
            } } }
            racks { edges { node { devices { edges { node {
              __typename
              ... on DcimDevice { interfaces { edges { node {
                ... on InterfacePhysical { connector { node { id } } }
              } } } }
            } } } } } }
          }
        } } } } }
      }
      ComputePhysicalServer {
        edges { node {
          interfaces { edges { node {
            ... on InterfacePhysical { connector { node { id } } }
          } } }
        } }
      }
    }
    """
    result = _client.execute_graphql(query, {"name": fabric_name}, branch=branch)

    link_ids = set()
    for pod_edge in result["NetworkFabric"]["edges"][0]["node"]["children"]["edges"]:
        pod = pod_edge["node"]
        for src in [
            pod.get("devices", {}),
            *[r["node"].get("devices", {}) for r in pod.get("racks", {}).get("edges", [])],
        ]:
            for dev_edge in src.get("edges", []):
                dev = dev_edge["node"]
                for iface_edge in dev.get("interfaces", {}).get("edges", []):
                    iface = iface_edge["node"]
                    connector = iface.get("connector") or {}
                    if connector.get("node"):
                        link_ids.add(connector["node"]["id"])

    # Also collect links from servers (queried separately)
    for srv_edge in result.get("ComputePhysicalServer", {}).get("edges", []):
        for iface_edge in srv_edge["node"].get("interfaces", {}).get("edges", []):
            iface = iface_edge["node"]
            connector = iface.get("connector") or {}
            if connector.get("node"):
                link_ids.add(connector["node"]["id"])

    if not link_ids:
        return []

    # Fetch links with full endpoint details
    links_query = """
    query($ids: [ID!]) {
      NetworkLink(ids: $ids) { edges { node {
        connected_endpoints { edges { node {
          __typename
          ... on InterfacePhysical {
            name { value }
            device { node {
              __typename
              ... on DcimDevice { name { value } role { value } }
              ... on ComputePhysicalServer { name { value } role { value } }
            } }
          }
          ... on DcimInterface {
            name { value }
            device { node {
              __typename
              ... on DcimDevice { name { value } role { value } }
              ... on ComputePhysicalServer { name { value } role { value } }
            } }
          }
        } } }
      } } }
    }
    """
    links = []
    batch_ids = list(link_ids)
    for i in range(0, len(batch_ids), 10):
        try:
            result = _client.execute_graphql(links_query, {"ids": batch_ids[i : i + 10]}, branch=branch)
        except Exception:
            continue
        for edge in result.get("NetworkLink", {}).get("edges", []):
            eps = edge["node"]["connected_endpoints"]["edges"]
            if len(eps) == 2:
                src = eps[0]["node"]
                dst = eps[1]["node"]
                src_dev = (src.get("device") or {}).get("node") or {}
                dst_dev = (dst.get("device") or {}).get("node") or {}
                if src_dev.get("name") and dst_dev.get("name"):
                    links.append(
                        {
                            "src_device": src_dev["name"]["value"],
                            "src_role": src_dev.get("role", {}).get("value", ""),
                            "src_interface": (src.get("name") or {}).get("value", ""),
                            "dst_device": dst_dev["name"]["value"],
                            "dst_role": dst_dev.get("role", {}).get("value", ""),
                            "dst_interface": (dst.get("name") or {}).get("value", ""),
                        }
                    )
    return links


def _render_cabling_topology(client: InfrahubClient, fabric_name: str, branch: str) -> None:
    """Render the physical cabling topology using React Flow."""
    from streamlit_flow import streamlit_flow
    from streamlit_flow.elements import StreamlitFlowEdge, StreamlitFlowNode
    from streamlit_flow.state import StreamlitFlowState

    with st.spinner("Loading cabling data — this may take a moment..."):
        try:
            links = _fetch_cabling_data(client, fabric_name, branch)
        except Exception as e:
            st.error(f"Error fetching cabling data: {e}")
            return

    if not links:
        st.warning("No cabling data found. Run the fabric generators first.")
        return

    # Collect unique devices and their roles
    devices: dict[str, str] = {}  # name -> role
    for link in links:
        devices[link["src_device"]] = link["src_role"]
        devices[link["dst_device"]] = link["dst_role"]

    # Group devices by role for layered positioning
    role_colors = {
        "super_spine": "#7c3aed",
        "spine": "#059669",
        "leaf": "#d97706",
        "l2leaf": "#6b7280",
    }
    role_order = ["super_spine", "spine", "leaf", "l2leaf"]
    role_y = {"super_spine": 0, "spine": 200, "leaf": 400, "l2leaf": 600}

    # Group devices by role
    by_role: dict[str, list[str]] = {}
    for name, role in sorted(devices.items()):
        by_role.setdefault(role, []).append(name)

    # Calculate positions
    nodes: list[StreamlitFlowNode] = []
    node_w = 120
    gap = 40
    slot = node_w + gap

    # Find the widest layer for centering
    max_width = max(len(devs) for devs in by_role.values()) if by_role else 1

    for role in role_order:
        devs = by_role.get(role, [])
        if not devs:
            continue
        # Center this layer
        start_x = (max_width * slot - len(devs) * slot) // 2
        y = role_y.get(role, 400)
        color = role_colors.get(role, "#6b7280")

        for i, name in enumerate(sorted(devs)):
            short = name.split("-")[-1] if len(name) > 15 else name
            nodes.append(
                StreamlitFlowNode(
                    id=name,
                    pos=(start_x + i * slot, y),
                    data={"content": f"**{name}**\n{role}"},
                    node_type="default",
                    style={
                        "background": color,
                        "color": "white",
                        "padding": "6px",
                        "borderRadius": "6px",
                        "width": node_w,
                        "fontSize": "9px",
                    },
                )
            )

    # Also add non-fabric devices (servers etc) that appear in links
    other_devs = {name for name, role in devices.items() if role not in role_order}
    if other_devs:
        start_x = (max_width * slot - len(other_devs) * slot) // 2
        for i, name in enumerate(sorted(other_devs)):
            nodes.append(
                StreamlitFlowNode(
                    id=name,
                    pos=(start_x + i * slot, 800),
                    data={"content": f"**{name}**\nserver"},
                    node_type="default",
                    style={
                        "background": "#374151",
                        "color": "white",
                        "padding": "6px",
                        "borderRadius": "6px",
                        "width": node_w,
                        "fontSize": "9px",
                    },
                )
            )

    # Build edges from links (dedupe by device pair)
    seen_pairs: set[tuple[str, str]] = set()
    flow_edges: list[StreamlitFlowEdge] = []
    for link in links:
        pair = tuple(sorted([link["src_device"], link["dst_device"]]))
        if pair in seen_pairs:
            # Count the connections for this pair
            continue
        seen_pairs.add(pair)

        # Count total links between this pair
        count = sum(1 for l in links if tuple(sorted([l["src_device"], l["dst_device"]])) == pair)

        edge_label = f"{count}x" if count > 1 else ""
        # Determine direction: source should be the higher-tier device
        src, tgt = pair[0], pair[1]
        src_role = devices.get(src, "")
        tgt_role = devices.get(tgt, "")
        src_tier = role_order.index(src_role) if src_role in role_order else 99
        tgt_tier = role_order.index(tgt_role) if tgt_role in role_order else 99
        if src_tier > tgt_tier:
            src, tgt = tgt, src

        flow_edges.append(
            StreamlitFlowEdge(
                id=f"{src}-{tgt}",
                source=src,
                target=tgt,
                source_handle="bottom",
                target_handle="top",
                label=edge_label,
                style={"stroke": "#4b5563", "strokeWidth": min(count, 4)},
            )
        )

    st.caption(f"{len(devices)} devices, {len(seen_pairs)} connections ({len(links)} total links)")

    cache_key = f"cabling_state_{fabric_name}_{branch}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = StreamlitFlowState(nodes=nodes, edges=flow_edges)

    streamlit_flow(
        "cabling_topology",
        st.session_state[cache_key],
        fit_view=True,
        height=700,
        get_node_on_click=False,
        get_edge_on_click=False,
        pan_on_drag=True,
        allow_zoom=True,
        enable_node_menu=False,
        enable_edge_menu=False,
        enable_pane_menu=False,
        hide_watermark=True,
    )


def _render_fabric_summary(data: dict[str, Any]) -> None:
    """Render fabric settings and summary metrics."""
    fabric = data["NetworkFabric"]["edges"][0]["node"]

    col1, col2, col3, col4 = st.columns(4)

    # Count devices by type
    total_devices = 0
    super_spines = fabric.get("amount_of_super_spines", {}).get("value", 0)
    total_spines = 0
    total_leafs = 0
    total_l2leafs = 0
    total_racks = 0

    for pod_edge in fabric["children"]["edges"]:
        pod = pod_edge["node"]
        pod_role = pod.get("role", {}).get("value", "")
        if pod_role != "fabric":
            total_spines += pod.get("amount_of_spines", {}).get("value", 0)
            for rack_edge in pod.get("racks", {}).get("edges", []):
                rack = rack_edge["node"]
                total_racks += 1
                total_leafs += rack.get("amount_of_leafs", {}).get("value", 0)
                total_l2leafs += rack.get("amount_of_l2leafs", {}).get("value", 0)

    total_devices = super_spines + total_spines + total_leafs + total_l2leafs

    col1.metric("Total Devices", total_devices)
    col2.metric("Super-Spines", super_spines)
    col3.metric("Spines", total_spines)
    col4.metric("Racks", total_racks)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("L3 Leafs", total_leafs)
    col2.metric("L2 Leafs", total_l2leafs)
    col3.metric("MLAG Pairs", total_leafs // 2)
    col4.metric("MLAG Domains", data.get("MlagDomain", {}).get("count", 0))


def _render_fabric_settings(data: dict[str, Any]) -> None:
    """Render fabric configuration settings."""
    fabric = data["NetworkFabric"]["edges"][0]["node"]

    st.subheader("Fabric Settings")
    col1, col2 = st.columns(2)

    with col1:
        settings = {
            "Underlay Protocol": fabric.get("underlay_routing_protocol", {}).get("value", "—"),
            "Overlay Protocol": fabric.get("overlay_routing_protocol", {}).get("value", "—"),
            "Virtual Router MAC": fabric.get("virtual_router_mac", {}).get("value", "—"),
            "P2P Uplinks MTU": fabric.get("p2p_uplinks_mtu", {}).get("value", "—"),
        }
        for k, v in settings.items():
            st.markdown(f"**{k}:** `{v}`")

    with col2:
        settings = {
            "Spanning Tree Mode": fabric.get("spanning_tree_mode", {}).get("value", "—"),
            "Spanning Tree Priority": fabric.get("spanning_tree_priority", {}).get("value", "—"),
        }
        for k, v in settings.items():
            st.markdown(f"**{k}:** `{v}`")


def _render_tenants(data: dict[str, Any]) -> None:
    """Render EVPN tenant summary."""
    tenants = data.get("EvpnTenant", {}).get("edges", [])
    if not tenants:
        st.info("No EVPN tenants configured for this fabric.")
        return

    st.subheader("EVPN Network Services")

    for tenant_edge in tenants:
        tenant = tenant_edge["node"]
        tenant_name = tenant["name"]["value"]
        vni_base = tenant.get("mac_vrf_vni_base", {}).get("value", "—")
        vrfs = tenant.get("vrfs", {}).get("edges", [])
        l2vlan_count = tenant.get("l2vlans", {}).get("count", 0)

        with st.expander(f"**{tenant_name}** (VNI Base: {vni_base})", expanded=True):
            if vrfs:
                vrf_data = []
                for vrf_edge in vrfs:
                    vrf = vrf_edge["node"]
                    vrf_data.append(
                        {
                            "VRF": vrf["name"]["value"],
                            "VNI": vrf.get("vrf_vni", {}).get("value", "—"),
                            "SVIs": vrf.get("svis", {}).get("count", 0),
                        }
                    )
                st.dataframe(vrf_data, use_container_width=True, hide_index=True)

            if l2vlan_count:
                st.markdown(f"**L2 VLANs:** {l2vlan_count}")


def _render_generate_action(client: InfrahubClient, fabric_name: str, current_branch: str) -> None:
    """Render the Generate AVD Configs action button."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("**Generate Fabric**")
        st.caption(
            "Create a new branch, run the fabric generator (creates devices, cabling, hostvars, configs), and open a proposed change."
        )

    with col2:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        default_branch = f"generate-{fabric_name.lower()}-{timestamp}"
        branch_name = st.text_input(
            "Branch name",
            value=default_branch,
            key=f"generate_branch_{fabric_name}",
            label_visibility="collapsed",
            placeholder="Branch name",
        )

    with col3:
        if st.button("Generate", type="primary", use_container_width=True):
            st.session_state["gen_running"] = True
            st.session_state["gen_branch"] = branch_name
            st.session_state["gen_fabric"] = fabric_name
            st.rerun()

    # Run the generation if triggered
    if st.session_state.get("gen_running"):
        gen_branch = st.session_state["gen_branch"]
        gen_fabric = st.session_state["gen_fabric"]
        st.session_state["gen_running"] = False

        try:
            with st.status("Generating fabric...", expanded=True) as status:
                st.write(f"Creating branch `{gen_branch}`...")
                client.create_branch(gen_branch)
                st.write("Branch created")

                st.write(f"Running fabric generator for {gen_fabric}...")
                st.caption("This triggers the full pipeline: fabric → pods → racks → hostvars → structured configs")
                result = client._run_generator("generate-fabric", branch=gen_branch, timeout=900, target=gen_fabric)  # noqa: SLF001

                if result:
                    st.write("Fabric generator completed")
                else:
                    st.write("Fabric generator timed out — check Infrahub for status")

                st.write("Creating proposed change...")
                pc = client.create_proposed_change(
                    branch=gen_branch,
                    name=f"Generate fabric: {gen_fabric}",
                    description=f"Full fabric generation for {gen_fabric} — devices, cabling, hostvars, and structured configs",
                )

                status.update(label="Generation complete!", state="complete")

            pc_url = client.get_proposed_change_url(pc["id"])
            display_success(f"Fabric generated on branch `{gen_branch}`")
            st.link_button("View Proposed Change", pc_url)

        except InfrahubConnectionError as e:
            display_error("Connection error", str(e))
        except InfrahubGraphQLError as e:
            display_error("GraphQL error", str(e))
        except InfrahubAPIError as e:
            display_error("API error", str(e))


def main() -> None:
    """Render the Fabric View page."""
    client = InfrahubClient(
        st.session_state.infrahub_url,
        api_token=INFRAHUB_API_TOKEN or None,
        ui_url=INFRAHUB_UI_URL,
    )

    st.title("Fabric Design View")

    # Fetch fabrics for selector
    try:
        fabrics = client.get_fabrics()
    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Unable to fetch fabrics", str(e))
        st.stop()
        return

    if not fabrics:
        st.warning("No fabrics found.")
        st.stop()
        return

    # Branch selector in sidebar (synced with query params)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Branch Selection")
    try:
        if "branches" not in st.session_state:
            st.session_state.branches = client.get_branches()
        branch_names = [b["name"] for b in st.session_state.branches]

        current = st.session_state.get("fabric_view_branch", "main")
        default_idx = branch_names.index(current) if current in branch_names else 0

        branch = st.sidebar.selectbox(
            "Select Branch",
            options=branch_names,
            index=default_idx,
            key="fabric_view_branch_selector",
        )

        # Sync to session state and query params
        st.session_state.fabric_view_branch = branch
        st.query_params["branch"] = branch
    except (InfrahubConnectionError, InfrahubGraphQLError):
        branch = "main"

    st.sidebar.info(f"Current Branch: **{branch}**")

    fabric_options = {f["name"]["value"]: f["name"]["value"] for f in fabrics}
    selected_fabric = st.selectbox("Select Fabric", options=list(fabric_options.keys()))

    if not selected_fabric:
        return

    try:
        with st.spinner("Loading fabric topology..."):
            data = _fetch_fabric_topology(client, selected_fabric, branch)
    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Unable to fetch topology", str(e))
        return

    if not data.get("NetworkFabric", {}).get("edges"):
        st.warning(f"Fabric '{selected_fabric}' not found on branch '{branch}'.")
        return

    # Summary metrics
    st.markdown("---")
    _render_fabric_summary(data)

    # Generate AVD configs action
    st.markdown("---")
    _render_generate_action(client, selected_fabric, branch)

    # Tabs for different views
    tab_design, tab_cabling, tab_settings, tab_tenants = st.tabs(
        ["Design Topology", "Cabling Topology", "Fabric Settings", "EVPN Tenants"]
    )

    with tab_design:
        _render_topology(data)

    with tab_cabling:
        _render_cabling_topology(client, selected_fabric, branch)

    with tab_settings:
        _render_fabric_settings(data)

    with tab_tenants:
        _render_tenants(data)


main()
