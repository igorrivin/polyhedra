"""Exact fixed Section 12, 14 and 16 identities and their stated conventions."""

from fractions import Fraction as Q
from math import gcd

from .exact import (
    ExactChecks, Quadratic, add, constant, cosh, derivative, determinant, eye,
    inverse, matadd, matmul, matscale, multiply, power, rational, reciprocal,
    require, scale, transpose, variable,
)


def weights(values, *, nonresonant=False):
    mu = tuple(rational(x) for x in values)
    if len(mu) != 4 or any(not 0 < w < 1 for w in mu) or sum(mu) != 2:
        raise ValueError("four weights in (0,1) summing exactly to two are required")
    if nonresonant and (mu[0]+mu[2] == 1 or mu[1]+mu[2] == 1):
        raise ValueError("nonresonant s/t bases require delta0 and delta1 nonzero")
    return mu


def fricke_checks(fixture):
    checks = ExactChecks()
    A = variable()
    a2 = constant(Q(0))
    a2[2], a2[4], a2[6] = Q(1, 16), -Q(1, 3072), Q(1, 1474560)
    results = []
    for index, (us, vs) in enumerate(fixture["heron_chart"]):
        u, v = rational(us), rational(vs)
        if u <= 0 or v <= 0:
            raise ValueError("Heron chart requires u,v>0")
        X, Y, Z = 1/(2*v), (u*u+v*v)/(2*v), ((u-1)**2+v*v)/(2*v)
        x, y, z = [add(constant(Q(-2)), scale(A, -value)) for value in (X, Y, Z)]
        phi = add(power(x, 2), power(y, 2), power(z, 2), multiply(multiply(x, y), z),
                  scale(multiply(a2, add(x, y, z)), -2), scale(a2, 4), power(a2, 2),
                  constant(Q(-4)))
        quadric = X*X+Y*Y+Z*Z-2*X*Y-2*X*Z-2*Y*Z+1
        linear = -X*Y*Z+(X+Y+Z)/8
        prefix = f"heron-{index}"
        checks.equal(prefix+"-fricke-A0-A4", phi[:5], [0, 0, quadric, linear, -Q(1, 768)])
        checks.equal(prefix+"-quadric", quadric, 0)
        checks.equal(prefix+"-orientation", X+Y-Z, u/v)
        # The Jacobian is independently differentiated from the explicit chart.
        Xu, Xv, Yu, Yv = Q(0), -1/(2*v*v), u/v, Q(1, 2)-u*u/(2*v*v)
        jacobian = Xu*Yv-Xv*Yu
        checks.equal(prefix+"-jacobian", jacobian, u/(2*v**3))
        Z1 = (1-u)*(v*v-u*(1-u))/(16*v*v)
        checks.equal(prefix+"-implicit-first-correction", 2*(Z-X-Y)*Z1+linear, 0)
        denominator0, denominator1 = 2*(X+Y-Z), -2*Z1+X*Y-Q(1, 8)
        leading = 2*jacobian/denominator0
        correction = -leading*denominator1/denominator0
        checks.equal(prefix+"-goldman-leading", leading, 1/(2*v*v))
        checks.equal(prefix+"-goldman-linear", correction, -(1+u*u+v*v)/(32*v**3))
        results.append({"u": u, "v": v, "X": X, "Y": Y, "Z0": Z, "Z1": Z1,
                        "WP_over_A_leading": leading, "WP_over_A_linear": correction})
    charges = []
    for row in fixture["period_weights"]:
        mu = weights(row["mu"])
        for bs in fixture["b_values"]:
            b = rational(bs)
            if not 0 < b < 1:
                raise ValueError("charge fixture requires 0<b<1")
            gamma, background = 2*b, b+1/b
            beta = [w/b for w in mu]
            pure_s = (sum(beta)-2*background)/gamma
            shifted = [w/b+b for w in mu]
            shifted_s = (sum(shifted)-2*background)/gamma
            checks.equal(f"{row['id']}-{bs}-screening", pure_s, -1)
            checks.equal(f"{row['id']}-{bs}-shifted", shifted_s, 1)
            require(all(w < background for w in beta), "Seiberg beta<Q failed")
            require(1 < 1/b**2 and all(1 < 1+(1-w)/b**2 for w in mu),
                    "extended first moment inequalities failed")
            checks.equal(f"{row['id']}-{bs}-kernel-weights", [gamma*x for x in beta],
                         [2*w for w in mu])
            # A/pi is rational; no numerical pi occurs in the scaling check.
            area_over_pi = Q(3, 7)
            heavy_sum = 2+area_over_pi/2
            checks.equal(f"{row['id']}-{bs}-heavy-path", (heavy_sum/b-2*background)/(2*b),
                         area_over_pi/(4*b*b)-1)
            charges.append({"weights_id": row["id"], "b": b, "pure_s": pure_s,
                            "unshifted_dictionary_s": shifted_s})
    auxiliary = [[Q(1), -Q(1, 3), 0, 0], [-Q(1, 3), 1, 0, 0],
                 [0, 0, 1, -Q(2, 5)], [0, 0, -Q(2, 5), 1]]
    checks.equal("auxiliary-full-rank-determinant", determinant(auxiliary), Q(56, 75))
    return checks.result(heron_fixtures=results, charges=charges,
                         auxiliary_gram_determinant=determinant(auxiliary))


def regular_checks():
    checks = ExactChecks()
    root2, root3 = Quadratic(0, 1, 2), Quadratic(0, 1, 3)
    x = variable(2)  # x=ell^2, coefficients through ell^4.
    cosh_ell = [Q(1), Q(1, 2), Q(1, 24)]
    cos_beta = multiply(cosh_ell, reciprocal(add(constant(Q(1), 2), cosh_ell)))
    area = add(scale(x, root3), scale(power(x, 2), -root3/8))
    beta_defect = scale(area, Q(1, 12))
    from_area = add(constant(Q(1, 2), 2), scale(beta_defect, root3/2),
                    scale(power(beta_defect, 2), -Q(1, 4)))
    checks.equal("regular-face-area-Taylor", from_area, cos_beta)
    t = add(scale(x, 1/(12*root2)), scale(power(x, 2), -23/(1152*root2)))
    cos_eta = multiply(cosh_ell, reciprocal(add(constant(Q(1), 2), scale(cosh_ell, 2))))
    from_t = add(constant(Q(1, 3), 2), scale(t, 2*root2/3), scale(power(t, 2), -Q(1, 6)))
    checks.equal("regular-dihedral-Taylor", from_t, cos_eta)
    checks.equal("Schlaefli-ell3", 2*t[1], 1/(6*root2))
    checks.equal("Schlaefli-ell5", Q(12, 5)*t[2], -23/(480*root2))
    checks.equal("area-to-volume-relative-correction", -Q(3, 16)-Q(1, 10), -Q(23, 80))
    euclidean = [[Q(1) if i == j else -Q(1, 3) for j in range(4)] for i in range(4)]
    checks.equal("regular-Euclidean-det", determinant(euclidean), 0)
    checks.equal("regular-Euclidean-principal-minor", determinant([r[:3] for r in euclidean[:3]]),
                 Q(16, 27))
    u = variable(4)
    folded = None
    for index, a in enumerate((Quadratic(2, 1, -2)/3, Quadratic(1, 2, -2)/3)):
        left = power(add(constant(Q(1), 4), scale(u, a**3)), 4)
        right = multiply(add(constant(Q(1), 4), scale(u, -1)),
                         power(add(constant(Q(1), 4), scale(u, -a**4)), 3))
        qa, qb, qc = a**8*(a*a-2*a+3), -3*a**4*(a-1)**2, 3*a*a-2*a+1
        poly = [qc, qb, qa, Q(0), Q(0)]
        checks.equal(f"regular-saddle-factor-{index}", add(left, scale(right, -1)),
                     scale(multiply(u, poly), (a+1)**2))
        checks.equal(f"regular-discriminant-{index}", qb*qb-4*qa*qc,
                     -a**8*(a+1)**2*(3*a*a-2*a+3))
        if index == 1:
            uE = a**-5
            checks.equal("regular-fold-root", uE, Quadratic(241, 22, -2)/243)
            checks.equal("regular-fold-polynomial", qa*uE*uE+qb*uE+qc, 0)
            checks.equal("regular-fold-first-derivative", 2*qa*uE+qb, 0)
            require(qa != 0 and uE != 1 and a**4*uE != 1 and -a**3*uE != 1,
                    "fold must be quadratic and away from the displayed dilogarithm branches")
            folded = {"a_E": a, "u_E": uE, "quadratic_coefficient": qa}
    # The reduced screened saddle has no quadratic term, independently of the regular fold.
    P, R = Q(2, 3), Q(-4, 5)
    left = multiply(add(constant(Q(1), 4), scale(u, -P)),
                    add(constant(Q(1), 4), scale(u, -R)))
    right = multiply(add(constant(Q(1), 4), scale(u, -1)),
                     add(constant(Q(1), 4), scale(u, -P*R)))
    checks.equal("screened-saddle-cancellation", add(left, scale(right, -1)), scale(u, (1-P)*(1-R)))
    return checks.result(area_in_ell_squared=area, dihedral_defect_in_ell_squared=t, fold=folded)


def validate_slope(p, q, rho, sigma, *, action=True):
    if any(type(x) is not int for x in (p, q, rho, sigma)):
        raise ValueError("slope and basis entries must be integers")
    if gcd(p, q) != 1 or p*sigma-q*rho != 1:
        raise ValueError("a primitive oriented SL2(Z) peripheral basis is required")
    if action and q == 0:
        raise ValueError("this action chart requires q!=0; exchange the peripheral basis")


def filling_inverse(tau, c3, c5, p, q):
    """Invert a=p*u+q*v through degree six; coefficients are solved recursively."""
    denominator = p+q*tau
    if denominator == 0:
        raise ValueError("the formal filling derivative is zero")
    result = constant(Q(0))
    for n in range(1, 7):
        nonlinear = add(scale(power(result, 3), q*c3), scale(power(result, 5), q*c5))
        result[n] = (Q(n == 1)-nonlinear[n])/denominator
    return result


def surgery_checks(fixture):
    checks = ExactChecks()
    root = Quadratic(0, 1, -3)
    tau, c3, c5 = 2*root, Q(2, 3)*root, Q(23, 90)*root
    u0 = variable()
    v0 = add(scale(u0, tau), scale(power(u0, 3), c3), scale(power(u0, 5), c5))
    checks.equal("figure-eight-local-curve-through-u6", cosh(scale(v0, Q(1, 2))),
                 add(constant(Q(1)), cosh(u0), scale(cosh(scale(u0, 2)), -1)))
    results = []
    for row in fixture["slopes"]:
        p, q, rho, sigma = row
        validate_slope(p, q, rho, sigma, action=False)
        prefix = f"slope-{p}-{q}"
        A = p+q*tau
        inv = filling_inverse(tau, c3, c5, p, q)
        explicit = constant(Q(0))
        explicit[1], explicit[3] = 1/A, -q*c3/A**4
        explicit[5] = 3*q*q*c3*c3/A**7-q*c5/A**6
        checks.equal(prefix+"-inverse", inv, explicit)
        v = add(scale(inv, tau), scale(power(inv, 3), c3), scale(power(inv, 5), c5))
        checks.equal(prefix+"-filling-residual-through-a6", add(scale(inv, p), scale(v, q)), variable())
        b = add(scale(inv, rho), scale(v, sigma))
        covariant = constant(Q(0))
        covariant[1], covariant[3] = (rho+sigma*tau)/A, c3/A**4
        covariant[5] = c5/A**6-3*q*c3*c3/A**7
        checks.equal(prefix+"-basis-covariance", b, covariant)
        transformed_tau = covariant[1]
        # Imag(tau)=2*sqrt(3), so compare coefficients of sqrt(3).
        checks.equal(prefix+"-positive-imaginary-transform", transformed_tau.b,
                     tau.b/(A*A.conjugate()).a)
        record = {"basis": row, "u_in_a": inv, "b_in_a": b}
        if q:
            validate_slope(p, q, rho, sigma)
            F = add(scale(power(inv, 2), tau/2), scale(power(inv, 4), c3/4),
                    scale(power(inv, 6), c5/6))
            action_a = add(F, scale(power(inv, 2), Q(p, 2*q)),
                           scale(multiply(variable(), inv), -Q(1, q)))
            action_theta = [value*((-1)**(n//2)) if n % 2 == 0 else value
                            for n, value in enumerate(action_a)]
            expected = constant(Q(0))
            expected[2], expected[4] = 1/(2*q*A), c3/(4*A**4)
            expected[6] = (3*q*c3*c3/A**7-c5/A**6)/6
            checks.equal(prefix+"-stationary-action-through-theta6", action_theta, expected)
            i_factored_u_theta = [value*((-1)**((n-1)//2)) if n % 2 else value
                                  for n, value in enumerate(inv)]
            checks.equal(prefix+"-envelope", derivative(action_theta),
                         scale(i_factored_u_theta, Q(1, q))[:-1])
            vprime = add(constant(tau), scale(power(inv, 2), 3*c3), scale(power(inv, 4), 5*c5))
            gaussian_squared = reciprocal(add(constant(Q(p)), scale(vprime, q)))
            checks.equal(prefix+"-Gaussian-Jacobian-through-a4", gaussian_squared[:5], derivative(inv)[:5])
            G = add(scale(power(inv, 2), Q(p, 4*q)),
                    scale(multiply(inv, variable()), -Q(1, 2*q)),
                    scale(power(variable(), 2), Q(sigma, 4*q)))
            boundary = scale(add(multiply(variable(), b), scale(multiply(inv, v), -1)), Q(1, 4))
            checks.equal(prefix+"-canonical-G", G, boundary)
            for uf, af in ((Q(2, 3), Q(4, 5)), (Q(-1, 2), Q(3, 7))):
                vf, bf = (af-p*uf)/q, (sigma*af-uf)/q
                checks.equal(prefix+f"-dGdu-{uf}", (p*uf-af)/(2*q), -vf/2)
                checks.equal(prefix+f"-dGda-{uf}", (sigma*af-uf)/(2*q), bf/2)
            record["action_in_theta"] = action_theta
            record["u_theta_divided_by_i"] = i_factored_u_theta
        results.append(record)
    return checks.result(tau=tau, c3=c3, c5=c5, slopes=results,
                         convention="u,v are multiplier logs; a=pu+qv; a=i*theta only after formal inversion")


def tensor_checks(fixture):
    checks = ExactChecks()
    sqrt3 = Quadratic(0, 1, 3)
    K = matscale([[4, -1, 3], [-1, 4, -3], [3, -3, 6]], 1/sqrt3)
    P = [[Q(0), -Q(1), Q(1)], [Q(2), -Q(2), Q(0)]]
    E = [[1, 0, 0], [0, 1, 0], [-1, -1, 0], [0, 0, 1], [1, -1, 1], [-1, 1, -2]]
    checks.equal("angle-Hessian-from-tetrahedron-angles", matscale(matmul(transpose(E), E), 1/sqrt3), K)
    Kinv = inverse(K)
    response = matmul(matmul(P, Kinv), transpose(P))
    checks.equal("figure-eight-peripheral-response", response, matscale([[1, 0], [0, 12]], 1/sqrt3))
    checks.equal("figure-eight-response-determinant", determinant(response), 4)
    results = []
    for p, q, rho, sigma in fixture["slopes"]:
        validate_slope(p, q, rho, sigma, action=False)
        prefix = f"tensor-{p}-{q}"
        L = matmul([[Q(p), Q(q)]], P)
        dual = matmul(Kinv, transpose(L))
        chi = matmul(L, dual)[0][0]
        D = p*p+12*q*q
        checks.equal(prefix+"-susceptibility", chi, D/sqrt3)
        e = matscale(dual, 1/chi)
        checks.equal(prefix+"-constrained-direction", e,
                     [[Q(6*q-p, 2*D)], [Q(-6*q-p, 2*D)], [Q(p-6*q, 2*D)]])
        R = matadd(Kinv, matscale(matmul(dual, transpose(dual)), 1/chi), -1)
        checks.equal(prefix+"-constraint", matmul(L, e), [[1]])
        checks.equal(prefix+"-projected-inverse", matmul(L, R), [[0, 0, 0]])
        Ee = [r[0] for r in matmul(E, e)]
        cubic = Q(4, 3)*sum(value**3 for value in Ee)
        checks.equal(prefix+"-odd-cubic", cubic, 0)
        t = matscale(matmul(transpose(E), [[value*value] for value in Ee]), Q(4, 3))
        fourth = -8/(3*sqrt3)*sum(value**4 for value in Ee)
        corrected = fourth+3*matmul(matmul(transpose(t), R), t)[0][0]
        expected = 2*sqrt3*Q(p**4-72*p*p*q*q+144*q**4, D**4)
        checks.equal(prefix+"-quartic-Schur-correction", corrected, expected)
        complex_root = Quadratic(0, 1, -3)
        complex_coefficient = Q(2, 3)*complex_root/(p+2*q*complex_root)**4
        checks.equal(prefix+"-quartic-NZ-match", corrected, 3*complex_coefficient.b*sqrt3)
        results.append({"slope": [p, q], "chi": chi, "cubic": cubic, "corrected_quartic": corrected})
    return checks.result(K=K, peripheral_response=response, slopes=results)


def block_matrix(aa, ab, ba, bb):
    return [x+y for x, y in zip(aa, ab)]+[x+y for x, y in zip(ba, bb)]


def hessian_checks():
    checks = ExactChecks()
    U = [[Q(2), 0, 2, 0], [Q(0), 1, 1, 0], [Q(1), 1, 1, 1]]
    J = [[Q(0), 0, 1, 0], [Q(0), 0, 0, 1], [-Q(1), 0, 0, 0], [Q(0), -1, 0, 0]]
    checks.equal("NZ-row-pairing", matmul(matmul(U, J), transpose(U)),
                 [[0, 2, 0], [-2, 0, 0], [0, 0, 0]])
    a, b = Q(2, 5), Q(7, 3)
    g = matscale([[a*a+b*b, -a], [-a, Q(1)]], 1/(2*b))
    response = matscale([[Q(1), a], [a, a*a+b*b]], 2/b)
    complex_structure = matscale([[-a, Q(1)], [-a*a-b*b, a]], 1/b)
    W = [[Q(0), -Q(1, 2)], [Q(1, 2), Q(0)]]
    coordinate = [[Q(0), Q(1)], [b, a]]
    checks.equal("one-cusp-Schur", matmul(g, response), eye(2))
    checks.equal("one-cusp-Hessian-determinant", determinant(g), Q(1, 4))
    checks.equal("one-cusp-complex-structure", matmul(complex_structure, complex_structure), matscale(eye(2), -1))
    checks.equal("one-cusp-compatible-metric", matmul(W, complex_structure), g)
    checks.equal("one-cusp-log-coordinate-metric", matmul(matmul(transpose(coordinate), g), coordinate), matscale(eye(2), b/2))
    # One conditional two-cusp point; symmetric A0 and positive definite B0.
    A = [[Q(1, 3), Q(1, 5)], [Q(1, 5), -Q(2, 7)]]
    B = [[Q(2), Q(1, 3)], [Q(1, 3), Q(3, 2)]]
    require(B[0][0] > 0 and determinant(B) > 0, "two-cusp B must be positive definite")
    Bi = inverse(B)
    top = matadd(B, matmul(matmul(A, Bi), A))
    metric = matscale(block_matrix(top, matscale(matmul(A, Bi), -1),
                                   matscale(matmul(Bi, A), -1), Bi), Q(1, 2))
    inv_metric = matscale(block_matrix(Bi, matmul(Bi, A), matmul(A, Bi), top), 2)
    zero = [[Q(0), Q(0)], [Q(0), Q(0)]]
    omega = matscale(block_matrix(zero, matscale(eye(2), -1), eye(2), zero), Q(1, 2))
    jt = matmul(inverse(omega), metric)
    checks.equal("two-cusp-block-Schur", matmul(metric, inv_metric), eye(4))
    checks.equal("two-cusp-determinant", determinant(metric), Q(1, 16))
    checks.equal("two-cusp-complex-structure", matmul(jt, jt), matscale(eye(4), -1))
    checks.equal("two-cusp-compatible-metric", matmul(omega, jt), metric)
    return checks.result(one_cusp_metric=g, two_cusp_A=A, two_cusp_B=B,
                         two_cusp_metric=metric, two_cusp_determinant=determinant(metric),
                         scope="Conditional matrix algebra at fixed rational data, not a manifold construction")
