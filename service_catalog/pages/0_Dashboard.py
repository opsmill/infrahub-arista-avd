"""Infrahub Service Catalog - Dashboard Page.

Displays fabrics, tenants, VRFs, and devices with branch selection.
"""

import streamlit as st  # type: ignore[import-untyped]
from utils import (
    DEFAULT_BRANCH,
    INFRAHUB_ADDRESS,
    INFRAHUB_API_TOKEN,
    INFRAHUB_UI_URL,
    InfrahubClient,
    display_error,
)
from utils.api import InfrahubConnectionError, InfrahubGraphQLError

# Read branch from query params, falling back to session state / default
query_params = st.query_params
if "branch" in query_params:
    initial_branch = query_params["branch"]
elif "selected_branch" in st.session_state:
    initial_branch = st.session_state.selected_branch
else:
    initial_branch = DEFAULT_BRANCH

st.session_state.selected_branch = initial_branch

if "infrahub_url" not in st.session_state:
    st.session_state.infrahub_url = INFRAHUB_ADDRESS


def _set_branch(branch: str) -> None:
    """Update branch in session state and query params."""
    st.session_state.selected_branch = branch
    st.query_params["branch"] = branch


def main() -> None:
    """Main function to render the dashboard."""
    client = InfrahubClient(
        st.session_state.infrahub_url,
        api_token=INFRAHUB_API_TOKEN or None,
        ui_url=INFRAHUB_UI_URL,
    )

    st.title("Infrahub Service Catalog")
    st.markdown("View and manage network services for your AI datacenter infrastructure.")

    # Branch selector in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Branch Selection")

    try:
        if "branches" not in st.session_state:
            with st.spinner("Loading branches..."):
                st.session_state.branches = client.get_branches()

        branches = st.session_state.branches

        if branches:
            branch_names = [branch["name"] for branch in branches]

            try:
                default_index = branch_names.index(st.session_state.selected_branch)
            except ValueError:
                default_index = 0
                _set_branch(branch_names[0] if branch_names else DEFAULT_BRANCH)

            selected_branch = st.sidebar.selectbox(
                "Select Branch",
                options=branch_names,
                index=default_index,
                help="Choose a branch to view its infrastructure resources",
                key="branch_selector",
            )

            if selected_branch != st.session_state.selected_branch:
                _set_branch(selected_branch)
                st.rerun()
        else:
            st.sidebar.warning("No branches found")

    except InfrahubConnectionError as e:
        display_error("Unable to connect to Infrahub", str(e))
        st.stop()
    except InfrahubGraphQLError as e:
        display_error("GraphQL Error", str(e))
        st.stop()

    # Ensure query param stays in sync
    st.query_params["branch"] = st.session_state.selected_branch
    st.sidebar.info(f"Current Branch: **{st.session_state.selected_branch}**")

    branch = st.session_state.selected_branch

    # Main content
    st.markdown("---")

    # Fabrics section
    st.header("Fabrics")

    try:
        with st.spinner(f"Loading fabrics from branch '{branch}'..."):
            fabrics = client.get_fabrics(branch)

        if fabrics:
            for fabric in fabrics:
                fabric_name = fabric.get("name", {}).get("value", "Unknown")
                fabric_id = fabric.get("id", "")
                fabric_link = f"{INFRAHUB_UI_URL}/objects/NetworkFabric/{fabric_id}?branch={branch}"

                with st.expander(f"**{fabric_name}**", expanded=True):
                    st.link_button("View in Infrahub", fabric_link)

            st.caption(f"Found {len(fabrics)} fabric(s)")
        else:
            st.info("No fabrics found in this branch.")

    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Error fetching fabrics", str(e))

    # Tenants section
    st.markdown("---")
    st.header("EVPN Tenants")

    try:
        with st.spinner("Loading tenants..."):
            tenants = client.get_tenants(branch)

        if tenants:
            tenant_data = []
            for t in tenants:
                fabric_names = ", ".join(
                    e["node"]["name"]["value"]
                    for e in t.get("fabrics", {}).get("edges", [])
                )
                tenant_data.append({
                    "Tenant": t.get("name", {}).get("value", ""),
                    "VNI Base": t.get("mac_vrf_vni_base", {}).get("value", ""),
                    "Fabrics": fabric_names,
                })
            st.dataframe(tenant_data, use_container_width=True, hide_index=True)
            st.caption(f"Found {len(tenants)} tenant(s)")
        else:
            st.info("No EVPN tenants found.")

    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Error fetching tenants", str(e))

    # VRFs section
    st.markdown("---")
    st.header("VRFs")

    try:
        with st.spinner("Loading VRFs..."):
            vrfs = client.get_vrfs(branch)

        if vrfs:
            vrf_data = []
            for v in vrfs:
                tenant_node = (v.get("tenant") or {}).get("node") or {}
                vrf_data.append({
                    "VRF": v.get("name", {}).get("value", ""),
                    "VNI": v.get("vrf_vni", {}).get("value", ""),
                    "Tenant": (tenant_node.get("name") or {}).get("value", ""),
                })
            st.dataframe(vrf_data, use_container_width=True, hide_index=True)
            st.caption(f"Found {len(vrfs)} VRF(s)")
        else:
            st.info("No VRFs found.")

    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Error fetching VRFs", str(e))

    # Devices summary
    st.markdown("---")
    st.header("Devices")

    try:
        with st.spinner("Loading device summary..."):
            query = """
            query {
                DcimDevice(role__values: ["super_spine", "spine", "leaf", "l2leaf"]) {
                    count
                    edges { node { role { value } } }
                }
            }
            """
            result = client.execute_graphql(query, branch=branch)
            devices = result.get("DcimDevice", {})
            total = devices.get("count", 0)

            if total > 0:
                role_counts: dict[str, int] = {}
                for edge in devices.get("edges", []):
                    role = edge["node"]["role"]["value"]
                    role_counts[role] = role_counts.get(role, 0) + 1

                cols = st.columns(len(role_counts))
                for i, (role, count) in enumerate(sorted(role_counts.items())):
                    cols[i].metric(role.replace("_", " ").title(), count)

                st.caption(f"{total} total devices")
            else:
                st.info("No devices found. Run the fabric generators to create devices.")

    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Error fetching devices", str(e))


main()
