"""Infrahub Service Catalog - Add Network Segment.

Creates a new EVPN network segment (VRF + VLAN + SVI) on a fabric via a proposed change.
Workflow: create branch -> create objects -> wait for hostvars -> open proposed change.
"""

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


def main() -> None:
    """Render the Add Network Segment page."""
    client = InfrahubClient(
        st.session_state.infrahub_url,
        api_token=INFRAHUB_API_TOKEN or None,
        ui_url=INFRAHUB_UI_URL,
    )

    st.title("Add Network Segment")
    st.markdown(
        "Create a new EVPN network segment (VRF, VLAN, SVI) on a fabric. "
        "Changes are made in a branch, hostvars are regenerated, and a proposed change is opened for review."
    )

    # Fetch data for dropdowns
    try:
        tenants = client.get_tenants()
        fabrics = client.get_fabrics()
        l2domains = client.get_l2domains()
    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Unable to fetch data from Infrahub", str(e))
        st.stop()
        return

    if not tenants:
        st.warning("No EVPN tenants found. Create a tenant first in Infrahub.")
        st.stop()
        return

    if not fabrics:
        st.warning("No fabrics found.")
        st.stop()
        return

    # Build form
    with st.form("add_segment_form"):
        st.subheader("Segment Details")

        col1, col2 = st.columns(2)

        with col1:
            segment_name = st.text_input("Segment Name", placeholder="e.g. web-services")

            tenant_options = {t["id"]: t["name"]["value"] for t in tenants}
            tenant_id = st.selectbox(
                "Tenant",
                options=list(tenant_options.keys()),
                format_func=lambda x: tenant_options[x],
            )

            vlan_id = st.number_input("VLAN ID", min_value=1, max_value=4094, value=100)

            gateway_ip = st.text_input("Gateway IP (CIDR)", placeholder="e.g. 10.10.100.1/24")

        with col2:
            vrf_name = st.text_input("VRF Name", placeholder="e.g. VRF-WEB (leave blank to use existing)")

            vrf_vni = st.number_input("VRF VNI", min_value=1, max_value=16777215, value=100)

            l2domain_options = {d["id"]: d["name"]["value"] for d in l2domains}
            l2domain_id = (
                st.selectbox(
                    "L2 Domain",
                    options=list(l2domain_options.keys()),
                    format_func=lambda x: l2domain_options[x],
                )
                if l2domains
                else None
            )

            fabric_options = {f["id"]: f["name"]["value"] for f in fabrics}
            fabric_id = st.selectbox(
                "Target Fabric",
                options=list(fabric_options.keys()),
                format_func=lambda x: fabric_options[x],
            )

        submitted = st.form_submit_button("Create Network Segment", type="primary")

    if submitted:
        if not segment_name:
            st.error("Segment Name is required.")
            return
        if not gateway_ip:
            st.error("Gateway IP is required.")
            return

        fabric_name = fabric_options[fabric_id]
        tenant_name = tenant_options[tenant_id]
        branch_name = f"add-segment-{segment_name.lower().replace(' ', '-')}"

        try:
            # Step 1: Create branch
            with st.spinner(f"Creating branch '{branch_name}'..."):
                client.create_branch(branch_name)
            st.info(f"Branch `{branch_name}` created")

            # Step 2: Create VLAN
            with st.spinner(f"Creating VLAN {vlan_id}..."):
                vlan_mutation = """
                mutation($name: String!, $vlan_id: BigInt!, $l2domain: String!) {
                    IpamVLANCreate(data: {
                        name: { value: $name }
                        vlan_id: { value: $vlan_id }
                        status: { value: "active" }
                        l2domain: { id: $l2domain }
                    }) { ok object { id } }
                }
                """
                vlan_result = client.execute_graphql(
                    vlan_mutation,
                    {
                        "name": segment_name,
                        "vlan_id": vlan_id,
                        "l2domain": l2domain_id,
                    },
                    branch=branch_name,
                )
                vlan_obj_id = vlan_result["IpamVLANCreate"]["object"]["id"]
            st.info(f"VLAN {vlan_id} ({segment_name}) created")

            # Step 3: Create VRF (if name provided)
            vrf_id = None
            if vrf_name:
                with st.spinner(f"Creating VRF {vrf_name}..."):
                    vrf_mutation = """
                    mutation($name: String!, $vrf_vni: BigInt!, $tenant: String!) {
                        IpamVRFCreate(data: {
                            name: { value: $name }
                            namespace: { id: "default" }
                            vrf_vni: { value: $vrf_vni }
                            tenant: { id: $tenant }
                        }) { ok object { id } }
                    }
                    """
                    vrf_result = client.execute_graphql(
                        vrf_mutation,
                        {
                            "name": vrf_name,
                            "vrf_vni": vrf_vni,
                            "tenant": tenant_id,
                        },
                        branch=branch_name,
                    )
                    vrf_id = vrf_result["IpamVRFCreate"]["object"]["id"]
                st.info(f"VRF {vrf_name} (VNI {vrf_vni}) created")
            else:
                # Use existing VRFs - let user pick
                st.warning("No new VRF created. SVI will need a VRF assigned manually.")

            # Step 4: Create SVI
            if vrf_id:
                with st.spinner(f"Creating SVI for VLAN {vlan_id}..."):
                    svi_mutation = """
                    mutation($name: String!, $svi_id: BigInt!, $ip: String!, $vrf: String!, $vlan: String!) {
                        EvpnSviCreate(data: {
                            name: { value: $name }
                            svi_id: { value: $svi_id }
                            ip_address_virtual: { value: $ip }
                            enabled: { value: true }
                            vrf: { id: $vrf }
                            vlan: { id: $vlan }
                        }) { ok object { id } }
                    }
                    """
                    client.execute_graphql(
                        svi_mutation,
                        {
                            "name": segment_name,
                            "svi_id": vlan_id,
                            "ip": gateway_ip,
                            "vrf": vrf_id,
                            "vlan": vlan_obj_id,
                        },
                        branch=branch_name,
                    )
                st.info(f"SVI {vlan_id} with gateway {gateway_ip} created in {vrf_name}")

            # Step 5: Run AVD generators (hostvars + structured config)
            with st.spinner("Running AVD generators — this may take a few minutes..."):
                results = client.run_avd_pipeline(branch=branch_name)

            if results["hostvars"]:
                st.success("Hostvars generated")
            else:
                st.warning("Hostvar generation timed out")
            if results["structured_config"]:
                st.success("Structured configs generated")
            else:
                st.warning("Structured config generation timed out")

            # Step 6: Create proposed change
            with st.spinner("Creating proposed change..."):
                pc = client.create_proposed_change(
                    branch=branch_name,
                    name=f"Add network segment: {segment_name}",
                    description=(
                        f"Add EVPN network segment '{segment_name}' "
                        f"(VLAN {vlan_id}, VRF {vrf_name or 'existing'}, gateway {gateway_ip}) "
                        f"to tenant {tenant_name} on fabric {fabric_name}"
                    ),
                )

            pc_url = client.get_proposed_change_url(pc["id"])
            display_success(f"Network segment '{segment_name}' created successfully!")
            st.link_button("View Proposed Change", pc_url)

        except InfrahubConnectionError as e:
            display_error("Connection error", str(e))
        except InfrahubGraphQLError as e:
            display_error("GraphQL error", str(e))
        except InfrahubAPIError as e:
            display_error("API error", str(e))


main()
