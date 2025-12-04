do_check_testsuite() {
    if [ -d "${B}/test" ]; then
        TEST_DIR="${B}/test"
    elif [ -d "${B}/${PN}/test" ]; then
        TEST_DIR="${B}/${PN}/test"
    else
        bbnote "No test directory found for ${PN}"
        return 0
    fi
    RESULT_LOG="${WORKDIR}/temp/native-results.log"
    LIT_BIN="${B}/bin/llvm-lit"

    # Common exclusions (archs + OSs)
    ALL_ARCHS="aarch64 arm i386 x86_64 mips riscv ppc ppc64 hexagon sparc sparcv9 msp430 loongarch"
    EXCLUDE_OS="Mac|macho|COFF|Darwin|OSX|Windows|Win|MinGW|FreeBSD|aix|fuchsia|ve|zos"

    FILTER_OUT=""
    for A in $ALL_ARCHS; do
        FILTER_OUT="${FILTER_OUT:+$FILTER_OUT|}$A"
    done
    FILTER_OUT="${FILTER_OUT}|${EXCLUDE_OS}"

    bbnote "Running $MODULE tests"
    bbnote "TESTDIR     : $TEST_DIR"
    bbnote "RESULT_LOG  : $RESULT_LOG"
    bbnote "FILTER_OUT  : $FILTER_OUT"

    ${LIT_BIN} ${LIT_COMMON_ARGS} --filter-out "$FILTER_OUT" "$TEST_DIR" -o "$RESULT_LOG"
}

addtask do_check_testsuite after do_compile do_install
do_check_testsuite[depends]   += "llvm-native:do_populate_sysroot clang-native:do_populate_sysroot lld-native:do_populate_sysroot libcxx-native:do_populate_sysroot compiler-rt-native:do_populate_sysroot ninja-native:do_populate_sysroot"
