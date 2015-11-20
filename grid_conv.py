'''Functions for testing convergence rates using grid convergence

'''

import numpy as np
from pysme.integrate import *
from joblib import Parallel, delayed

def l1_norm(vec):
    return np.sum(np.abs(vec))

def double_increments(times, U1s, U2s=None):
    r'''Take a list of times (assumed to be evenly spaced) and standard-normal
    random variables used to define the Ito integrals on the intervals and
    return the equivalent lists for doubled time intervals. The new
    standard-normal random variables are defined in terms of the old ones by

    .. math:

       \begin{align}
       \tilde{U}_{1,n}&=\frac{U_{1,n}+U_{1,n+1}}{\sqrt{2}} \\
       \tilde{U}_{2,n}&=\frac{\sqrt{3}}{2}\frac{U_{1,n}-U_{1,n+1}}{\sqrt{2}}
                        +\frac{1}{2}\frac{U_{2,n}+U_{2,n+1}}{\sqrt{2}}
       \end{align}

    :param times:   List of evenly spaced times defining an even number of
                    time intervals.
    :type times:    numpy.array
    :param U1s:     Samples from a standard-normal distribution used to
                    construct Wiener increments :math:`\Delta W` for each time
                    interval. Multiple rows may be included for independent
                    trajectories.
    :type U1s:      numpy.array(N, len(times) - 1)
    :param U2s:     Samples from a standard-normal distribution used to
                    construct multiple-Ito increments :math:`\Delta Z` for each
                    time interval. Multiple rows may be included for independent
                    trajectories.
    :type U2s:      numpy.array(N, len(times) - 1)
    :returns:       Times sampled at half the frequency and the modified
                    standard-normal-random-variable samples for the new
                    intervals. If ``U2s=None``, only new U1s are returned.
    :rtype:         (numpy.array(len(times)//2 + 1),
                     numpy.array(len(times)//2)[, numpy.array(len(times)//2]))

    '''

    new_times = times[::2]
    even_U1s = U1s[:,::2]
    odd_U1s = U1s[:,1::2]
    new_U1s = (even_U1s + odd_U1s)/np.sqrt(2)

    if U2s is None:
        return new_times, new_U1s
    else:
        even_U2s = U2s[:,::2]
        odd_U2s = U2s[:,1::2]
        new_U2s = (np.sqrt(3)*(even_U1s - odd_U1s) +
                   even_U2s + odd_U2s)/(2*np.sqrt(2))
        return new_times, new_U1s, new_U2s

def trajectory_convergence(rho_0, c_op, M_sq, N, H, basis, times, U1s=None,
                           U2s=None):

    return None

def milstein_grid_convergence(rho_0, c_op, M_sq, N, H, basis, times, Us=None):
    r"""Calculate the same trajectory for time increments :math:`\Delta t`,
    :math:`2\Delta t`, and :math:`4\Delta t` using Milstein integration.

    :param rho_0:   The initial state of the system
    :type rho_0:    numpy.array
    :param c_op:    The coupling operator
    :type c_op:     numpy.array
    :param M_sq:    The squeezing parameter
    :type M_sq:     complex
    :param N:       The thermal parameter
    :type N:        positive real
    :param H:       The plant Hamiltonian
    :type H:        numpy.array
    :param basis:   The Hermitian basis to vectorize the operators in terms of
                    (with the component proportional to the identity in last
                    place)
    :type basis:    list(numpy.array)
    :param times:   A sequence of time points for which to solve for rho. The
                    length should be such that (len(times) - 1)%4 == 0.
    :type times:    list(real)
    :param Us:      A sequence of normalized Wiener increments (samples from a
                    normal distribution with mean 0 and variance 1). If None,
                    then this function will generate its own samples. The length
                    should be len(times) - 1.
    :type Us:       list(real)
    :returns:       The components of the vecorized :math:`\rho` for all
                    specified times, first for Milstein and then for Taylor 1.5
    :rtype:         (list(numpy.array), list(numpy.array))

    """

    increments = len(times) - 1
    if Us is None:
        Us = np.random.randn(1, increments)

    # Calculate times and random variables for the double and quadruple
    # intervals
    times_2, Us_2 = double_increments(times, Us)
    times_4, Us_4 = double_increments(times_2, Us_2)

    rhos = homodyne_gauss_integrate(rho_0, c_op, M_sq, N, H, basis, times,
                                    Us[0])
    rhos_2 = homodyne_gauss_integrate(rho_0, c_op, M_sq, N, H, basis, times_2,
                                      Us_2[0])
    rhos_4 = homodyne_gauss_integrate(rho_0, c_op, M_sq, N, H, basis, times_4,
                                      Us_4[0])

    return [(rhos, times), (rhos_2, times_2), (rhos_4, times_4)]

def faulty_milstein_grid_convergence(rho_0, c_op, M_sq, N, H, basis, times,
                                     Us=None):
    r"""Calculate the same trajectory for time increments :math:`\Delta t`,
    :math:`2\Delta t`, and :math:`4\Delta t` using faulty Milstein integration
    (i.e. missing the factor of 1/2 in the term added to Euler integration).

    :param rho_0:   The initial state of the system
    :type rho_0:    numpy.array
    :param c_op:    The coupling operator
    :type c_op:     numpy.array
    :param M_sq:    The squeezing parameter
    :type M_sq:     complex
    :param N:       The thermal parameter
    :type N:        positive real
    :param H:       The plant Hamiltonian
    :type H:        numpy.array
    :param basis:   The Hermitian basis to vectorize the operators in terms of
                    (with the component proportional to the identity in last
                    place)
    :type basis:    list(numpy.array)
    :param times:   A sequence of time points for which to solve for rho. The
                    length should be such that (len(times) - 1)%4 == 0.
    :type times:    list(real)
    :param Us:      A sequence of normalized Wiener increments (samples from a
                    normal distribution with mean 0 and variance 1). If None,
                    then this function will generate its own samples. The length
                    should be len(times) - 1.
    :type Us:       numpy.array(1, len(times) -1)
    :returns:       The components of the vecorized :math:`\rho` for all
                    specified times, first for Milstein and then for Taylor 1.5
    :rtype:         (list(numpy.array), list(numpy.array))

    """

    increments = len(times) - 1
    if Us is None:
        Us = np.random.randn(1, increments)

    # Calculate times and random variables for the double and quadruple
    # intervals
    times_2, Us_2 = double_increments(times, Us)
    times_4, Us_4 = double_increments(times_2, Us_2)

    rhos = faulty_homodyne_gauss_integrate(rho_0, c_op, M_sq, N, H, basis,
                                           times, Us[0])
    rhos_2 = faulty_homodyne_gauss_integrate(rho_0, c_op, M_sq, N, H, basis,
                                             times_2, Us_2[0])
    rhos_4 = faulty_homodyne_gauss_integrate(rho_0, c_op, M_sq, N, H, basis,
                                             times_4, Us_4[0])

    return [(rhos, times), (rhos_2, times_2), (rhos_4, times_4)]

def homodyne_strong_calc_rate(integrator_fn, keyword_args, times, U1s, U2s,
                              times_2, U1s_2, U2s_2, times_4, U1s_4, U2s_4):
    keyword_args_2 = keyword_args.copy()
    keyword_args_4 = keyword_args.copy()

    keyword_args.update({'ts': times, 'U1s': U1s, 'U2s': U2s})
    keyword_args_2.update({'ts': times_2, 'U1s': U1s_2, 'U2s': U2s_2})
    keyword_args_4.update({'ts': times_4, 'U1s': U1s_4, 'U2s': U2s_4})

    rhos = integrator_fn(**keyword_args)
    rhos_2 = integrator_fn(**keyword_args_2)
    rhos_4 = integrator_fn(**keyword_args_4)
    rate = (np.log(l1_norm(rhos_4[-1] - rhos_2[-1])) -
            np.log(l1_norm(rhos_2[-1] - rhos[-1])))/np.log(2)

    return rate

def homodyne_strong_grid_convergence(rho_0, c_op, M_sq, N, H, basis, prep_fn,
                                     integrator_fn, times, U1s=None, U2s=None,
                                     trajectories=256):
    r'''Calculate the strong convergence rate for an integrator on the
    Gaussian homodyne stochastic master equation.

    :param rho_0:   The initial state of the system
    :type rho_0:    numpy.array
    :param c_op:    The coupling operator
    :type c_op:     numpy.array
    :param M_sq:    The squeezing parameter
    :type M_sq:     complex
    :param N:       The thermal parameter
    :type N:        positive real
    :param H:       The plant Hamiltonian
    :type H:        numpy.array
    :param basis:   The Hermitian basis to vectorize the operators in terms of
                    (with the component proportional to the identity in last
                    place)
    :type basis:    list(numpy.array)
    :param prep_fn:         Function to prepare arguments for the integrator.
    :param integrator_fn:   Function to perform the integration.
    :param times:   A sequence of time points for which to solve for rho
    :type times:    list(real)
    :param U1s:     Samples from a standard-normal distribution used to
                    construct Wiener increments :math:`\Delta W` for each time
                    interval for each trajectory.
    :type U1s:      numpy.array(trajectories, len(times) - 1)
    :param U2s:     Samples from a standard-normal distribution used to
                    construct multiple-Ito increments :math:`\Delta Z` for each
                    time interval for each trajectory.
    :type U2s:      numpy.array(trajectories, len(times) - 1)
    :param trajectories:    Number of trajectories to calculate the convergence
                            for
    :type trajectories:     int
    :returns:               List of convergence rates.

    '''

    keyword_args = prep_homodyne_gauss_1_5(rho_0, c_op, M_sq, N, H, basis)
    # keyword_args = prep_fn(rho_0, c_op, M_sq, N, H, basis)

    increments = len(times) - 1
    if U1s is None:
        U1s = np.random.randn(trajectories, increments)
    if U2s is None:
        U2s = np.random.randn(trajectories, increments)

    # Calculate times and random variables for the double and quadruple
    # intervals
    times_2, U1s_2, U2s_2 = double_increments(times, U1s, U2s)
    times_4, U1s_4, U2s_4 = double_increments(times_2, U1s_2, U2s_2)

    meta_kwargs = [{'integrator_fn': integrator_fn,
                    'keyword_args': keyword_args, 'times': times, 'U1s': U1,
                    'U2s': U2, 'times_2': times_2, 'U1s_2': U1_2, 'U2s_2': U2_2,
                    'times_4': times_4, 'U1s_4': U1_4, 'U2s_4': U2_4}
                   for U1, U2, U1_2, U2_2, U1_4, U2_4
                   in zip(U1s, U2s, U1s_2, U2s_2, U1s_4, U2s_4)]

    """
    rates = Parallel(n_jobs=2)(delayed(homodyne_strong_calc_rate)(**meta_kwarg)
                               for meta_kwarg in meta_kwargs)
    rates = np.zeros(trajectories)



    for index in range(trajectories):
        rhos = integrator_fn(*arguments, ts=times, U1s=U1s[index],
                             U2s=U2s[index])
        rhos_2 = integrator_fn(*arguments, ts=times_2, U1s=U1s_2[index],
                               U2s=U2s_2[index])
        rhos_4 = integrator_fn(*arguments, ts=times_4, U1s=U1s_4[index],
                               U2s=U2s_4[index])

        rates[index] = (np.log(l1_norm(rhos_4[-1] - rhos_2[-1])) -
                        np.log(l1_norm(rhos_2[-1] - rhos[-1])))/np.log(2)
    """


    return meta_kwargs
