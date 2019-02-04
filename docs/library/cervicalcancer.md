# Cervical cancer

**Name**: Cervical cancer

**Description**: Framework for a 4-stage cervical cancer cascade model, with vital dynamics and new cases

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

### Compartment: Without cervical cancer

- Code name: `sus`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Undiagnosed

- Code name: `undx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Screened

- Code name: `scr`
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

### Compartment: Dead (other)

- Code name: `dead`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Dead (cervical cancer)

- Code name: `dead_cc`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: Population size

- Code name: `alive`
- Value can be used for calibration
- Includes:
	- Without cervical cancer
	- Undiagnosed
	- Screened
	- Diagnosed
	- Treated
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of women with cervical cancer

- Code name: `all_people`
- Value can be used for calibration
- Includes:
	- Undiagnosed
	- Screened
	- Diagnosed
	- Treated
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of women with cervical cancer who have ever been screened

- Code name: `all_screened`
- Value can be used for calibration
- Includes:
	- Screened
	- Diagnosed
	- Treated
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of women with cervical cancer who have ever been diagnosed

- Code name: `all_dx`
- Value can be used for calibration
- Includes:
	- Diagnosed
	- Treated
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of women being treated for cervical cancer

- Code name: `all_tx`
- Value can be used for calibration
- Includes:
	- Treated
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
	- "Source" to "Without cervical cancer"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Estimated number of new cervical cancer cases annually

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
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Without cervical cancer" to "Undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_acq/max(sus,num_acq)`
- Depends on:
	- "Estimated number of new cervical cancer cases annually"
	- "Without cervical cancer"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number screened

- Code name: `num_screen`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
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
- This parameter's value is computed by a function: `undx/(undx+sus)`
- Depends on:
	- "Without cervical cancer"
	- "Undiagnosed"
- Used to compute:
	- "Annual number screened positive"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number screened positive

- Code name: `pos_screen`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_screen*screen_yield`
- Depends on:
	- "Annual number screened"
	- "Screening yield"
- Used to compute:
	- "Screening sensitivity"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Screening sensitivity

- Code name: `screen`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Undiagnosed" to "Screened"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `pos_screen/max(undx,pos_screen)`
- Depends on:
	- "Annual number screened positive"
	- "Undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number of new diagnoses

- Code name: `num_diag`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Probability of a positive confirmation following screening"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Probability of a positive confirmation following screening

- Code name: `diag`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Screened" to "Diagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_diag/max(scr,num_diag)`
- Depends on:
	- "Screened"
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

### Parameter: Mortality rate

- Code name: `death`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Without cervical cancer" to "Dead (other)"
	- "Undiagnosed" to "Dead (other)"
	- "Screened" to "Dead (other)"
	- "Diagnosed" to "Dead (other)"
	- "Treated" to "Dead (other)"
- Default value: 0.015
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Mortality rate for those with untreated cervical cancer

- Code name: `death_cc`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Undiagnosed" to "Dead (cervical cancer)"
	- "Screened" to "Dead (cervical cancer)"
	- "Diagnosed" to "Dead (cervical cancer)"
- Default value: 0.05
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: Cervical cancer cascade

- Description: <ENTER DESCRIPTION>
- Stages:
	- All women with cervical cancer
		- Estimated number of women with cervical cancer
	- Ever screened
		- Estimated number of women with cervical cancer who have ever been screened
	- Ever diagnosed
		- Estimated number of women with cervical cancer who have ever been diagnosed
	- Currently treated
		- Estimated number of women being treated for cervical cancer

