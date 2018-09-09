<!--
Scenarios page

Last update: 2018-09-06
-->

<template>
  <div>

    <div v-if="projectID ==''">
      <div style="font-style:italic">
        <p>No project is loaded.</p>
      </div>
    </div>

    <div v-else-if="!hasData">
      <div style="font-style:italic">
        <p>Data not yet uploaded for the project.  Please upload a databook in the Projects page.</p>
      </div>
    </div>

    <div v-else-if="!hasPrograms">
      <div style="font-style:italic">
        <p>Programs not yet uploaded for the project.  Please upload a program book in the Projects page.</p>
      </div>
    </div>

    <div v-else>

      <!-- ### Start: scenarios card ### -->
      <div class="card">
        <help reflink="scenarios" label="Define scenarios"></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th>Name</th>
            <th>Active</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="scenSummary in scenSummaries">
            <td>
              <b>{{ scenSummary.name }}</b>
            </td>
            <td style="text-align: center">
              <input type="checkbox" v-model="scenSummary.active"/>
            </td>
            <td style="white-space: nowrap">
              <button class="btn btn-icon" @click="editScen(scenSummary)" data-tooltip="Edit scenario"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyScen(scenSummary)" data-tooltip="Copy scenario"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteScen(scenSummary)" data-tooltip="Delete scenario"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn __green" :disabled="!scenariosLoaded" @click="runScens()">Run scenarios</button>
          <button class="btn __blue" :disabled="!scenariosLoaded" @click="addBudgetScenModal()">Add scenario</button>
        </div>
      </div>
      <!-- ### End: scenarios card ### -->

      <!-- ### Start: results card ### -->
      <div class="PageSection">
        <div class="card" v-if="hasGraphs">

          <!-- ### Start: plot controls ### -->
          <div class="calib-title">
            <help reflink="results-plots" label="Results"></help>
            <div>

              <b>Year: &nbsp;</b>
              <select v-model="endYear" @change="plotScenarios(true)">
                <option v-for='year in simYears'>
                  {{ year }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;
              <b>Population: &nbsp;</b>
              <select v-model="activePop" @change="plotScenarios(true)">
                <option v-for='pop in activePops'>
                  {{ pop }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;<!-- CASCADE-TB DIFFERENCE -->
              <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
              <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
              <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>
              &nbsp;&nbsp;&nbsp;
              <button class="btn" @click="exportGraphs(projectID)">Export graphs</button>
              <button class="btn" :disabled="true" @click="exportResults(serverDatastoreId)">Export data</button>
              <button v-if="$globaltool=='tb'" class="btn btn-icon" @click="toggleShowingPlotControls()"><i class="ti-settings"></i></button>

            </div>
          </div>
          <!-- ### End: plot controls ### -->

          <!-- ### Start: results and plot selectors ### -->
          <div class="calib-card-body">

            <!-- ### Start: plots ### -->
            <div class="calib-card-body">
              <div class="calib-graphs">
                <div class="featured-graphs">
                  <div :id="'fig0'">
                    <!-- mpld3 content goes here, no legend for it -->
                  </div>
                </div>
                <div class="other-graphs">
                  <div v-for="index in placeholders">
                    <div :id="'figcontainer'+index" style="display:flex; justify-content:flex-start; padding:5px; border:1px solid #ddd" v-show="showGraphDivs[index]">
                      <div :id="'fig'+index" class="calib-graph">
                        <!--mpld3 content goes here-->
                      </div>
                      <div style="display:inline-block">
                        <button class="btn __bw btn-icon" @click="maximize(index)" data-tooltip="Show legend"><i class="ti-menu-alt"></i></button>
                      </div>
                    </div>
                  </div>
                  <!-- ### End: plots ### -->

                  <!-- ### Start: cascade table ### -->
                  <div class="calib-tables" v-if="table" style="display:inline-block; padding-top:30px">
                    <h4>Cascade stage losses</h4>
                    <table class="table table-striped" style="text-align:right;">
                      <thead>
                      <tr>
                        <th></th>
                        <th v-for="label in table.collabels.slice(0, -1)">{{label}}</th>
                      </tr>
                      </thead>
                      <tbody>
                      <tr v-for="(label, index) in table.rowlabels">
                        <td>{{label}}</td>
                        <td v-for="text in table.text[index].slice(0, -1)">{{text}}</td>
                      </tr>
                      </tbody>
                    </table>
                  </div>
                  <!-- ### End: cascade table ### -->

                </div>
              </div>
            </div>
          </div>
          <!-- ### End: plots card ### -->

          <!-- CASCADE-TB DIFFERENCE -->
          <!-- ### Start: plot selectors ### -->
          <div class="plotopts-main" :class="{'plotopts-main--full': !areShowingPlotControls}" v-if="areShowingPlotControls">
            <div class="plotopts-params">
              <table class="table table-bordered table-hover table-striped" style="width: 100%">
                <thead>
                <tr>
                  <th>Plot</th>
                  <th>Active</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="item in plotOptions">
                  <td>
                    {{ item.plot_name }}
                  </td>
                  <td style="text-align: center">
                    <input type="checkbox" v-model="item.active"/>
                  </td>
                </tr>
                </tbody>
              </table>
            </div>
          </div>
          <!-- ### End: plots card ### -->

          <!-- ### Start: dialogs ### -->
          <div v-for="index in placeholders">
            <div class="dialogs" :id="'legendcontainer'+index" style="display:flex" v-show="showLegendDivs[index]">
              <dialog-drag
                :id="'DD'+index"
                :key="index"
                @close="minimize(index)"
                :options="{top: openDialogs[index].options.top, left: openDialogs[index].options.left}">

                <span slot='title' style="color:#fff">Legend</span>
                <div :id="'legend'+index">
                  <!-- Legend content goes here-->
                </div>
              </dialog-drag>
            </div>
          </div>
          <!-- ### End: dialogs ### -->

        </div>  <!-- ### End: hasGraphs ### -->
      </div> <!-- ### End: pageSection ### -->
      <!-- ### End: results section ### -->

    </div> <!-- ### End: v-else project ### -->


    <!-- START ADD-SCENARIO MODAL -->
    <modal name="add-budget-scen"
           height="auto"
           :scrollable="true"
           :width="500"
           :classes="['v--modal', 'vue-dialog']"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title" v-if="addEditModal.mode=='add'">
          Add scenario
        </div>
        <div class="dialog-c-title" v-else>
          Edit scenario
        </div>
        <div class="dialog-c-text">
          <b>Scenario name</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.scenSummary.name"/><br>
          <b>Parameter set</b><br>
          <select v-model="parsetOptions[0]">
            <option v-for='parset in parsetOptions'>
              {{ parset }}
            </option>
          </select><br><br>
          <b>Program set</b><br>
          <select v-model="progsetOptions[0]">
            <option v-for='progset in progsetOptions'>
              {{ progset }}
            </option>
          </select><br><br>
          <b>Budget year</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.scenSummary.start_year"/><br>
          <table class="table table-bordered table-hover table-striped" style="width: 100%">
            <thead>
            <tr>
              <th>Program</th>
              <th>Budget</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="item in addEditModal.scenSummary.alloc">
              <td>
                {{ item[2] }}
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       v-model="item[1]"
                       style="text-align: right"
                />
              </td>
            </tr>
            </tbody>
          </table>
        </div>
        <div style="text-align:justify">
          <button @click="addBudgetScen()" class='btn __green' style="display:inline-block">
            Save scenario
          </button>
          <button @click="$modal.hide('add-budget-scen')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>
    </modal>
    <!-- END ADD-SCENARIO MODAL -->

  </div>

</template>


<script>
  import axios from 'axios'
  let filesaver = require('file-saver')
  import utils from '@/js/utils'
  import rpcs from '@/js/rpc-service'
  import status from '@/js/status-service'
  import router from '@/router'

  export default {
    name: 'ScenariosPage',

    data() {
      return {
        scenSummaries: [],
        defaultBudgetScen: {},
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
        startYear: 0,
        endYear: 0,
        areShowingPlotControls: false,
        plotOptions: [],
        scenariosLoaded: false,
        table: null,
        activePop: "All",
        endYear: 0,
        addEditModal: {
          scenSummary: {},
          origName: '',
          mode: 'add'
        },
        figscale: 1.0,
        hasGraphs: false,
        serverDatastoreId: '',
        openDialogs: [],
        showGraphDivs: [], // These don't actually do anything, but they force binding to happen, otherwise the page doesn't update...argh!!!!
        showLegendDivs: [],
        mousex:-1,
        mousey:-1,
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      hasPrograms()  { return utils.hasPrograms(this) },
      simStart()     { return utils.simStart(this) },
      simEnd()       { return utils.simEnd(this) },
      simYears()     { return utils.simYears(this) },
      activePops()   { return utils.activePops(this) },
      placeholders() { return utils.placeholders(this, 1) },
    },

    created() {
      utils.addListener(this)
      utils.createDialogs(this)
      if (this.$store.state.currentUser.displayname === undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      }
      else if ((this.$store.state.activeProject.project !== undefined) &&
        (this.$store.state.activeProject.project.hasData) &&
        (this.$store.state.activeProject.project.hasPrograms)) {
        console.log('created() called')
        this.startYear = this.simStart
        this.endYear = this.simEnd
        this.popOptions = this.activePops
        this.serverDatastoreId = this.$store.state.activeProject.project.id + ':scenarios'
        this.getPlotOptions()
          .then(response => {
            this.updateSets()
              .then(response2 => {
                // The order of execution / completion of these doesn't matter.
                this.getScenSummaries()
                this.getDefaultBudgetScen()
                this.plotScenarios(false)
              })
          })
      }
    },

    methods: {

      maximize(id)    { return utils.maximize(this, id)},
      minimize(id)    { return utils.minimize(this, id)},

      getPlotOptions()            { return utils.getPlotOptions(this) },
      clearGraphs()               { return utils.clearGraphs() },
      makeGraphs(graphs, legends) { return utils.makeGraphs(this, graphs, legends) },
      exportGraphs()              { return utils.exportGraphs(this) },
      exportResults(datastoreID)  { return utils.exportResults(this, datastoreID) },

      notImplemented() {
        status.fail(this, 'Sorry, this feature is not implemented')
      },

      scaleFigs(frac) {
        this.figscale = this.figscale*frac;
        if (frac === 1.0) {
          frac = 1.0/this.figscale
          this.figscale = 1.0
        }
        return utils.scaleFigs(frac)
      },

      clipValidateYearInput() {
        if (this.startYear > this.simEnd) {
          this.startYear = this.simEnd
        }
        else if (this.startYear < this.simStart) {
          this.startYear = this.simStart
        }
        if (this.endYear > this.simEnd) {
          this.endYear = this.simEnd
        }
        else if (this.endYear < this.simStart) {
          this.endYear = this.simStart
        }
      },

      updateSets() {
        return new Promise((resolve, reject) => {
          console.log('updateSets() called')
          rpcs.rpc('get_parset_info', [this.projectID]) // Get the current user's parsets from the server.

            .then(response => {
              this.parsetOptions = response.data // Set the scenarios to what we received.
              if (this.parsetOptions.indexOf(this.activeParset) === -1) {
                console.log('Parameter set ' + this.activeParset + ' no longer found')
                this.activeParset = this.parsetOptions[0] // If the active parset no longer exists in the array, reset it
              } else {
                console.log('Parameter set ' + this.activeParset + ' still found')
              }

              this.newParsetName = this.activeParset // WARNING, KLUDGY
              console.log('Parset options: ' + this.parsetOptions)
              console.log('Active parset: ' + this.activeParset)
              rpcs.rpc('get_progset_info', [this.projectID]) // Get the current user's progsets from the server.
                .then(response => {
                  this.progsetOptions = response.data // Set the scenarios to what we received.
                  if (this.progsetOptions.indexOf(this.activeProgset) === -1) {
                    console.log('Program set ' + this.activeProgset + ' no longer found')
                    this.activeProgset = this.progsetOptions[0] // If the active parset no longer exists in the array, reset it
                  } else {
                    console.log('Program set ' + this.activeProgset + ' still found')
                  }
                  this.newProgsetName = this.activeProgset // WARNING, KLUDGY
                  console.log('Progset options: ' + this.progsetOptions)
                  console.log('Active progset: ' + this.activeProgset)
                  resolve(response)
                })
                .catch(error => {
                  status.fail(this, 'Could not get progset info', error)
                  reject(error)
                })
            })
            .catch(error => {
              status.fail(this, 'Could not get parset info', error)
              reject(error)
            })
        })
          .catch(error => {
            status.fail(this, 'Could not get parset info', error)
            reject(error)
          })
      },

      getDefaultBudgetScen() {
        console.log('getDefaultBudgetScen() called')
        rpcs.rpc('get_default_budget_scen', [this.projectID])
          .then(response => {
            this.defaultBudgetScen = response.data // Set the scenario to what we received.
            console.log('This is the default:')
            console.log(this.defaultBudgetScen);
          })
          .catch(error => {
            status.fail(this, 'Could not get default budget scenario', error)
          })
      },

      getScenSummaries() {
        console.log('getScenSummaries() called')
        status.start(this)
        rpcs.rpc('get_scen_info', [this.projectID])
          .then(response => {
            this.scenSummaries = response.data // Set the scenarios to what we received.
            console.log('Scenario summaries:')
            console.log(this.scenSummaries)
            this.scenariosLoaded = true
            status.succeed(this, 'Scenarios loaded')
          })
          .catch(error => {
            status.fail(this, 'Could not get scenarios', error)
          })
      },

      setScenSummaries() {
        console.log('setScenSummaries() called')
        status.start(this)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenarios saved')
          })
          .catch(error => {
            status.fail(this, 'Could not save scenarios', error)
          })
      },

      addBudgetScenModal() {
        // Open a model dialog for creating a new project
        console.log('addBudgetScenModal() called');
        rpcs.rpc('get_default_budget_scen', [this.projectID])
          .then(response => {
            this.defaultBudgetScen = response.data // Set the scenario to what we received.
            this.addEditModal.scenSummary = _.cloneDeep(this.defaultBudgetScen)
            this.addEditModal.origName = this.addEditModal.scenSummary.name
            this.addEditModal.mode = 'add'
            this.$modal.show('add-budget-scen');
            console.log(this.defaultBudgetScen)
          })
          .catch(error => {
            status.fail(this, 'Could not open add scenario modal', error)
          })
      },

      addBudgetScen() {
        console.log('addBudgetScen() called')
        this.$modal.hide('add-budget-scen')
        status.start(this)
        let newScen = _.cloneDeep(this.addEditModal.scenSummary) // Get the new scenario summary from the modal.
        let scenNames = [] // Get the list of all of the current scenario names.
        this.scenSummaries.forEach(scenSum => {
          scenNames.push(scenSum.name)
        })
        if (this.addEditModal.mode == 'edit') { // If we are editing an existing scenario...
          let index = scenNames.indexOf(this.addEditModal.origName) // Get the index of the original (pre-edited) name
          if (index > -1) {
            this.scenSummaries[index].name = newScen.name  // hack to make sure Vue table updated
            this.scenSummaries[index] = newScen
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }
        }
        else { // Else (we are adding a new scenario)...
          newScen.name = utils.getUniqueName(newScen.name, scenNames)
          this.scenSummaries.push(newScen)
        }
        console.log(newScen)
        console.log(this.scenSummaries)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenario added')
          })
          .catch(error => {
            status.fail(this, 'Could not add scenario', error)
          })
      },

      editScen(scenSummary) {
        // Open a model dialog for creating a new project
        console.log('editScen() called');
        this.defaultBudgetScen = scenSummary
        console.log('defaultBudgetScen')
        console.log(this.defaultBudgetScen)
        this.addEditModal.scenSummary = _.cloneDeep(this.defaultBudgetScen)
        this.addEditModal.origName = this.addEditModal.scenSummary.name
        this.addEditModal.mode = 'edit'
        this.$modal.show('add-budget-scen');
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        status.start(this)
        var newScen = _.cloneDeep(scenSummary);
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = utils.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenario copied')
          })
          .catch(error => {
            status.fail(this, 'Could not copy scenario', error)
          })
      },

      deleteScen(scenSummary) {
        console.log('deleteScen() called')
        status.start(this)
        for(var i = 0; i< this.scenSummaries.length; i++) {
          if(this.scenSummaries[i].name === scenSummary.name) {
            this.scenSummaries.splice(i, 1);
          }
        }
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenario deleted')
          })
          .catch(error => {
            status.fail(this, 'Could not delete scenario', error)
          })
      },

      toggleShowingPlotControls() {
        this.areShowingPlotControls = !this.areShowingPlotControls
      },

      runScens() {
        console.log('runScens() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries]) // Make sure they're saved first
          .then(response => {
            // Go to the server to get the results from the package set.
            rpcs.rpc('run_scenarios', [this.projectID, this.serverDatastoreId, this.plotOptions],
              {saveresults: false, tool:this.$globaltool, plotyear:this.endYear, pops:this.activePop})
              .then(response => {
                this.table = response.data.table
                this.makeGraphs(response.data.graphs, response.data.legends)
                status.succeed(this, '') // Success message in graphs function
              })
              .catch(error => {
                status.fail(this, 'Could not run scenarios', error)
              })
          })
          .catch(error => {
            status.fail(this, 'Could not set scenarios', error)
          })
      },

      plotScenarios(showNoCacheError) {
        console.log('plotScens() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this)
        this.$Progress.start(2000)  // restart just the progress bar, and make it slower
        // Make sure they're saved first
        rpcs.rpc('plot_results_cache_entry', [this.projectID, this.serverDatastoreId, this.plotOptions],
          {tool:this.$globaltool, plotyear:this.endYear, pops:this.activePop})
          .then(response => {
            this.makeGraphs(response.data.graphs, response.data.legends)
            this.table = response.data.table
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            if (showNoCacheError) {
              status.fail(this, 'Could not make graphs', error)
            }
            else {
              status.succeed(this, '')  // Silently stop progress bar and spinner.
            }
          })
      },
    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
