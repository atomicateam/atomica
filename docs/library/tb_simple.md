# TB simple model

**Name**: Simple TB

**Description**: Framework for a simple TB model, without vital dynamics or new cases

## Contents
- [Compartments](#compartments)
- [Characteristics](#characteristics)
- [Parameters](#parameters)
- [Interactions](#interactions)

- [Cascades](#cascades)

## Compartments

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

## Characteristics

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
- Appears in the databook
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

- Code name: `succ_rate`
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

