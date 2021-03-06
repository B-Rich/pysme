"""Numerical integration techniques

    .. module:: sde.py
       :synopsis: Numerical integration techniques
    .. moduleauthor:: Jonathan Gross <jarthurgross@gmail.com>

"""

import numpy as np

def euler(drift_fn, diffusion_fn, X0, ts, Us):
    r"""Integrate a system of ordinary stochastic differential equations subject
    to scalar noise:

    .. math::

       d\vec{X}=\vec{a}(\vec{X},t)\,dt+\vec{b}(\vec{X},t)\,dW_t

    Uses the Euler method:

    .. math::

       \vec{X}_{i+1}=\vec{X}_i+\vec{a}(\vec{X}_i,t_i)\Delta t_i+
       \vec{b}(\vec{X}_i,t_i)\Delta W_i

    where :math:`\Delta W_i=U_i\sqrt{\Delta t}`, :math:`U` being a normally
    distributed random variable with mean 0 and variance 1.

    Parameters
    ----------
    drift_fn : callable(X, t)
        Computes the drift coefficient :math:`\vec{a}(\vec{X},t)`
    diffusion_fn : callable(X, t)
        Computes the diffusion coefficient :math:`\vec{b}(\vec{X},t)`
    X0 : numpy.array
        Initial condition on X
    ts : numpy.array
        A sequence of time points for which to solve for X.  The initial value
        point should be the first element of this sequence.
    Us : array, shape=(len(t) - 1)
        Normalized Weiner increments for each time step (i.e. samples from a
        Gaussian distribution with mean 0 and variance 1).

    Returns
    -------
    numpy.array, shape=(len(ts), len(X0))
        Array containing the value of X for each desired time in t, with the
        initial value `X0` in the first row.

    """

    dts = [tf - ti for tf, ti in zip(ts[1:], ts[:-1])]
    # Scale the Weiner increments to the time increments.
    sqrtdts = np.sqrt(dts)
    dWs = np.product(np.array([sqrtdts, Us]), axis=0)

    X = np.array([X0])

    for t, dt, dW in zip(ts[:-1], dts, dWs):
        X = np.vstack((X, X[-1] + drift_fn(X[-1], t)*dt +
                       diffusion_fn(X[-1], t)*dW))

    return X

def meas_euler(drift_fn, diffusion_fn, dW_fn, X0, ts, dMs):
    r"""Integrate a system of ordinary stochastic differential equations
    conditioned on an incremental measurement record:

    .. math::

       d\vec{X}=\vec{a}(\vec{X},t)\,dt+\vec{b}(\vec{X},t)\,dW_t

    Uses the Euler method:

    .. math::

       \vec{X}_{i+1}=\vec{X}_i+\vec{a}(\vec{X}_i,t_i)\Delta t_i+
       \vec{b}(\vec{X}_i,t_i)\Delta W_i

    where :math:`\Delta W_i=f(\Delta M_i,\vec{X}, t)`, :math:`\Delta M_i` being
    the incremental measurement record being used to drive the SDE.

    Parameters
    ----------
    drift_fn : callable(X, t)
        Computes the drift coefficient :math:`\vec{a}(\vec{X},t)`
    diffusion_fn : callable(X, t)
        Computes the diffusion coefficient :math:`\vec{b}(\vec{X},t)`
    dW_fn : callable(dM, dt, X, t)
        The function that converts the incremental measurement and current
        state to the Wiener increment.
    X0 : array
        Initial condition on X
    ts : array
        A sequence of time points for which to solve for X.  The initial value
        point should be the first element of this sequence.
    dMs : array, shape=(len(t) - 1)
        Incremental measurement outcomes used to drive the SDE.

    Returns
    -------
    numpy.array, shape=(len(ts), len(X0))
        Array containing the value of X for each desired time in t, with the
        initial value `X0` in the first row.

    """

    dts = [tf - ti for tf, ti in zip(ts[1:], ts[:-1])]

    X = np.array([X0])

    for t, dt, dM in zip(ts[:-1], dts, dMs):
        dW = dW_fn(dM, dt, X[-1], t)
        X = np.vstack((X, X[-1] + drift_fn(X[-1], t)*dt +
                       diffusion_fn(X[-1], t)*dW))

    return X

def milstein(drift, diffusion, b_dx_b, X0, ts, Us):
    r"""Integrate a system of ordinary stochastic differential equations subject
    to scalar noise:

    .. math::

       d\vec{X}=\vec{a}(\vec{X},t)\,dt+\vec{b}(\vec{X},t)\,dW_t

    Uses the Milstein method:

    .. math::

       \vec{X}_{i+1}=\vec{X}_i+\vec{a}(\vec{X}_i,t_i)\Delta t_i+
       \vec{b}(\vec{X}_i,t_i)\Delta W_i+
       \frac{1}{2}\left(\vec{b}(\vec{X}_i,t_i)\cdot\vec{\nabla}_{\vec{X}}\right)
       \vec{b}(\vec{X}_i,t_i)\left((\Delta W_i)^2-\Delta t_i\right)

    where :math:`\Delta W_i=U_i\sqrt{\Delta t}`, :math:`U` being a normally
    distributed random variable with mean 0 and variance 1.

    Parameters
    ----------
    drift : callable(X, t)
        Computes the drift coefficient :math:`\vec{a}(\vec{X},t)`
    diffusion : callable(X, t)
        Computes the diffusion coefficient :math:`\vec{b}(\vec{X},t)`
    b_dx_b : callable(X, t)
        Computes the correction coefficient
        :math:`\left(\vec{b}(\vec{X},t)\cdot
        \vec{\nabla}_{\vec{X}}\right)\vec{b}(\vec{X},t)`
    X0 : numpy.array
        Initial condition on X
    ts : numpy.array
        A sequence of time points for which to solve for X.  The initial value
        point should be the first element of this sequence.
    Us : array, shape=(len(t) - 1)
        Normalized Weiner increments for each time step (i.e. samples from a
        Gaussian distribution with mean 0 and variance 1).

    Returns
    -------
    numpy.array, shape=(len(ts), len(X0))
        Array containing the value of X for each desired time in t, with the
        initial value `X0` in the first row.

    """

    dts = [tf - ti for tf, ti in zip(ts[1:], ts[:-1])]
    # Scale the Weiner increments to the time increments.
    sqrtdts = np.sqrt(dts)
    dWs = np.product(np.array([sqrtdts, Us]), axis=0)

    X = np.array([X0])

    for t, dt, dW in zip(ts[:-1], dts, dWs):
        X = np.vstack((X, X[-1] + drift(X[-1], t)*dt + diffusion(X[-1], t)*dW +
                      b_dx_b(X[-1], t)*(dW**2 - dt)/2))

    return X

def meas_milstein(drift_fn, diffusion_fn, b_dx_b_fn, dW_fn, X0, ts, dMs):
    r"""Integrate a system of ordinary stochastic differential equations
    conditioned on an incremental measurement record:

    .. math::

       d\vec{X}=\vec{a}(\vec{X},t)\,dt+\vec{b}(\vec{X},t)\,dW_t

    Uses the Milstein method:

    .. math::

       \vec{X}_{i+1}=\vec{X}_i+\vec{a}(\vec{X}_i,t_i)\Delta t_i+
       \vec{b}(\vec{X}_i,t_i)\Delta W_i+
       \frac{1}{2}\left(\vec{b}(\vec{X}_i,t_i)\cdot\vec{\nabla}_{\vec{X}}\right)
       \vec{b}(\vec{X}_i,t_i)\left((\Delta W_i)^2-\Delta t_i\right)

    where :math:`\Delta W_i=f(\Delta M_i,\vec{X}, t)`, :math:`\Delta M_i` being
    the incremental measurement record being used to drive the SDE.

    Parameters
    ----------
    drift_fn : callable(X, t)
        Computes the drift coefficient :math:`\vec{a}(\vec{X},t)`
    diffusion_fn : callable(X, t)
        Computes the diffusion coefficient :math:`\vec{b}(\vec{X},t)`
    b_dx_b_fn : callable(X, t)
        Computes the correction coefficient
        :math:`\left(\vec{b}(\vec{X},t)\cdot
        \vec{\nabla}_{\vec{X}}\right)\vec{b}(\vec{X},t)`
    dW_fn : callable(dM, dt, X, t)
        The function that converts the incremental measurement and current
        state to the Wiener increment.
    X0 : numpy.array
        Initial condition on X
    ts : numpy.array
        A sequence of time points for which to solve for X.  The initial value
        point should be the first element of this sequence.
    dMs : numpy.array, shape=(len(t) - 1)
        Incremental measurement outcomes used to drive the SDE.

    Returns
    -------
    numpy.array, shape=(len(ts), len(X0))
        Array containing the value of X for each desired time in t, with the
        initial value `X0` in the first row.

    """

    dts = [tf - ti for tf, ti in zip(ts[1:], ts[:-1])]

    X = np.array([X0])

    for t, dt, dM in zip(ts[:-1], dts, dMs):
        dW = dW_fn(dM, dt, X[-1], t)
        X = np.vstack((X, X[-1] + drift_fn(X[-1], t)*dt +
                       diffusion_fn(X[-1], t)*dW +
                       b_dx_b_fn(X[-1], t)*(dW**2 - dt)/2))

    return X

def time_ind_taylor_1_5(drift, diffusion, b_dx_b, b_dx_a, a_dx_b, a_dx_a,
                        b_dx_b_dx_b, b_b_dx_dx_b, b_b_dx_dx_a,
                        X0, ts, U1s, U2s):
    r"""Integrate a system of ordinary stochastic differential equations with
    time-independent coefficients subject to scalar noise:

    .. math::

       d\vec{X}=\vec{a}(\vec{X})\,dt+\vec{b}(\vec{X})\,dW_t

    Uses an order 1.5 Taylor method:

    .. math::

       \begin{align}
       \rho^\mu_{i+1}&=\rho^\mu_i+a^\mu_i\Delta t_i+
       b^\mu_i\Delta W_i+\frac{1}{2}b^\nu_i\partial_\nu b^\mu_i\left(
       (\Delta W_i)^2-\Delta t_i\right)+ \\
       &\quad b^\nu_i\partial_\nu a^\mu_i\Delta Z_i
       +\left(a^\nu_i\partial_\nu
       +\frac{1}{2}b^\nu_ib^\sigma_i\partial_\nu\partial_\sigma\right)
       b^\mu_i\left(\Delta W_i\Delta t_i-\Delta Z_i\right)+ \\
       &\quad\frac{1}{2}\left(a^\nu_i\partial_\nu
       +\frac{1}{2}b^\nu_ib^\sigma_i\partial_\nu\partial_\sigma\right)
       a^\mu_i\Delta t_i^2
       +\frac{1}{2}b^\nu_i\partial_\nu b^\sigma_i\partial_\sigma b^\mu_i\left(
       \frac{1}{3}(\Delta W_i)^2-\Delta t_i\right)\Delta W_i
       \end{align}

    Parameters
    ----------
    drift : callable(X)
        Computes the drift coefficient :math:`\vec{a}(\vec{X})`
    diffusion : callable(X)
        Computes the diffusion coefficient :math:`\vec{b}(\vec{X})`
    b_dx_b : callable(X)
        Computes the coefficient :math:`\left(\vec{b}(\vec{X})\cdot
        \vec{\nabla}_{\vec{X}}\right)\vec{b}(\vec{X})`
    b_dx_a : callable(X)
        Computes the coefficient :math:`\left(\vec{b}(\vec{X})\cdot
        \vec{\nabla}_{\vec{X}}\right)\vec{a}(\vec{X})`
    a_dx_b : callable(X)
        Computes the coefficient :math:`\left(\vec{a}(\vec{X})\cdot
        \vec{\nabla}_{\vec{X}}\right)\vec{b}(\vec{X})`
    a_dx_a : callable(X)
        Computes the coefficient :math:`\left(\vec{a}(\vec{X})\cdot
        \vec{\nabla}_{\vec{X}}\right)\vec{a}(\vec{X})`
    b_dx_b_dx_b : callable(X)
        Computes the coefficient :math:`\left(\vec{b}(\vec{X})\cdot
        \vec{\nabla}_{\vec{X}}\right)^2\vec{b}(\vec{X})`
    b_b_dx_dx_b : callable(X)
        Computes :math:`b^\nu b^\sigma\partial_\nu\partial_\sigma
        b^\mu\hat{e}_\mu`.
    b_b_dx_dx_a : callable(X)
        Computes :math:`b^\nu b^\sigma\partial_\nu\partial_\sigma
        a^\mu\hat{e}_\mu`.
    X0 : numpy.array
        Initial condition on X
    ts : numpy.array
        A sequence of time points for which to solve for X.  The initial value
        point should be the first element of this sequence.
    U1s : numpy.array, shape=(len(t) - 1)
        Normalized Weiner increments for each time step (i.e. samples from a
        Gaussian distribution with mean 0 and variance 1).
    U2s : numpy.array, shape=(len(t) - 1)
        Normalized Weiner increments for each time step (i.e. samples from a
        Gaussian distribution with mean 0 and variance 1).

    Returns
    -------
    numpy.array, shape=(len(t), len(X0))
        Array containing the value of X for each desired time in t, with the
        initial value `X0` in the first row.

    """

    dts = ts[1:] - ts[:-1]
    sqrtdts = np.sqrt(dts)
    dWs = U1s*sqrtdts
    dZs = (U1s + U2s/np.sqrt(3))*sqrtdts*dts/2

    Xs = [np.array(X0)]

    for t, dt, dW, dZ in zip(ts[:-1], dts, dWs, dZs):
        X = Xs[-1]
        Xs = np.vstack((Xs, X + drift(X)*dt + diffusion(X)*dW +
                        b_dx_b(X)*(dW**2 - dt)/2 + b_dx_a(X)*dZ +
                        (a_dx_b(X)+b_b_dx_dx_b(X)/2)*(dW*dt - dZ) +
                        (a_dx_a(X)+b_b_dx_dx_a(X)/2)*dt**2/2 +
                        b_dx_b_dx_b(X)*(dW**2/3 - dt)*dW/2))

    return Xs

def faulty_milstein(drift, diffusion, b_dx_b, X0, ts, Us):
    r"""Integrate a system of ordinary stochastic differential equations subject
    to scalar noise:

    .. math::

       d\vec{X}=\vec{a}(\vec{X},t)\,dt+\vec{b}(\vec{X},t)\,dW_t

    Uses a faulty Milstein method (i.e. missing the factor of 1/2 in the term
    added to Euler integration):

    .. math::

       \vec{X}_{i+1}=\vec{X}_i+\vec{a}(\vec{X}_i,t_i)\Delta t_i+
       \vec{b}(\vec{X}_i,t_i)\Delta W_i+
       \left(\vec{b}(\vec{X}_i,t_i)\cdot\vec{\nabla}_{\vec{X}}\right)
       \vec{b}(\vec{X}_i,t_i)\left((\Delta W_i)^2-\Delta t_i\right)

    where :math:`\Delta W_i=U_i\sqrt{\Delta t}`, :math:`U` being a normally
    distributed random variable with mean 0 and variance 1.

    Parameters
    ----------
    drift : callable(X, t)
        Computes the drift coefficient :math:`\vec{a}(\vec{X},t)`
    diffusion : callable(X, t)
        Computes the diffusion coefficient :math:`\vec{b}(\vec{X},t)`
    b_dx_b : callable(X, t)
        Computes the correction coefficient
        :math:`\left(\vec{b}(\vec{X},t)\cdot
        \vec{\nabla}_{\vec{X}}\right)\vec{b}(\vec{X},t)`
    X0 : numpy.array
        Initial condition on X
    ts : numpy.array
        A sequence of time points for which to solve for X.  The initial value
        point should be the first element of this sequence.
    Us : numpy.array, shape=(len(t) - 1)
        Normalized Weiner increments for each time step (i.e. samples from a
        Gaussian distribution with mean 0 and variance 1).

    Returns
    -------
    numpy.array, shape=(len(t), len(X0))
        Array containing the value of X for each desired time in t, with the
        initial value `X0` in the first row.

    """

    dts = [tf - ti for tf, ti in zip(ts[1:], ts[:-1])]
    # Scale the Weiner increments to the time increments.
    sqrtdts = np.sqrt(dts)
    dWs = np.product(np.array([sqrtdts, Us]), axis=0)

    X = [np.array(X0)]

    for t, dt, dW in zip(ts[:-1], dts, dWs):
        X.append(X[-1] + drift(X[-1], t)*dt + diffusion(X[-1], t)*dW +
                 b_dx_b(X[-1], t)*(dW**2 - dt))

    return X
