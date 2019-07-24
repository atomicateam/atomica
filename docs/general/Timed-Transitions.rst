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

Timed compartments and junctions
********************************

Timed compartments can be used in conjunction with junctions


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

Transfers
*********

- To a shorter duration, they are all inserted into the initial subcompartment. However, because they have already been in the duration group, they get advanced in the update
- To a longer duration, the status is maintained

Test cases
**********

x - Finish lifespan test (transitions with junctions)
x - Indirect flows (multiple junctions)
x - Transfers with different durations in same group
x - TimedCompartments with duration less than one timestep
x - Check initialization works correctly with cascaded junctions
- Various invalid junctions

