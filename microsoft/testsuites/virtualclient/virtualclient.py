from typing import List, Optional

from lisa import (
    Environment,
    TestCaseMetadata,
    TestSuite,
    TestSuiteMetadata,
    schema,
    search_space,
    simple_requirement,
)
from lisa.operating_system import Debian
from lisa.tools import VcRunner


@TestSuiteMetadata(
    area="virtual_client",
    category="performance",
    description="""
        This test suite runs the performance test cases with Virtual Client.
    """,
)
class VirtualClient(TestSuite):
    @TestCaseMetadata(
        description="""
            This test is to run redis workload testing with Virtual Client.
        """,
        priority=2,
        requirement=simple_requirement(
            supported_os=[Debian],
            min_count=2,
        ),
    )
    def perf_vc_redis(self, environment: Environment) -> None:
        self._run_work_load(
            environment=environment, profile_name="PERF-REDIS", roles=["client"]
        )

    @TestCaseMetadata(
        description="""
            This test is to run PostgreSQL workload testing with Virtual Client.
        """,
        priority=3,
        requirement=simple_requirement(
            supported_os=[Debian],
            min_count=2,
            disk=schema.DiskOptionSettings(
                data_disk_count=2,
                data_disk_size=search_space.IntRange(min=256),
            ),
        ),
        timeout=3000,
    )
    def perf_vc_postgresql(self, environment: Environment) -> None:
        self._run_work_load(
            environment=environment,
            profile_name="PERF-POSTGRESQL-HAMMERDB-TPCC",
            timeout=45,
        )

    def _run_work_load(
        self,
        environment: Environment,
        profile_name: str,
        timeout: int = 10,
        roles: Optional[List[str]] = None,
    ) -> None:
        if roles is None:
            roles = ["client", "server"]

        vc_runner: VcRunner = VcRunner(environment, roles)
        vc_runner.run(
            profile_name=profile_name,
            timeout=timeout,
        )
