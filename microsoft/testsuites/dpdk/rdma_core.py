# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import re
from enum import Enum
from pathlib import PurePath
from typing import Dict
from urllib.parse import urlparse

from assertpy import fail

from lisa import Node
from lisa.operating_system import Debian, Fedora, OperatingSystem, Suse
from lisa.tools import Git, Make, Pkgconfig, Tar, Wget
from lisa.util import LisaException, SkippedException
from microsoft.testsuites.dpdk.common import InstallArch, InstallOS


class RdmaCoreManager:
    _install_cmake_line = {
        InstallArch.i386: (
            "PKG_CONFIG_LIBDIR=/usr/lib/i386-linux-gnu/pkgconfig cmake -DIN_PLACE=0 "
            "-DNO_MAN_PAGES=1 -DCMAKE_INSTALL_PREFIX=/usr "
            "-DCMAKE_C_COMPILER=/usr/bin/i686-linux-gnu-gcc -DCMAKE_C_FLAGS=-m32"
        ),
        InstallArch.x86_64: "cmake -DIN_PLACE=0 -DNO_MAN_PAGES=1 -DCMAKE_INSTALL_PREFIX=/usr",
    }
    _install_packages = {
        InstallArch.x86_64: {
            InstallOS.Debian: (
                "cmake libudev-dev "
                "libnl-3-dev libnl-route-3-dev ninja-build pkg-config "
                "valgrind python3-dev cython3 python3-docutils pandoc "
                "libssl-dev libelf-dev python3-pip libnuma-dev"
            ),
            InstallOS.Fedora: (
                "cmake gcc libudev-devel "
                "libnl3-devel pkg-config "
                "valgrind python3-devel python3-docutils  "
                "openssl-devel unzip "
                "elfutils-devel python3-pip libpcap-devel  "
                "tar wget dos2unix psmisc kernel-devel-$(uname -r)  "
                "librdmacm-devel libmnl-devel kernel-modules-extra numactl-devel  "
                "kernel-headers elfutils-libelf-devel meson ninja-build libbpf-devel "
            ),
        },
        InstallArch.i386: {
            InstallOS.Debian: (
                "gcc:i386 cmake ninja-build meson libnl-3-dev:i386 "
                "libnl-route-3-dev:i386 pkg-config valgrind libelf-dev:i386"
            ),
        },
    }

    def __init__(
        self,
        node: Node,
        rdma_core_source: str,
        rdma_core_ref: str,
        install_arch: InstallArch = InstallArch.x86_64,
    ) -> None:
        self.is_installed_from_source = False
        self.node = node
        self._rdma_core_source = rdma_core_source
        self._rdma_core_ref = rdma_core_ref
        self._build_arch = install_arch

    def get_missing_distro_packages(self) -> str:
        distro = self.node.os
        package = ""
        # check if rdma-core is installed already...
        if self.node.tools[Pkgconfig].package_info_exists("libibuverbs"):
            return package
        if isinstance(distro, Debian):
            package = "rdma-core ibverbs-providers libibverbs-dev"
        elif isinstance(distro, Suse):
            package = "rdma-core-devel librdmacm1"
        elif isinstance(distro, Fedora):
            package = "librdmacm-devel"
        else:
            fail("Invalid OS for rdma-core source installation.")
        return package

    def _check_source_install(self) -> None:
        if self._rdma_core_source:
            # accept either a tar.gz or a git tree
            if self.is_from_tarball():
                self._rdma_core_ref = ""
            elif self.is_from_git():
                # will check ref later
                pass
            else:
                raise SkippedException(
                    "rdma-core source must be rdma-core.*tar.gz "
                    f"or https://.../rdma-core.git. found {self._rdma_core_source}"
                )
        elif self._rdma_core_ref:
            # if there's a ref but no tree, use a default tree
            self._rdma_core_source = "https://github.com/linux-rdma/rdma-core.git"
        else:
            # no ref, no tree, use a default tar.gz
            self._rdma_core_source = (
                "https://github.com/linux-rdma/rdma-core/releases/"
                "download/v51.1/rdma-core-51.1.tar.gz"
            )

        self.is_installed_from_source = True

    def _get_source_pkg_error_message(self) -> str:
        return (
            "rdma-source package provided did not validate. "
            "Use https for a git named rdma-core.git or "
            "https/sftp to fetch a tar.gz package named rdma-core(.xx).tar.gz. "
            "Source site must be at visualstudio, gitlab, github, or git.launchpad.net."
            f"Found: {self._rdma_core_source}"
        )

    def is_from_git(self) -> bool:
        return bool(
            self._rdma_core_source and self._rdma_core_source.endswith("rdma-core.git")
        )

    def is_from_tarball(self) -> bool:
        return bool(
            self._rdma_core_source and self._rdma_core_source.endswith(".tar.gz")
        )

    def can_install_from_source(self) -> bool:
        return bool(self._rdma_core_source or self._rdma_core_ref)

    def do_source_install(self) -> None:
        node = self.node
        wget = node.tools[Wget]
        make = node.tools[Make]
        tar = node.tools[Tar]
        distro = node.os

        # install dependencies

        # setup looks at options and selects some reasonable defaults
        # allow a tar.gz or git
        # if ref and no tree, use the default tree at github
        # if tree and no ref, checkout latest tag
        # if tree and ref... you get the idea
        self._check_source_install()

        # for dependencies, see https://github.com/linux-rdma/rdma-core#building
        if isinstance(distro, Debian):
            distro.install_packages(
                self._install_packages[self._build_arch][InstallOS.Debian]
            )
        elif isinstance(distro, Fedora):
            distro.group_install_packages("Development Tools")
            distro.install_packages(
                self._install_packages[self._build_arch][InstallOS.Fedora]
            )
        else:
            # no-op, throw for invalid distro is before this function
            return

        if self.is_from_git():
            git = node.tools[Git]
            source_path = git.clone(
                self._rdma_core_source, cwd=node.working_path, ref=self._rdma_core_ref
            )
            # if there wasn't a ref provided, check out the latest tag
            if not self._rdma_core_ref:
                git_ref = git.get_tag(cwd=source_path)
            git.checkout(git_ref, cwd=source_path)
        elif self.is_from_tarball():
            if not urlparse(self._rdma_core_source):
                # TODO: check if this is a local file we can copy?
                raise LisaException(
                    "Expected a remote url for tarball rdma-core install."
                )
            tar_path = wget.get(
                url=(self._rdma_core_source),
                file_path=str(node.working_path),
            )

            tar.extract(tar_path, dest_dir=str(node.working_path), gzip=True, sudo=True)
            source_folder = tar_path.replace(".tar.gz", "")
            source_path = node.get_pure_path(source_folder)
        else:
            raise SkippedException(self._get_source_pkg_error_message())

        node.execute(
            self._install_cmake_line[self._build_arch],
            shell=True,
            cwd=source_path,
            sudo=True,
        )
        make.make_install(source_path)
