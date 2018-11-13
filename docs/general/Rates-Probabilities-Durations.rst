
Rates and Probabilities
=======================

There are broadly two ways of specifying how rapidly people move across a transition in the model


* *Rate* which is a number of people per unit time
* *Probability* which is the likelihood for an individual to transition per unit time

Although these appear similar, they behave differently when the integration step size is changed. Consider the example where 1200 people have transitioned in 1 year, in a population of 10000


* The *rate* is 1200 people/year
* The *probability* is 1200/10000 = 0.12 per year

Now, consider how these could be converted to per-month quantities. The rate can simply be divided i.e. 100 people/month = 1200 people/year. However, the probability of a transition is cumulative. That is, suppose was ask what the probability is of having at least one transition in the year, if we sample once every month. This would be

.. code-block:: text

   P(remain_for_a_year) = P(remain_for_dt)^(1/dt)
   1-P(move_after_a_year) = (1-P(move_after_dt))^(1/dt)
   1-P(move_after_dt) = (1-P(move_after_a_year))^dt
   P(move_after_dt) = 1 - (1-P(move_after_a_year))^dt


where dt here is 1 month (the value would be 1/12 normalized by year). So here, the probability of moving per month is 0.0106. In a population of 1000, this corresponds to 106 people, so the difference is not so significant. But consider how this changes as a function of the probability of moving

.. csv-table::
   :header: "Flow" , "Prob"   , "Prob per month" , "Flow per month" , "Probabilistic flow"

   0    , 0      , 0              , 0              , 0
   500  , 0.0500 , 0.0043         , 42             , 43
   1000 , 0.1000 , 0.0087         , 83             , 87
   1500 , 0.1500 , 0.0135         , 125            , 135
   2000 , 0.2000 , 0.0184         , 167            , 184
   2500 , 0.2500 , 0.0237         , 208            , 237
   3000 , 0.3000 , 0.0293         , 250            , 293
   3500 , 0.3500 , 0.0353         , 292            , 353
   4000 , 0.4000 , 0.0417         , 333            , 417
   4500 , 0.4500 , 0.0486         , 375            , 486
   5000 , 0.5000 , 0.0561         , 417            , 561
   5500 , 0.5500 , 0.0644         , 458            , 644
   6000 , 0.6000 , 0.0735         , 500            , 735
   6500 , 0.6500 , 0.0838         , 542            , 838
   7000 , 0.7000 , 0.0955         , 583            , 955
   7500 , 0.7500 , 0.1091         , 625            , 1091
   8000 , 0.8000 , 0.1255         , 667            , 1255
   8500 , 0.8500 , 0.1462         , 708            , 1462
   9000 , 0.9000 , 0.1746         , 750            , 1746
   9500 , 0.9500 , 0.2209         , 792            , 2209



The reason this occurs is because the probability is computed for an individual, and thus the number of people leaving in any given month is proportionate to the number of people in the compartment. So the probabilistic flow here only applies to the first month, when there are 10000 people in the compartment. For example

.. list-table::
   :header-rows: 1

   * - Month
     - People remaining
     - Number of people who transitioned
   * - 0
     - 10000
     - 0
   * - 1
     - 7791
     - 2209
   * - 2
     - 6070
     - 1721
   * - 3
     - 4729
     - 1341
   * - 4
     - 3684
     - 1045
   * - 5
     - 2871
     - 814
   * - 6
     - 2236
     - 634
   * - 7
     - 1742
     - 494
   * - 8
     - 1358
     - 385
   * - 9
     - 1058
     - 300
   * - 10
     - 824
     - 234
   * - 11
     - 642
     - 182
   * - 12
     - 500
     - 142


Similarly, notice that a constant flow rate would correspond to an increasing probability of transitioning per person for each person remaining in the compartment. Both formulations are valid, but are suitable for different purposes. For example, consider the case where the compartments correspond to age (e.g. 20 years old and 21 years old) and the population's age is uniformly distributed. Then, we would expect the same number of people to transition from 20 to 21 years old each month, and in the last month, we know that anyone who has not already transitioned is guaranteed to transition. So in this case, the flow is uniformly distributed over the course of the year but the probability of transitioning is not. Similarly, suppose that we had a program for treatment that would move 500 people every month from the Infected compartment to the Recovered compartment. Again, this would correspond to a variable probability over the course of the year as the compartment empties, because the probability of a person being one of the 500 people each month increases as the compartment gets smaller. But if the disease had a fixed probability of resolving itself, then this would remain constant over the course of the year, so fewer people would have their diseases resolve as the compartment became smaller.

Replenishing compartments and effective flow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One complication is what happens when the compartment is replenished by inflowing people at each timestep. In that case, the effective flow rate could be greater than 1. Consider the case where 2209 people are added each month, so there is no net change in population each month. Then we would have

.. list-table::
   :header-rows: 1

   * - Month
     - People remaining
     - Number of people who transitioned
   * - 0
     - 10000
     - 0
   * - 1
     - 7791+2209 new
     - 2209
   * - 2
     - 7791+2209 new
     - 2209
   * - 3
     - 7791+2209 new
     - 2209
   * - 4
     - 7791+2209 new
     - 2209
   * - 5
     - 7791+2209 new
     - 2209
   * - 6
     - 7791+2209 new
     - 2209
   * - 7
     - 7791+2209 new
     - 2209
   * - 8
     - 7791+2209 new
     - 2209
   * - 9
     - 7791+2209 new
     - 2209
   * - 10
     - 7791+2209 new
     - 2209
   * - 11
     - 7791+2209 new
     - 2209
   * - 12
     - 7791+2209 new
     - 2209


However, this means that 26508 have left the compartment - although this is 265% of the initial compartment size, note that it is only 0.73 of all the people who were ever in this compartment at some point in the year. The flow rate of 9500/10000 naively giving a probability of 0.95 does not account for the fact that some people were able to both enter the compartment and leave the compartment within the same year. Similarly, the effective probability being 0.73 rather than 0.95 reflects the fact that people who entered the compartment late in the year are less likely to have left it that same year. Alternatively, if 0.95 of the population flowed out every month, then the net annual flow would be 25183 for the people who arrived during the year, plus another 9500 for the initial contents of the compartment. And we would have

.. list-table::
   :header-rows: 1

   * - Month
     - People remaining
     - Number of people who transitioned
   * - 0
     - 10000
     - 0
   * - 1
     - 500+2209 new
     - 9500
   * - 2
     - 135+2209 new
     - 2574
   * - 3
     - 117+2209 new
     - 2227
   * - 4
     - 116+2209 new
     - 2210
   * - 5
     - 116+2209 new
     - 2209
   * - 6
     - 116+2209 new
     - 2209
   * - 7
     - 116+2209 new
     - 2209
   * - 8
     - 116+2209 new
     - 2209
   * - 9
     - 116+2209 new
     - 2209
   * - 10
     - 116+2209 new
     - 2209
   * - 11
     - 116+2209 new
     - 2209
   * - 12
     - 116+2209 new
     - 2209


for a total outflow of 34183.

Does this depend on the units provided by the user?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Essentially the answer would appear to be no. If we make the statement that '9500 left the compartment in 2010' then this does not provide any information about whether that number was uniformly distributed over the course of the year, or whether it scales with population size over the course of the year. In particular, based on the example above, converting the 9500 people to a probability requires knowing both the initial population size *and* the number of people entering the compartment and leaving the compartment due to other reasons. When the population size varies over the course of the year, it can be misleading to normalize the number of people transitioning over the course of the year by the initial number of people in the compartment. That is, if there were 10000 people present in the compartment in Jan 2010, it could be misleading to quote the flow rate as 9500/10000=0.95 because this does not account for people entering the compartment. It ought to be normalized by the number of people who were present in the compartment at any point during the year, but of course, this cannot be done prior to running the simulation. Rather, a flow rate that is provided as a net number of people per year corresponds to an unknown probability that is a candidate for calibration. On the other hand, if the probability is known, then the corresponding flow rate can be dynamically computed during the simulation.

Currently, in Atomica, if a fraction of people is provided, it is assumed to correspond to an annual probability i.e. if 'Fraction 0.95' is input, it is assumed to correspond to a probability of 0.95, which is converted to a timestep-based probability for integration. But if a number of people is provided, it is divided uniformly and distributed evenly across the course of the year. However, whether this target number of people can be reached depends on whether there are a sufficient number of people in the compartment e.g. if the birth rate is too low, there may simply be an insufficient number of people moved over.

An example of a parameter that may be provided as a fraction is the death rate or diagnosis rate - for an individual person, the probability that something happens to them. A parameter that may be provided as an absolute number is the number of notified cases.

Expected duration
^^^^^^^^^^^^^^^^^

Suppose we have a transition probability :math:`p` of leaving a compartment at each timestep. What is the expected amount of time spent in the compartment? If we consider :math:`p` as being a 'probability of success', since the probability is independent of the number of samples, we can treat this as a series of Bernoulli trials, and the appropriate distribution for the number of trials needed to get one success is the geometric distribution. The mean of this distribution is simply `1/p` where the result is the expected number of trials needed. The duration can be estimated by multiplying the expected number of trials by the timestep ``dt``.

In the continuous case, the geometric distribution is replaced with an exponential distribution. The inverse of the rate parameter, the mean of the distribution, still corresponds to the average duration of time spent in the compartment. However, now we use integration to convert from rate to probability.

Often, there will be a discrepancy between the time over which the probabilities were calculated in data, and the simulation time step. For example, a person on treatment may have a probability of treatment success after 1 week of 50%, but the integration time step is 3 months. In such cases, the probability needs to be rescaled to match the simulation time step. In previous implementations, this was accomplished by having users annualize all input probabilities, and then the probability would be rescaled based on the number of samples per year. This approach had the limitation that when the time scale of the input data was small (e.g. daily outcomes) and the simulation time step is also small (e.g. weekly timesteps) then the conversion from daily probability to annual probability and then to weekly probability would run the risk of failure due to loss of precision (since a high daily probability of success results in an annual probability approaching 1).

The approach taken in Atomica currently is to specify the time scale for probability inputs, and then to directly convert from one timescale to another.

From :math:`p_1` over time period :math:`t_1` to annual probability :math:`p_a` (where :math:`t_1` is in units of years)

.. math::

    p_a = 1 - (1 - p_1)^{\frac{1}{t_1}}

From :math:`p_a` to :math:`p_2` over time period :math:`t_2`

.. math::

    p_2 =  1 - (1 - p_a)^{t_2}

From :math:`p_1` to :math:`p_2` directly

.. math::

    p_2 = 1 - (1 - p_1)^{\frac{t_2}{t_1}}

Demonstration numerical implementation:

::

    def convert_probability(p1,t1,t2):
        pa = 1 - (1 - p1)**(1. / t1)
        p2 = 1. - (1. - pa)**t2
        pd = 1 - (1 - p1)**(t2/t1)
        print('Indirect: %g, Direct: %g' % (p2,pd))

In cases where the duration is specified, we can convert it to an equivalent probability. For an exponential distribution, the question is what is the probability of a transition taking place within a year. This is computed by integrating over the distribution e.g.

.. math::

    P(X<=t) &= \int_0^t \lambda e^{-\lambda x}\\
    &= 1 - e^{-\lambda t}

This formula gives the probability of an event happening in a certain amount of time, given the rate parameter lambda. Noting that the duration can be expressed as :math:`d = 1/\lambda`, we end up with the original operation

.. math::

    P(X<=1) = 1 - e^{-1/d}

or

::

    probability = 1.0 - np.exp(-1.0 / duration)

where the probability is annual probability, and duration :math:`d` is in units of years. Then, the timestep conversion proceeded as usual.

In order to perform the calculation more directly, we need to compute the integral such that the upper bound is the time step. That is,

.. math::

    P(X<=\Delta t) &= \int_0^{\Delta t} \lambda e^{-\lambda x}\\
    &= 1 - e^{-\Delta t/d}

where both the timestep and duration are in the same units.

Demonstration numerical implementation:

::

    def convert_duration(d,dt):
        p_annual = 1.0 - np.exp(-1.0 / d)
        p2 = 1. - (1. - p)**dt
        pd = 1.0 - np.exp(-dt / d)
        print('Indirect: %g, Direct: %g' % (p2,pd))