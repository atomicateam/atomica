# UDT model with dynamics

**Name**: UDT

**Description**: UDT example

## Contents
- [Compartments](#compartments)
- [Characteristics](#characteristics)
- [Parameters](#parameters)
- [Interactions](#interactions)

- [Cascades](#cascades)

## Compartments

### Compartment: Births

- Code name: `birth`
- Is source
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

### Compartment: Treated

- Code name: `tx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: dead

- Code name: `dead`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: All people with condition

- Code name: `all_people`
- Value can be used for calibration
- Includes:
	- Undiagnosed
	- Diagnosed
	- Treated
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Diagnosed people

- Code name: `all_dx`
- Value can be used for calibration
- Includes:
	- Diagnosed
	- Treated
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Currently treated

- Code name: `all_tx`
- Value can be used for calibration
- Includes:
	- Treated
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Parameters

### Parameter: Annual number of new diagnoses

- Code name: `num_diag`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Diagnosis rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Diagnosis rate

- Code name: `diag`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Undiagnosed" to "Diagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_diag/max(undx,num_diag)`
- Depends on:
	- "Undiagnosed"
	- "Annual number of new diagnoses"

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
	- "Diagnosed" to "Treated"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_initiate/max(dx,num_initiate)`
- Depends on:
	- "Diagnosed"
	- "Annual number newly initiated onto treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number lost to follow-up

- Code name: `num_loss`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Loss-to-follow-up rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Loss-to-follow-up rate

- Code name: `loss`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Treated" to "Diagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_loss/max(tx,num_loss)`
- Depends on:
	- "Treated"
	- "Annual number lost to follow-up"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Birth rate

- Code name: `b_rate`
- Units/format: number
- Contributes to transitions from:
	- "Births" to "Undiagnosed"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Untreated death rate

- Code name: `inf_death`
- Units/format: probability
- Contributes to transitions from:
	- "Undiagnosed" to "dead"
	- "Diagnosed" to "dead"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Treated death rate

- Code name: `tx_death`
- Units/format: probability
- Contributes to transitions from:
	- "Treated" to "dead"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: Cascade

- Description: <ENTER DESCRIPTION>
- Stages:
	- All people with condition
		- All people with condition
	- Diagnosed people
		- Diagnosed people
	- Currently treated
		- Currently treated

