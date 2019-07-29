.. _timed-transitions:

Timed transitions
#################

Motivation
**********

In Atomica, compartments typically correspond to states than an individual can be in. Often, in reality an individual needs to spend a certain amount of time in a particular state. For example, a particular treatment might have a certain duration, or an asymptomatic initial infection state might last for a particular amount of time. In a compartment based model that has reached a steady state, the inflow of people into a compartment is equal to the outflow. In that case, the equilibrium value of the compartment is equal to the duration. For example, suppose a compartment has an inflow of 100 people/year. If the duration is 5 years, the equilibrium value would be 500 people - each year, 100 people arrive and 100 people leave, so on average, it takes 5 years to leave the compartment.

This approach is widely used and is entirely valid in the steady state. In the steady state, the arrival times of people in the compartment can be considered uniformly distributed over the compartment's duration, so randomly selecting a portion of people to move out of the compartment results in the correct number of transitions. This assumption breaks down when inflow to the compartment varies over time. Because the true arrival time is not tracked, it's possible for someone to enter the compartment and immediately leave it in the next time step. This is reflected in the fact that the duration of a particular compartment is really an average duration, not a strict duration. 

In most circumstances, the standard compartment assumptions are sufficiently satisfied for the model to produce results within required tolerances. In particular, the fact that the duration assumptions are not exactly met is of secondary importance either when the inflow and outflow is approximately matched (typically when the inflow is significantly smaller than the compartment's size, which implies that the inflow has only a small effect on the outflow) or when the compartment's duration is short (e.g. a few timesteps).

There are some circumstances however, when both of these requirements are grossly violated. In that case, the model does not produce usable results. A common example would be mass vaccination campaigns. In that case, the proportion of people vaccinated changes very quickly, e.g. from 0% to 70% in a single year. Further, the duration of protection of vaccines tends to be quite long, for example, 5 years. In a simulation with quarterly timesteps, this would correspond to 20 timesteps. We might model this as vaccination moving people from a 'susceptible' compartment to a 'vaccinated' compartment, and protection wearing off as a transition from 'vaccinated' back to 'susceptible'. However, if we simply used the standard compartment assumptions, then people would be allowed to transition from 'vaccinated' to 'susceptible' immediately after being vaccinated. In this example, it is particularly noticable because the initial proportion vaccinated was 0% - therefore, it is obvious that _nobody_ should lose their vaccinated status until after 5 years. Further, the dynamics of the simulation would be significantly affected because the proportion vaccinated was very large (70%). Finally, if the mass vaccination is a temporary program (e.g. 1 year long) then the vaccination rate changes rapidly (from 0, to 70% of the population, then back to 0) over just a few timesteps. The standard compartment assumptions will not produce useful projections in these circumstances, so a different approach is required. To address this, Atomica implements **timed compartments** that explictly track arrival times, and allow transitions to take place only after a period of time has elapsed.

.. caution::

	Timed compartments add complexity and decrease performance. They should mainly be considered when **both** of these conditions are met:

	- The inflow into the compartment has extremely large, rapid changes
	- The duration of the compartment is much longer than the simulation timestep

Basic implementation
********************

Fundamentally, timed compartments leverage the fact that in Atomica, an individual must spend at least one timestep in each compartment (except for junction compartments) because new arrivals to a compartment are not eligible to move out of the compartment in the same timestep. Thus, we can explictly model a duration within the standard Atomica framework as a chain of compartments, where there are multiple compartments corresponding to a single state. For example, consider the case where a state lasts for 1 year, and there are quarterly timesteps. This could be set up as shown in the top part of the figure below:

.. image:: schematic/Slide1.PNG
	:width: 500px
    :alt: Basic compartment expansion

Instead of one compartment for the state, there are 4 compartments. People arrive at the 'T=1' compartment on the left of the figure. Each timestep, they move to the next compartment in the chain. After 4 compartments (corresponding to one year), they then leave the state. This is essentially the implementation of timed compartments - after a period of time has elapsed, all people in the timed state (blue boxes) are forced to move out to a different state (orange). This movement out of the state at the end of the duration period is referred to as 'flushing'. 

Although the chain of compartments at the top is functional without needing any additional functionality in Atomica, it is undesirable for two reasons. First, it would add significant complexity to the model framework, where single states could have many replicated compartments. And second, it introduces a coupling between the framework and the simulation step size, because the number of compartments required depends on both the duration and the simulation step size. 

Therefore, timed compartments are implemented as the bottom sequence shown below. 'State 1' is a single compartment in the framework file. The framework then specifies a special 'timed' duration parameter, that links 'State 1' to the orange compartment. The parameter is a 'timed' parameter, and the link from state 1 to the orange state is referred to as the 'flush link'. If the value of the parameter is 1 year and the simulation time step was 0.25, the duration of the compartment would then be 4 time steps. Internally, the model would be expanded into the top sequence of compartments. However, now the simulation step size can be freely changed, and further, the duration can also be easily modified in the databook. 

.. note::

	- A 'timed parameter' is one that is marked with a 'y' in the 'Timed' column of the framework
	- A 'flush link' is a transition goverened by a 'timed parameter'. There can only be one flush link per compartment. After the duration period has expired, all individuals that have been in the compartment for the specified duration are moved out of the compartment via the flush link. The figure shows the flush link as a red dashed arrow.
	- A 'timed compartment' is a compartment that has a flush link
	- The 'flush state' is the compartment that the flush link transfers people to
	- The 'initial subcompartment' is the 'compartment' where new arrivals enter (the 'T=1' compartment in the figure above)
	- The 'final subcompartment' is the 'compartment' from which people are flushed after the duration period has elapsed (the 'T=4' compartment in the figure above) 

Normal transitions
******************

After the duration period has elapsed, people are 'flushed' via the flush link to a single state. For the vaccination example, this would be from 'vaccinated' back to 'susceptible'. Another example might be modelling early and late latency in TB - if early latency is considered a timed state, after a set period has elapsed, people could be flushed into a late latent state. However, often transitions out of the timed compartment are possible before the duration period has elapsed. These transitions are typically to a different state than the flush state. For example, it would be possible for someone that is vaccinated to die of natural causes prior to their vaccination losing efficacy. 

This type of transition is equivalent to transitions from each subcompartment out to a specified compartment, as shown in the figure below. As with the example above, in Atomica this can be expressed simply as a transition from 'State 1' to 'Death', with the model automatically converting the simplified representation in the lower part of the figure, into the full representation in the top part of the figure.


.. image:: schematic/Slide2.PNG
	:width: 500px
    :alt: Expanded compartments with normal outflow

Most importantly, when transitioning out of the timed state (State 1), transitioning to 'Death' results in leaving the state, the same as transitioning to the orange flush state. Therefore, people in the final subcompartment (T=4) are also eligible for the transition, because it doesn't matter whether they leave State 1 to go to 'Death' or to go to the flush state, they have still left State 1 as required by the duration of the state. 

Duration groups
***************

As mentioned above, people in the final subcompartment are required to leave the timed compartment, but it doesn't matter whether they leave via the flush link or via a different transition. In some cases, the other transition might be to another timed compartment. In cases where the destination timed compartment is unrelated, there is no problem. For example, consider the case of someone that is vaccinated and transitioning to an infected state with an incubation period. Suppose further that the incubation state is also a timed compartment. In that case, anyone in a vaccinated subcompartment could transition into incubation, and they would enter incubation at the very start of the process, so they enter the second timed compartment as usual (via the initial subcompartment) and spend the full duration in the second state.

A special case, however, occurs if there need to be transitions that preserve the time spent in a state. In this case, the timed state does not map directly to a compartment - instead, it maps to a set of compartments. For example, suppose that we have a model where it is possible to acquire harmless symptoms mimicking the condition of interest (e.g. typhoid-like symptoms). This can be important to model if tests or treatments are being provided to people with symptoms prior to knowing whether they actually have the condition, in which case the expense of the intervention would be incurred without it having any effect on the epidemic. Suppose someone is vaccinated against typhoid with a duration of protection of 5 years. During this time, they may start off asymptomatic, but then acquire typhoid-like symptoms. They would then need to move to a 'vaccinated + typhoid-like symptoms' compartment. After some time, their symptoms might resolve, and they would move back to the 'vaccinated' state. However, the transition to and from typhoid-like symptoms should not affect the duration of protection. 

In this case, the 'vaccinated' meta-state applies to both the 'vaccinated' and 'vaccinated + typhoid-like symptoms' compartments. It is a state associated with the timed parameter, rather than the compartments. The transitions out of the two vaccinated compartments would likely be set up as follows

- A timed parameter, 'dur' representing the duration of protection
- 'vaccinated' flushing to 'susceptible', driven by the 'dur' parameter
- 'vaccinated + typhoid-like symptoms' flushing to 'susceptible + typhoid-like symptoms', also driven by the 'dur' parameter
- A transition from 'vaccinated' to 'vaccinated + typhoid-like symptoms' that preserves the time already spent in the 'vaccinated' compartment
- A transition from 'vaccinated + typhoid-like symptoms' back to 'vaccinated' that preserves the time already spent in the 'vaccinated + typhoid-like symptoms' compartment

In this way, the 'vaccinated' and 'vaccinated + typhoid-like symptoms' can be considered part of a 'duration group' because they share the same timed parameter, and transitions between them preserve the time spent in any compartment towards the duration specified by 'dur'. 

.. note::

	- A 'duration group' is the set of compartments that have flush links driven by the same timed parameter

The duration group can be implemented at the subcompartment level as shown below

.. image:: schematic/Slide3.PNG
	:width: 500px
    :alt: Expanded compartments with timed outflow

The key feature here is that because only one transition is possible in each timestep, the link from 'State 1' to 'State 2' also takes into account progression towards the total duration. 'T=1' in State 1 links to 'T=2' in State 2, and so on, resulting in the diagonal links shown in the figure above. Crucially, consider flows out of 'T=4', the final subcompartment. If an individual transitioned from State 1 'T=4' to State 2 'T=4', they would have to remain there for an additional timestep. This would result in them spending too much time in the duration group. Therefore, people in the final subcompartment are not eligible for transitions within the same duration group, as otherwise the total duration would not be preserved (keeping in mind that the use cases for timed compartments are ones where exactly preserving the duration is critically important). Therefore, in the figure above, the only transitions allowed out of the final subcompartment are to the flush state. 

These links within duration groups can coexist with links to other unrelated states as described above. For example, we could also include transitions to a death state, as shown below:

.. image:: schematic/Slide4.PNG
	:width: 500px
    :alt: Expanded compartments with mixed outflow

As before, Atomica simplifies this representation when defining the model, as shown below:

.. image:: schematic/Slide5.PNG
	:width: 500px
    :alt: Overall simplified structure

The flush links are shown as red dashed arrows. However, there is a red link between State 1 and State 2, because they belong to the same duration group and the transition between them preserves time spent in the group. This link is referred to as a 'timed link'. In contrast, a normal blue link joins 'State 1' and 'Death', because they are not part of the same duration group. 

.. note::

	- A 'timed link' connects compartments that belong to the same duration group. Transitions that go via a timed link preserve time spent in the duration group.

In practice, defining this setup in an Atomica framework file is simple. Suppose we had the following states

- Susceptible
- State 1
- State 2
- Death

and the following parameters

- 'inflow' moving people from susceptible into State 1
- 'transfer' moving people from State 1 into State 2
- 'd_rate' corresponding to the death rate 
- 'flush' corresponding to the duration spent in State 1 or State 2 (with those compartments belonging to the same duration group)

In the framework, the parameters would be defined as usual, but with 'flush' marked as a timed parameter. The transition matrix then looks like:

.. image:: schematic/transition_matrix_example.png
	:width: 500px
    :alt: Transition matrix example

This is all that is required to define the model - the software will automatically set up 'state_1' and 'state_2' to be timed compartments, and it will automatically determine that 'state_1' and 'state_2' belong to the same duration group and set up a timed link between them. 

Architecture
************

.. image:: schematic/Slide6.PNG
	:width: 500px
    :alt: TimedCompartment internal architecture

.. image:: schematic/Slide7.PNG
	:width: 500px
    :alt: Outflow paths from TimedCompartments

.. image:: schematic/Slide8.PNG
	:width: 500px
    :alt: Inflow and update for TimedCompartments

.. image:: schematic/Slide10.PNG
	:width: 500px
    :alt: TimedCompartment disaggregation



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

Note - what does it mean to be 'in' a compartment for a duration. Easiest way is to think of it as the number of chances to undergo a transition e.g. dt=0.25 and 1 year duration, there are 4 timesteps where you'd be eligible for transitions

Timed parameter restrictions

x - If a junction has a timed compartment input, it cannot have any untimed inputs
x - If a junction receives flush inputs, it cannot have outflows that end up in the same duration group
x - If the same timed parameter is used for multiple compartments, the destination compartments cannot be in the group of source compartments (cannot flush into the duration group)
x - If entered in the databook, only a constant value can be provided
x - If it has a function, then it must be precomputable and have the same value at all times
x - Cannot be marked as a derivative
x - Must be in 'duration' units
x - Cannot be marked as 'targetable' (i.e. cannot be changed by programs)
x - Any given compartment can have a maximum of one outgoing timed transition
x - The timed compartment cannot be a birth, death, or junction compartment
x - A timedcompartment cannot flush into a junction if one of the junction outputs belongs to the same duration group
x - A junction cannot receive inflow from more than one duration group

A timed parameter defines a shared state
The quantity being tracked is 'time until the person needs to be moved'

Transfers
*********

- To a shorter duration, they are all inserted into the initial subcompartment. However, because they have already been in the duration group, they get advanced in the update
- To a longer duration, the status is maintained

.. image:: schematic/Slide9.PNG
	:width: 500px
    :alt: TimedCompartment duration mismatch


Timed compartments and junctions
********************************

Timed compartments can be used in conjunction with junctions

We have defined previously the behaviours for transitions out of a TimedCompartment, namely that they can be
Transitions to another TimedCompartment in the same duration group, in which the final subcompartment is not eligible for the transition
Transitions to a normal compartment or a TimedCompartment in a different duration group, in which case the final subcompartment is eligible for the transition
These are mutually exclusive, because the final subcompartment either is or is not eligible for the transition
A junction can be thought of as disaggregating a single link out of the source compartment – that is, one link flows out of the source into the junction, but it ends up populating multiple downstream compartments
This is not logically possible if the downstream compartments mix the two cases described above, because the single link flowing out of the source compartment cannot simultaneously satisfy both cases
Therefore, in such cases we need to apply restrictions such that either the first case or the second case above is met, but not both
Namely, either all of the downstream compartments are in the same duration group as the source compartment, or none of them are
For this purpose, a junction also needs to be considered part of a duration group in this validation

A junction is attached to a duration group if it directly or indirectly has a TimedLink connecting it to a TimedCompartment and indirect paths only pass through JunctionCompartments. Attachment is directional
A junction belongs to a duration group if it attached to an upstream duration group, and also attached to the same group downstream
A junction can only belong to one duration group
If a junction is attached to an upstream duration group, it can either be attached to only the same downstream duration group, or it can be attached to any downstream groups except the upstream group
A junction that belongs to a duration group can only be connected, directly or indirectly, to TimedCompartments

.. image:: schematic/Slide11.PNG
	:width: 500px
    :alt: Junction flows

.. image:: schematic/Slide12.PNG
	:width: 500px
    :alt: Junction mixed output schematic

.. image:: schematic/Slide13.PNG
	:width: 500px
    :alt: Junction valid examples

.. image:: schematic/Slide14.PNG
	:width: 500px
    :alt: Junction examples of valid and invalid structures

.. image:: schematic/Slide15.PNG
	:width: 500px
    :alt: Indirect junctions examples

.. image:: schematic/Slide16.PNG
	:width: 500px
    :alt: Indirect junctions additional examples



Example calculation
*******************

Consider the example model shown below. There are 4 states in two groups, corresponding to vaccination status and diagnosis restricted. Individuals become diagnosis restricted by being treated (in this very simple example, perhaps prophylatically).  Here, ``dur`` is a timed parameter corresponding to the duration of protection for the vaccine. This means that ``vac`` and ``vacdxr`` are timed compartments, and the ``tx`` link between them (``vac:vacdxr``) is a duration-preserving timed link, while the ``tx`` link from ``sus:dxr`` is a normal link. From any compartment, transition to death is possible.

At each timestep, any individuals needing to be flushed from the compartment are resolved separately from all other transitions. That is, updating the compartment sizes now involves two steps

1. Non-flush link values are computed all flush links and assuming everyone is eligible for these transitions
2. The flush link value is computed based on inflow into the flush subcompartment. This is a separate compute stage because normal inflow into the compartment will affect how many people will be flushed
3. An update is carried out by
    1. Advancing the keyring, then
    2. Resolving all links, where the flush link acts on the first row, ``TimedLinks`` act on the top ``n-1`` rows, and normal ``Links`` act on the last row

To reduce storage requirements, the top row is omitted and that way ``TimedLink`` instances act on entire columns at a time.

Step (2) in this calculation populates the flush links with the number of people in each ``TimedCompartment`` that need to be cleared from the state. Therefore, they have their values set based on the ``TimedCompartment`` they are associated with during step (2), and are not updated during ``update_links``.

- Watch out for number parameters. In general the flow out of a timed compartment will be less. For example, suppose we have a number parameter moving 50 people out of vac to vacinf. But we have 100 people in vac and 10 of them due to move to sus. We end up moving 45 people from vac to vacinf. Because we cannot identify which people in vac are due to be flushed.


Test cases
**********

x - Finish lifespan test (transitions with junctions)
x - Indirect flows (multiple junctions)
x - Transfers with different durations in same group
x - TimedCompartments with duration less than one timestep
x - Check initialization works correctly with cascaded junctions
- Various invalid junctions

