"""Exact arithmetic illustrations for the independent Section 9 proof review.

These checks verify rational constants, not the general mathematical arguments.
No maintained package or numerical solver is imported.
"""

from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path


def encode(value):
    return {"numerator": value.numerator, "denominator": value.denominator}


def main():
    centered = Q(1, 4)
    parameter_change_at_m_one = Q(1, 20)
    before = (1 + parameter_change_at_m_one) * centered + parameter_change_at_m_one
    exact_after = (before / (1 - before)) ** 2
    eta = before / 100
    radius = before + eta
    inexact_after = eta / (1 - radius) + radius**2 / (1 - radius) ** 2
    gap_at_m_one = 1 + (1 + centered) * centered / (1 - centered)
    assert before == Q(5, 16)
    assert exact_after == Q(25, 121) < centered
    assert eta == Q(1, 320)
    assert radius == Q(101, 320) < 1
    assert inexact_after == Q(10420, 47961) < centered
    assert gap_at_m_one == Q(17, 12)
    # For u=sqrt(m)>=1, the gap coefficient comparison is a polynomial
    # identity with a nonnegative factored remainder (u-1)(5u+1)/12.
    # Coefficients are in increasing order: constant, u, u^2.
    direct = [-Q(1, 12), -Q(1, 3), Q(17, 12) - 1]
    factored = [-Q(1, 12), -Q(4, 12), Q(5, 12)]
    assert direct == factored
    script = Path(__file__).resolve()
    result = {
        "status": "exact_rational_constant_checks_passed",
        "scope": "Finite arithmetic illustrations; general proofs are in proof-review.md.",
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "values": {
            "new_parameter_decrement_upper_bound": encode(before),
            "exact_step_decrement_upper_bound": encode(exact_after),
            "exact_step_margin_below_one_quarter": encode(centered - exact_after),
            "inexact_step_error_upper_bound": encode(eta),
            "inexact_step_norm_upper_bound": encode(radius),
            "inexact_step_decrement_upper_bound": encode(inexact_after),
            "inexact_step_margin_below_one_quarter": encode(centered - inexact_after),
            "finite_center_gap_factor_at_m_one": encode(gap_at_m_one),
        },
        "general_m_remainder": "(sqrt(m)-1)*(5*sqrt(m)+1)/12 >= 0 for m>=1",
    }
    script.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "output": str(script.with_suffix('.json'))}))


if __name__ == "__main__":
    main()
