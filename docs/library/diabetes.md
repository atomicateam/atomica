# Diabetes

**Name**: Diabetes

**Description**: Framework for a diabetes model, including vital dynamics and new cases

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

### Compartment: Unaware & uncomplicated

- Code name: `unsc_uncomp`
- Value can be used for calibration
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Unaware & vascular damage

- Code name: `unsc_vd`
- Value can be used for calibration
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Screened & uncomplicated

- Code name: `sc_uncomp`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Screened & vascular damage

- Code name: `sc_vd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Diagnosed & uncomplicated

- Code name: `dx_uncomp`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Diagnosed & vascular damage

- Code name: `dx_vd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Successful treatment & uncomplicated

- Code name: `txs_uncomp`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Successful treatment & vascular damage

- Code name: `txs_vd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Treatment failure & uncomplicated

- Code name: `txf_uncomp`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Treatment failure & vascular damage

- Code name: `txf_vd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Dead (diabetes)

- Code name: `dead_dm`
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
	- Unaware & uncomplicated
	- Unaware & vascular damage
	- Screened & uncomplicated
	- Screened & vascular damage
	- Diagnosed & uncomplicated
	- Diagnosed & vascular damage
	- Successful treatment & uncomplicated
	- Successful treatment & vascular damage
	- Treatment failure & uncomplicated
	- Treatment failure & vascular damage
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: All people with T2DM

- Code name: `ch_all`
- Value can be used for calibration
- Includes:
	- Unaware & uncomplicated
	- Unaware & vascular damage
	- Screened & uncomplicated
	- Screened & vascular damage
	- Diagnosed & uncomplicated
	- Diagnosed & vascular damage
	- Successful treatment & uncomplicated
	- Successful treatment & vascular damage
	- Treatment failure & uncomplicated
	- Treatment failure & vascular damage
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People screened for T2DM

- Code name: `ch_screened`
- Value can be used for calibration
- Includes:
	- Screened & uncomplicated
	- Screened & vascular damage
	- Diagnosed & uncomplicated
	- Diagnosed & vascular damage
	- Successful treatment & uncomplicated
	- Successful treatment & vascular damage
	- Treatment failure & uncomplicated
	- Treatment failure & vascular damage
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People diagnosed with T2DM

- Code name: `ch_diag`
- Value can be used for calibration
- Includes:
	- Diagnosed & uncomplicated
	- Diagnosed & vascular damage
	- Successful treatment & uncomplicated
	- Successful treatment & vascular damage
	- Treatment failure & uncomplicated
	- Treatment failure & vascular damage
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People treated for T2DM

- Code name: `ch_tx`
- Value can be used for calibration
- Includes:
	- Successful treatment & uncomplicated
	- Successful treatment & vascular damage
	- Treatment failure & uncomplicated
	- Treatment failure & vascular damage
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: People with HbA1c control

- Code name: `ch_succ`
- Value can be used for calibration
- Includes:
	- Successful treatment & uncomplicated
	- Successful treatment & vascular damage
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion screened for T2DM

- Code name: `ch_propscreened`
- Includes:
	- People screened for T2DM
- Denominator: All people with T2DM
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion diagnosed with T2DM

- Code name: `ch_propdiag`
- Includes:
	- People diagnosed with T2DM
- Denominator: All people with T2DM
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion treated for T2DM

- Code name: `ch_proptx`
- Includes:
	- People treated for T2DM
- Denominator: All people with T2DM
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion with HbA1c control

- Code name: `ch_propsucc`
- Includes:
	- People with HbA1c control
- Denominator: All people with T2DM
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Parameters

### Parameter: Annual number of births

- Code name: `birth_rate`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Source" to "Susceptible"
- Default value: 15828
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Estimated number of new diabetes cases annually

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
	- "Susceptible" to "Unaware & uncomplicated"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_acq/max(sus,num_acq)`
- Depends on:
	- "Estimated number of new diabetes cases annually"
	- "Susceptible"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Time before progression to vascular damage

- Code name: `prog_rate`
- Units/format: duration
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Unaware & uncomplicated" to "Unaware & vascular damage"
	- "Screened & uncomplicated" to "Screened & vascular damage"
	- "Diagnosed & uncomplicated" to "Diagnosed & vascular damage"
	- "Treatment failure & uncomplicated" to "Treatment failure & vascular damage"
- Default value: 1
- Appears in the databook

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

### Parameter: Yield among those screened

- Code name: `screen_yield`
- Units/format: probability
- Value restrictions: 0-1.0000
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `(unsc_uncomp+unsc_vd)/(unsc_uncomp+unsc_vd+sus)`
- Depends on:
	- "Unaware & uncomplicated"
	- "Susceptible"
	- "Unaware & vascular damage"
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
	- "Yield among those screened"
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
	- "Unaware & uncomplicated" to "Screened & uncomplicated"
	- "Unaware & vascular damage" to "Screened & vascular damage"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `pos_screen/max(unsc_uncomp+unsc_vd,pos_screen)`
- Depends on:
	- "Unaware & uncomplicated"
	- "Annual number screened positive"
	- "Unaware & vascular damage"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Annual number of new diagnoses

- Code name: `num_diag`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "Diagnosis sensitivity"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Diagnosis sensitivity

- Code name: `diag`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Screened & uncomplicated" to "Diagnosed & uncomplicated"
	- "Screened & vascular damage" to "Diagnosed & vascular damage"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_diag/max(sc_uncomp+sc_vd,num_diag)`
- Depends on:
	- "Screened & vascular damage"
	- "Annual number of new diagnoses"
	- "Screened & uncomplicated"

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
	- "Diagnosed & uncomplicated" to "Successful treatment & uncomplicated"
	- "Diagnosed & vascular damage" to "Successful treatment & vascular damage"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `num_initiate/max(dx_uncomp+dx_vd,num_initiate)`
- Depends on:
	- "Diagnosed & uncomplicated"
	- "Diagnosed & vascular damage"
	- "Annual number newly initiated onto treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Treatment failure rate

- Code name: `treat_fail`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Successful treatment & uncomplicated" to "Treatment failure & uncomplicated"
	- "Successful treatment & vascular damage" to "Treatment failure & vascular damage"
- Default value: 0.5
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Proportion of those experiencing treatment failure who are offered support

- Code name: `treat_suc`
- Value can be used for calibration
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Treatment failure & uncomplicated" to "Successful treatment & uncomplicated"
	- "Treatment failure & vascular damage" to "Successful treatment & vascular damage"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Death rate for diabetes with vascular damage

- Code name: `death_vd`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Unaware & vascular damage" to "Dead (diabetes)"
	- "Screened & vascular damage" to "Dead (diabetes)"
	- "Diagnosed & vascular damage" to "Dead (diabetes)"
	- "Successful treatment & vascular damage" to "Dead (diabetes)"
	- "Treatment failure & vascular damage" to "Dead (diabetes)"
- Default value: 0.025
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Background mortality rate

- Code name: `death_other`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Susceptible" to "Dead (other)"
	- "Unaware & uncomplicated" to "Dead (other)"
	- "Unaware & vascular damage" to "Dead (other)"
	- "Screened & uncomplicated" to "Dead (other)"
	- "Screened & vascular damage" to "Dead (other)"
	- "Diagnosed & uncomplicated" to "Dead (other)"
	- "Diagnosed & vascular damage" to "Dead (other)"
	- "Successful treatment & uncomplicated" to "Dead (other)"
	- "Successful treatment & vascular damage" to "Dead (other)"
	- "Treatment failure & uncomplicated" to "Dead (other)"
	- "Treatment failure & vascular damage" to "Dead (other)"
- Default value: 0.015
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: Diabetes care cascade

- Description: <ENTER DESCRIPTION>
- Stages:
	- All people with T2DM
		- Unaware & uncomplicated
		- Unaware & vascular damage
		- Screened & uncomplicated
		- Screened & vascular damage
		- Diagnosed & uncomplicated
		- Diagnosed & vascular damage
		- Successful treatment & uncomplicated
		- Successful treatment & vascular damage
		- Treatment failure & uncomplicated
		- Treatment failure & vascular damage
	- Screened
		- Screened & uncomplicated
		- Screened & vascular damage
		- Diagnosed & uncomplicated
		- Diagnosed & vascular damage
		- Successful treatment & uncomplicated
		- Successful treatment & vascular damage
		- Treatment failure & uncomplicated
		- Treatment failure & vascular damage
	- Diagnosed
		- Diagnosed & uncomplicated
		- Diagnosed & vascular damage
		- Successful treatment & uncomplicated
		- Successful treatment & vascular damage
		- Treatment failure & uncomplicated
		- Treatment failure & vascular damage
	- Treated
		- Successful treatment & uncomplicated
		- Successful treatment & vascular damage
		- Treatment failure & uncomplicated
		- Treatment failure & vascular damage
	- HbA1c control
		- Successful treatment & uncomplicated
		- Successful treatment & vascular damage

### Cascade: Diabetes care cascade - vascular damage

- Description: <ENTER DESCRIPTION>
- Stages:
	- All people
		- Unaware & vascular damage
		- Screened & vascular damage
		- Diagnosed & vascular damage
		- Successful treatment & vascular damage
		- Treatment failure & vascular damage
	- Screened
		- Screened & vascular damage
		- Diagnosed & vascular damage
		- Successful treatment & vascular damage
		- Treatment failure & vascular damage
	- Diagnosed
		- Diagnosed & vascular damage
		- Successful treatment & vascular damage
		- Treatment failure & vascular damage
	- Treated
		- Successful treatment & vascular damage
		- Treatment failure & vascular damage
	- HbA1c control
		- Successful treatment & vascular damage

### Cascade: Diabetes care cascade - uncomplicated cases

- Description: <ENTER DESCRIPTION>
- Stages:
	- All people
		- Unaware & uncomplicated
		- Screened & uncomplicated
		- Diagnosed & uncomplicated
		- Successful treatment & uncomplicated
		- Treatment failure & uncomplicated
	- Screened
		- Screened & uncomplicated
		- Diagnosed & uncomplicated
		- Successful treatment & uncomplicated
		- Treatment failure & uncomplicated
	- Diagnosed
		- Diagnosed & uncomplicated
		- Successful treatment & uncomplicated
		- Treatment failure & uncomplicated
	- Treated
		- Successful treatment & uncomplicated
		- Treatment failure & uncomplicated
	- HbA1c control
		- Successful treatment & uncomplicated

