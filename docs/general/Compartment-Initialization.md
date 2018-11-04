# Initializing compartments

An important step in integrating the model equations is specifying the initial conditions. There are two challenges to overcome

- Computing initial compartment sizes _based on the values entered in the databook_
- Computing the initial compartment sizes _at an arbitrary initial time_

We will discuss these two issues in turn.

## Characteristics to Compartments

The first challenge is related to the fact that in the databook, users enter initial values for characteristics, not just compartments. This is motivated by the fact that application data may correspond to characteristics rather than compartments. **The guiding principle is that the databook should strive to directly accept as much data as the user has available**. That is, the databook aims to be as complete a record of the available data as possible, with as little manual user processing as possible.

To see why initial values are often drawn via characteristics, consider the TB cascade. Because latent infection has a separate stream for vaccinated and unvaccinated individuals, the model contains the following compartments

Short name | Long name
--- | ---
`vac`	| Vaccinated
`ltex`	| Early latent (undiagnosable)
`ltlx`	| Late latent (undiagnosable)

All of the people in these compartments have recieved a vaccine, because the `ltex` and `ltlx` compartments are specific to vaccinated individuals. Thus, the `vac` *compartment* corresponds to people who have been vaccinated, but who have _not_ acquired a latent TB infection. However, data is likely to be available for the total number of vaccinated people regardless of their latent infection status. Thus, the data is likely to correspond to a characteristic defined as `vac+ltex+ltlx`. Similarly, there is typically good demographic data available for the total population size. However, the total population size is given by the sum of all of the compartments in the model.

Given a set of characteristics, the goal is then to compute the corresponding compartment sizes. For example, if we know

	nvac = vac+ltex+ltlt (total number of vaccinated individuals)
	ltx = ltex+ltlx (total number of latent infections in the vaccinated population)
	ltlx (number of late latent infections)

where `nvac` and `ltx` are the names of the characteristics, then we can readily use substitutions to infer the initial compartment sizes.

### Optima TB and entry points

In Optima TB, this calculation was implemented as an iterative explicit substitution. The user was required to specify for each characteristic an 'entry point'. The 'entry point' corresponds to the compartment that the characteristic is supplying values for. Each compartment is required to appear as the entry point for exactly one characteristic. For example

Characteristic | Entry point | Equation
--- | --- | ---
`nvac` | `vac` | `vac = nvac - ltex - ltlt`
`ltx` | `ltex` | `ltex = ltx - ltlx`
`ltlx` | `ltlx` | `ltlx = ltlx`

When computing the compartment value, it is assumed that an explicit value has already been calculated for all of the remaining characteristics. That is, we assume that it is possible to evaluate the equations listed above based on the values supplied either in the databook or computed from other characteristics. The computation would proceed as follows

1. Use the third equation to supply the value for `ltlx` based on the databook
2. Use the value computed for `ltlx` together with the value of `ltx` supplied in the databook to compute the initial value for `ltex`
3. Use the values computed for `ltex` and `ltlx` together with the value of `nvac` supplied in the databook to compute the initial value for `vac`

The implementation essentially proceeds as described above, in a loop. In the general case, there could be many arbitrary combinations of compartments. The main issues with this approach are that a lot of logic is needed in the implementation to determine the correct order in which to initialize the compartments, which is complicated and **difficult to ensure correctness**, and that it is up to the modeller to decide which compartment to assign as the entry point for each characteristic (for example, in theory *any* one compartment could be listed as the entry point for the `alive` characteristic).

### Matrix-based approach

The equations for the characteristics

	nvac = vac+ltex+ltlt
	ltx = ltex+ltlx
	ltlx

can be readily recognized as a system of simultaneous equations. This can be written in matrix form as follows

	[nvac]   [1 1 1]    [vac ]
	[ltx ] = [0 1 1] *  [ltex]
	[ltlx]   [0 0 1]    [ltlx]

where the column vector on the left corresponds to the characteristics that the user enters in the databook, the matrix in the middle corresponds to the included compartments for each characteristic defined in the Framework, and the column vector on the right corresponds to the compartment sizes for all compartments in the model. We therefore want to solve for the values in the column vector on the right, given the values for the characteristics on the left, and the compartment membership matrix in the middle. This is the familiar system

	y = A*x

which can be solved using any number of standard linear algebra functions (e.g. `numpy.linalg.solve`). Subject to the limitations imposed on the system by the Optima TB databook (namely that each characteristic has one entry point, and every compartment appears exactly once in the list of entry points) this linear algebra based routine is **functionally identical** to the original implementation, except

- It is considerably shorter because the complexity is offloaded to numpy/scipy
- It is more reliable because no complex logic to validate

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

then a negative value for `sus` would be a consequence of the value for the characteristic `nvac` which itself could be the result of a computation. Thus, the user has to look at a set of characteristics and compartments to trace where the original inconsistency occurred. As a result, the most helpful output for the user to debug this is a dump of all of the compartment and characteristic values, which is the same in both the original and the linear algebra based approach.

#### Underdetermined system

With the introduction of the linear algebra based approach, specification of entry points is no longer required (because in actuality that information is redundant). In Optima TB, it was possible to throw an error if a compartment was not included as an entry point in any of the characteristics, thus preventing its value from being computed. In the linear algebra approach, this condition can be directly detected based on the `A` matrix. For example, consider the system

	nvac = vac + ltex + ltlx
	ltx = ltex + ltlx

By inspection, there is clearly insufficient information provided to be able to uniquely solve for the compartment sizes. The corresponding matrix equation is

	[nvac]   [1 1 1]    [vac ]
	[ltx ] = [0 1 1] *  [ltex]
	                    [ltlx]

(which is of course a valid matrix equation, with dimensions `(2x1) = (2x3)*(3x1)`). The fact that there is insufficient information can be detected by comparing the rank of the `A` matrix with the number of compartments. Specifically, `y=A*x` is underdetermined if the rank of `A` is less than the length of `x`. This can be trivially checked using Numpy's built in `numpy.linalg.matrix_rank` function. Note that this is a stricter condition than simply counting the number of characteristics on the left hand side, because it is possible for a characteristic to not to provide any unique information if that characteristic can be expressed as a linear combination of other characteristics in the system. Thus, instead of using the entry points, we can check the rank of the matrix to directly identify cases where there is insufficient information for initialization.

#### Inconsistent system

In the case where the number of characteristics used for initialization is the same as the number of compartments, there exists a single unique solution for the compartment values that exactly matches the characteristic values. For example, if we have

	alive = sus + vac

and are also given that

	alive = 100
	vac = 120

then we have the unique solution

	sus = -20
	vac = 120
	alive = -20 + 120 = 100

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

In this case though, the consequence of the inconsistency is *not* that a compartment value becomes negative. Instead, it is manifested as a nonzero residual when comparing the provided input values to the calculated initialization. Which inconsistent initialization should be chosen? In Optima TB, the approach is that the entry points specify the initialization and redundant conflicting information is ignored. For example, if we have

Characteristic | Entry point
--- | ---
`alive` | `sus`
`sus` | `-`
`vac` | `vac`

then the initialization will proceed with

1. `vac=50`
2. `sus = alive-vac = 100-50 = 50`

And note that the `sus = 60` information specified by the user is ignored entirely. The fact that this information was ignored is a consequence of the choice of entry points. If we instead had

Characteristic | Entry point
--- | ---
`alive` | `vac`
`sus` | `sus`
`vac` | `-`

then the calculation would proceed with the equally valid

1. `sus = 60`
2. `vac = alive - sus = 100-60 = 40`

In general, with a large number of characteristics and compartments, it is not easy to determine which information in the databook will take priority in the initialization. In the linear algebra based approach, we can write out the matrix equation as

	[alive]   [1 1]    [sus ]
	[sus  ] = [1 0] *  [vac ]
	[vac  ]   [0 1]

Notice how this system is obviously overdetermined, because the column vector on the left is longer than the column vector on the right. We can solve this overdetermined system using a standard least squares approach (e.g. `np.linalg.lstsq`). In the case where all of the information provided is consistent, the residual for the fit will be `0`. If the values are inconsistent, the least squares solution will solve for the compartment sizes on the right that best match the set of characteristics on the left. In this case, this would be

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

where the initialization penalizes discrepancies in `alive` and `vac` more than discrepancies in `sus`. This is a simple case of weighted least squares, and can be readily incorporated into the algorithm. To cater for this, the user needs to specify a **setup weight** for each characteristic.

## Additional open questions

The linear algebra method solves the core of the problem of inverting characteristic values to solve for compartment values given a set of characteristics. The key questions on the input side are

- How and where to specify which characteristics to use for initialization
- How and where to specify the setup weights

The simplest approach would be to simply read all of the characteristics in the databook and use them all to calculate the compartment sizes. This approach will work in general as long as the databook contains a sufficient set of characteristics for the system to not be underdetermined. It is currently up to the modeller to ensure that the 'databook order' in the Framework results in a sufficient set of charcteristics will appear in the databook.

However, a characteristic is ignored for initialization if the setup weight is 0. If the user is able to set setup weights, then it is possible that the user could set some of the characteristics to be ignored for initialization such that the system becomes underdetermined, resulting in an error. To prevent this, the setup weights are currently specified in the Framework, which users are not expected to edit.

The general philosophy is that

- Modellers interact primarily with frameworks
- Users interact primarily with databooks
- Users are not expected to be able to diagnose and fix errors such as the system being underdetermined

On the other hand, the setup weight is currently proposed to mainly reflect data quality, which means that it _ought_ to be specified in the databook so that different projects with different data can share the framework file but perform their initialization differently due to their differing data. This is currently not possible, because the setup weights are in the framework file.

A proposed simplification without loss of functionality is:

- The 'setup weights' are removed from the Framework, with characteristics in the databook assumed to have a setup weight of `1.0`
- A _nonzero_ setup weight can be _optionally_ specified in the databook, which overrides the default value of `1.0`

Here, it is still the modeller's responsiblity to select a suitable set of characteristics to appear in the databook. However, the user is now able to provide weights that reflect their data quality without the possibility of those weights resulting in the system becoming underdetermined. The conditions for a nonzero setup weight to be used are

- The provided characteristic values are inconsistent, _and_
- Some of the data is known to be of higher quality than others, _and_
- Those characteristics are also the ones where the inconsistency occurs

Thus, _for the majority of applications, no setup weight would need to be entered_. If the provided characteristic values are inconsistent, this is detected automatically based on the residual being large, and the user is warned accordingly. At that point, the user can decide whether or not they need to specify different setup weights.

## Computing initial values at arbitrary times

The initial compartment values are computed based on the characteristic values at a specific point in time. However, the data values entered in the databook are in general provided at sparse, arbitrary times. Therefore, it is typically necessary to interpolate each of the characteristics onto the initial simulation time prior to calculating the initial compartment values.

The critical issue here is that inconsistencies in the values can be time dependent. For example, the user may enter a consistent set of values in 1990 but an invalid set of values in 2000. If the simulation is started in 1990 then it may run fine, but if started in 2000 it is possible that an inconsistency could result in negative compartment sizes. More insidious is the possibility that interpolation could result in inconsistent values. For example, suppose that the values are consistent in 1990 *and* in 2000. It is still possible that in 1995 the interpolated values are not consistent, particularly if some of the characteristics have data values between 1990 and 2000 and others do not.

Because the interpolation routine uses the nearest-neighbour value for times before and after the first or last data point, respectively, if the simulation is started from the first year in the databook then it is possible to directly read out the characteristic values used for interpolation, which makes diagnosing inconsistencies easier. However, if interpolation results in inconsistencies, the input characteristic values will not correspond to anything entered in the databook. So it is important to keep this issue in mind when diagnosing inconsistent initializations when the simulation start year is different to the data start year.