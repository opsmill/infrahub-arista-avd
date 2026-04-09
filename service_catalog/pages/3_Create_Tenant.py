"""Infrahub Service Catalog - Create Tenant.

Creates a new EVPN tenant with initial VRFs and VLANs on a fabric via a proposed change.
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
    """Render the Create Tenant page."""
    client = InfrahubClient(
        st.session_state.infrahub_url,
        api_token=INFRAHUB_API_TOKEN or None,
        ui_url=INFRAHUB_UI_URL,
    )

    st.title("Create Tenant")
    st.markdown(
        "Create a new EVPN tenant with VNI base allocation. "
        "The tenant can then have VRFs and network segments added to it."
    )

    # Fetch fabrics
    try:
        fabrics = client.get_fabrics()
    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Unable to fetch data from Infrahub", str(e))
        st.stop()
        return

    if not fabrics:
        st.warning("No fabrics found.")
        st.stop()
        return

    with st.form("create_tenant_form"):
        st.subheader("Tenant Details")

        col1, col2 = st.columns(2)

        with col1:
            tenant_name = st.text_input("Tenant Name", placeholder="e.g. ACME-Corp")
            vni_base = st.number_input(
                "MAC VRF VNI Base",
                min_value=1,
                max_value=16777000,
                value=20000,
                help="Base VNI number. VLAN VNI = base + VLAN ID",
            )

        with col2:
            fabric_options = {f["id"]: f["name"]["value"] for f in fabrics}
            selected_fabrics = st.multiselect(
                "Target Fabrics",
                options=list(fabric_options.keys()),
                format_func=lambda x: fabric_options[x],
                default=list(fabric_options.keys())[:1],
            )

        submitted = st.form_submit_button("Create Tenant", type="primary")

    if submitted:
        if not tenant_name:
            st.error("Tenant Name is required.")
            return
        if not selected_fabrics:
            st.error("At least one fabric must be selected.")
            return

        branch_name = f"add-tenant-{tenant_name.lower().replace(' ', '-')}"
        fabric_names = [fabric_options[fid] for fid in selected_fabrics]

        try:
            with st.spinner(f"Creating branch '{branch_name}'..."):
                client.create_branch(branch_name)
            st.info(f"Branch `{branch_name}` created")

            with st.spinner(f"Creating tenant '{tenant_name}'..."):
                mutation = """
                mutation($name: String!, $vni_base: BigInt!, $fabrics: [RelatedNodeInput!]) {
                    EvpnTenantCreate(data: {
                        name: { value: $name }
                        mac_vrf_vni_base: { value: $vni_base }
                        fabrics: $fabrics
                    }) { ok object { id } }
                }
                """
                fabric_refs = [{"id": fid} for fid in selected_fabrics]
                client.execute_graphql(
                    mutation,
                    {
                        "name": tenant_name,
                        "vni_base": vni_base,
                        "fabrics": fabric_refs,
                    },
                    branch=branch_name,
                )
            st.info(f"Tenant {tenant_name} (VNI base {vni_base}) created on {', '.join(fabric_names)}")

            # Run AVD generators
            with st.spinner("Running AVD generators — this may take a few minutes..."):
                results = client.run_avd_pipeline(branch=branch_name)
            if results.get("hostvars"):
                st.success("Hostvars generated")
            if results.get("structured_config"):
                st.success("Structured configs generated")

            with st.spinner("Creating proposed change..."):
                pc = client.create_proposed_change(
                    branch=branch_name,
                    name=f"Add tenant: {tenant_name}",
                    description=f"Create EVPN tenant '{tenant_name}' (VNI base {vni_base}) on {', '.join(fabric_names)}",
                )

            pc_url = client.get_proposed_change_url(pc["id"])
            display_success(f"Tenant '{tenant_name}' created successfully!")
            st.link_button("View Proposed Change", pc_url)

        except InfrahubConnectionError as e:
            display_error("Connection error", str(e))
        except InfrahubGraphQLError as e:
            display_error("GraphQL error", str(e))
        except InfrahubAPIError as e:
            display_error("API error", str(e))


main()
