
Units
========

Propagation of units through the code

- Two representations
    - a pairing of a format and timescale
        - 'Duration', 1/12
        - 'Probability', 1/52
        - 'Number', 1/365
    - a single string
        - 'Duration (months)'
        - 'Probability (per week)'
        - 'Number (per day)'

Two key points above

    1. In the second format, have to parse the string to work out how to scale the probabilities during integration
    2. In the second format, there is a difference between 'months' and 'per month'

The first format is desirable for defining the parameters and actually performing the integration, while the second format is desirable for presentation in the databook and in finished plots.



-> Do we ever want to sum? Rather than integrating? If we want things to come out in units of 'person years' then always need to be multiplying by the timestep. So maybe we do always want the integral, even for DALYs? Especially if DALYs are a cumulative sum of time spent in the death compartment. In that case
    - Always annualize numbers
    - Bad idea to integrate probabilities or durations
    - If there is a timescale denominator, it becomes None
    - If there is no timescale denominator, we acquire 'years' in the numerator
        - But, unlike 'Duration (months)' it would be 'Number of people' -> 'Number of person years'

