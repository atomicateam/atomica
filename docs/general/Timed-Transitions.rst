.. _timed-transitions:

Maximum compartment duration
****************************

Intended usage
- NOT used when there is a constant inflow/outflow or if inflows and outflows are slowly changing
- In a compartment model, the amount of time people spend in the compartment follows an exponential distribution. In the steady state, only the mean matters. When things change rapidly, then discrepencies can occur. These discrepencies are largest if the compartment has a long expected duration relative to the step size, and if the inflow changes dramatically.

Therefore, the maximum compartment duration is suitable under the following circumstances
- The expected time in the compartment is long relative to the step size (e.g. >4 timesteps), and
- At the end of the duration, all individuals transition to the same compartment (although this could be a junction), and
- There are sharp changes to inflow or outflow

Two examples of where this usage might be appropriate:

- A mass vaccination schedule where
    - A large proportion of the population is vaccinated at the same time
    - The duration of protection is several years
    - At the end, all uninfected individuals return to the susceptible compartment
- TB early to late latent states
    - The time spent in the early latent state is several years
    - At the end, all infected individuals progress to late latent
    - The inflow changes rapidly if the force of infection changes due to interventions e.g. treatment scale-up reducing the number of new infections

One example of where this usage would be inappropriate
- Treatment lasts 6 months
    - The expected time spent in the compartment is only 1-2 timesteps, so the approximation that the time spent in the compartment by individuals is uniformly distributed is sufficiently good even if the treatment initiation rate changes rapidly


Timed parameter restrictions

- If the same timed parameter is used for multiple compartments, the destination compartments cannot be in the group of source compartments
x - If entered in the databook, only a constant value can be provided
- If it has a function, then it must be precomputable and have the same value at all times
x - Cannot be marked as a derivative
x - Must be in 'duration' units
x - Cannot be marked as 'targetable' (i.e. cannot be changed by programs)
x - Any given compartment can have a maximum of one outgoing timed transition
x - The timed compartment cannot be a birth, death, or junction compartment

A timed parameter defines a shared state
The quantity being tracked is 'time until the person needs to be moved'

Example calculation
*******************

Consider the example model shown below. There are 4 states in two groups, corresponding to vaccination status and diagnosis restricted. Individuals become diagnosis restricted by being treated (in this very simple example, perhaps prophylatically).  Here, ``dur`` is a timed parameter corresponding to the duration of protection for the vaccine. This means that ``vac`` and ``vacdxr`` are timed compartments, and the ``tx`` link between them (``vac:vacdxr``) is a duration-preserving timed link, while the ``tx`` link from ``sus:dxr`` is a normal link. From any compartment, transition to death is possible.

Next, suppose the current compartment sizes are ``sus=200`` and ``vac=100``. Further, suppose that the duration of protection is 10 years, the simulation time step is 1 year, and the ``vac`` individuals are uniformly distributed in arrival time. Therefore, of the 100 people in the overall vaccinated state, 10 of them need to move to an unvaccinated state. If ``tx=0`` then 10 people would flow from ``vac->sus`` in the next time step.  The use of a timed parameter implies that maintaining the duration of the state is of the highest priority. For example, it would be problematic if it was possible to extend the duration of protection by some of those 10 people instead flowing ``vac->vacdxr->dxr`` which would take two timesteps. With the exception of junctions, only one compartment transition is permitted per timestep, which ensures that individuals spend at least one timestep in each state they pass through. Note also that this is essential to ensure that the basic relationship that the change in compartment size is equal to the sum of outflows and inflows for

Individuals in the final time bin (i.e., the 10 individuals scheduled to leave the vaccinated group of compartments) must leave the duration group. Therefore, those individuals cannot be eligible for transitions into another compartment within the group. However, they _are_ eligible for any of the normal transitions out of the group. So consider the number of people eligble for the 3 Links flowing out of ``vac``

1. ``vac:sus`` 10 eligible
2. ``vac:death`` 100 eligible
3. ``vac:vacdxr`` 90 eligible

For disaggregation then, the ``vac:sus`` and ``vac:death`` transitions compete, and the ``vac:vacdxr`` and ``vac:death`` transitions compete, but there is no competition between ``vac:sus`` and ``vac:vacdxr``. Note however, that because ``vac:sus`` is the flush link associated with a timed transition, it never has a specific number of people to move. Instead, it simply flushes anyone remaining in the final time bin. Thus, we do not need to explicitly calculate its value or include it in any disaggregation calculations as long as we ensure that the ``vac:vacdxr`` transition does not include anyone in that final bin.

In the case where the total outflow is less than the compartment size, there should not be any issue. In the case where the outflow via ``death`` and ``tx`` is greater than the compartment size, then we have to rescale the links as required. There are two disaggregations we need to perform here that involve timed links:

1. Disaggregate ``tx`` between ``sus:dxr`` and ``vac:vacdxr``
2. Disaggregate ``tx`` and ``death`` between ``vac:vacdxr`` and ``vac:death``

First, consider disaggregating the ``tx`` _parameter_. If ``tx`` is in duration or probability units, no disaggregation is required. If ``tx`` is in number units, then it does need to be disaggregated.

Suppose we disaggregate between ``sus:dxr`` and ``vac:vacdxr`` treating both links as normal links. The source compartment sizes are 200 and 100, respectively. Suppose further that the value of the ``tx`` parameter is 60, and for the moment, suppose ``death=0``. Then, the disaggregation would provide ``sus:dxr=40`` and ``vac:vacdxr=20``. There are 90 people eligible for  ``vac:vacdxr`` so all of the 20 individuals eligble for ``vac:vacdxr`` make the transition. Now suppose the value of ``tx`` is 290. If we use the same disaggregation, we would get ``sus:dxr=193.3`` and ``vac:vacdxr=96.7``. However, only 90 people are eligible for ``vac:vacdxr``, so the total flow from ``tx`` would be ``283.3``. This would be incorrect at the higher level though, because ignoring death, there are in fact 290 individuals eligible for the ``tx`` transition. The disaggregation instead needs to be based on the 90 people eligble for ``vac:vacdxr``, not the 100 people in ``vac``. The ``source_popsize`` for ``tx`` needs to take into account eligibility for any ``TimedLink`` transitions associated with it.

Now, suppose ``tx`` is being calculated using programs. Program coverage is strictly compartment based, and therefore we can only target it at the entire compartments of ``sus`` and ``vac``. Thus, program coverage will always be based on the entire compartment size. This also makes sense because in general, it would not be possible to identify those individuals that are due to leave the timed group at the next timestep. In general then, we would overspend on the program because of the 300 people being covered, only 290 are actually eligible to make the transition. This is generally the case though, if a program is targeted at a compartment where it is possible for people to make other transitions - for example, a treatment program could be targeted at an infected compartment, but some of the treatments could be used on people that end up dying during the timestep, so the actual yield of the program is in general affected by other possible transitions. In view of this, the main question is whether we prioritize the duration of the state or the yield of the program (i.e. do we preference moving ``vac:vacdxr`` over ``vac:sus``) but as discussed above, if someone scheduled to be flushed via ``vac:sus`` instead transitions to ``vacdxr`` then they will have their duration in the timed group extended, which is likely to be _more_ problematic than the program yield being lower.

Thus, consider the case where ``tx`` is in number units, and the program spend is such that 150 people have been reached, so the program fractional coverage is 0.5. The outcome for the program is 1 (an individual reached by the program and eligible for the transition is guaranteed to transition) so the program's outcome value is ``0.5*1=0.5``. We interpret this as 'Of the people eligible for the transition, what proportion actually transition'. Therefore, we get ``sus:dxr=100``, and ``vac:vacdxr=45`` for a total of 145 transitions. It _would_ be possible in this case to have 150 people transition since there are more than 150 people eligible for the transition. That is, we have paid for 150 doses and allocated 100 doses to ``sus`` and 50 doses to ``vac``, and it would be _possible_ to provide those 50 doses to people who are not about to leave the compartment. However, we have no way of identifying those individuals, and thus the reduction in yield from 50 transitions to 45 transitions reflects the fact that 10% of the people are scheduled to leave the compartment anyway. It's worth noting that these types of sub-timestep effects could be reasoned differently depending on the order of events within the timestep. For example, whether an individual receives a treatment dose before or after they lose their vaccination status. In some cases, this is unresolvable. If someone dies before receiving a dose, then logically the dose could be given to someone else, but if someone dies after receiving a dose, then the dose is effectively wasted. The overall recommendation in this case is to reduce the time step size to increase temporal granuarity. This will have the effect of reducing the number of people required to leave the compartment group at each time step and thus reduce the competition between ``tx`` and ``dur``. Note that is is equally true for normal links in the model - there is equally competition between ``sus:death`` and ``sus:dxr`` so of the 100 doses allocated to ``sus``, some of those will be lost on people transitioning to death. _The fundamental assumption we are then making is that it is not possible for programs to identify how long individuals have been in the state_ which is fully consistent with the fact that programs are targeted at entire compartments.

.. tip::

    Overall, this all implies that ``Parameter.source_popsize`` should reflect the number of people _eligible_ for the transition, not simply the number of people in the source compartments.

The second disaggregation we need to examine is between ``vac:vacdxr`` and ``vac:death`` where the entire compartment is eligible for the death transition, and only part of the compartment is eligible for the ``tx`` transition. There are 4 cases

- Both in fraction units
- ``death`` as fraction, ``tx`` as number
- ``death`` as number, ``tx`` as fraction
- Both as number

First, consider the case where both are in fraction units, and further, suppose that the sum ``tx+death`` is greater than 1. For example, let's suppose that the death rate is 60%, and the ``tx`` rate is 50%. Of the 100 people in the compartment, 60 of them are expected to die. Of those 60, 6 of them would be in the subgroup of 10 individuals scheduled to leave the state, and would therefore be ineligible for the ``vac:vacdxr`` transition. Suppose then that ``tx`` was 0.5. If the model had been defined _without_ timed parameters, the ``dur`` transition would be ``0.1`` (to achieve a 10 year duration of protection under the steady state assumption). Then, the total fraction outflow would be ``0.1+0.5+0.6=1.2``. Therefore, we would divide each by ``1.2`` and obtain

- ``dur``: 8.3
- ``tx``: 41.7
- ``death``: 50

And the compartment would be emptied entirely. Now, consider disaggregating as follows: for the final bin, the eligible transitions are all normal transitions and the flush transition. However, the flush transition is a fallback if other transitions are not used to otherwise leave the state. Therefore, we disaggregate the normal transitions as usual, and then any remainder gets cleared via the flush junction. So of the 10 people scheduled to leave, 6 leave via ``death`` and 4 leave via ``sus``. Then, we disaggregate the remaining timesteps between the normal transition and any timed links, keeping in mind that the timed links are still removing the same proportion of each time bin (i.e. unless the source compartment is empty, we can always express the timed link as a fraction). Thus, we disaggregate a fraction outflow of 1.1 for the 90 people that are _not_ eligible for the flush transition. This yields a flow of 49.1 for ``death`` and ``40.9`` for ``tx``. The final outflow is then

- ``dur``: 4
- ``tx``: 40.9
- ``death``: 55.1

Now suppose the timestep was 10 times smaller. Now only 1 person is scheduled to leave the compartment group. Thus we get 0.6 leaving via death and 0.4 leaving via `dur`.


The important point here is that ``dur`` does not compete with ``death`` because ``dur`` represents loss of vaccine protection, but it is agnostic as to how this takes place - so it's equally fine for someone to lose their protection due to death.



