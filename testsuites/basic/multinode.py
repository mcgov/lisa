from assertpy import assert_that  # type: ignore

from lisa import Environment, Node, TestCaseMetadata, TestSuite, TestSuiteMetadata
from lisa.operating_system import Windows
from lisa.testsuite import simple_requirement
from lisa.environment import EnvironmentStatus
from lisa.features import SerialConsole
from lisa.testsuite import simple_requirement
from lisa.util import LisaException, PassedException
from lisa.tools import Lscpu, Ntttcp, Git, Cat
from pathlib import PurePath, Path

TIME_OUT = 1200


class InitialXdpSetup:
    def __init__(self, suite: TestSuite, environment: Environment):
        suite.log.info(f"node count: {len(environment.nodes)}")
        for node in environment.nodes.list():
            lscpu = node.tools[Lscpu]
            core_count = lscpu.get_core_count()
            suite.log.info(f"index: {node.index}, core_count: {core_count}")

        server_node = environment.nodes[0]

        client_node = environment.nodes[1]

        for node in environment.nodes.list():
            result = node.execute("uname -a")
            suite.log.info(result.stdout)
            git = node.tools[Git]
            git.clone("https://github.com/mcgov/xdp_scripts.git", Path('.'))

            constant_file = ""
            constant_file += "server={}\n".format(server_node.internal_address)
            constant_file += "client={}\n".format(client_node.internal_address)
            constant_file += "ip={}\n".format(node.internal_address)
            #result = node.execute("sh -c \"ip -o -4 route show to default | awk '{print $5}'\"")
            #self.log.info(result.stdout)
            # {}\n".format(result.stdout  ) #get nic name
            constant_file += "nicName=eth0\n"
            constant_file += "testDuration={}\n".format(TIME_OUT)
            constant_file += "testType=xdp\n"

            with open("constants.sh", "w") as tempfile:
                tempfile.write(constant_file)
                tempfile.flush()

            node.shell.copy(Path("constants.sh"), Path("xdp_scripts/constants.sh"))

            result = node.execute(
                "chmod +x ./XDPDumpSetup.sh ./utils.sh ./XDPUtils.sh ./XDP-Action.sh ./util-change-mtu.sh ./utils-ping-test-client-setup.sh", cwd=Path("xdp_scripts"))
            suite.log.info(result.stdout)


@TestSuiteMetadata(
    area="provisioning",
    category="functional",
    description="""
        Check XDP functionality
        (requires accelerated networking)
    """,
)
class MultinodeDemo(TestSuite):
    path = Path("xdp_scripts")
    # @TestCaseMetadata(
    #     description="""
    #         Check installation of XDP dependencies and test run XDPDump
    #     """,
    #     priority=0,
    #     requirement=simple_requirement(
    #         environment_status=EnvironmentStatus.Deployed,
    #         supported_features=[SerialConsole],
    #         min_count=2,
    #     ),
    # )
    # def run_xdp_dump_test(self, environment: Environment) -> None:
    #     for node in environment.nodes.list():
    #         self.log.info("Setting up XDP dump on all nodes")
    #         setup_xdp_dump = InitialXdpSetup(self, environment)

    #         result = node.execute(
    #             "sh -c \"./XDPUtils.sh && ./XDPDumpSetup.sh\"", cwd=Path("xdp_scripts"))
    #         self.log.info(result.stdout)
    #         self.log.info(result.stderr)

    #     raise PassedException

    @TestCaseMetadata(
        description="""
            Test ability to change mtu
        """,
        priority=0,
        requirement=simple_requirement(
            environment_status=EnvironmentStatus.Deployed,
            supported_features=[SerialConsole],
            min_count=2,
        ),
    )
    def run_xdp_mtu_tests(self, environment: Environment) -> None:
        for node in environment.nodes.list():
            self.log.info("Setting up XDP dump on all nodes")
            setup_xdp_dump = InitialXdpSetup(self, environment)
        
        client_node = environment.nodes[1]
        server_node = environment.nodes[0]


        for mtu in [1000,2000,3000,4000]:
            for node in environment.nodes.list():
                #set MTU on both nodes
                mtu_command = "./util-change-mtu.sh eth0 {} ".format(mtu)
                result = node.execute(mtu_command, cwd=Path("xdp_scripts"))
                self.log.info(result.stdout)
                self.log.info(result.stderr)
        
            #start the client async
            client_result = client_node.execute_async("./utils-ping-test-client-setup.sh", cwd=Path("xdp_scripts"))
            #start the server pinging the client
            ping_command = "ping -I eth0 -c 10 -M do -s {0} {1} > ~/pingOut_${0}.txt".format(mtu-28, client_node.internal_address)
            server_result = server_node.execute("sh -c \"{}\"".format(ping_command))
            self.log.info(server_result.stdout)

            #check the output
            server_result = server_node.execute("sh -c \"cat ~/pingOut_${0}.txt\"".format(mtu))
            self.log.info(server_result.stdout)
            ping_check_string = "{0} bytes from {1}".format(mtu - 28, client_node.internal_address)

            # validate the packets were received and were the correct size, max_mtu-28 (ip header size)
            assert_that(ping_check_string in server_result.stdout)
            #TODO: should validate that no packets were lost

        #TODO: check max mtu, how does this get set?
        #client_result = client_node.execute("ip ")







"""
server=10.0.0.6
client="10.0.0.12,10.0.0.10,10.0.0.4,10.0.0.8,10.0.0.5,10.0.0.7,10.0.0.9,10.0.0.11"
nicName=eth0
testDuration=300
testType=udp
bufferLength=1024
testConnections=(8 16 32 64 128 256 512 1024)
ntttcpVersion=1.4.0
lagscopeVersion=v0.2.0
"""
