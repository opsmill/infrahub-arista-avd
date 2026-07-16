"""Infrahub Service Catalog - Add Server Page.

Provides a form to create a new ComputePhysicalServer in a compute rack
via a proposed change workflow.
"""

import streamlit as st  # type: ignore[import-untyped]
from utils import (
    DEFAULT_BRANCH,
    INFRAHUB_ADDRESS,
    INFRAHUB_API_TOKEN,
    INFRAHUB_UI_URL,
    InfrahubClient,
    display_error,
    display_success,
)
from utils.api import InfrahubAPIError, InfrahubConnectionError, InfrahubGraphQLError

# Read branch from query params, falling back to session state / default
query_params = st.query_params
if "branch" in query_params:
    initial_branch = query_params["branch"]
elif "selected_branch" in st.session_state:
    initial_branch = st.session_state.selected_branch
else:
    initial_branch = DEFAULT_BRANCH

st.session_state.selected_branch = initial_branch
st.query_params["branch"] = st.session_state.selected_branch

if "infrahub_url" not in st.session_state:
    st.session_state.infrahub_url = INFRAHUB_ADDRESS


def main() -> None:
    """Main function to render the add server page."""

    client = InfrahubClient(
        st.session_state.infrahub_url,
        api_token=INFRAHUB_API_TOKEN or None,
        ui_url=INFRAHUB_UI_URL,
    )

    st.title("Add Server")
    st.markdown("Add a new physical server to a compute rack in the fabric.")

    branch = st.session_state.selected_branch

    # Fetch compute racks and server templates
    try:
        racks = _get_compute_racks(client, branch)
        templates = _get_server_templates(client, branch)
    except (InfrahubConnectionError, InfrahubGraphQLError) as e:
        display_error("Unable to fetch data from Infrahub", str(e))
        st.stop()
        return

    if not racks:
        st.warning("No compute racks found. Ensure racks with type 'compute' exist.")
        st.stop()
        return

    if not templates:
        st.warning("No server templates found (TemplateComputePhysicalServer).")
        st.stop()
        return

    # Build form
    with st.form("add_server_form"):
        st.subheader("Server Details")

        col1, col2 = st.columns(2)

        with col1:
            server_name = st.text_input(
                "Server Name",
                placeholder="e.g. compute-pod-a2-3-1",
                help="Hostname for the new server",
            )

            rack_options = {r["id"]: f"{r['name']} ({r['pod_name']})" for r in racks}
            rack_id = st.selectbox(
                "Rack",
                options=list(rack_options.keys()),
                format_func=lambda x: rack_options[x],
                help="Only compute racks are shown",
            )

        with col2:
            template_options = {t["id"]: t["name"] for t in templates}
            template_id = st.selectbox(
                "Server Template",
                options=list(template_options.keys()),
                format_func=lambda x: template_options[x],
                help="Determines interfaces and role",
            )

        submitted = st.form_submit_button("Add Server", type="primary")

    if submitted:
        if not server_name:
            st.error("Server Name is required.")
            return

        try:
            # Create branch for the change
            branch_name = f"add-server-{server_name.lower().replace(' ', '-')}"
            with st.spinner(f"Creating branch '{branch_name}'..."):
                client.create_branch(branch_name)

            # Create the server
            with st.spinner(f"Creating server '{server_name}'..."):
                server = _create_server(
                    client,
                    branch=branch_name,
                    name=server_name,
                    rack_id=rack_id,
                    template_id=template_id,
                )

            # Wait for Infrahub to run generators (server cabling + AVD cascade)
            import time

            with st.spinner("Waiting for generators to complete (60s)..."):
                time.sleep(60)

            # Create proposed change
            with st.spinner("Creating proposed change..."):
                pc = client.create_proposed_change(
                    branch=branch_name,
                    name=f"Add server: {server_name}",
                    description=f"Create server '{server_name}' in rack {rack_options[rack_id]} using template '{template_options[template_id]}'",
                )

            pc_url = client.get_proposed_change_url(pc["id"])
            server_url = f"{INFRAHUB_UI_URL}/objects/ComputePhysicalServer/{server['id']}?branch={branch_name}"

            display_success(f"Server '{server_name}' created successfully!")
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("View Server", server_url)
            with col2:
                st.link_button("View Proposed Change", pc_url)

        except InfrahubConnectionError as e:
            display_error("Connection error", str(e))
        except InfrahubGraphQLError as e:
            display_error("GraphQL error", str(e))
        except InfrahubAPIError as e:
            display_error("API error", str(e))
        except Exception as e:
            display_error("Unexpected error", str(e))


def _get_compute_racks(client: InfrahubClient, branch: str) -> list:
    """Fetch only racks with rack_type 'compute'."""
    query = """
    query GetComputeRacks {
        LocationRack(rack_type__value: "compute") {
            edges {
                node {
                    id
                    name { value }
                    pod {
                        node {
                            name { value }
                        }
                    }
                }
            }
        }
    }
    """
    result = client.execute_graphql(query, branch=branch)
    racks = []
    for edge in result.get("LocationRack", {}).get("edges", []):
        node = edge["node"]
        pod_node = node.get("pod", {}).get("node", {})
        racks.append(
            {
                "id": node["id"],
                "name": node.get("name", {}).get("value", "Unknown"),
                "pod_name": pod_node.get("name", {}).get("value", "") if pod_node else "",
            }
        )
    return racks


def _get_server_templates(client: InfrahubClient, branch: str) -> list:
    """Fetch available server templates."""
    query = """
    query GetServerTemplates {
        TemplateComputePhysicalServer {
            edges {
                node {
                    id
                    template_name { value }
                }
            }
        }
    }
    """
    result = client.execute_graphql(query, branch=branch)
    templates = []
    for edge in result.get("TemplateComputePhysicalServer", {}).get("edges", []):
        node = edge["node"]
        templates.append(
            {
                "id": node["id"],
                "name": node.get("template_name", {}).get("value", "Unknown"),
            }
        )
    return templates


def _create_server(
    client: InfrahubClient,
    branch: str,
    name: str,
    rack_id: str,
    template_id: str,
) -> dict:
    """Create a ComputePhysicalServer as a member of the ``servers`` group.

    Group membership is set atomically inside the upsert rather than as a
    separate follow-up write. The ``servers`` group is the target of the
    ``generate-server-cabling`` generator, so adding a member emits a
    ``GroupMemberAdded`` event that triggers the generator for the new node.
    Infrahub then re-queries the group's members on the branch and asserts the
    node is present — a separate add-to-group write races that trigger and can
    fail with ``Target ... is not part of the group ...`` because the membership
    is not yet visible on the branch when the generator runs. Committing the
    server and its membership in one transaction closes that race (this mirrors
    how the device generators enroll devices in ``avd_devices`` at creation).
    """
    servers_group_id = _get_group_id(client, group_name="servers", branch=branch)

    mutation = """
    mutation CreateServer(
        $name: String!,
        $rack_id: String!,
        $template_id: String!,
        $servers_group_id: String!
    ) {
        ComputePhysicalServerUpsert(
            data: {
                name: { value: $name }
                rack: { id: $rack_id }
                object_template: { id: $template_id }
                status: { value: "provisioning" }
                member_of_groups: [{ id: $servers_group_id }]
            }
        ) {
            ok
            object {
                id
                name { value }
            }
        }
    }
    """

    variables = {
        "name": name,
        "rack_id": rack_id,
        "template_id": template_id,
        "servers_group_id": servers_group_id,
    }

    result = client.execute_graphql(mutation, variables, branch)

    if not result.get("ComputePhysicalServerUpsert", {}).get("ok"):
        raise InfrahubAPIError(f"Failed to create server: {result}")

    return result["ComputePhysicalServerUpsert"]["object"]


def _get_group_id(client: InfrahubClient, group_name: str, branch: str) -> str:
    """Resolve a CoreStandardGroup id by name on the given branch."""
    query = """
    query GetGroup($name: String!) {
        CoreStandardGroup(name__value: $name) {
            edges { node { id } }
        }
    }
    """
    result = client.execute_graphql(query, {"name": group_name}, branch)
    edges = result.get("CoreStandardGroup", {}).get("edges", [])
    if not edges:
        raise InfrahubAPIError(f"Group '{group_name}' not found on branch '{branch}'")
    return edges[0]["node"]["id"]


main()
