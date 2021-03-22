# Initializing compartments

An important step in integrating the model equations is specifying the initial conditions. There are two challenges to overcome

- Computing initial compartment sizes *based on the values entered in the databook*
- Computing the initial compartment sizes *at an arbitrary initial time*

We will discuss these two issues in turn.

## Characteristics to Compartments

The first challenge is related to the fact that in the databook, users enter initial values for characteristics, not just compartments. This is motivated by the fact that application data may correspond to characteristics rather than compartments. **The guiding principle is that the databook should strive to directly accept as much data as the user has available**. That is, the databook aims to be as complete a record of the available data as possible, with as little manual user processing as possible.

To see why initial values are often drawn via characteristics, consider a standard TB model. Because latent infection has a separate stream for vaccinated and unvaccinated individuals, the model contains the following compartments

Short name | Long name
--- | ---
`vac`	| Vaccinated
`ltex`	| Early latent (undiagnosable)
`ltlx`	| Late latent (undiagnosable)

All of the people in these compartments have received a vaccine, because the `ltex` and `ltlx` compartments are specific to vaccinated individuals. Thus, the `vac` *compartment* corresponds to people who have been vaccinated, but who have _not_ acquired a latent TB infection. However, data is likely to be available for the total number of vaccinated people regardless of their latent infection status. Thus, the data is likely to correspond to a characteristic defined as `vac+ltex+ltlx`. Similarly, there is typically good demographic data available for the total population size. However, the total population size is given by the sum of all of the compartments in the model.

Given a set of characteristics, the goal is then to compute the corresponding compartment sizes. For example, if we know

    nvac = vac+ltex+ltlx (total number of vaccinated individuals)
    ltx = ltex+ltlx (total number of latent infections in the vaccinated population)
    ltlx (number of late latent infections)

where `nvac` and `ltx` are the names of the characteristics, then we can readily use substitutions to infer the initial compartment sizes. However, the equations for the characteristics

    nvac = vac+ltex+ltlx
    ltx = ltex+ltlx
    ltlx

can be readily recognized as a system of simultaneous equations. This can be written in matrix form as follows

    [nvac]   [1 1 1]    [vac ]
    [ltx ] = [0 1 1] *  [ltex]
    [ltlx]   [0 0 1]    [ltlx]

where the column vector on the left corresponds to the characteristics that the user enters in the databook, the matrix in the middle corresponds to the included compartments for each characteristic defined in the Framework, and the column vector on the right corresponds to the compartment sizes for all compartments in the model. We therefore want to solve for the values in the column vector on the right, given the values for the characteristics on the left, and the compartment membership matrix in the middle. This is the familiar system

    y = A*x

which can be solved using any number of standard linear algebra functions (e.g. `numpy.linalg.solve`).

### Problems and solutions

#### Negative initial compartment sizes

It is possible for the initial characteristic values provided by the user to lead to negative initial compartment sizes. For example, if the user specified

    alive = sus + vac
    alive = 100
    vac = 120

then the value for `vac` is clearly critically inconsistent with the value for `alive`, because the corresponding value for `sus` must be `-20`. In the previous Optima TB approach, this error can be isolated to the computation of the `alive` characteristic, whereas in the linear algebra approach, it is the consequence of the matrix operation and thus cannot be isolated directly. However, in practice this did not make much difference in Optima TB because characteristics are typically nested. That is, if we instead had

    alive = sus + nvac
    nvac = vac + ltex + ltlt
    ...

then a negative value for `sus` would be a consequence of the value for the characteristic `nvac` which itself could be the result of a computation. Thus, the user has to look at a set of characteristics and compartments to trace where the original inconsistency occurred. As a result, the most helpful output for the user to debug this is a dump of all of the compartment and characteristic values, which is the same in both the original and the linear algebra-based approach.

#### Underdetermined system

An initialization is underdetermined if the input data is not sufficient to uniquely specify the initialization without additional assumptions. This condition can be directly detected based on the `A` matrix. For example, consider the system

    nvac = vac + ltex + ltlx
    ltx = ltex + ltlx

By inspection, there is clearly insufficient information provided to be able to uniquely solve for the compartment sizes. The corresponding matrix equation is

    [nvac]   [1 1 1]    [vac ]
    [ltx ] = [0 1 1] *  [ltex]
                        [ltlx]

(which is of course a valid matrix equation, with dimensions `(2x1) = (2x3)*(3x1)`). The fact that there is insufficient information can be detected by comparing the rank of the `A` matrix with the number of compartments. Specifically, `y=A*x` is underdetermined if the rank of `A` is less than the length of `x`. This can be trivially checked using Numpy's built in `numpy.linalg.matrix_rank` function. Note that this is a stricter condition than simply counting the number of characteristics on the left-hand side, because it is possible for a characteristic to not to provide any unique information if that characteristic can be expressed as a linear combination of other characteristics in the system. 

In Atomica, underdetermined systems are handled by returning the minimum norm solution, so any compartments missing entirely will be initialized with 0, and in cases where compartments are nonzero but not uniquely constrained, people will be uniformly distributed across those compartments. 

#### Inconsistent system

In the case where the number of characteristics used for initialization is the same as the number of compartments, there exists a single unique solution for the compartment values that exactly matches the characteristic values. For example, if we have

```
alive = sus + vac
```

and are also given that 

```
alive = 100
vac = 120
```

then we have the unique solution

```
sus = -20
vac = 120
alive = -20 + 120 = 100
```

which exactly matches the specified values `alive=100` and `vac=120`. The inconsistency in the system therefore results in a negative compartment size appearing in one or more compartments, and this can be detected regardless of the implementation used for initialization.

#### Inconsistent overdetermined system

As described above, the guiding principle for the databook is that it strives to be a complete, direct record of all available data. In pursuing this, it is possible that the user could provide an overspecification of the system. For example, suppose we have a characteristic `alive = sus + vac` and the user has the following values from their data sources

    alive = 100
    sus = 60
    vac = 50

This situation (where the data values are not entirely consistent) can occur when users are compiling data from multiple sources. How should this inconsistency be resolved? Note that in the case where the system is overdetermined, the inconsistent values mean that it is not possible to choose initial values for `sus` and `vac` that exactly satisfy the provided values. For example, we could have

    sus = 60
    vac = 50
    alive = 60+50=110 (does not match provided value)

or we could have

    sus = 50 (does not match provided value)
    vac = 50
    alive = 50 + 50 = 100

In this case though, the consequence of the inconsistency is *not* that a compartment value becomes negative. Instead, it is manifested as a nonzero residual when comparing the provided input values to the calculated initialization. We can write out the matrix equation as

    [alive]   [1 1]    [sus ]
    [sus  ] = [1 0] *  [vac ]
    [vac  ]   [0 1]

Notice how this system is obviously overdetermined because the column vector on the left is longer than the column vector on the right. We can solve this overdetermined system using a standard least squares approach (e.g. `np.linalg.lstsq`). In the case where all of the information provided is consistent, the residual for the fit will be `0`. If the values are inconsistent, the least squares solution will solve for the compartment sizes on the right that best match the set of characteristics on the left. In this case, this would be

    sus = 56.66
    vac = 46.66

and the corresponding value of alive would be 103.32. In this way, the difference between the data provided by the user and the values used for initialization is minimized across all of the values provided. The least squares solution also has the useful property that it is unique.

#### Resolving inconsistencies - initialization weight

In the example above, where the inconsistent input values of

    sus = 60
    vac = 50
    alive = 100

were resolved with the valid initialization

    sus = 56.66
    vac = 46.66
    alive = 103.32

the overall residual has been minimized across all of the provided characteristics. However, in general there are likely to be uncertainties in the data. The user may wish to more closely match the data they are most certain about. For example, if there was a census in that year so that `alive=100` is quite likely, and there was also good data on vaccination stating that `vac=50` then it may be preferable to use an initialization like

    sus = 50.2
    vac = 49.9
    alive = 100.2

where the initialization penalizes discrepancies in `alive` and `vac` more than discrepancies in `sus`. This is a simple case of weighted least squares and can be readily incorporated into the algorithm. To cater for this, the user needs to specify a **setup weight** for each characteristic. **However, using the provided setup weights has not been implemented in Atomica yet**. 

## Computing initial values at arbitrary times

The initial compartment values are computed based on the characteristic values at a specific point in time. However, the data values entered in the databook are in general provided at sparse, arbitrary times. Therefore, it is typically necessary to interpolate each of the characteristics onto the initial simulation time prior to calculating the initial compartment values.

The critical issue here is that inconsistencies in the values can be time dependent. For example, the user may enter a consistent set of values in 1990 but an invalid set of values in 2000. If the simulation is started in 1990 then it may run fine, but if started in 2000 it is possible that an inconsistency could result in negative compartment sizes. More insidious is the possibility that interpolation could result in inconsistent values. For example, suppose that the values are consistent in 1990 *and* in 2000. It is still possible that in 1995 the interpolated values are not consistent, particularly if some of the characteristics have data values between 1990 and 2000 and others do not.

Because the interpolation routine uses the nearest-neighbour value for times before and after the first or last data point, respectively, if the simulation is started from the first year in the databook then it is possible to directly read out the characteristic values used for interpolation, which makes diagnosing inconsistencies easier. However, if interpolation results in inconsistencies, the input characteristic values will not correspond to anything entered in the databook. So it is important to keep this issue in mind when diagnosing inconsistent initializations when the simulation start year is different to the data start year.
