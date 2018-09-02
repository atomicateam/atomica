<!--
Scenarios Page

Last update: 2018-08-22
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

    <div v-else>
      <div class="card">
        <help reflink="scenarios" label="Define scenarios"></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th>Name</th>
            <th>Active?</th>
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
              <button class="btn btn-icon" @click="editScen(scenSummary)"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyScen(scenSummary)"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteScen(scenSummary)"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn __green" :disabled="!scenariosLoaded" @click="runScens()">Run scenarios</button>
          <button class="btn __blue" :disabled="!scenariosLoaded" @click="addBudgetScenModal()">Add scenario</button>
        </div>
      </div>

      <!-- ### Start: results card ### -->
      <div class="card full-width-card">
        <!-- ### Start: plot controls ### -->
        <div class="calib-title">
          <help reflink="results-plots" label="Results"></help>
          <div>
            <!--<b>Start year: &nbsp;</b>-->
            <!--<input type="text"-->
            <!--class="txbox"-->
            <!--v-model="startYear"-->
            <!--style="display: inline-block; width:70px"/>-->
            <!--&nbsp;&nbsp;&nbsp;-->
            <b>Year: &nbsp;</b>
            <select v-model="endYear" v-on:change="manualCalibration(projectID)">
              <option v-for='year in simYears'>
                {{ year }}
              </option>
            </select>
            &nbsp;&nbsp;&nbsp;
            <b>Population: &nbsp;</b>
            <select v-model="activePop" v-on:change="manualCalibration(projectID)">
              <option v-for='pop in activePops'>
                {{ pop }}
              </option>
            </select>
            &nbsp;&nbsp;&nbsp;<!-- CASCADE-TB DIFFERENCE -->
            <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
            <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
            <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>
            &nbsp;&nbsp;&nbsp;
            <button class="btn" @click="exportGraphs()">Export plots</button>
            <button class="btn" @click="exportResults(projectID)">Export data</button>
            <button class="btn btn-icon" @click="toggleShowingPlotControls()"><i class="ti-settings"></i></button>

          </div>
        </div>
        <!-- ### End: plot controls ### -->

        <!-- ### Start: results and plot selectors ### -->
        <div class="calib-card-body">

          <!-- ### Start: plots ### -->
          <div class="calib-graphs">
            <div class="featured-graphs">
              <div :id="'fig0'">
                <!--mpld3 content goes here-->
              </div>
            </div>
            <div class="other-graphs">
              <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
                <!--mpld3 content goes here-->
              </div>
            </div>
          </div>
          <!-- ### End: plots ### -->

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
          <!-- ### End: plot selectors ### -->
        </div>
        <!-- ### End: results and plot selectors ### -->
      </div>
      <!-- ### End: results card ### -->


      <modal name="add-budget-scen"
             height="auto"
             :scrollable="true"
             :width="900"
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
            Scenario name:<br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.scenSummary.name"/><br>
            Parameter set:<br>
            <select v-model="parsetOptions[0]">
              <option v-for='parset in parsetOptions'>
                {{ parset }}
              </option>
            </select><br><br>
            Program set:<br>
            <select v-model="progsetOptions[0]">
              <option v-for='progset in progsetOptions'>
                {{ progset }}
              </option>
            </select><br><br>
            Budget year:<br>
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

    </div>
  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import utils from '@/services/utils'
  import rpcs from '@/services/rpc-service'
  import taskservice from '@/services/task-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import help from '@/app/HelpLink.vue'

  export default {
    name: 'ScenariosPage',

    components: {
      help
    },

    data() {
      return {
        response: 'no response',
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
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      simStart()     { return utils.simStart(this) },
      simEnd()       { return utils.simEnd(this) },
      simYears()     { return utils.simYears(this) },
      activePops()   { return utils.activePops(this) },
      placeholders() { return utils.placeholders() },
    },

    created() {
      if (this.$store.state.currentUser.displayname == undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      }
      else if ((this.$store.state.activeProject.project != undefined) &&
        (this.$store.state.activeProject.project.hasData) ) {
        console.log('created() called')
        this.startYear = this.simStart
        this.endYear = this.simEnd
        this.popOptions = this.activePops
        utils.sleep(1)  // used so that spinners will come up by callback func
          .then(response => {
            this.getScenSummaries()
            this.getDefaultBudgetScen()
            this.updateSets()
            this.getPlotOptions()
          })
      }
    },

    methods: {

      getPlotOptions()          { return utils.getPlotOptions(this) },
      clearGraphs()             { this.table = null; return utils.clearGraphs() },
      makeGraphs(graphdata)     { return utils.makeGraphs(this, graphdata) },
      exportGraphs()            { return utils.exportGraphs(this) },
      exportResults(project_id) { return utils.exportResults(this, project_id) },

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
              })
              .catch(error => {
                status.failurePopup(this, 'Could not get progset info: ' + error.message)
              })
          })
          .catch(error => {
            status.failurePopup(this, 'Could not get parset info: ' + error.message)
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
            status.failurePopup(this, 'Could not get default budget scenario: ' + error.message)
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
            this.response = 'There was an error: ' + error.message // Pull out the error message.
            status.fail(this, 'Could not get scenarios: ' + error.message)
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
            status.fail(this, 'Could not save scenarios: ' + error.message)
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
            this.response = 'There was an error: ' + error.message // Pull out the error message.
            status.failurePopup(this, 'Could not open add scenario modal: '  + error.message)
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
            status.fail(this, 'Could not add scenario: ' + error.message)
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
        var newScen = _.cloneDeep(scenSummary); // You've got to be kidding me, buster
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
            status.fail(this, 'Could not copy scenario: ' + error.message)
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
            status.fail(this, 'Could not delete scenario: ' + error.message)
          })
      },

      toggleShowingPlotControls() {
        this.areShowingPlotControls = !this.areShowingPlotControls
      },

      runScens() {
        console.log('runScens() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this)
        // Make sure they're saved first
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then(response => {
            // Go to the server to get the results from the package set.
            rpcs.rpc('run_scenarios', [this.projectID, this.plotOptions],
              {saveresults: false, tool:'tb', plotyear:this.endYear, pops:this.activePop}) // CASCADE-TB DIFFERENCE
              .then(response => {
                this.makeGraphs(response.data.graphs)
//                this.table = response.data.table // CASCADE-TB DIFFERENCE
                status.succeed(this, 'Graphs created')
              })
              .catch(error => {
                console.log('There was an error: ' + error.message) // Pull out the error message.
                status.fail(this, 'Could not run scenarios: ' + error.message) // Indicate failure.
              })
          })
          .catch(error => {
            this.response = 'There was an error: ' + error.message
            status.fail(this, 'Could not set scenarios: ' + error.message)
          })
      },

      plotScenarios() {
        console.log('plotScens() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this)
        this.$Progress.start(2000)  // restart just the progress bar, and make it slower
        // Make sure they're saved first
        rpcs.rpc('plot_scenarios', [this.projectID, this.plotOptions],
          {tool:'tb', plotyear:this.endYear}) // CASCADE-TB DIFFERENCE
          .then(response => {
            this.makeGraphs(response.data.graphs)
//            this.table = response.data.table // CASCADE-TB DIFFERENCE
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
            this.servererror = error.message // Set the server error.
            status.fail(this, 'Could not make graphs') // Indicate failure.
          })
      },
    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

