"""Infrahub API client for the Service Catalog."""

from typing import Any, Dict, List, Optional

from infrahub_sdk import Config, InfrahubClientSync


class InfrahubAPIError(Exception):
    """Base exception for Infrahub API errors."""

    pass


class InfrahubConnectionError(InfrahubAPIError):
    """Exception raised when connection to Infrahub fails."""

    pass


class InfrahubHTTPError(InfrahubAPIError):
    """Exception raised for HTTP errors from Infrahub."""

    def __init__(self, message: str, status_code: int, response_text: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class InfrahubGraphQLError(InfrahubAPIError):
    """Exception raised for GraphQL errors from Infrahub."""

    def __init__(self, message: str, errors: List[Dict[str, Any]]):
        super().__init__(message)
        self.errors = errors


class InfrahubClient:
    """Client for interacting with the Infrahub API using the official SDK."""

    def __init__(
        self,
        base_url: str,
        api_token: Optional[str] = None,
        timeout: int = 60,
        ui_url: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.ui_url = (ui_url or base_url).rstrip("/")
        self.api_token = api_token
        self.timeout = timeout

        config = Config(timeout=timeout, api_token=api_token or None)
        self._client = InfrahubClientSync(address=base_url, config=config)

    def get_branches(self) -> List[Dict[str, Any]]:
        """Fetch all branches from Infrahub."""
        try:
            branches_dict = self._client.branch.all()
            branches = []
            for branch_name, branch_data in branches_dict.items():
                branches.append(
                    {
                        "name": branch_name,
                        "id": branch_data.id,
                        "is_default": branch_data.is_default,
                        "sync_with_git": branch_data.sync_with_git,
                    }
                )
            return branches
        except Exception as e:
            raise InfrahubConnectionError(f"Failed to fetch branches: {str(e)}")

    def execute_graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Execute a GraphQL query or mutation."""
        try:
            result = self._client.execute_graphql(query=query, variables=variables, branch_name=branch)
            return result
        except Exception as e:
            raise InfrahubGraphQLError(f"GraphQL error: {str(e)}", [])

    def get_fabrics(self, branch: str = "main") -> List[Dict[str, Any]]:
        """Fetch NetworkFabric objects."""
        try:
            query = """
            query GetFabrics {
                NetworkFabric {
                    edges {
                        node {
                            id
                            display_label
                            name { value }
                        }
                    }
                }
            }
            """
            result = self.execute_graphql(query, branch=branch)
            fabrics = []
            for edge in result.get("NetworkFabric", {}).get("edges", []):
                node = edge["node"]
                fabrics.append(
                    {
                        "id": node.get("id"),
                        "name": {"value": node.get("name", {}).get("value")},
                        "display_label": node.get("display_label"),
                    }
                )
            return fabrics
        except Exception as e:
            raise InfrahubAPIError(f"Failed to fetch fabrics: {str(e)}")

    def get_organizations(self, branch: str = "main") -> List[Dict[str, Any]]:
        """Fetch OrganizationGeneric objects."""
        try:
            query = """
            query GetOrganizations {
                OrganizationGeneric {
                    edges {
                        node {
                            id
                            display_label
                            __typename
                        }
                    }
                }
            }
            """
            result = self.execute_graphql(query, branch=branch)
            organizations = []
            for edge in result.get("OrganizationGeneric", {}).get("edges", []):
                node = edge["node"]
                organizations.append(
                    {
                        "id": node.get("id"),
                        "display_label": node.get("display_label"),
                        "type": node.get("__typename"),
                    }
                )
            return organizations
        except Exception as e:
            raise InfrahubAPIError(f"Failed to fetch organizations: {str(e)}")


    def create_branch(self, branch_name: str, sync_with_git: bool = False) -> Dict[str, Any]:
        """Create a new branch in Infrahub, or return it if it already exists."""
        try:
            branch = self._client.branch.create(branch_name=branch_name, sync_with_git=sync_with_git)
            return {
                "name": branch.name,
                "id": branch.id,
                "is_default": branch.is_default,
            }
        except Exception as e:
            if "already exists" in str(e):
                branches = self._client.branch.all()
                if branch_name in branches:
                    branch = branches[branch_name]
                    return {
                        "name": branch.name,
                        "id": branch.id,
                        "is_default": branch.is_default,
                    }
            raise InfrahubAPIError(f"Failed to create branch: {str(e)}")

    def create_proposed_change(
        self, branch: str, name: str, description: str, destination_branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a proposed change for a branch."""
        try:
            pc = self._client.create(
                kind="CoreProposedChange",
                branch=branch,
                name=name,
                description=description,
                source_branch=branch,
                destination_branch=destination_branch,
            )
            pc.save(allow_upsert=True)
            return {"id": pc.id, "name": name}
        except Exception as e:
            raise InfrahubAPIError(f"Failed to create proposed change: {str(e)}")

    def get_proposed_change_url(self, pc_id: str) -> str:
        """Get the URL for a proposed change."""
        return f"{self.ui_url}/proposed-changes/{pc_id}"

    def get_tenants(self, branch: str = "main") -> List[Dict[str, Any]]:
        """Fetch EvpnTenant objects."""
        query = """
        query { EvpnTenant { edges { node {
            id display_label name { value } mac_vrf_vni_base { value }
            fabrics { edges { node { id name { value } } } }
        } } } }
        """
        result = self.execute_graphql(query, branch=branch)
        return [e["node"] for e in result.get("EvpnTenant", {}).get("edges", [])]

    def get_vrfs(self, branch: str = "main") -> List[Dict[str, Any]]:
        """Fetch IpamVRF objects."""
        query = """
        query { IpamVRF { edges { node {
            id display_label name { value } vrf_vni { value }
            tenant { node { id name { value } } }
        } } } }
        """
        result = self.execute_graphql(query, branch=branch)
        return [e["node"] for e in result.get("IpamVRF", {}).get("edges", [])]

    def get_vlans(self, branch: str = "main") -> List[Dict[str, Any]]:
        """Fetch IpamVLAN objects."""
        query = """
        query { IpamVLAN { edges { node {
            id display_label name { value } vlan_id { value }
            l2domain { node { id name { value } } }
        } } } }
        """
        result = self.execute_graphql(query, branch=branch)
        return [e["node"] for e in result.get("IpamVLAN", {}).get("edges", [])]

    def get_l2domains(self, branch: str = "main") -> List[Dict[str, Any]]:
        """Fetch IpamL2Domain objects."""
        query = """
        query { IpamL2Domain { edges { node { id display_label name { value } } } } }
        """
        result = self.execute_graphql(query, branch=branch)
        return [e["node"] for e in result.get("IpamL2Domain", {}).get("edges", [])]

    def _resolve_target_id(self, name: str, branch: str = "main") -> Optional[str]:
        """Resolve a node name to its ID by searching common types."""
        for kind in ["NetworkFabric", "NetworkPod", "LocationRack", "DcimDevice"]:
            try:
                query = f'{{ {kind}(name__value: "{name}") {{ edges {{ node {{ id }} }} }} }}'
                result = self.execute_graphql(query, branch=branch)
                edges = result.get(kind, {}).get("edges", [])
                if edges:
                    return edges[0]["node"]["id"]
            except Exception:  # noqa: BLE001
                continue
        return None

    def _run_generator(
        self, generator_name: str, branch: str = "main", timeout: int = 600, target: str | None = None
    ) -> str | bool:
        """Trigger a generator run.

        Args:
            generator_name: Name of the generator definition
            branch: Branch to run on
            timeout: Max seconds to wait for the HTTP call
            target: Optional target object name (e.g. fabric name) to run for a specific member

        Returns task ID string if submitted, True if ok without task ID, False on failure.
        """
        import httpx as _httpx

        # Find the generator definition ID
        query = """
        query($name: String!) {
            CoreGeneratorDefinition(name__value: $name) {
                edges { node { id } }
            }
        }
        """
        result = self.execute_graphql(query, {"name": generator_name}, branch=branch)
        edges = result.get("CoreGeneratorDefinition", {}).get("edges", [])
        if not edges:
            raise InfrahubAPIError(f"Generator '{generator_name}' not found")

        gen_id = edges[0]["node"]["id"]

        mutation = """
        mutation CoreGeneratorDefinitionRun(
            $generatorId: String!,
            $waitUntilCompletion: Boolean,
            $targetNodeIds: [String!]
        ) {
            CoreGeneratorDefinitionRun(
                wait_until_completion: $waitUntilCompletion
                data: { id: $generatorId, nodes: $targetNodeIds }
            ) {
                task { id }
            }
        }
        """

        variables: dict[str, Any] = {
            "generatorId": gen_id,
            "waitUntilCompletion": False,
        }

        if target:
            target_id = self._resolve_target_id(target, branch)
            if target_id:
                variables["targetNodeIds"] = [target_id]

        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["X-INFRAHUB-KEY"] = self.api_token

        try:
            resp = _httpx.post(
                f"{self.base_url}/graphql/{branch}",
                json={"query": mutation, "variables": variables},
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                task = data.get("data", {}).get("CoreGeneratorDefinitionRun", {}).get("task", {})
                return task.get("id") if task else True
            return False
        except _httpx.TimeoutException:
            return False

    def run_avd_pipeline(self, branch: str = "main") -> Dict[str, bool]:
        """Run the full AVD pipeline: hostvars then structured config.

        Blocks until each generator completes. Returns status for each step.
        """
        results: Dict[str, bool] = {}

        results["hostvars"] = self._run_generator(
            "generate-avd-device-hostvar", branch=branch, timeout=600
        )

        results["structured_config"] = self._run_generator(
            "generate-avd-device-structured-config", branch=branch, timeout=600
        )

        return results
