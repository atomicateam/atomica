# Hypertension with dynamics

**Name**: Hypertension with dynamics

**Description**: Framework for a hypertension model, with vital dynamics and new cases

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

### Compartment: No hypertension

- Code name: `sus`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Undiagnosed

- Code name: `undx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Screened, not diagnosed

- Code name: `scr`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Diagnosed, not treated

- Code name: `dx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Treated, not controlled

- Code name: `tx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Controlled

- Code name: `con`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Dead (hypertension)

- Code name: `dead_hyp`
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
	- No hypertension
	- Undiagnosed
	- Screened, not diagnosed
	- Diagnosed, not treated
	- Treated, not controlled
	- Controlled
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: All people with condition

- Code name: `all_people`
- Value can be used for calibration
- Includes:
	- Undiagnosed
	- Screened, not diagnosed
	- Diagnosed, not treated
	- Treated, not controlled
	- Controlled
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Screened people

- Code name: `all_screened`
- Value can be used for calibration
- Includes:
	- Screened, not diagnosed
	- Diagnosed, not treated
	- Treated, not controlled
	- Controlled
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Diagnosed people

- Code name: `all_dx`
- Value can be used for calibration
- Includes:
	- Diagnosed, not treated
	- Treated, not controlled
	- Controlled
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Currently treated

- Code name: `all_tx`
- Value can be used for calibration
- Includes:
	- Treated, not controlled
	- Controlled
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Blood pressure controlled

- Code name: `all_con`
- Value can be used for calibration
- Includes:
	- Controlled
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
	- "Source" to "No hypertension"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Estimated number of new cases annually

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
	- "No hypertension" to "Undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_acq/max(sus,num_acq)`
- Depends on:
	- "No hypertension"
	- "Estimated number of new cases annually"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number screened

- Code name: `num_screen`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Screening coverage shares"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Target population for screening programs

- Code name: `screen_target`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `undx+sus`
- Depends on:
	- "No hypertension"
	- "Undiagnosed"
- Used to compute:
	- "Annual number screened positive"
	- "Screening coverage shares"
	- "Screening yield"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Screening coverage shares

- Code name: `screen_cov`
- Units/format: proportion
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_screen/screen_target`
- Depends on:
	- "Annual number screened"
	- "Target population for screening programs"
- Used to compute:
	- "Annual number screened positive"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Screening yield

- Code name: `screen_yield`
- Units/format: probability
- Value restrictions: 0-1.0000
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `undx/screen_target`
- Depends on:
	- "Target population for screening programs"
	- "Undiagnosed"
- Used to compute:
	- "Annual number screened positive"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number screened positive

- Code name: `pos_screen`
- Value can be used for calibration
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Undiagnosed" to "Screened, not diagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `screen_cov*screen_target*screen_yield`
- Depends on:
	- "Target population for screening programs"
	- "Screening coverage shares"
	- "Screening yield"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number of new diagnoses

- Code name: `num_diag`
- Value can be used for calibration
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Screened, not diagnosed" to "Diagnosed, not treated"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number newly initiated onto treatment

- Code name: `num_initiate`
- Value can be used for calibration
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Diagnosed, not treated" to "Treated, not controlled"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Loss-to-follow-up rate

- Code name: `loss`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Treated, not controlled" to "Diagnosed, not treated"
	- "Controlled" to "Diagnosed, not treated"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Time after initiating treatment to achieve BP control (years)

- Code name: `cont_rate`
- Units/format: duration
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Treated, not controlled" to "Controlled"
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
	- "Controlled" to "Treated, not controlled"
- Default value: 0.16
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Death rate for those with untreated hypertension

- Code name: `death_hyp`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Undiagnosed" to "Dead (hypertension)"
	- "Screened, not diagnosed" to "Dead (hypertension)"
	- "Diagnosed, not treated" to "Dead (hypertension)"
- Default value: 0.025
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Background mortality rate

- Code name: `death_other`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "No hypertension" to "Dead (other)"
	- "Undiagnosed" to "Dead (other)"
	- "Screened, not diagnosed" to "Dead (other)"
	- "Diagnosed, not treated" to "Dead (other)"
	- "Treated, not controlled" to "Dead (other)"
	- "Controlled" to "Dead (other)"
- Default value: 0.015
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: Hypertension care cascade

- Description: <ENTER DESCRIPTION>
- Stages:
	- Prevalent
		- All people with condition
	- Screened
		- Screened people
	- Diagnosed
		- Diagnosed people
	- Treated
		- Currently treated
	- Controlled
		- Blood pressure controlled

