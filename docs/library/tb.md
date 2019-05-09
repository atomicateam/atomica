# TB full model

**Name**: TB

**Description**: A full TB model including dynamics

## Contents
- [Compartments](#compartments)
- [Characteristics](#characteristics)
- [Parameters](#parameters)
- [Interactions](#interactions)

- [Plots](#plots)

- [Cascades](#cascades)

## Compartments

### Compartment: Initialization population size

- Code name: `initj`
- Is junction
- Appears in the databook
- Databook values will be used for model initialization

- Description: <ENTER DESCRIPTION>
- Data entry guidance: Enter the total number of people in each population

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

### Compartment: Early latent untreated (diagnosable)

- Code name: `lteu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Early latent on treatment

- Code name: `ltet`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: Latent early treatment outcome

- Code name: `ltetoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Late latent untreated (diagnosable)

- Code name: `ltlu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Late latent on treatment

- Code name: `ltlt`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: Latent late treatment outcome

- Code name: `ltltoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Susceptible (diagnosis restricted)

- Code name: `susx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Early latent untreated (diagnosis restricted)

- Code name: `ltex`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Late latent untreated (diagnosis restricted)

- Code name: `ltlx`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: Smear disaggregator for new active

- Code name: `acj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: Strain disaggregator for new smear positive

- Code name: `spj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-DS undiagnosed

- Code name: `spdu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-DS diagnosed but not on treatment

- Code name: `spdd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-DS on treatment

- Code name: `spdt`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: SP-DS treatment outcome

- Code name: `spdtoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-MDR undiagnosed

- Code name: `spmu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-MDR diagnosed but not on treatment

- Code name: `spmd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-MDR on treatment

- Code name: `spmt`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: SP-MDR treatment outcome

- Code name: `spmtoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-XDR undiagnosed

- Code name: `spxu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-XDR diagnosed but not on treatment

- Code name: `spxd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SP-XDR on treatment

- Code name: `spxt`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: SP-XDR treatment outcome

- Code name: `spxtoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: Strain disaggregator for new smear negative

- Code name: `snj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-DS undiagnosed

- Code name: `sndu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-DS diagnosed but not on treatment

- Code name: `sndd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-DS on treatment

- Code name: `sndt`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: SN-DS treatment outcome

- Code name: `sndtoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-MDR undiagnosed

- Code name: `snmu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-MDR diagnosed but not on treatment

- Code name: `snmd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-MDR on treatment

- Code name: `snmt`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: SN-MDR treatment outcome

- Code name: `snmtoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-XDR undiagnosed

- Code name: `snxu`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-XDR diagnosed but not on treatment

- Code name: `snxd`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: SN-XDR on treatment

- Code name: `snxt`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: SN-XDR treatment outcome

- Code name: `snxtoj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Completed treatment (active)

- Code name: `acr`
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Source: Origin of births

- Code name: `bir`
- Is source
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Source: Origin of immigration

- Code name: `immi`
- Is source
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Junction: Infection status of immigrants

- Code name: `imj`
- Is junction
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Sink: Cumulative TB deaths over simulation

- Code name: `ddis`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Sink: Cumulative non-TB deaths over simulation

- Code name: `doth`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Compartment: Sink: Cumulative emigration over simulation

- Code name: `emi`
- Is sink
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Characteristics

### Characteristic: Latent TB infections on treatment

- Code name: `ltt_inf`
- Includes:
	- Early latent on treatment
	- Late latent on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected diagnosis restricted latent infections

- Code name: `ltx_inf`
- Includes:
	- Early latent untreated (diagnosis restricted)
	- Late latent untreated (diagnosis restricted)
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected undiagnosed latent infections

- Code name: `lt_undiag`
- Includes:
	- Early latent untreated (diagnosable)
	- Late latent untreated (diagnosable)
	- Early latent untreated (diagnosis restricted)
	- Late latent untreated (diagnosis restricted)
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected early latent infections

- Code name: `lte_inf`
- Includes:
	- Early latent untreated (diagnosable)
	- Early latent on treatment
	- Early latent untreated (diagnosis restricted)
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected late latent infections

- Code name: `ltl_inf`
- Includes:
	- Late latent untreated (diagnosable)
	- Late latent on treatment
	- Late latent untreated (diagnosis restricted)
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected latent infections

- Code name: `lt_inf`
- Includes:
	- Suspected early latent infections
	- Suspected late latent infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Known SP-DS infections

- Code name: `spdk_inf`
- Includes:
	- SP-DS diagnosed but not on treatment
	- SP-DS on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Known SP-MDR infections

- Code name: `spmk_inf`
- Includes:
	- SP-MDR diagnosed but not on treatment
	- SP-MDR on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Known SP-XDR infections

- Code name: `spxk_inf`
- Includes:
	- SP-XDR diagnosed but not on treatment
	- SP-XDR on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Known SN-DS infections

- Code name: `sndk_inf`
- Includes:
	- SN-DS diagnosed but not on treatment
	- SN-DS on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Known SN-MDR infections

- Code name: `snmk_inf`
- Includes:
	- SN-MDR diagnosed but not on treatment
	- SN-MDR on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Known SN-XDR infections

- Code name: `snxk_inf`
- Includes:
	- SN-XDR diagnosed but not on treatment
	- SN-XDR on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Known active TB infections

- Code name: `known_inf`
- Includes:
	- Known SP-DS infections
	- Known SP-MDR infections
	- Known SP-XDR infections
	- Known SN-DS infections
	- Known SN-MDR infections
	- Known SN-XDR infections
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Diagnosed number of living people that developed active TB

- Code name: `known_cascade`
- Includes:
	- Known active TB infections
	- Completed treatment (active)
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP-DS infections

- Code name: `spd_inf`
- Includes:
	- SP-DS undiagnosed
	- Known SP-DS infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP-MD infections

- Code name: `spm_inf`
- Includes:
	- SP-MDR undiagnosed
	- Known SP-MDR infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP-XDR infections

- Code name: `spx_inf`
- Includes:
	- SP-XDR undiagnosed
	- Known SP-XDR infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN-DS infections

- Code name: `snd_inf`
- Includes:
	- SN-DS undiagnosed
	- Known SN-DS infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN-MDR infections

- Code name: `snm_inf`
- Includes:
	- SN-MDR undiagnosed
	- Known SN-MDR infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN-XDR infections

- Code name: `snx_inf`
- Includes:
	- SN-XDR undiagnosed
	- Known SN-XDR infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP infections

- Code name: `sp_inf`
- Includes:
	- Junction: Strain disaggregator for new smear positive
	- Suspected SP-DS infections
	- Suspected SP-MD infections
	- Suspected SP-XDR infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN infections

- Code name: `sn_inf`
- Includes:
	- Junction: Strain disaggregator for new smear negative
	- Suspected SN-DS infections
	- Suspected SN-MDR infections
	- Suspected SN-XDR infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of people with DS TB

- Code name: `ds_inf`
- Includes:
	- Suspected SP-DS infections
	- Suspected SN-DS infections
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of people with MDR TB

- Code name: `mdr_inf`
- Includes:
	- Suspected SP-MD infections
	- Suspected SN-MDR infections
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of people with XDR TB

- Code name: `xdr_inf`
- Includes:
	- Suspected SP-XDR infections
	- Suspected SN-XDR infections
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of people with DR TB

- Code name: `dr_inf`
- Includes:
	- Estimated number of people with MDR TB
	- Estimated number of people with XDR TB
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of people with active TB

- Code name: `ac_inf`
- Includes:
	- Junction: Smear disaggregator for new active
	- Suspected SP infections
	- Suspected SN infections
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Estimated number of living people that developed active TB

- Code name: `ac_cascade`
- Includes:
	- Estimated number of people with active TB
	- Completed treatment (active)
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Population size

- Code name: `alive`
- Includes:
	- Initialization population size
	- Susceptible
	- Vaccinated
	- Susceptible (diagnosis restricted)
	- Completed treatment (active)
	- Suspected latent infections
	- Estimated number of people with active TB
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SP-DS infections

- Code name: `spd_infx`
- Includes:
	- SP-DS undiagnosed
	- SP-DS diagnosed but not on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SP-MDR infections

- Code name: `spm_infx`
- Includes:
	- SP-MDR undiagnosed
	- SP-MDR diagnosed but not on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SP-XDR infections

- Code name: `spx_infx`
- Includes:
	- SP-XDR undiagnosed
	- SP-XDR diagnosed but not on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SN-DS infections

- Code name: `snd_infx`
- Includes:
	- SN-DS undiagnosed
	- SN-DS diagnosed but not on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SN-MDR infections

- Code name: `snm_infx`
- Includes:
	- SN-MDR undiagnosed
	- SN-MDR diagnosed but not on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SN-XDR infections

- Code name: `snx_infx`
- Includes:
	- SN-XDR undiagnosed
	- SN-XDR diagnosed but not on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SP-DS prevalence

- Code name: `spd_prevx`
- Includes:
	- Suspected untreated SP-DS infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SP-MDR prevalence

- Code name: `spm_prevx`
- Includes:
	- Suspected untreated SP-MDR infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SP-XDR prevalence

- Code name: `spx_prevx`
- Includes:
	- Suspected untreated SP-XDR infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SN-DS prevalence

- Code name: `snd_prevx`
- Includes:
	- Suspected untreated SN-DS infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SN-MDR prevalence

- Code name: `snm_prevx`
- Includes:
	- Suspected untreated SN-MDR infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected untreated SN-XDR prevalence

- Code name: `snx_prevx`
- Includes:
	- Suspected untreated SN-XDR infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected LTBI prevalence

- Code name: `lt_prev`
- Includes:
	- Suspected latent infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP-DS prevalence

- Code name: `spd_prev`
- Includes:
	- Suspected SP-DS infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP-MDR prevalence

- Code name: `spm_prev`
- Includes:
	- Suspected SP-MD infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP-XDR prevalence

- Code name: `spx_prev`
- Includes:
	- Suspected SP-XDR infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN-DS prevalence

- Code name: `snd_prev`
- Includes:
	- Suspected SN-DS infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN-MDR prevalence

- Code name: `snm_prev`
- Includes:
	- Suspected SN-MDR infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN-XDR prevalence

- Code name: `snx_prev`
- Includes:
	- Suspected SN-XDR infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SP prevalence

- Code name: `sp_prev`
- Includes:
	- Suspected SP infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected SN prevalence

- Code name: `sn_prev`
- Includes:
	- Suspected SN infections
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected DS prevalence

- Code name: `ds_prev`
- Includes:
	- Estimated number of people with DS TB
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected DR prevalence

- Code name: `dr_prev`
- Includes:
	- Estimated number of people with DR TB
- Denominator: Population size
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected MDR prevalence

- Code name: `mdr_prev`
- Includes:
	- Estimated number of people with MDR TB
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected XDR prevalence

- Code name: `xdr_prev`
- Includes:
	- Estimated number of people with XDR TB
- Denominator: Population size
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected active TB prevalence

- Code name: `ac_prev`
- Includes:
	- Estimated number of people with active TB
- Denominator: Population size
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected undiagnosed DS infections

- Code name: `num_undiag_ds`
- Includes:
	- SP-DS undiagnosed
	- SN-DS undiagnosed
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected undiagnosed MDR infections

- Code name: `num_undiag_mdr`
- Includes:
	- SP-MDR undiagnosed
	- SN-MDR undiagnosed
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Suspected undiagnosed XDR infections

- Code name: `num_undiag_xdr`
- Includes:
	- SP-XDR undiagnosed
	- SN-XDR undiagnosed
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Diagnosed DS infections

- Code name: `num_diag_ds`
- Includes:
	- SP-DS diagnosed but not on treatment
	- SP-DS on treatment
	- SN-DS diagnosed but not on treatment
	- SN-DS on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Diagnosed MDR infections

- Code name: `num_diag_mdr`
- Includes:
	- SP-MDR diagnosed but not on treatment
	- SP-MDR on treatment
	- SN-MDR diagnosed but not on treatment
	- SN-MDR on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Diagnosed XDR infections

- Code name: `num_diag_xdr`
- Includes:
	- SP-XDR diagnosed but not on treatment
	- SP-XDR on treatment
	- SN-XDR diagnosed but not on treatment
	- SN-XDR on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: DS cases on treatment

- Code name: `num_treat_ds`
- Includes:
	- SP-DS on treatment
	- SN-DS on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: MDR cases on treatment

- Code name: `num_treat_mdr`
- Includes:
	- SP-MDR on treatment
	- SN-MDR on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: XDR cases on treatment

- Code name: `num_treat_xdr`
- Includes:
	- SP-XDR on treatment
	- SN-XDR on treatment
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Active TB cases on treatment

- Code name: `num_treat`
- Includes:
	- DS cases on treatment
	- MDR cases on treatment
	- XDR cases on treatment
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Number of living people that have recovered from active TB in the previous 2 years

- Code name: `treat_cascade`
- Includes:
	- Completed treatment (active)
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Diagnosis sufficiency (known versus suspected infections)

- Code name: `diag_suff`
- Includes:
	- Known active TB infections
- Denominator: Estimated number of people with active TB
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Characteristic: Treatment sufficiency (on-treatment versus known infections)

- Code name: `treat_suff`
- Includes:
	- Active TB cases on treatment
- Denominator: Known active TB infections
- Does not appear in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Parameters

### Parameter: Initialization proportion of the population with active TB

- Code name: `aci_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: Vaccinated"
	- "Initialization proportion: SP-MDR diagnosed but not on treatment"
	- "Initialization proportion: Susceptible (diagnosis restricted)"
	- "Initialization proportion: SP-MDR on treatment"
	- "Initialization proportion: SN-MDR on treatment"
	- "Initialization proportion: SP-MDR undiagnosed"
	- "Initialization proportion: SP-DS on treatment"
	- "Initialization proportion: SN-DS diagnosed but not on treatment"
	- "Initialization proportion: Susceptible"
	- "Initialization proportion: SN-XDR diagnosed but not on treatment"
	- "Initialization proportion: SN-DS on treatment"
	- "Initialization proportion: SN-MDR diagnosed but not on treatment"
	- "Initialization proportion: SP-XDR on treatment"
	- "Initialization proportion: SP-XDR diagnosed but not on treatment"
	- "Initialization proportion: SN-MDR undiagnosed"
	- "Initialization proportion: SP-DS diagnosed but not on treatment"
	- "Initialization proportion: SP-DS undiagnosed"
	- "Initialization proportion: SN-XDR on treatment"
	- "Initialization proportion: SN-XDR undiagnosed"
	- "Initialization proportion: SP-XDR undiagnosed"
	- "Initialization proportion: SN-DS undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion of the population with latent TB

- Code name: `lti_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: Late latent untreated (diagnosable)"
	- "Initialization proportion: Late latent untreated (diagnosis restricted)"
	- "Initialization proportion: Vaccinated"
	- "Initialization proportion: Late latent on treatment"
	- "Initialization proportion: Susceptible"
	- "Initialization proportion: Susceptible (diagnosis restricted)"
	- "Initialization proportion: Early latent untreated (diagnosis restricted)"
	- "Initialization proportion: Early latent untreated (diagnosable)"
	- "Initialization proportion: Early latent on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion of latent TB cases that are early latent

- Code name: `ltei_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.1
- Appears in the databook
- Used to compute:
	- "Initialization proportion: Late latent untreated (diagnosable)"
	- "Initialization proportion: Late latent untreated (diagnosis restricted)"
	- "Initialization proportion: Late latent on treatment"
	- "Early latent proportion of new immigrants"
	- "Initialization proportion: Early latent untreated (diagnosis restricted)"
	- "Initialization proportion: Early latent untreated (diagnosable)"
	- "Initialization proportion: Early latent on treatment"
	- "Late latent proportion of new immigrants"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion of latent TB cases that are on treatment

- Code name: `lteti_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Initialization proportion: Late latent untreated (diagnosable)"
	- "Initialization proportion: Late latent untreated (diagnosis restricted)"
	- "Initialization proportion: Late latent on treatment"
	- "Initialization proportion: Early latent untreated (diagnosis restricted)"
	- "Initialization proportion: Early latent untreated (diagnosable)"
	- "Initialization proportion: Early latent on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion of active TB cases that are diagnosed

- Code name: `acdi_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SN-DS undiagnosed"
	- "Initialization proportion: SP-DS on treatment"
	- "Initialization proportion: SN-DS diagnosed but not on treatment"
	- "Initialization proportion: SP-XDR diagnosed but not on treatment"
	- "Initialization proportion: SP-MDR diagnosed but not on treatment"
	- "Initialization proportion: SN-XDR diagnosed but not on treatment"
	- "Initialization proportion: SN-XDR on treatment"
	- "Initialization proportion: SP-MDR undiagnosed"
	- "Initialization proportion: SN-MDR on treatment"
	- "Initialization proportion: SN-XDR undiagnosed"
	- "Initialization proportion: SN-DS on treatment"
	- "Initialization proportion: SP-MDR on treatment"
	- "Initialization proportion: SN-MDR undiagnosed"
	- "Initialization proportion: SP-XDR undiagnosed"
	- "Initialization proportion: SP-XDR on treatment"
	- "Initialization proportion: SN-MDR diagnosed but not on treatment"
	- "Initialization proportion: SP-DS diagnosed but not on treatment"
	- "Initialization proportion: SP-DS undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion of diagnosed TB cases that are on treatment

- Code name: `dti_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SP-DS on treatment"
	- "Initialization proportion: SN-DS diagnosed but not on treatment"
	- "Initialization proportion: SP-XDR diagnosed but not on treatment"
	- "Initialization proportion: SP-MDR diagnosed but not on treatment"
	- "Initialization proportion: SN-XDR diagnosed but not on treatment"
	- "Initialization proportion: SN-XDR on treatment"
	- "Initialization proportion: SN-DS on treatment"
	- "Initialization proportion: SP-MDR on treatment"
	- "Initialization proportion: SN-MDR diagnosed but not on treatment"
	- "Initialization proportion: SP-XDR on treatment"
	- "Initialization proportion: SN-MDR on treatment"
	- "Initialization proportion: SP-DS diagnosed but not on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion of the population that have previously been vaccinated

- Code name: `vaci_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Initialization proportion: Vaccinated"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion of the population that have previously been infected with TB

- Code name: `und_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Initialization proportion: Late latent untreated (diagnosable)"
	- "Initialization proportion: Late latent untreated (diagnosis restricted)"
	- "Initialization proportion: Susceptible"
	- "Initialization proportion: Susceptible (diagnosis restricted)"
	- "Initialization proportion: Early latent untreated (diagnosis restricted)"
	- "Initialization proportion: Early latent untreated (diagnosable)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New active infections: proportion of population that are SP

- Code name: `p_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Smear disaggregator for new active" to "Junction: Strain disaggregator for new smear positive"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SP-DS on treatment"
	- "Initialization proportion: SP-XDR diagnosed but not on treatment"
	- "Initialization proportion: SP-MDR diagnosed but not on treatment"
	- "Initialization proportion: SP-MDR undiagnosed"
	- "Initialization proportion: SP-MDR on treatment"
	- "Initialization proportion: SP-XDR undiagnosed"
	- "Initialization proportion: SP-XDR on treatment"
	- "Initialization proportion: SP-DS diagnosed but not on treatment"
	- "Initialization proportion: SP-DS undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New active infections: proportion of population that are SN

- Code name: `n_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Smear disaggregator for new active" to "Junction: Strain disaggregator for new smear negative"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SN-DS diagnosed but not on treatment"
	- "Initialization proportion: SN-XDR diagnosed but not on treatment"
	- "Initialization proportion: SN-XDR on treatment"
	- "Initialization proportion: SN-XDR undiagnosed"
	- "Initialization proportion: SN-DS on treatment"
	- "Initialization proportion: SN-MDR undiagnosed"
	- "Initialization proportion: SN-MDR diagnosed but not on treatment"
	- "Initialization proportion: SN-MDR on treatment"
	- "Initialization proportion: SN-DS undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New SP infections: proportion of population that are SP-DS

- Code name: `pd_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Strain disaggregator for new smear positive" to "SP-DS undiagnosed"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SP-DS on treatment"
	- "Initialization proportion: SP-DS diagnosed but not on treatment"
	- "Initialization proportion: SP-DS undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New SP infections: proportion of population that are SP-MDR

- Code name: `pm_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Strain disaggregator for new smear positive" to "SP-MDR undiagnosed"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SP-MDR diagnosed but not on treatment"
	- "Initialization proportion: SP-MDR undiagnosed"
	- "Initialization proportion: SP-MDR on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New SP infections: proportion of population that are SP-XDR

- Code name: `px_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Strain disaggregator for new smear positive" to "SP-XDR undiagnosed"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SP-XDR undiagnosed"
	- "Initialization proportion: SP-XDR on treatment"
	- "Initialization proportion: SP-XDR diagnosed but not on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New SN infections: proportion of population that are SN-DS

- Code name: `nd_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Strain disaggregator for new smear negative" to "SN-DS undiagnosed"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SN-DS on treatment"
	- "Initialization proportion: SN-DS diagnosed but not on treatment"
	- "Initialization proportion: SN-DS undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New SN infections: proportion of population that are SN-MDR

- Code name: `nm_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Strain disaggregator for new smear negative" to "SN-MDR undiagnosed"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SN-MDR on treatment"
	- "Initialization proportion: SN-MDR diagnosed but not on treatment"
	- "Initialization proportion: SN-MDR undiagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: New SN infections: proportion of population that are SN-XDR

- Code name: `nx_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Strain disaggregator for new smear negative" to "SN-XDR undiagnosed"
- Default value: None
- Appears in the databook
- Used to compute:
	- "Initialization proportion: SN-XDR diagnosed but not on treatment"
	- "Initialization proportion: SN-XDR undiagnosed"
	- "Initialization proportion: SN-XDR on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Infection vulnerability factor (relative population susceptibility)

- Code name: `inf_sus`
- Units/format: None
- Value restrictions: At least 0
- Default value: 1
- Appears in the databook
- Used to compute:
	- "Reinfection rate (susceptible to diagnosis restricted for diagnosis restricted)"
	- "Infection rate (susceptible to diagnosable latent)"
	- "Infection rate (vaccinated to diagnosis restricted latent)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Infection vulnerability factor (vaccinated versus susceptible)

- Code name: `vac_fac`
- Units/format: None
- Value restrictions: At least 0
- Default value: 0.5
- Appears in the databook
- Used to compute:
	- "Infection rate (vaccinated to diagnosis restricted latent)"
	- "Initialization proportion: Vaccinated"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Infection vulnerability factor (recovered versus susceptible)

- Code name: `lat_fac`
- Units/format: None
- Value restrictions: At least 0
- Default value: 0.5
- Appears in the databook
- Used to compute:
	- "Reinfection rate (susceptible to diagnosis restricted for diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS infectiousness

- Code name: `spd_infxness`
- Units/format: None
- Value restrictions: At least 0
- Default value: 1
- Appears in the databook
- Used to compute:
	- "SN-MDR infectiousness"
	- "SN-XDR infectiousness"
	- "SN-DS infectiousness"
	- "SP-XDR infectiousness"
	- "SP-MDR infectiousness"
	- "Force of infection from SP prevalence"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Relative infectiousness (SN versus SP)

- Code name: `sn_fac`
- Units/format: None
- Value restrictions: At least 0
- Default value: 0.22
- Appears in the databook
- Used to compute:
	- "SN-XDR infectiousness"
	- "SN-MDR infectiousness"
	- "SN-DS infectiousness"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Relative infectiousness (MDR versus DS)

- Code name: `mdr_fac`
- Units/format: None
- Value restrictions: At least 0
- Default value: 1
- Appears in the databook
- Used to compute:
	- "SP-MDR infectiousness"
	- "SN-MDR infectiousness"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Relative infectiousness (XDR versus DS)

- Code name: `xdr_fac`
- Units/format: None
- Value restrictions: At least 0
- Default value: 1
- Appears in the databook
- Used to compute:
	- "SN-XDR infectiousness"
	- "SP-XDR infectiousness"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Early latent untreated (diagnosable)

- Code name: `lteu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Early latent untreated (diagnosable)"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `lti_idiv*ltei_idiv*(1-und_idiv)*(1-lteti_idiv)`
- Depends on:
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of the population that have previously been infected with TB"
	- "Initialization proportion of latent TB cases that are on treatment"
	- "Initialization proportion of latent TB cases that are early latent"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Early latent on treatment

- Code name: `ltet_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Early latent on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `lti_idiv*ltei_idiv*lteti_idiv`
- Depends on:
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of latent TB cases that are on treatment"
	- "Initialization proportion of latent TB cases that are early latent"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Late latent untreated (diagnosable)

- Code name: `ltlu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Late latent untreated (diagnosable)"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `lti_idiv*(1-ltei_idiv)*(1-und_idiv)*(1-lteti_idiv)`
- Depends on:
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of the population that have previously been infected with TB"
	- "Initialization proportion of latent TB cases that are on treatment"
	- "Initialization proportion of latent TB cases that are early latent"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Late latent on treatment

- Code name: `ltlt_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Late latent on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `lti_idiv*(1-ltei_idiv)*lteti_idiv`
- Depends on:
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of latent TB cases that are on treatment"
	- "Initialization proportion of latent TB cases that are early latent"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Early latent untreated (diagnosis restricted)

- Code name: `ltex_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Early latent untreated (diagnosis restricted)"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `lti_idiv*ltei_idiv*und_idiv*(1-lteti_idiv)`
- Depends on:
	- "Initialization proportion of latent TB cases that are on treatment"
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of the population that have previously been infected with TB"
	- "Initialization proportion of latent TB cases that are early latent"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Late latent untreated (diagnosis restricted)

- Code name: `ltlx_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Late latent untreated (diagnosis restricted)"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `lti_idiv*(1-ltei_idiv)*und_idiv*(1-lteti_idiv)`
- Depends on:
	- "Initialization proportion of latent TB cases that are on treatment"
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of the population that have previously been infected with TB"
	- "Initialization proportion of latent TB cases that are early latent"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-DS undiagnosed

- Code name: `spdu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-DS undiagnosed"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*pd_div*(1-acdi_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "New SP infections: proportion of population that are SP-DS"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-DS diagnosed but not on treatment

- Code name: `spdd_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-DS diagnosed but not on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*pd_div*acdi_idiv*(1-dti_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SP infections: proportion of population that are SP-DS"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-DS on treatment

- Code name: `spdt_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-DS on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*pd_div*acdi_idiv*dti_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SP infections: proportion of population that are SP-DS"
- Used to compute:
	- "Initialization proportion: Completed treatment (active)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-MDR undiagnosed

- Code name: `spmu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-MDR undiagnosed"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*pm_div*(1-acdi_idiv)`
- Depends on:
	- "New SP infections: proportion of population that are SP-MDR"
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-MDR diagnosed but not on treatment

- Code name: `spmd_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-MDR diagnosed but not on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*pm_div*acdi_idiv*(1-dti_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "New SP infections: proportion of population that are SP-MDR"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-MDR on treatment

- Code name: `spmt_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-MDR on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*pm_div*acdi_idiv*dti_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "New SP infections: proportion of population that are SP-MDR"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
- Used to compute:
	- "Initialization proportion: Completed treatment (active)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-XDR undiagnosed

- Code name: `spxu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-XDR undiagnosed"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*px_div*(1-acdi_idiv)`
- Depends on:
	- "New SP infections: proportion of population that are SP-XDR"
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-XDR diagnosed but not on treatment

- Code name: `spxd_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-XDR diagnosed but not on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*px_div*acdi_idiv*(1-dti_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SP infections: proportion of population that are SP-XDR"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SP-XDR on treatment

- Code name: `spxt_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SP-XDR on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*p_div*px_div*acdi_idiv*dti_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SP"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SP infections: proportion of population that are SP-XDR"
- Used to compute:
	- "Initialization proportion: Completed treatment (active)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-DS undiagnosed

- Code name: `sndu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-DS undiagnosed"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nd_div*(1-acdi_idiv)`
- Depends on:
	- "New SN infections: proportion of population that are SN-DS"
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SN"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-DS diagnosed but not on treatment

- Code name: `sndd_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-DS diagnosed but not on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nd_div*acdi_idiv*(1-dti_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SN"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SN infections: proportion of population that are SN-DS"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-DS on treatment

- Code name: `sndt_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-DS on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nd_div*acdi_idiv*dti_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SN"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SN infections: proportion of population that are SN-DS"
- Used to compute:
	- "Initialization proportion: Completed treatment (active)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-MDR undiagnosed

- Code name: `snmu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-MDR undiagnosed"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nm_div*(1-acdi_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New SN infections: proportion of population that are SN-MDR"
	- "New active infections: proportion of population that are SN"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-MDR diagnosed but not on treatment

- Code name: `snmd_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-MDR diagnosed but not on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nm_div*acdi_idiv*(1-dti_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SN"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SN infections: proportion of population that are SN-MDR"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-MDR on treatment

- Code name: `snmt_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-MDR on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nm_div*acdi_idiv*dti_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SN"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
	- "New SN infections: proportion of population that are SN-MDR"
- Used to compute:
	- "Initialization proportion: Completed treatment (active)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-XDR undiagnosed

- Code name: `snxu_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-XDR undiagnosed"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nx_div*(1-acdi_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New SN infections: proportion of population that are SN-XDR"
	- "New active infections: proportion of population that are SN"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-XDR diagnosed but not on treatment

- Code name: `snxd_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-XDR diagnosed but not on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nx_div*acdi_idiv*(1-dti_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SN"
	- "New SN infections: proportion of population that are SN-XDR"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: SN-XDR on treatment

- Code name: `snxt_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "SN-XDR on treatment"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `aci_idiv*n_div*nx_div*acdi_idiv*dti_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "New active infections: proportion of population that are SN"
	- "New SN infections: proportion of population that are SN-XDR"
	- "Initialization proportion of diagnosed TB cases that are on treatment"
	- "Initialization proportion of active TB cases that are diagnosed"
- Used to compute:
	- "Initialization proportion: Completed treatment (active)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Completed treatment (active)

- Code name: `acr_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Completed treatment (active)"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `1.5*(spdt_idiv+spmt_idiv+spxt_idiv+sndt_idiv+snmt_idiv+snxt_idiv)`
- Depends on:
	- "Initialization proportion: SP-DS on treatment"
	- "Initialization proportion: SN-XDR on treatment"
	- "Initialization proportion: SN-DS on treatment"
	- "Initialization proportion: SP-MDR on treatment"
	- "Initialization proportion: SP-XDR on treatment"
	- "Initialization proportion: SN-MDR on treatment"
- Used to compute:
	- "Initialization proportion: Susceptible"
	- "Initialization proportion: Vaccinated"
	- "Initialization proportion: Susceptible (diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Vaccinated

- Code name: `vac_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Vaccinated"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `(1-vac_fac*(aci_idiv-lti_idiv-acr_idiv))*vaci_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "Initialization proportion of the population that have previously been vaccinated"
	- "Initialization proportion: Completed treatment (active)"
	- "Initialization proportion of the population with latent TB"
	- "Infection vulnerability factor (vaccinated versus susceptible)"
- Used to compute:
	- "Initialization proportion: Susceptible"
	- "Initialization proportion: Susceptible (diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Susceptible

- Code name: `sus_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Susceptible"
- Default value: 1
- Does not appear in the databook
- This parameter's value is computed by a function: `(1-aci_idiv-lti_idiv-vac_idiv-acr_idiv)*(1-und_idiv)`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "Initialization proportion: Vaccinated"
	- "Initialization proportion: Completed treatment (active)"
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of the population that have previously been infected with TB"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Initialization proportion: Susceptible (diagnosis restricted)

- Code name: `susx_idiv`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Initialization population size" to "Susceptible (diagnosis restricted)"
- Default value: 0
- Does not appear in the databook
- This parameter's value is computed by a function: `(1-aci_idiv-lti_idiv-vac_idiv-acr_idiv)*und_idiv`
- Depends on:
	- "Initialization proportion of the population with active TB"
	- "Initialization proportion: Vaccinated"
	- "Initialization proportion: Completed treatment (active)"
	- "Initialization proportion of the population with latent TB"
	- "Initialization proportion of the population that have previously been infected with TB"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number of births

- Code name: `b_rate`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Source: Origin of births" to "Susceptible"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Non-TB deaths

- Code name: `doth_rate`
- Units/format: probability
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Susceptible" to "Sink: Cumulative non-TB deaths over simulation"
	- "Vaccinated" to "Sink: Cumulative non-TB deaths over simulation"
	- "Early latent untreated (diagnosable)" to "Sink: Cumulative non-TB deaths over simulation"
	- "Early latent on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "Late latent untreated (diagnosable)" to "Sink: Cumulative non-TB deaths over simulation"
	- "Late latent on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "Susceptible (diagnosis restricted)" to "Sink: Cumulative non-TB deaths over simulation"
	- "Early latent untreated (diagnosis restricted)" to "Sink: Cumulative non-TB deaths over simulation"
	- "Late latent untreated (diagnosis restricted)" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-DS undiagnosed" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-DS diagnosed but not on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-DS on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-MDR undiagnosed" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-MDR diagnosed but not on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-MDR on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-XDR undiagnosed" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-XDR diagnosed but not on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SP-XDR on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-DS undiagnosed" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-DS diagnosed but not on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-DS on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-MDR undiagnosed" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-MDR diagnosed but not on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-MDR on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-XDR undiagnosed" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-XDR diagnosed but not on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "SN-XDR on treatment" to "Sink: Cumulative non-TB deaths over simulation"
	- "Completed treatment (active)" to "Sink: Cumulative non-TB deaths over simulation"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number of new immigrants

- Code name: `i_rate`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Source: Origin of immigration" to "Junction: Infection status of immigrants"
- Default value: 0
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number of departing emigrants

- Code name: `e_rate`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Susceptible" to "Sink: Cumulative emigration over simulation"
	- "Vaccinated" to "Sink: Cumulative emigration over simulation"
	- "Early latent untreated (diagnosable)" to "Sink: Cumulative emigration over simulation"
	- "Early latent on treatment" to "Sink: Cumulative emigration over simulation"
	- "Late latent untreated (diagnosable)" to "Sink: Cumulative emigration over simulation"
	- "Late latent on treatment" to "Sink: Cumulative emigration over simulation"
	- "Susceptible (diagnosis restricted)" to "Sink: Cumulative emigration over simulation"
	- "Early latent untreated (diagnosis restricted)" to "Sink: Cumulative emigration over simulation"
	- "Late latent untreated (diagnosis restricted)" to "Sink: Cumulative emigration over simulation"
	- "SP-DS undiagnosed" to "Sink: Cumulative emigration over simulation"
	- "SP-DS diagnosed but not on treatment" to "Sink: Cumulative emigration over simulation"
	- "SP-DS on treatment" to "Sink: Cumulative emigration over simulation"
	- "SP-MDR undiagnosed" to "Sink: Cumulative emigration over simulation"
	- "SP-MDR diagnosed but not on treatment" to "Sink: Cumulative emigration over simulation"
	- "SP-MDR on treatment" to "Sink: Cumulative emigration over simulation"
	- "SP-XDR undiagnosed" to "Sink: Cumulative emigration over simulation"
	- "SP-XDR diagnosed but not on treatment" to "Sink: Cumulative emigration over simulation"
	- "SP-XDR on treatment" to "Sink: Cumulative emigration over simulation"
	- "SN-DS undiagnosed" to "Sink: Cumulative emigration over simulation"
	- "SN-DS diagnosed but not on treatment" to "Sink: Cumulative emigration over simulation"
	- "SN-DS on treatment" to "Sink: Cumulative emigration over simulation"
	- "SN-MDR undiagnosed" to "Sink: Cumulative emigration over simulation"
	- "SN-MDR diagnosed but not on treatment" to "Sink: Cumulative emigration over simulation"
	- "SN-MDR on treatment" to "Sink: Cumulative emigration over simulation"
	- "SN-XDR undiagnosed" to "Sink: Cumulative emigration over simulation"
	- "SN-XDR diagnosed but not on treatment" to "Sink: Cumulative emigration over simulation"
	- "SN-XDR on treatment" to "Sink: Cumulative emigration over simulation"
	- "Completed treatment (active)" to "Sink: Cumulative emigration over simulation"
- Default value: 0
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Number of vaccinations administered

- Code name: `v_num`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Susceptible" to "Vaccinated"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI treatment initiations through mass screening

- Code name: `l_ntreat_ms`
- Units/format: number
- Value restrictions: At least 0
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Late-LTBI annual number initiating treatment"
	- "Early-LTBI annual number initiating treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI treatment initiations through contact tracing

- Code name: `l_ntreat_ct`
- Units/format: number
- Value restrictions: At least 0
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Early-LTBI annual number initiating treatment"
	- "Early-LTBI (diagnosis restricted) annual number initiating treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI treatment average duration of full course

- Code name: `l_duration`
- Units/format: days
- Value restrictions: At least 1.0000
- Default value: 180
- Appears in the databook
- Used to compute:
	- "LTBI treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI treatment proportion of lost to follow up

- Code name: `lt_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.07
- Appears in the databook
- Used to compute:
	- "Early-LTBI treatment abandonment rate"
	- "Late-LTBI treatment abandonment rate"
	- "LTBI treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI treatment proportion of successful completions

- Code name: `lt_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.93
- Appears in the databook
- Used to compute:
	- "Late-LTBI treatment success rate"
	- "Early-LTBI treatment success rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI treatment average duration until outcome

- Code name: `ltt_dur`
- Units/format: duration
- Contributes to transitions from:
	- "Early latent on treatment" to "Junction: Latent early treatment outcome"
	- "Late latent on treatment" to "Junction: Latent late treatment outcome"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `l_duration*(1-0.5*lt_fail_div)/365`
- Depends on:
	- "LTBI treatment proportion of lost to follow up"
	- "LTBI treatment average duration of full course"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early-LTBI annual number initiating treatment

- Code name: `le_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Early latent untreated (diagnosable)" to "Early latent on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `l_ntreat_ct*(lteu/max(lteu+ltex, 1.)) + l_ntreat_ms*(lteu/max(lteu+ltlu, 1.))`
- Depends on:
	- "Early latent untreated (diagnosable)"
	- "Late latent untreated (diagnosable)"
	- "LTBI treatment initiations through mass screening"
	- "LTBI treatment initiations through contact tracing"
	- "Early latent untreated (diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early-LTBI (diagnosis restricted) annual number initiating treatment

- Code name: `lx_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Early latent untreated (diagnosis restricted)" to "Early latent on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `l_ntreat_ct*(ltex/max(lteu+ltex, 1.))`
- Depends on:
	- "LTBI treatment initiations through contact tracing"
	- "Early latent untreated (diagnosable)"
	- "Early latent untreated (diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Late-LTBI annual number initiating treatment

- Code name: `ll_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "Late latent untreated (diagnosable)" to "Late latent on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `l_ntreat_ms*(ltlu/max(lteu+ltlu, 1.))`
- Depends on:
	- "Late latent untreated (diagnosable)"
	- "Early latent untreated (diagnosable)"
	- "LTBI treatment initiations through mass screening"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early-LTBI treatment abandonment rate

- Code name: `let_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Latent early treatment outcome" to "Early latent untreated (diagnosis restricted)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `lt_fail_div`
- Depends on:
	- "LTBI treatment proportion of lost to follow up"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early-LTBI treatment success rate

- Code name: `let_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Latent early treatment outcome" to "Susceptible (diagnosis restricted)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `lt_succ_div`
- Depends on:
	- "LTBI treatment proportion of successful completions"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Late-LTBI treatment abandonment rate

- Code name: `llt_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Latent late treatment outcome" to "Late latent untreated (diagnosis restricted)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `lt_fail_div`
- Depends on:
	- "LTBI treatment proportion of lost to follow up"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Late-LTBI treatment success rate

- Code name: `llt_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Latent late treatment outcome" to "Susceptible (diagnosis restricted)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `lt_succ_div`
- Depends on:
	- "LTBI treatment proportion of successful completions"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early latency departure rate

- Code name: `e_dep`
- Units/format: None
- Value restrictions: 0-1.0000
- Default value: 0.2
- Appears in the databook
- Used to compute:
	- "LTBI-active progression rate (early diagnosis restricted)"
	- "LTBI-active progression rate (early diagnosable)"
	- "Early-late LTBI progression rate (diagnosable)"
	- "Early-late LTBI progression rate (diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Late latency departure rate

- Code name: `l_dep`
- Units/format: None
- Value restrictions: 0-1.0000
- Default value: 0.003
- Appears in the databook
- Used to compute:
	- "LTBI-active progression rate (late diagnosable)"
	- "LTBI-active progression rate (late diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Probability of early-active versus early-late progression

- Code name: `p_branch`
- Units/format: None
- Value restrictions: At least 0
- Default value: 0.177
- Appears in the databook
- Used to compute:
	- "LTBI-active progression rate (early diagnosis restricted)"
	- "LTBI-active progression rate (early diagnosable)"
	- "Early-late LTBI progression rate (diagnosable)"
	- "Early-late LTBI progression rate (diagnosis restricted)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early-late LTBI progression rate (diagnosable)

- Code name: `lu_prog`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Early latent untreated (diagnosable)" to "Late latent untreated (diagnosable)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `(1-p_branch)*e_dep`
- Depends on:
	- "Early latency departure rate"
	- "Probability of early-active versus early-late progression"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early-late LTBI progression rate (diagnosis restricted)

- Code name: `lx_prog`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Early latent untreated (diagnosis restricted)" to "Late latent untreated (diagnosis restricted)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `(1-p_branch)*e_dep`
- Depends on:
	- "Early latency departure rate"
	- "Probability of early-active versus early-late progression"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI-active progression rate (early diagnosable)

- Code name: `leu_act`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Early latent untreated (diagnosable)" to "Junction: Smear disaggregator for new active"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `p_branch*e_dep`
- Depends on:
	- "Early latency departure rate"
	- "Probability of early-active versus early-late progression"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI-active progression rate (early diagnosis restricted)

- Code name: `lex_act`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Early latent untreated (diagnosis restricted)" to "Junction: Smear disaggregator for new active"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `p_branch*e_dep`
- Depends on:
	- "Early latency departure rate"
	- "Probability of early-active versus early-late progression"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI-active progression rate (late diagnosable)

- Code name: `llu_act`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Late latent untreated (diagnosable)" to "Junction: Smear disaggregator for new active"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `l_dep`
- Depends on:
	- "Late latency departure rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: LTBI-active progression rate (late diagnosis restricted)

- Code name: `llx_act`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Late latent untreated (diagnosis restricted)" to "Junction: Smear disaggregator for new active"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `l_dep`
- Depends on:
	- "Late latency departure rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR infectiousness

- Code name: `spm_infxness`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `spd_infxness*mdr_fac`
- Depends on:
	- "SP-DS infectiousness"
	- "Relative infectiousness (MDR versus DS)"
- Used to compute:
	- "Force of infection from SP prevalence"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR infectiousness

- Code name: `spx_infxness`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `spd_infxness*xdr_fac`
- Depends on:
	- "Relative infectiousness (XDR versus DS)"
	- "SP-DS infectiousness"
- Used to compute:
	- "Force of infection from SP prevalence"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS infectiousness

- Code name: `snd_infxness`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `sn_fac*spd_infxness`
- Depends on:
	- "Relative infectiousness (SN versus SP)"
	- "SP-DS infectiousness"
- Used to compute:
	- "Force of infection from SN prevalence"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR infectiousness

- Code name: `snm_infxness`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `sn_fac*spd_infxness*mdr_fac`
- Depends on:
	- "Relative infectiousness (SN versus SP)"
	- "SP-DS infectiousness"
	- "Relative infectiousness (MDR versus DS)"
- Used to compute:
	- "Force of infection from SN prevalence"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR infectiousness

- Code name: `snx_infxness`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `sn_fac*spd_infxness*xdr_fac`
- Depends on:
	- "Relative infectiousness (SN versus SP)"
	- "Relative infectiousness (XDR versus DS)"
	- "SP-DS infectiousness"
- Used to compute:
	- "Force of infection from SN prevalence"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Force of infection from SP prevalence

- Code name: `foi_p`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `spd_infxness*spd_prevx+spm_infxness*spm_prevx+spx_infxness*spx_prevx`
- Depends on:
	- "SP-XDR infectiousness"
	- "Suspected untreated SP-DS prevalence"
	- "SP-MDR infectiousness"
	- "SP-DS infectiousness"
	- "Suspected untreated SP-MDR prevalence"
	- "Suspected untreated SP-XDR prevalence"
- Used to compute:
	- "Force of infection imparted by population"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Force of infection from SN prevalence

- Code name: `foi_n`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `snd_infxness*snd_prevx+snm_infxness*snm_prevx+snx_infxness*snx_prevx`
- Depends on:
	- "SN-MDR infectiousness"
	- "Suspected untreated SN-XDR prevalence"
	- "SN-DS infectiousness"
	- "SN-XDR infectiousness"
	- "Suspected untreated SN-DS prevalence"
	- "Suspected untreated SN-MDR prevalence"
- Used to compute:
	- "Force of infection imparted by population"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Force of infection imparted by population

- Code name: `foi_out`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `foi_p+foi_n`
- Depends on:
	- "Force of infection from SN prevalence"
	- "Force of infection from SP prevalence"
- Used to compute:
	- "Force of infection experienced by population"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Force of infection experienced by population

- Code name: `foi_in`
- Units/format: None
- Value restrictions: At least 0
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `SRC_POP_AVG(foi_out, w_ctc, alive)`
- Depends on:
	- "Population size"
	- "Force of infection imparted by population"
	- "Preference weighting for one population interacting with another"
- Used to compute:
	- "Reinfection rate (susceptible to diagnosis restricted for diagnosis restricted)"
	- "Infection rate (susceptible to diagnosable latent)"
	- "Infection rate (vaccinated to diagnosis restricted latent)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Infection rate (susceptible to diagnosable latent)

- Code name: `l_inf`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Susceptible" to "Early latent untreated (diagnosable)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `foi_in*inf_sus`
- Depends on:
	- "Force of infection experienced by population"
	- "Infection vulnerability factor (relative population susceptibility)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Infection rate (vaccinated to diagnosis restricted latent)

- Code name: `v_inf`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Vaccinated" to "Early latent untreated (diagnosis restricted)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `foi_in*inf_sus*vac_fac`
- Depends on:
	- "Force of infection experienced by population"
	- "Infection vulnerability factor (vaccinated versus susceptible)"
	- "Infection vulnerability factor (relative population susceptibility)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Reinfection rate (susceptible to diagnosis restricted for diagnosis restricted)

- Code name: `lr_inf`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Susceptible (diagnosis restricted)" to "Early latent untreated (diagnosis restricted)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `foi_in*inf_sus*lat_fac`
- Depends on:
	- "Force of infection experienced by population"
	- "Infection vulnerability factor (recovered versus susceptible)"
	- "Infection vulnerability factor (relative population susceptibility)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Relapse rate for completed treatment (active) cases

- Code name: `ar_act`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Completed treatment (active)" to "Junction: Smear disaggregator for new active"
- Default value: 0.2
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Full recovery rate for completed treatment (active) cases

- Code name: `ar_rec`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Completed treatment (active)" to "Susceptible (diagnosis restricted)"
- Default value: 0.5
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Proportion of new immigrants with LTBI

- Code name: `im_lat_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Infection status of immigrants" to "Late latent untreated (diagnosable)"
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Susceptible proportion of immigrants"
	- "Late latent proportion of new immigrants"
	- "Early latent proportion of new immigrants"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Early latent proportion of new immigrants

- Code name: `im_late_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `im_lat_div*ltei_idiv`
- Depends on:
	- "Initialization proportion of latent TB cases that are early latent"
	- "Proportion of new immigrants with LTBI"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Late latent proportion of new immigrants

- Code name: `im_latl_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `im_lat_div*(1-ltei_idiv)`
- Depends on:
	- "Initialization proportion of latent TB cases that are early latent"
	- "Proportion of new immigrants with LTBI"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Proportion of new immigrants with active TB infections

- Code name: `im_act_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Infection status of immigrants" to "Junction: Smear disaggregator for new active"
- Default value: 0
- Appears in the databook
- Used to compute:
	- "Susceptible proportion of immigrants"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Susceptible proportion of immigrants

- Code name: `im_sus_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: Infection status of immigrants" to "Susceptible"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `1-im_lat_div-im_act_div`
- Depends on:
	- "Proportion of new immigrants with LTBI"
	- "Proportion of new immigrants with active TB infections"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS diagnosis notifications

- Code name: `pd_ndiag`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SP-DS undiagnosed" to "SP-DS diagnosed but not on treatment"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR diagnosis notifications

- Code name: `pm_ndiag`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SP-MDR undiagnosed" to "SP-MDR diagnosed but not on treatment"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR diagnosis notifications

- Code name: `px_ndiag`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SP-XDR undiagnosed" to "SP-XDR diagnosed but not on treatment"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS diagnosis notifications

- Code name: `nd_ndiag`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SN-DS undiagnosed" to "SN-DS diagnosed but not on treatment"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR diagnosis notifications

- Code name: `nm_ndiag`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SN-MDR undiagnosed" to "SN-MDR diagnosed but not on treatment"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR diagnosis notifications

- Code name: `nx_ndiag`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SN-XDR undiagnosed" to "SN-XDR diagnosed but not on treatment"
- Default value: None
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment number of initiations

- Code name: `d_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "SP-DS treatment number of initiations"
	- "SN-DS treatment number of initiations"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS treatment number of initiations

- Code name: `pd_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SP-DS diagnosed but not on treatment" to "SP-DS on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_ntreat*(spdd/max(spdd+sndd, 1.))`
- Depends on:
	- "SP-DS diagnosed but not on treatment"
	- "SN-DS diagnosed but not on treatment"
	- "DS treatment number of initiations"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS treatment number of initiations

- Code name: `nd_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SN-DS diagnosed but not on treatment" to "SN-DS on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_ntreat*(spdd/max(spdd+sndd, 1.))`
- Depends on:
	- "SP-DS diagnosed but not on treatment"
	- "SN-DS diagnosed but not on treatment"
	- "DS treatment number of initiations"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment average duration of completed treatment

- Code name: `d_duration`
- Units/format: days
- Value restrictions: At least 1.0000
- Default value: 180
- Appears in the databook
- Used to compute:
	- "DS treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `d_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.07
- Appears in the databook
- Used to compute:
	- "SN-DS treatment proportion of loss to follow up (require re-diagnosis)"
	- "DS treatment average duration until outcome"
	- "SP-DS treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `d_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.02
- Appears in the databook
- Used to compute:
	- "SP-DS treatment proportion failed (no escalation, no need to re-diagnose)"
	- "SN-DS treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment proportion failed (escalation to MDR, require re-diagnosis)

- Code name: `d_esc_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.02
- Appears in the databook
- Used to compute:
	- "SP-DS treatment proportion failed (escalation to MDR, require re-diagnosis)"
	- "DS treatment average duration until outcome"
	- "SN-DS treatment proportion failed (escalation to MDR, require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment proportion of treatments completed + success

- Code name: `d_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.83
- Appears in the databook
- Used to compute:
	- "SP-DS treatment proportion of treatments completed + success"
	- "SN-DS treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment proportion of deaths

- Code name: `d_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.06
- Appears in the databook
- Used to compute:
	- "SN-DS treatment proportion of deaths"
	- "DS treatment average duration until outcome"
	- "SP-DS treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DS treatment average duration until outcome

- Code name: `dt_dur`
- Units/format: duration
- Contributes to transitions from:
	- "SP-DS on treatment" to "Junction: SP-DS treatment outcome"
	- "SN-DS on treatment" to "Junction: SN-DS treatment outcome"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_duration*(1-0.5*(d_ltfu_div+d_sad_div+d_esc_div))/365`
- Depends on:
	- "DS treatment proportion failed (escalation to MDR, require re-diagnosis)"
	- "DS treatment proportion of loss to follow up (require re-diagnosis)"
	- "DS treatment proportion of deaths"
	- "DS treatment average duration of completed treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `pd_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-DS treatment outcome" to "SP-DS undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_ltfu_div`
- Depends on:
	- "DS treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `pd_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-DS treatment outcome" to "SP-DS diagnosed but not on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_fail_div`
- Depends on:
	- "DS treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS treatment proportion failed (escalation to MDR, require re-diagnosis)

- Code name: `pd_esc_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-DS treatment outcome" to "SP-MDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_esc_div`
- Depends on:
	- "DS treatment proportion failed (escalation to MDR, require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS treatment proportion of treatments completed + success

- Code name: `pd_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-DS treatment outcome" to "Completed treatment (active)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_succ_div`
- Depends on:
	- "DS treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS treatment proportion of deaths

- Code name: `pd_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-DS treatment outcome" to "Sink: Cumulative TB deaths over simulation"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_sad_div`
- Depends on:
	- "DS treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `nd_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-DS treatment outcome" to "SN-DS undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_ltfu_div`
- Depends on:
	- "DS treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `nd_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-DS treatment outcome" to "SN-DS diagnosed but not on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_fail_div`
- Depends on:
	- "DS treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS treatment proportion failed (escalation to MDR, require re-diagnosis)

- Code name: `nd_esc_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-DS treatment outcome" to "SN-MDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_esc_div`
- Depends on:
	- "DS treatment proportion failed (escalation to MDR, require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS treatment proportion of treatments completed + success

- Code name: `nd_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-DS treatment outcome" to "Completed treatment (active)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_succ_div`
- Depends on:
	- "DS treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS treatment proportion of deaths

- Code name: `nd_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-DS treatment outcome" to "Sink: Cumulative TB deaths over simulation"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `d_sad_div`
- Depends on:
	- "DS treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment number of initiations

- Code name: `m_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "SP-MDR treatment number of initiations"
	- "SN-MDR treatment number of initiations"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR treatment number of initiations

- Code name: `pm_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SP-MDR diagnosed but not on treatment" to "SP-MDR on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_ntreat*(spmd/max(spmd+snmd, 1.))`
- Depends on:
	- "SN-MDR diagnosed but not on treatment"
	- "MDR treatment number of initiations"
	- "SP-MDR diagnosed but not on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR treatment number of initiations

- Code name: `nm_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SN-MDR diagnosed but not on treatment" to "SN-MDR on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_ntreat*(snmd/max(spmd+snmd, 1.))`
- Depends on:
	- "SN-MDR diagnosed but not on treatment"
	- "MDR treatment number of initiations"
	- "SP-MDR diagnosed but not on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment average duration of completed treatment

- Code name: `m_duration`
- Units/format: days
- Value restrictions: At least 1.0000
- Default value: 540
- Appears in the databook
- Used to compute:
	- "MDR treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `m_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.147
- Appears in the databook
- Used to compute:
	- "SN-MDR treatment proportion of loss to follow up (require re-diagnosis)"
	- "MDR treatment average duration until outcome"
	- "SP-MDR treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `m_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.07
- Appears in the databook
- Used to compute:
	- "SN-MDR treatment proportion failed (no escalation, no need to re-diagnose)"
	- "SP-MDR treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment proportion failed (escalation to XDR, require re-diagnosis)

- Code name: `m_esc_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.02
- Appears in the databook
- Used to compute:
	- "SN-MDR treatment proportion failed (escalation to XDR, require re-diagnosis)"
	- "SP-MDR treatment proportion failed (escalation to XDR, require re-diagnosis)"
	- "MDR treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment proportion of treatments completed + success

- Code name: `m_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.634
- Appears in the databook
- Used to compute:
	- "SP-MDR treatment proportion of treatments completed + success"
	- "SN-MDR treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment proportion of deaths

- Code name: `m_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.129
- Appears in the databook
- Used to compute:
	- "SN-MDR treatment proportion of deaths"
	- "MDR treatment average duration until outcome"
	- "SP-MDR treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: MDR treatment average duration until outcome

- Code name: `mt_dur`
- Units/format: duration
- Contributes to transitions from:
	- "SP-MDR on treatment" to "Junction: SP-MDR treatment outcome"
	- "SN-MDR on treatment" to "Junction: SN-MDR treatment outcome"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_duration*(1-0.5*(m_ltfu_div+m_sad_div+m_esc_div))/365`
- Depends on:
	- "MDR treatment proportion of loss to follow up (require re-diagnosis)"
	- "MDR treatment average duration of completed treatment"
	- "MDR treatment proportion failed (escalation to XDR, require re-diagnosis)"
	- "MDR treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `pm_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-MDR treatment outcome" to "SP-MDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_ltfu_div`
- Depends on:
	- "MDR treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `pm_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-MDR treatment outcome" to "SP-MDR diagnosed but not on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_fail_div`
- Depends on:
	- "MDR treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR treatment proportion failed (escalation to XDR, require re-diagnosis)

- Code name: `pm_esc_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-MDR treatment outcome" to "SP-XDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_esc_div`
- Depends on:
	- "MDR treatment proportion failed (escalation to XDR, require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR treatment proportion of treatments completed + success

- Code name: `pm_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-MDR treatment outcome" to "Completed treatment (active)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_succ_div`
- Depends on:
	- "MDR treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR treatment proportion of deaths

- Code name: `pm_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-MDR treatment outcome" to "Sink: Cumulative TB deaths over simulation"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_sad_div`
- Depends on:
	- "MDR treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `nm_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-MDR treatment outcome" to "SN-MDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_ltfu_div`
- Depends on:
	- "MDR treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `nm_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-MDR treatment outcome" to "SN-MDR diagnosed but not on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_fail_div`
- Depends on:
	- "MDR treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR treatment proportion failed (escalation to XDR, require re-diagnosis)

- Code name: `nm_esc_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-MDR treatment outcome" to "SN-XDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_esc_div`
- Depends on:
	- "MDR treatment proportion failed (escalation to XDR, require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR treatment proportion of treatments completed + success

- Code name: `nm_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-MDR treatment outcome" to "Completed treatment (active)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_succ_div`
- Depends on:
	- "MDR treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR treatment proportion of deaths

- Code name: `nm_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-MDR treatment outcome" to "Sink: Cumulative TB deaths over simulation"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `m_sad_div`
- Depends on:
	- "MDR treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: XDR treatment number of initiations

- Code name: `x_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Default value: None
- Appears in the databook
- Used to compute:
	- "SN-XDR treatment number of initiations"
	- "SP-XDR treatment number of initiations"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR treatment number of initiations

- Code name: `px_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SP-XDR diagnosed but not on treatment" to "SP-XDR on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_ntreat*(spxd/max(spxd+snxd, 1.))`
- Depends on:
	- "XDR treatment number of initiations"
	- "SP-XDR diagnosed but not on treatment"
	- "SN-XDR diagnosed but not on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR treatment number of initiations

- Code name: `nx_ntreat`
- Units/format: number
- Value restrictions: At least 0
- Contributes to transitions from:
	- "SN-XDR diagnosed but not on treatment" to "SN-XDR on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_ntreat*(snxd/max(spxd+snxd, 1.))`
- Depends on:
	- "XDR treatment number of initiations"
	- "SP-XDR diagnosed but not on treatment"
	- "SN-XDR diagnosed but not on treatment"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: XDR treatment average duration of completed treatment

- Code name: `x_duration`
- Units/format: days
- Value restrictions: At least 1.0000
- Default value: 720
- Appears in the databook
- Used to compute:
	- "XDR treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: XDR treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `x_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.21
- Appears in the databook
- Used to compute:
	- "SN-XDR treatment proportion of loss to follow up (require re-diagnosis)"
	- "SP-XDR treatment proportion of loss to follow up (require re-diagnosis)"
	- "XDR treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: XDR treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `x_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.21
- Appears in the databook
- Used to compute:
	- "SN-XDR treatment proportion failed (no escalation, no need to re-diagnose)"
	- "SP-XDR treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: XDR treatment proportion of treatments completed + success

- Code name: `x_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.3
- Appears in the databook
- Used to compute:
	- "SP-XDR treatment proportion of treatments completed + success"
	- "SN-XDR treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: XDR treatment proportion of deaths

- Code name: `x_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Default value: 0.28
- Appears in the databook
- Used to compute:
	- "SP-XDR treatment proportion of deaths"
	- "SN-XDR treatment proportion of deaths"
	- "XDR treatment average duration until outcome"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: XDR treatment average duration until outcome

- Code name: `xt_dur`
- Units/format: duration
- Contributes to transitions from:
	- "SP-XDR on treatment" to "Junction: SP-XDR treatment outcome"
	- "SN-XDR on treatment" to "Junction: SN-XDR treatment outcome"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_duration*(1-0.5*(x_ltfu_div+x_sad_div))/365`
- Depends on:
	- "XDR treatment average duration of completed treatment"
	- "XDR treatment proportion of deaths"
	- "XDR treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `px_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-XDR treatment outcome" to "SP-XDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_ltfu_div`
- Depends on:
	- "XDR treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `px_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-XDR treatment outcome" to "SP-XDR diagnosed but not on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_fail_div`
- Depends on:
	- "XDR treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR treatment proportion of treatments completed + success

- Code name: `px_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-XDR treatment outcome" to "Completed treatment (active)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_succ_div`
- Depends on:
	- "XDR treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR treatment proportion of deaths

- Code name: `px_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SP-XDR treatment outcome" to "Sink: Cumulative TB deaths over simulation"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_sad_div`
- Depends on:
	- "XDR treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR treatment proportion of loss to follow up (require re-diagnosis)

- Code name: `nx_ltfu_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-XDR treatment outcome" to "SN-XDR undiagnosed"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_ltfu_div`
- Depends on:
	- "XDR treatment proportion of loss to follow up (require re-diagnosis)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR treatment proportion failed (no escalation, no need to re-diagnose)

- Code name: `nx_fail_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-XDR treatment outcome" to "SN-XDR diagnosed but not on treatment"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_fail_div`
- Depends on:
	- "XDR treatment proportion failed (no escalation, no need to re-diagnose)"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR treatment proportion of treatments completed + success

- Code name: `nx_succ_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-XDR treatment outcome" to "Completed treatment (active)"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_succ_div`
- Depends on:
	- "XDR treatment proportion of treatments completed + success"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR treatment proportion of deaths

- Code name: `nx_sad_div`
- Units/format: proportion
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "Junction: SN-XDR treatment outcome" to "Sink: Cumulative TB deaths over simulation"
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `x_sad_div`
- Depends on:
	- "XDR treatment proportion of deaths"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS natural recovery rate

- Code name: `pd_rec`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SP-DS undiagnosed" to "Completed treatment (active)"
	- "SP-DS diagnosed but not on treatment" to "Completed treatment (active)"
- Default value: 0.03
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR natural recovery rate

- Code name: `pm_rec`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SP-MDR undiagnosed" to "Completed treatment (active)"
	- "SP-MDR diagnosed but not on treatment" to "Completed treatment (active)"
- Default value: 0.03
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR natural recovery rate

- Code name: `px_rec`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SP-XDR undiagnosed" to "Completed treatment (active)"
	- "SP-XDR diagnosed but not on treatment" to "Completed treatment (active)"
- Default value: 0.03
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS natural recovery rate

- Code name: `nd_rec`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SN-DS undiagnosed" to "Completed treatment (active)"
	- "SN-DS diagnosed but not on treatment" to "Completed treatment (active)"
- Default value: 0.16
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR natural recovery rate

- Code name: `nm_rec`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SN-MDR undiagnosed" to "Completed treatment (active)"
	- "SN-MDR diagnosed but not on treatment" to "Completed treatment (active)"
- Default value: 0.16
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR natural recovery rate

- Code name: `nx_rec`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SN-XDR undiagnosed" to "Completed treatment (active)"
	- "SN-XDR diagnosed but not on treatment" to "Completed treatment (active)"
- Default value: 0.16
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-DS death rate (untreated)

- Code name: `pd_term`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SP-DS undiagnosed" to "Sink: Cumulative TB deaths over simulation"
	- "SP-DS diagnosed but not on treatment" to "Sink: Cumulative TB deaths over simulation"
- Default value: 0.12
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-MDR death rate (untreated)

- Code name: `pm_term`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SP-MDR undiagnosed" to "Sink: Cumulative TB deaths over simulation"
	- "SP-MDR diagnosed but not on treatment" to "Sink: Cumulative TB deaths over simulation"
- Default value: 0.12
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SP-XDR death rate (untreated)

- Code name: `px_term`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SP-XDR undiagnosed" to "Sink: Cumulative TB deaths over simulation"
	- "SP-XDR diagnosed but not on treatment" to "Sink: Cumulative TB deaths over simulation"
- Default value: 0.12
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-DS death rate (untreated)

- Code name: `nd_term`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SN-DS undiagnosed" to "Sink: Cumulative TB deaths over simulation"
	- "SN-DS diagnosed but not on treatment" to "Sink: Cumulative TB deaths over simulation"
- Default value: 0.02
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-MDR death rate (untreated)

- Code name: `nm_term`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SN-MDR undiagnosed" to "Sink: Cumulative TB deaths over simulation"
	- "SN-MDR diagnosed but not on treatment" to "Sink: Cumulative TB deaths over simulation"
- Default value: 0.02
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: SN-XDR death rate (untreated)

- Code name: `nx_term`
- Units/format: probability
- Value restrictions: 0-1.0000
- Contributes to transitions from:
	- "SN-XDR undiagnosed" to "Sink: Cumulative TB deaths over simulation"
	- "SN-XDR diagnosed but not on treatment" to "Sink: Cumulative TB deaths over simulation"
- Default value: 0.02
- Appears in the databook

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Disutility weight for active TB

- Code name: `disutility_weight`
- Units/format: None
- Default value: 1
- Appears in the databook
- Used to compute:
	- "YLD rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: YLD rate

- Code name: `yld_rate`
- Units/format: Number of people
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `disutility_weight*(spdu+spdd+spmu+spmd+spxu+spxd+sndu+sndd+snmu+snmd+snxu+snxd+spdt+spmt+spxt+sndt+snmt+snxt)`
- Depends on:
	- "SN-XDR undiagnosed"
	- "SN-MDR on treatment"
	- "Disutility weight for active TB"
	- "SP-XDR diagnosed but not on treatment"
	- "SP-XDR on treatment"
	- "SN-DS diagnosed but not on treatment"
	- "SP-DS on treatment"
	- "SN-DS on treatment"
	- "SP-DS diagnosed but not on treatment"
	- "SN-MDR diagnosed but not on treatment"
	- "SP-DS undiagnosed"
	- "SP-MDR undiagnosed"
	- "SP-XDR undiagnosed"
	- "SP-MDR on treatment"
	- "SN-XDR diagnosed but not on treatment"
	- "SN-DS undiagnosed"
	- "SN-MDR undiagnosed"
	- "SP-MDR diagnosed but not on treatment"
	- "SN-XDR on treatment"
- Used to compute:
	- "DALYs"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: Estimated number of years of life remaining

- Code name: `life_expectancy`
- Units/format: years
- Default value: 30
- Appears in the databook
- Used to compute:
	- "YLL rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: YLL rate

- Code name: `yll_rate`
- Units/format: Number of people
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `life_expectancy*:ddis`
- Depends on:
	- "Flow to Sink: Cumulative TB deaths over simulation"
	- "Estimated number of years of life remaining"
- Used to compute:
	- "DALYs"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

### Parameter: DALYs

- Code name: `daly_rate`
- Units/format: Number of people
- Default value: None
- Does not appear in the databook
- This parameter's value is computed by a function: `yll_rate + yld_rate`
- Depends on:
	- "YLD rate"
	- "YLL rate"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Interactions

### Interaction: Preference weighting for one population interacting with another

- Code name: `w_ctc`
- Used to compute:
	- "Force of infection experienced by population"

- Description: <ENTER DESCRIPTION>
- Data entry guidance: <ENTER GUIDANCE>

## Plots

### Plot: Population size

- Definition: `alive`
- Description: <ENTER DESCRIPTION>

### Plot: Latent infections

- Definition: `lt_inf`
- Description: <ENTER DESCRIPTION>

### Plot: Active TB

- Definition: `ac_inf`
- Description: <ENTER DESCRIPTION>

### Plot: Active DS-TB

- Definition: `ds_inf`
- Description: <ENTER DESCRIPTION>

### Plot: Active MDR-TB

- Definition: `mdr_inf`
- Description: <ENTER DESCRIPTION>

### Plot: Active XDR-TB

- Definition: `xdr_inf`
- Description: <ENTER DESCRIPTION>

### Plot: New active TB infections

- Definition: `{'New incident cases':['leu_act:flow','llu_act:flow', 'lex_act:flow', 'llx_act:flow', ]}`
- Description: <ENTER DESCRIPTION>

### Plot: Activated TB infections inc. relapse and immigration

- Definition: `{'Incident cases':['p_div:flow','n_div:flow']}`
- Description: <ENTER DESCRIPTION>

### Plot: Smear negative active TB

- Definition: `sn_inf`
- Description: <ENTER DESCRIPTION>

### Plot: Smear positive active TB

- Definition: `sp_inf`
- Description: <ENTER DESCRIPTION>

### Plot: Latent diagnoses

- Definition: `{'Latent diagnoses':['le_ntreat:flow', 'lx_ntreat:flow', 'll_ntreat:flow']}`
- Description: <ENTER DESCRIPTION>

### Plot: New active TB diagnoses

- Definition: `{'Active TB diagnoses':['pd_ndiag:flow','pm_ndiag:flow','px_ndiag:flow','nd_ndiag:flow','nm_ndiag:flow','nx_ndiag:flow']}`
- Description: <ENTER DESCRIPTION>

### Plot: Latent treatment

- Definition: `ltt_inf`
- Description: <ENTER DESCRIPTION>

### Plot: Active treatment

- Definition: `num_treat`
- Description: <ENTER DESCRIPTION>

### Plot: TB-related deaths

- Definition: `:ddis`
- Description: <ENTER DESCRIPTION>

### Plot: Latent prevalence

- Definition: `lt_prev`
- Description: <ENTER DESCRIPTION>

### Plot: Active prevalence

- Definition: `ac_prev`
- Description: <ENTER DESCRIPTION>

### Plot: DR prevalence

- Definition: `dr_prev`
- Description: <ENTER DESCRIPTION>

### Plot: New active SP-DS diagnoses

- Definition: `pd_ndiag:flow`
- Description: <ENTER DESCRIPTION>

### Plot: New active SP-MDR diagnoses

- Definition: `pm_ndiag:flow`
- Description: <ENTER DESCRIPTION>

### Plot: New active SP-XDR diagnoses

- Definition: `px_ndiag:flow`
- Description: <ENTER DESCRIPTION>

### Plot: New active SN-DS diagnoses

- Definition: `nd_ndiag:flow`
- Description: <ENTER DESCRIPTION>

### Plot: New active SN-MDR diagnoses

- Definition: `nm_ndiag:flow`
- Description: <ENTER DESCRIPTION>

### Plot: New active SN-XDR diagnoses

- Definition: `nx_ndiag:flow`
- Description: <ENTER DESCRIPTION>

### Plot: DS number initiating treatment

- Definition: `{'Active DS-TB treatment initiation':['pd_ntreat:flow','nd_ntreat:flow']}`
- Description: <ENTER DESCRIPTION>

### Plot: MDR number initiating treatment

- Definition: `{'Active MDR-TB treatment initiation':['pm_ntreat:flow','nm_ntreat:flow']}`
- Description: <ENTER DESCRIPTION>

### Plot: XDR number initiating treatment

- Definition: `{'Active XDR-TB treatment initiation':['px_ntreat:flow','nx_ntreat:flow']}`
- Description: <ENTER DESCRIPTION>

## Cascades

### Cascade: TB treatment (including recovered)

- Description: <ENTER DESCRIPTION>
- Stages:
	- Active TB
		- Estimated number of people with active TB
	- Diagnosed
		- Known active TB infections
	- Treated
		- Active TB cases on treatment

### Cascade: SP treatment

- Description: <ENTER DESCRIPTION>
- Stages:
	- Active SP-TB
		- Suspected SP infections
	- Diagnosed
		- Known SP-DS infections
		- Known SP-MDR infections
		- Known SP-XDR infections
	- Treated
		- SP-DS on treatment
		- SP-MDR on treatment
		- SP-XDR on treatment

### Cascade: SN treatment

- Description: <ENTER DESCRIPTION>
- Stages:
	- Active SN-TB
		- Suspected SN infections
	- Diagnosed
		- Known SN-DS infections
		- Known SN-MDR infections
		- Known SN-XDR infections
	- Treated
		- SN-DS on treatment
		- SN-MDR on treatment
		- SN-XDR on treatment

