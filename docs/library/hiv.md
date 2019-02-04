# HIV without dynamics

**Name**: HIV without dynamics

**Description**: Framework for an HIV model, without vital dynamics or new infections

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

### Compartment: Linked to care

- Code name: `linked`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Treated

- Code name: `tx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Lost to follow-up

- Code name: `lost`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Virally suppressed (comp)

- Code name: `vs`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: All PLHIV

- Code name: `all_people`
- Value can be used for calibration
- Includes:
	- Undiagnosed
	- Diagnosed
	- Linked to care
	- Treated
	- Lost to follow-up
	- Virally suppressed (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Aware of their status

- Code name: `all_dx`
- Value can be used for calibration
- Includes:
	- Diagnosed
	- Linked to care
	- Treated
	- Lost to follow-up
	- Virally suppressed (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Ever in care

- Code name: `all_ever_linked`
- Value can be used for calibration
- Includes:
	- Linked to care
	- Treated
	- Lost to follow-up
	- Virally suppressed (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Currently in care

- Code name: `all_curr_linked`
- Value can be used for calibration
- Includes:
	- Linked to care
	- Treated
	- Virally suppressed (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Currently treated

- Code name: `all_tx`
- Value can be used for calibration
- Includes:
	- Treated
	- Virally suppressed (comp)
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Virally suppressed

- Code name: `all_vs`
- Value can be used for calibration
- Includes:
	- Virally suppressed (comp)
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

### Parameter: Average time taken to be linked to care (years)

- Code name: `link_time`
- Value can be used for calibration
- Units/format: duration
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Diagnosed" to "Linked to care"
	- "Lost to follow-up" to "Linked to care"
- Default value: None
- Appears in the databook

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
	- "Linked to care" to "Treated"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_initiate/max(linked,num_initiate)`
- Depends on:
	- "Linked to care"
	- "Annual number newly initiated onto treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Loss-to-follow-up rate

- Code name: `loss`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Linked to care" to "Lost to follow-up"
	- "Treated" to "Lost to follow-up"
	- "Virally suppressed (comp)" to "Lost to follow-up"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Time after initiating ART to achieve viral suppression (years)

- Code name: `supp_rate`
- Units/format: duration
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Treated" to "Virally suppressed (comp)"
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
	- "Virally suppressed (comp)" to "Treated"
- Default value: 0.16
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: main

- Description: <ENTER DESCRIPTION>
- Stages:
	- All PLHIV
		- All PLHIV
	- Aware of their status
		- Aware of their status
	- Ever in care
		- Ever in care
	- Currently in care
		- Currently in care
	- Currently treated
		- Currently treated
	- Virally suppressed
		- Virally suppressed

