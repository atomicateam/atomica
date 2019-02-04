# TB simple with dynamics

**Name**: TB with dynamics

**Description**: Framework for a simple TB model with vital dynamics and new cases

## Contents
- [Compartments](#compartments)
- [Characteristics](#characteristics)
- [Parameters](#parameters)
- [Interactions](#interactions)

- [Cascades](#cascades)

## Compartments

### Compartment: Source

- Code name: `source`
- Is source
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Susceptible

- Code name: `sus`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Vaccinated

- Code name: `vac`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Undiagnosed

- Code name: `undx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Diagnosed

- Code name: `dx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Notified and treated

- Code name: `tx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Lost to follow-up

- Code name: `lost`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Successfully treated (comp)

- Code name: `txs`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Dead (TB)

- Code name: `dead_tb`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Dead (other)

- Code name: `dead_other`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: Population size

- Code name: `alive`
- Value can be used for calibration
- Includes:
	- Susceptible
	- Vaccinated
	- Undiagnosed
	- Diagnosed
	- Notified and treated
	- Lost to follow-up
	- Successfully treated (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: TB burden

- Code name: `all_people`
- Value can be used for calibration
- Includes:
	- Undiagnosed
	- Diagnosed
	- Notified and treated
	- Lost to follow-up
	- Successfully treated (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Notified

- Code name: `all_dx`
- Value can be used for calibration
- Includes:
	- Diagnosed
	- Notified and treated
	- Lost to follow-up
	- Successfully treated (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: In care

- Code name: `all_curr_linked`
- Value can be used for calibration
- Includes:
	- Diagnosed
	- Notified and treated
	- Successfully treated (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Treated

- Code name: `all_tx`
- Value can be used for calibration
- Includes:
	- Notified and treated
	- Successfully treated (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Successfully treated

- Code name: `all_vs`
- Value can be used for calibration
- Includes:
	- Successfully treated (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Parameters

### Parameter: Annual number of births

- Code name: `birth_rate`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Source" to "Susceptible"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Estimated number of new TB cases annually

- Code name: `num_acq`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Acquisition rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Acquisition rate

- Code name: `acq_rate`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Susceptible" to "Undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_acq/max(sus,num_acq)`
- Depends on:
	- "Susceptible"
	- "Estimated number of new TB cases annually"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Natural recovery rate

- Code name: `rec_rate`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Undiagnosed" to "Susceptible"
	- "Diagnosed" to "Susceptible"
	- "Notified and treated" to "Susceptible"
	- "Lost to follow-up" to "Susceptible"
	- "Successfully treated (comp)" to "Susceptible"
- Default value: 0.16
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number vaccinated

- Code name: `num_vac`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Vaccination rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Vaccination rate

- Code name: `vac_rate`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Susceptible" to "Vaccinated"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_vac/max(sus,num_vac)`
- Depends on:
	- "Annual number vaccinated"
	- "Susceptible"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number of tests done

- Code name: `num_test`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Annual number tested positive"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Test yield

- Code name: `test_yield`
- Units/format: probability
- Value restrictions: 0-1.0000
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `undx/(undx+sus)`
- Depends on:
	- "Susceptible"
	- "Undiagnosed"
- Used to compute:
	- "Annual number tested positive"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number tested positive

- Code name: `pos_test`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_test*test_yield`
- Depends on:
	- "Annual number of tests done"
	- "Test yield"
- Used to compute:
	- "Test sensitivity"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Test sensitivity

- Code name: `diag`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Undiagnosed" to "Diagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `pos_test/max(undx,pos_test)`
- Depends on:
	- "Undiagnosed"
	- "Annual number tested positive"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number newly initiated onto treatment

- Code name: `num_initiate`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initiation rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initiation rate

- Code name: `initiate`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Diagnosed" to "Notified and treated"
	- "Lost to follow-up" to "Notified and treated"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_initiate/max(dx,num_initiate)`
- Depends on:
	- "Diagnosed"
	- "Annual number newly initiated onto treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Loss-to-follow-up rate

- Code name: `loss`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Notified and treated" to "Lost to follow-up"
	- "Successfully treated (comp)" to "Lost to follow-up"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Time after initiating treatment to treatment success (years)

- Code name: `supp_rate`
- Units/format: duration
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Notified and treated" to "Successfully treated (comp)"
- Default value: 0.2
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Treatment failure rate

- Code name: `fail_rate`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Successfully treated (comp)" to "Notified and treated"
- Default value: 0.16
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Death rate for those with untreated TB

- Code name: `death_tb`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Undiagnosed" to "Dead (TB)"
	- "Diagnosed" to "Dead (TB)"
	- "Lost to follow-up" to "Dead (TB)"
- Default value: 0.12
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Death rate for those unsuccessfully treated

- Code name: `death_tbtx`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Notified and treated" to "Dead (TB)"
- Default value: 0.06
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Death rate for those successfully treated

- Code name: `death_tbtxs`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Successfully treated (comp)" to "Dead (TB)"
- Default value: 0.03
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Background mortality rate

- Code name: `death_other`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Susceptible" to "Dead (other)"
	- "Vaccinated" to "Dead (other)"
	- "Undiagnosed" to "Dead (other)"
	- "Diagnosed" to "Dead (other)"
	- "Notified and treated" to "Dead (other)"
	- "Lost to follow-up" to "Dead (other)"
	- "Successfully treated (comp)" to "Dead (other)"
- Default value: 0.015
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: TB care cascade

- Description: <ENTER DESCRIPTION>
- Stages:
	- TB burden
		- TB burden
	- Notified
		- Notified
	- In care
		- In care
	- Treated
		- Treated
	- Successfully treated
		- Successfully treated

