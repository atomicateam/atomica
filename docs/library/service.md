# Service modalities

**Name**: Service

**Description**: Service Modalities cascade

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

### Compartment: Unaware of own need

- Code name: `unaware`
- Value can be used for calibration
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Aware but not linked to services

- Code name: `unlinked`
- Value can be used for calibration
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Linked to service provider

- Code name: `untx`
- Value can be used for calibration
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Receiving services

- Code name: `txf`
- Value can be used for calibration
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Successful outcome

- Code name: `txs`
- Value can be used for calibration
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Dead

- Code name: `dead`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: All people

- Code name: `ch_all`
- Value can be used for calibration
- Includes:
	- Unaware of own need
	- Aware but not linked to services
	- Linked to service provider
	- Receiving services
	- Successful outcome
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People aware of need

- Code name: `ch_aware`
- Value can be used for calibration
- Includes:
	- Aware but not linked to services
	- Linked to service provider
	- Receiving services
	- Successful outcome
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People linked to services

- Code name: `ch_linked`
- Value can be used for calibration
- Includes:
	- Linked to service provider
	- Receiving services
	- Successful outcome
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People receiving services

- Code name: `ch_tx`
- Value can be used for calibration
- Includes:
	- Receiving services
	- Successful outcome
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People with successful outcomes

- Code name: `ch_succ`
- Value can be used for calibration
- Includes:
	- Successful outcome
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion aware of need

- Code name: `ch_propaware`
- Value can be used for calibration
- Includes:
	- Aware but not linked to services
	- Linked to service provider
	- Receiving services
	- Successful outcome
- Denominator: All people
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion linked to services

- Code name: `ch_proplinked`
- Value can be used for calibration
- Includes:
	- Linked to service provider
	- Receiving services
	- Successful outcome
- Denominator: All people
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion receiving services

- Code name: `ch_proptx`
- Value can be used for calibration
- Includes:
	- Receiving services
	- Successful outcome
- Denominator: All people
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion with successful outcomes

- Code name: `ch_propsucc`
- Value can be used for calibration
- Includes:
	- Successful outcome
- Denominator: All people
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Parameters

### Parameter: Number of new cases (annual)

- Code name: `acq_rate`
- Units/format: number
- Contributes to transitions from:
	- "Source" to "Unaware of own need"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number becoming aware of need (annual)

- Code name: `num_screen`
- Value can be used for calibration
- Units/format: number
- Contributes to transitions from:
	- "Unaware of own need" to "Aware but not linked to services"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number linked to services (annual)

- Code name: `num_diag`
- Value can be used for calibration
- Units/format: number
- Contributes to transitions from:
	- "Aware but not linked to services" to "Linked to service provider"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number initiated onto services (annual)

- Code name: `num_treat`
- Value can be used for calibration
- Units/format: number
- Contributes to transitions from:
	- "Linked to service provider" to "Receiving services"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Proportion of those without successful outcomes who are offered further support

- Code name: `treat_suc`
- Value can be used for calibration
- Units/format: probability
- Contributes to transitions from:
	- "Receiving services" to "Successful outcome"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Probability of successful outcome among those receiving services

- Code name: `treat_fail`
- Value can be used for calibration
- Units/format: probability
- Contributes to transitions from:
	- "Successful outcome" to "Receiving services"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Background mortality rate

- Code name: `death`
- Units/format: probability
- Contributes to transitions from:
	- "Unaware of own need" to "Dead"
	- "Aware but not linked to services" to "Dead"
	- "Linked to service provider" to "Dead"
	- "Receiving services" to "Dead"
	- "Successful outcome" to "Dead"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: main

- Description: <ENTER DESCRIPTION>
- Stages:
	- All people
		- All people
	- People aware of need
		- People aware of need
	- People linked to services
		- People linked to services
	- People receiving services
		- People receiving services
	- Successful outcome
		- Successful outcome

