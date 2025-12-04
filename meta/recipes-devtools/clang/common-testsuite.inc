SUMMARY = "LLVM + Clang + LLD TestSuite"

# Common variables
LIT_COMMON_ARGS = "-v"
RESULT_DIR      = "${WORKDIR}/temp"

# ===========================
# LLVM Test
# ===========================

do_check_llvm() {
    LLVM_RESULT_LOG="${RESULT_DIR}/llvm-native-results.log"
    LIT_BIN="${B}/bin/llvm-lit"

    bbnote "Running NATIVE LLVM tests"
    bbnote "LIT         : ${LIT_BIN}"
    bbnote "TESTDIR     : ${B}/test"
    bbnote "RESULT_LOG  : ${LLVM_RESULT_LOG}"

    ${LIT_BIN} ${LIT_COMMON_ARGS} \
        --filter-out 'tools/llvm-ifs/fail-file-write.test' \
        ${B}/test \
        -o ${LLVM_RESULT_LOG}
}

# ===========================
# Clang Test
# ===========================

do_check_clang() {
    CLANG_RESULT_LOG="${RESULT_DIR}/clang-native-results.log"
    LIT_BIN="${B}/bin/llvm-lit"

    bbnote "Running NATIVE Clang tests"
    bbnote "LIT         : ${LIT_BIN}"
    bbnote "TESTDIR     : ${B}/test"
    bbnote "RESULT_LOG  : ${CLANG_RESULT_LOG}"

    ${LIT_BIN} ${LIT_COMMON_ARGS} \
        --filter-out "Clang :: Driver/aix-ld.c|Clang :: Driver/aix-rtlib.c|Clang :: Driver/amdgpu-toolchain.c|Clang :: Driver/android-unversioned-fallback-warning.cpp|Clang :: Driver/arch-specific-libdir-rpath.c|Clang :: Driver/arch-specific-libdir.c|Clang :: Driver/arm-float-abi-runtime-path.c|Clang :: Driver/avr-toolchain.c|Clang :: Driver/clang-translation.c|Clang :: Driver/compiler-rt-unwind.c|Clang :: Driver/coverage-ld.c|Clang :: Driver/csky-toolchain.c|Clang :: Driver/darwin-print-file-name.c|Clang :: Driver/fuchsia.c|Clang :: Driver/fuchsia.cpp|Clang :: Driver/fveclib.c|Clang :: Driver/instrprof-ld.c|Clang :: Driver/linux-cross.cpp|Clang :: Driver/linux-header-search.cpp|Clang :: Driver/linux-ld.c|Clang :: Driver/linux-per-target-runtime-dir.c|Clang :: Driver/mips-abi.c|Clang :: Driver/mips-cs.cpp|Clang :: Driver/mips-fsf.cpp|Clang :: Driver/mips-img-v2.cpp|Clang :: Driver/mips-img.cpp|Clang :: Driver/mips-mti.cpp|Clang :: Driver/print-file-name.c|Clang :: Driver/print-runtime-dir.c|Clang :: Driver/riscv32-toolchain-extra.c|Clang :: Driver/riscv64-toolchain-extra.c|Clang :: Driver/sanitizer-ld.c|Clang :: Driver/ve-toolchain.c|Clang :: Driver/ve-toolchain.cpp|Clang :: Driver/zos-ld.c" \
        ${B}/test \
        -o ${CLANG_RESULT_LOG}
}

# ===========================
# LLD Test
# ===========================

do_check_lld() {
    LLD_RESULT_LOG="${RESULT_DIR}/lld-native-results.log"
    LIT_BIN="${B}/bin/llvm-lit"

    bbnote "Running NATIVE LLD tests"
    bbnote "LIT         : ${LIT_BIN}"
    bbnote "TESTDIR     : ${B}/test"
    bbnote "RESULT_LOG  : ${LLD_RESULT_LOG}"

    ${LIT_BIN} ${LIT_COMMON_ARGS} --filter-out 'COFF|MachO' ${B}/test -o ${LLD_RESULT_LOG}
}

# ===========================
# Add tasks
# ===========================
addtask check_llvm after do_compile do_install
addtask check_clang after do_compile do_install
addtask check_lld after do_compile do_install

# ===========================
# Dependencies
# ===========================
do_check_llvm[depends]  += "llvm-native:do_populate_sysroot ninja-native:do_populate_sysroot"
do_check_clang[depends] += "clang-native:do_populate_sysroot ninja-native:do_populate_sysroot"
do_check_lld[depends]   += "lld-native:do_populate_sysroot ninja-native:do_populate_sysroot"
