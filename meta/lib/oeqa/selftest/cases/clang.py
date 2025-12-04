#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#

import time
import logging
import contextlib

from oeqa.core.decorator import OETestTag
from oeqa.selftest.case import OESelftestTestCase
from oeqa.utils.commands import bitbake, get_bb_var, runqemu
from oeqa.utils.nfs import unfs_server

class LLVMClangLLDNativeTests(OESelftestTestCase):
    """
    Run the full LLVM, Clang and LLD native lit test suites
    plus optional target builds.
    """

    def run_native_check_task(self, recipe, task):
        """Run a single -c check_* task and return duration in seconds"""
        self.logger.info("Running bitbake %s -c %s", recipe, task)
        start_time = time.time()
        try:
            bitbake(f"{recipe} -c {task}")
            passed = True
        except Exception as e:
            self.logger.error("bitbake %s -c %s FAILED: %s", recipe, task, e)
            passed = False
        finally:
            duration = int(time.time() - start_time)
            status = "PASSED" if passed else "FAILED"
            self.logger.info("%s -c %s → %s (%d seconds)", recipe, task, status, duration)

        if not passed:
            raise AssertionError(f"{recipe} -c {task} failed — see log above")
        return duration

    def run_target_build(self, recipe):
        """Run a full target bitbake build (no -c argument) and return duration"""
        self.logger.info("Running bitbake %s", recipe)
        start_time = time.time()
        try:
            bitbake(recipe)
            passed = True
        except Exception as e:
            self.logger.error("bitbake %s FAILED: %s", recipe, e)
            passed = False
        finally:
            duration = int(time.time() - start_time)
            status = "PASSED" if passed else "FAILED"
            self.logger.info("%s → %s (%d seconds)", recipe, status, duration)

        if not passed:
            raise AssertionError(f"{recipe} build failed — see log above")
        return duration

    @OETestTag("toolchain-user")
    @OETestTag("run-on-build")
    def test_native_llvm_clang_lld_lit_suites(self):
        """Run native LLVM/Clang/LLD lit test suites."""
        self.logger.info("=" * 70)
        self.logger.info("STARTING LLVM + CLANG + LLD NATIVE LIT TEST SUITES")
        self.logger.info("=" * 70)

        total_start = time.time()
        llvm_duration  = self.run_native_check_task("llvm-native",  "check_llvm")
        clang_duration = self.run_native_check_task("clang-native", "check_clang")
        lld_duration   = self.run_native_check_task("lld-native",   "check_lld")
        total_duration = int(time.time() - total_start)

        self.logger.info("=" * 70)
        self.logger.info("ALL LIT TEST SUITES COMPLETED SUCCESSFULLY")
        self.logger.info("  llvm-native  -c check_llvm  : %d s", llvm_duration)
        self.logger.info("  clang-native -c check_clang : %d s", clang_duration)
        self.logger.info("  lld-native   -c check_lld   : %d s", lld_duration)
        self.logger.info("  TOTAL EXECUTION TIME        : %d s", total_duration)
        self.logger.info("=" * 70)

        self.assertTrue(True, "All LLVM/Clang/LLD native lit suites passed")

    @OETestTag("toolchain-user")
    @OETestTag("run-on-build")
    def test_target_llvm_clang_lld_builds(self):
        """Build LLVM/Clang/LLD for target, start QEMU, setup NFS, run llvm-lit."""
        self.logger.info("=" * 70)
        self.logger.info("STARTING TARGET LLVM/CLANG/LLD BUILDS")
        self.logger.info("=" * 70)

        total_start = time.time()
        llvm_duration  = self.run_target_build("llvm")
        clang_duration = self.run_target_build("clang")
        lld_duration   = self.run_target_build("lld")
        cim_duration   = self.run_target_build("core-image-minimal")
        total_duration = int(time.time() - total_start)

        self.logger.info("=" * 70)
        self.logger.info("ALL TARGET BUILDS COMPLETED SUCCESSFULLY")
        self.logger.info("  llvm  build : %d s", llvm_duration)
        self.logger.info("  clang build : %d s", clang_duration)
        self.logger.info("  lld   build : %d s", lld_duration)
        self.logger.info("  core-image-minimal build : %d s", cim_duration)
        self.logger.info("  TOTAL BUILD TIME : %d s", total_duration)
        self.logger.info("=" * 70)

        # === Start QEMU + NFS setup ===
        with contextlib.ExitStack() as s:
            tmpdir = get_bb_var("TMPDIR")
            qemu = s.enter_context(runqemu("core-image-minimal", runqemuparams="nographic", qemuparams = "-m 8192"))
            nfsport, mountport = s.enter_context(unfs_server(tmpdir))

            # Validate SSH
            status, _ = qemu.run("uname")
            self.assertEqual(status, 0, "QEMU SSH check failed")

            # Setup NFS mount on target
            status, _ = qemu.run(f"mkdir -p \"{tmpdir}\"")
            if status != 0:
                raise Exception("Failed to setup NFS mount directory on target")

            mountcmd = (
                f"mount -o noac,nfsvers=3,port={nfsport},udp,mountport={mountport} "
                f"\"{qemu.server_ip}:{tmpdir}\" \"{tmpdir}\""
            )
            status, output = qemu.run(mountcmd)
            if status != 0:
                raise Exception(f"Failed to setup NFS mount on target ({repr(output)})")

            self.logger.info("Successfully mounted")

            # Run llvm-lit on target
            build_dir_lld  = f"{tmpdir}/work/x86-64-v3-oe-linux/lld/21.1.4/build"
            lit_bin_lld    = f"{build_dir_lld}/bin/llvm-lit"
            test_dir_lld   = f"{build_dir_lld}/test"
            host_result_lld = f"{build_dir_lld}/lld-target-results.log"

            build_dir_llvm  = f"{tmpdir}/work/x86-64-v3-oe-linux/llvm/21.1.4/build"
            lit_bin_llvm    = f"{build_dir_llvm}/bin/llvm-lit"
            test_dir_llvm   = f"{build_dir_llvm}/test"
            host_result_llvm = f"{build_dir_llvm}/llvm-target-results.log"

            build_dir_clang  = f"{tmpdir}/work/x86-64-v3-oe-linux/clang/21.1.4/build"
            lit_bin_clang    = f"{build_dir_clang}/bin/llvm-lit"
            test_dir_clang   = f"{build_dir_clang}/test"
            host_result_clang = f"{build_dir_clang}/clang-target-results.log"
 
            guest_result_lld = "/tmp/lld-target-results.json"
            guest_result_llvm = "/tmp/llvm-target-results.json"
            guest_result_clang = "/tmp/clang-target-results.json"

            self.logger.info("Running llvm-lit directly on target")
            self.logger.info(f"  LIT BIN  : {lit_bin_lld}")
            self.logger.info(f"  TESTDIR  : {test_dir_lld}")
            self.logger.info(f"  LOGFILE  : {guest_result_lld}")

            cmd = f"cd {build_dir_lld}/bin && ./llvm-lit -v --filter-out 'COFF|MachO|MinGW' -j1 ../test -o {guest_result_lld}"
            status, output = qemu.run(cmd)
            if status != 0:
                self.logger.error("llvm-lit tests FAILED on target for lld")
                self.logger.error(output)
                raise AssertionError("llvm-lit failed on target for lld — see log above")

            status, _ = qemu.run(f"cp {guest_result_lld} {host_result_lld}")
            if status != 0:
                raise AssertionError("Failed to copy LLD lit results back to host")

            self.logger.info(f"  LIT BIN  : {lit_bin_llvm}")
            self.logger.info(f"  TESTDIR  : {test_dir_llvm}")
            self.logger.info(f"  LOGFILE  : {guest_result_llvm}")

            cmd = f"cd {build_dir_llvm}/bin && ./llvm-lit --filter-out 'COFF|MachO|MinGW' -j1 ../test -o {guest_result_llvm}"
            status, output = qemu.run(cmd)
            if status != 0:
                self.logger.error("llvm-lit tests FAILED on target for llvm")
                self.logger.error(output)
                raise AssertionError("llvm-lit failed on target for llvm — see log above")

            status, _ = qemu.run(f"cp {guest_result_llvm} {host_result_llvm}")
            if status != 0:
                raise AssertionError("Failed to copy llvm lit results back to host")

            self.logger.info(f"  LIT BIN  : {lit_bin_clang}")
            self.logger.info(f"  TESTDIR  : {test_dir_clang}")
            self.logger.info(f"  LOGFILE  : {guest_result_clang}")
              
            cmd = f"cd {build_dir_clang}/bin && ./llvm-lit -j2 ../test -o {guest_result_clang}"
            status, output = qemu.run(cmd, timeout=1000)
            if status != 0:
                self.logger.error("llvm-lit tests FAILED on target for clang")
                self.logger.error(output)
                raise AssertionError("llvm-lit failed on target for clang — see log above")

            status, _ = qemu.run(f"cp {guest_result_clang} {host_result_clang}")
            if status != 0:
                raise AssertionError("Failed to copy LLVM lit results back to host")

            self.logger.info("llvm-lit tests completed successfully on target")
            self.logger.info(output)

        self.assertTrue(True, "All target LLVM/Clang/LLD builds and NFS tests passed")
