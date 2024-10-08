#!/bin/bash
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the Apache License.

sys_kexec_crash=/sys/kernel/kexec_crash_loaded

#
# Source utils.sh to get more utils
# Get $DISTRO, LogMsg directly from utils.sh
#
. utils.sh || {
    echo "Error: unable to source utils.sh!"
    exit 0
}

. constants.sh || {
    LogMsg "Warn: No constants.sh found"
}

#
# Source constants file and initialize most common variables
#
UtilsInit

Exec_Rhel()
{
    LogMsg "Waiting 50 seconds for kdump to become active."
    sleep 50

    case $DISTRO in
    "redhat_6" | "centos_6")
        #
        # RHEL6, kdump status has "operational" and "not operational"
        # So, select "not operational" to check inactive
        #
        service kdump status | grep "not operational"
        if  [ $? -eq 0 ]
        then
            LogErr "kdump service is not active after reboot!"
            SetTestStateAborted
            exit 0
        else
            UpdateSummary "Success: kdump service is active after reboot."
        fi
        ;;
    "redhat_7" | "redhat_8" | "centos_7" | "centos_8" | "fedora" | "almalinux_8" | "rockylinux_8")
        #
        # RHEL7, kdump status has "Active: active" and "Active: inactive"
        # So, select "Active: active" to check active
        #
        timeout=50
        while [ $timeout -ge 0 ]; do
            service kdump status | grep "Active: active" &>/dev/null
            if [ $? -eq 0 ];then
                break
            else
                LogMsg "Wait for kdump service to be active."
                timeout=$((timeout-5))
                sleep 5
            fi
        done
        if  [ $timeout -gt 0 ]; then
            UpdateSummary "Success: kdump service is active after reboot."
        else
            LogErr "kdump service is not active after reboot!"
            SetTestStateAborted
            exit 0
        fi
        ;;
        *)
            LogErr "FAIL: Unknown OS!"
            SetTestStateAborted
            exit 0
        ;;
    esac
}

Exec_Sles()
{
    LogMsg "Waiting 50 seconds for kdump to become active."
    sleep 50

    if systemctl is-active kdump.service | grep -q "active"; then
        UpdateSummary "Success: kdump service is active after reboot."
    else
        rckdump status | grep "running"
        if [ $? -ne 0 ]; then
            LogErr "ERROR: kdump service is not active after reboot!"
            SetTestStateAborted
            exit 0
        else
            UpdateSummary "Success: kdump service is active after reboot."
        fi
    fi
}

Exec_Debian()
{
    LogMsg "Waiting 50 seconds for kdump to become active."
    sleep 50

    if [ -e $sys_kexec_crash -a $(cat $sys_kexec_crash) -eq 1 ]; then
        UpdateSummary "Success: kdump service is active after reboot."
    else
        LogErr "ERROR: kdump service is not active after reboot!"
        SetTestStateAborted
        exit 0
    fi
}

Check_KDUMP()
{
    LogMsg "Checking if kdump is loaded after reboot..."
    CRASHKERNEL=$(grep -i crashkernel= /proc/cmdline);

    if [ ! -e $sys_kexec_crash ] && [ -z "$CRASHKERNEL" ] ; then
        LogErr "FAILED: Verify the configuration settings for kdump and grub. Kdump is not enabled after reboot."
        SetTestStateFailed
        exit 0
    else
        UpdateSummary "Success: Kdump is loaded after reboot."
    fi
}

Exec_mariner()
{
    LogMsg "Waiting 50 seconds for kdump to become active."
    sleep 50

    timeout=50
    while [ $timeout -ge 0 ]; do
        systemctl status kdump | grep "Active: active" &>/dev/null
        if [ $? -eq 0 ];then
            break
        else
            LogMsg "Wait for kdump service to be active."
            timeout=$((timeout-5))
            sleep 5
        fi
    done
    if  [ $timeout -gt 0 ]; then
        UpdateSummary "Success: kdump service is active after reboot."
    else
        LogErr "kdump service is not active after reboot!"
        SetTestStateFailed
        exit 0
    fi
}

Configure_NMI()
{
    # /proc/sys/kernel/unknown_nmi_panic:
    # The value in this file affects behavior of handling NMI. When the value is
    # non-zero, unknown NMI is trapped and then panic occurs. If need to dump the
    # crash, the value should be set 1.
    # Some architectures don't provide architected NMIs,such as ARM64. So this file
    # doesn't exist.
    if [ -e "/proc/sys/kernel/unknown_nmi_panic" ] ; then
        sysctl -w kernel.unknown_nmi_panic=1
        if [ $? -ne 0 ]; then
            LogErr "Failed to enable kernel to call panic when it receives a NMI."
            SetTestStateAborted
            exit 0
        else
            UpdateSummary "Success: enabling kernel to call panic when it receives a NMI."
        fi
    else
        UpdateSummary "The kernel may not support to NMI. Ignore it and keep running."
    fi
}

#######################################################################
#
# Main script body
#
#######################################################################

#
# Configure kdump - this has distro specific behaviour
#
# Must allow some time for the kdump service to become active
GetDistro

Configure_NMI
[[ "$OS_FAMILY" == "Sles" ]] && systemctl start atd

Check_KDUMP
Exec_"${OS_FAMILY}"

LogMsg "Preparing for kernel panic..."
sync && sleep 10

echo 1 > /proc/sys/kernel/sysrq

SetTestStateCompleted
exit 0
