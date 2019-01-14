# Diagnosis-Treated

**Name**: DT

**Description**: Framework for a simple 2-stage diagnosed-treated model

## Contents
- [Compartments](#compartments)
- [Characteristics](#characteristics)
- [Parameters](#parameters)
- [Interactions](#interactions)

- [Cascades](#cascades)

## Compartments

### Compartment: Diagnosed, not treated

- Code name: `dx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Treated

- Code name: `tx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: All diagnosed

- Code name: `all_dx`
- Value can be used for calibration
- Includes:
	- Diagnosed, not treated
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

### Parameter: Annual number newly initiated onto treatment

- Code name: `initiate`
- Value can be used for calibration
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Diagnosed, not treated" to "Treated"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number lost to follow-up

- Code name: `num_loss`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Proportion of those on treatment lost-to-follow-up"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Proportion of those on treatment lost-to-follow-up

- Code name: `loss`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Treated" to "Diagnosed, not treated"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_loss/tx`
- Depends on:
	- "Treated"
	- "Annual number lost to follow-up"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: Cascade

- Description: <ENTER DESCRIPTION>
- Stages:
	- All diagnosed
		- All diagnosed
	- Currently treated
		- Currently treated

