# SIR model

**Name**: SIR

**Description**: The SIR model

## Contents
- [Compartments](#compartments)
- [Characteristics](#characteristics)
- [Parameters](#parameters)
- [Interactions](#interactions)

- [Cascades](#cascades)

## Compartments

### Compartment: Susceptible

- Code name: `sus`
- Value can be used for calibration
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Infected

- Code name: `inf`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Recovered

- Code name: `rec`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Dead

- Code name: `dead`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: Total number of entities

- Code name: `ch_all`
- Value can be used for calibration
- Includes:
	- Susceptible
	- Infected
	- Recovered
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Prevalence

- Code name: `ch_prev`
- Value can be used for calibration
- Includes:
	- Infected
- Denominator: Total number of entities
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Number ever infected

- Code name: `ch_infrec`
- Includes:
	- Infected
	- Recovered
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Number infected or susceptible

- Code name: `ch_infsus`
- Includes:
	- Infected
	- Susceptible
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Number not at risk of death

- Code name: `ch_newinf`
- Includes:
	- Susceptible
	- Recovered
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion ever infected

- Code name: `ch_propinfrec`
- Includes:
	- Number ever infected
- Denominator: Total number of entities
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion infected or susceptible

- Code name: `ch_propinfsus`
- Includes:
	- Number infected or susceptible
- Denominator: Total number of entities
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Proportion not at risk of death

- Code name: `ch_propnewinf`
- Includes:
	- Number not at risk of death
- Denominator: Total number of entities
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Parameters

### Parameter: Transmission probability per contact

- Code name: `transpercontact`
- Value can be used for calibration
- Units/format: probability
- Default value: 0.0008
- Appears in the databook
- Used to compute:
	- "Force of infection"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number of contacts annually

- Code name: `contacts`
- Value can be used for calibration
- Units/format: None
- Default value: 80
- Appears in the databook
- Used to compute:
	- "Force of infection"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Average duration of infections (years)

- Code name: `recrate`
- Value can be used for calibration
- Units/format: duration
- Contributes to transitions from:
	- "Infected" to "Recovered"
- Default value: 0.5
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Death rate for infected people

- Code name: `infdeath`
- Value can be used for calibration
- Units/format: probability
- Contributes to transitions from:
	- "Infected" to "Dead"
- Default value: 0.016
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Death rate for susceptible people

- Code name: `susdeath`
- Value can be used for calibration
- Units/format: probability
- Contributes to transitions from:
	- "Susceptible" to "Dead"
	- "Infected" to "Dead"
	- "Recovered" to "Dead"
- Default value: 0.008
- Appears in the databook
- Used to compute:
	- "Force of infection"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Force of infection

- Code name: `foi`
- Units/format: probability
- Contributes to transitions from:
	- "Susceptible" to "Infected"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `(1 - (1-ch_prev*transpercontact)**floor(contacts)*(1-ch_prev*transpercontact*(contacts-floor(contacts))))*(1-susdeath)`
- Depends on:
	- "Prevalence"
	- "Transmission probability per contact"
	- "Death rate for susceptible people"
	- "Number of contacts annually"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

## Cascades

### Cascade: main

- Description: <ENTER DESCRIPTION>
- Stages:
	- Total number of entities
		- Total number of entities
	- Number ever infected
		- Infected
		- Recovered
	- Recovered
		- Recovered

