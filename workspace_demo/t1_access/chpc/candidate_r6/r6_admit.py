"""R6' admission wrapper (test_r6_fleet.py only): run the REAL prod_launch.main() of a fake promoted tree.

    python3 r6_admit.py <fake t1_access> <prod_launch arguments...>

The ONE declared substitution: the toolchain tarball pin (bench_launch.PINS['t1_toolchain_lengau.tgz']) is set to the
synthetic tarball's sha256 in $R6_TARBALL_SHA, exactly as aws_ec2/tests/test_prod_launch.py does; the 224 MB real tarball
is neither read nor needed. Everything else - the global authority lock, the run lock, the ledgers, the sealed inventory
generations, the budget/fleet/epoch reservations, the receipt and STOP gates, dispatch and the detached reaper - is the
fake tree's unmodified code, which resolves every path inside that tree."""
import os, sys

t1 = os.path.abspath(sys.argv[1])
aws = os.path.join(t1, "aws_ec2")
sys.path.insert(0, aws)
import prod_launch as PL                                   # the fake tree's copy (its own file resolves T1 and HERE)
assert os.path.dirname(os.path.abspath(PL.__file__)) == aws and PL.PA.HERE == aws, (PL.__file__, PL.PA.HERE)
PL.L.PINS = dict(PL.L.PINS, **{"t1_toolchain_lengau.tgz": os.environ["R6_TARBALL_SHA"]})
sys.argv = [os.path.join(aws, "prod_launch.py")] + sys.argv[2:]
sys.exit(PL.main())
