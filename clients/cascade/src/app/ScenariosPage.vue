<!--
Scenarios page

Last update: 2018-09-09
-->

<template>
  <div class="SitePage">

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
      <div class="PageSection" v-if="hasGraphs">
        <div class="card">
          <!-- ### Start: plot controls ### -->
          <div class="calib-title">
            <help reflink="results-plots" label="Results"></help>
            <div>

              <b>Year: &nbsp;</b>
              <select v-model="endYear" @change="reloadGraphs(true)">
                <option v-for='year in projectionYears'>
                  {{ year }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;
              <b>Population: &nbsp;</b>
              <select v-model="activePop" @change="reloadGraphs(true)">
                <option v-for='pop in activePops'>
                  {{ pop }}
                </option>
              </select>&nbsp;&nbsp;&nbsp;
              <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
              <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
              <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>&nbsp;&nbsp;&nbsp;
              <button class="btn" @click="exportGraphs()">Export graphs</button>
              <button class="btn" @click="exportResults(serverDatastoreId)">Export data</button>
              <button v-if="false" class="btn btn-icon" @click="togglePlotControls()"><i class="ti-settings"></i></button> <!-- When popups are working: v-if="$globaltool=='tb'" -->
            </div>
          </div>
          <!-- ### End: plot controls ### -->


          <!-- ### Start: results and plot selectors ### -->
          <div class="calib-card-body">

            <!-- ### Start: plots ### -->
            <div class="calib-card-body">
              <div class="calib-graphs">

                <div class="other-graphs">
                  <div v-for="index in placeholders">
                    <div :id="'figcontainer'+index" style="display:flex; justify-content:flex-start; padding:5px; border:1px solid #ddd" v-show="showGraphDivs[index]">
                      <div :id="'fig'+index" class="calib-graph">
                        <!--mpld3 content goes here-->
                      </div>
                      <!--<div style="display:inline-block">-->
                      <!--<button class="btn __bw btn-icon" @click="maximize(index)" data-tooltip="Show legend"><i class="ti-menu-alt"></i></button>-->
                      <!--</div>-->
                    </div>
                  </div>
                </div>

                <!-- ### Start: Cascade plot ### -->
                <div class="featured-graphs">
                  <div :id="'fig0'">
                    <!-- mpld3 content goes here, no legend for it -->
                  </div>
                </div>
                <!-- ### End: Cascade plot ### -->

                <!-- ### Start: cascade table ### -->
                <div v-if="$globaltool=='cascade' && table" class="calib-tables">
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

              </div> <!-- ### End: calib-graphs ### -->
            </div>
            <!-- ### End: plots ### -->

            <!-- ### Start: dialogs ### -->
            <!--<div v-for="index in placeholders">-->
            <!--<div class="dialogs" :id="'legendcontainer'+index" style="display:flex" v-show="showLegendDivs[index]">-->
            <!--<dialog-drag :id="'DD'+index"-->
            <!--:key="index"-->
            <!--@close="minimize(index)"-->
            <!--:options="{top: openDialogs[index].options.top, left: openDialogs[index].options.left}">-->

            <!--<span slot='title' style="color:#fff">Legend</span>-->
            <!--<div :id="'legend'+index">-->
            <!--&lt;!&ndash; Legend content goes here&ndash;&gt;-->
            <!--</div>-->
            <!--</dialog-drag>-->
            <!--</div>-->
            <!--</div>-->
            <!-- ### End: dialogs ### -->


            <!-- ### Start: plot selectors ### -->
            <div class="plotopts-main" :class="{'plotopts-main--full': !showPlotControls}" v-if="showPlotControls">
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

          </div>  <!-- ### End: card body ### -->
        </div> <!-- ### End: results card ### -->

        

      </div> <!-- ### End: PageSection/hasGraphs ### -->

      <!-- ### Start: JS Cascade plot ### -->
      <div style="margin: 0 auto;">
        <multibar-view class="cascade"
          :scenariosData="jsonData"
          :colourScheme="jsonColors"
        />
      </div>
      <!-- ### End: Cascade plot ### -->
      
    </div> <!-- ### End: v-else project (results) ### -->


    <!-- ### Start: add scenarios modal ### -->
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
                 v-model="addEditModal.scenSummary.alloc_year"/><br>
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
    <!-- ### End: add scenarios modal ### -->

  </div>
</template>


<script>
  var filesaver = require('file-saver')
  import axios  from 'axios'
  import router from '@/router'
  import utils  from '@/js/utils'
  import graphs from '@/js/graphs'
  import shared from '@/js/shared'
  import rpcs   from '@/js/rpc-service'
  import status from '@/js/status-service'
  import MultibarView from './Vis/Multibar/MultibarView.vue'

  export default {
    name: 'ScenariosPage',

    components: {
      MultibarView,
    },

    data() {
      return {
        // Parameter and program set information
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions: [],
        progsetOptions: [],

        // Plotting data
        showPlotControls: false,
        hasGraphs: false,
        table: null,
        startYear: 0,
        endYear: 2018, // TEMP FOR DEMO
        activePop: "All",
        popOptions: [],
        plotOptions: [],
        yearOptions: [],
        serverDatastoreId: '',
        openDialogs: [],
        showGraphDivs: [], // These don't actually do anything, but they're here for future use
        showLegendDivs: [],
        mousex:-1,
        mousey:-1,
        figscale: 1.0,

        // Page-specific data
        scenSummaries: [],
        defaultBudgetScen: {},
        scenariosLoaded: false,
        addEditModal: {
          scenSummary: {},
          origName: '',
          mode: 'add'
        },

        // Cascade plot data
        jsonData: null,
        jsonColors: [],
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      hasPrograms()  { return utils.hasPrograms(this) },
      simStart()     { return utils.dataEnd(this) },
      simEnd()       { return utils.simEnd(this) },
      projectionYears()     { return utils.projectionYears(this) },
      activePops()   { return utils.activePops(this) },
      placeholders() { return graphs.placeholders(this, 1) },
    },

    created() {
      graphs.addListener(this)
      graphs.createDialogs(this)
      if ((this.$store.state.activeProject.project !== undefined) &&
        (this.$store.state.activeProject.project.hasData) &&
        (this.$store.state.activeProject.project.hasPrograms)) {
        console.log('created() called')
        this.startYear = this.simStart
        this.endYear = this.simEnd
        this.popOptions = this.activePops
        this.serverDatastoreId = this.$store.state.activeProject.project.id + ':scenario'
        this.getPlotOptions(this.$store.state.activeProject.project.id)
          .then(response => {
            this.updateSets()
              .then(response2 => {
                // The order of execution / completion of these doesn't matter.
                this.getScenSummaries()
                this.getDefaultBudgetScen()
                this.reloadGraphs(false)
              })
          })
      }
    },

    methods: {

      validateYears()                   { return utils.validateYears(this) },
      updateSets()                      { return shared.updateSets(this) },
      exportGraphs()                    { return shared.exportGraphs(this) },
      exportResults(datastoreID)        { return shared.exportResults(this, datastoreID) },
      scaleFigs(frac)                   { return graphs.scaleFigs(this, frac)},
      clearGraphs()                     { return graphs.clearGraphs(this) },
      togglePlotControls()              { return graphs.togglePlotControls(this) },
      getPlotOptions(project_id)        { return graphs.getPlotOptions(this, project_id) },
      makeGraphs(graphdata)             {
        this.jsonData = graphdata.jsondata
        this.jsonColors = graphdata.jsoncolors
        return graphs.makeGraphs(this, graphdata, '/scenarios')
      },
      reloadGraphs(showErr)             { return graphs.reloadGraphs(this, this.projectID, this.serverDatastoreId, showErr, false, true) }, // Set to calibration=false, plotbudget=true
      maximize(legend_id)               { return graphs.maximize(this, legend_id) },
      minimize(legend_id)               { return graphs.minimize(this, legend_id) },

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

      runScens() {
        console.log('runScens() called')
        this.validateYears()  // Make sure the start end years are in the right range.
        status.start(this)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries]) // Make sure they're saved first
          .then(response => {
            // Go to the server to get the results from the package set.
            rpcs.rpc('run_scenarios', [this.projectID, this.serverDatastoreId, this.plotOptions],
              {saveresults: false, tool:this.$globaltool, plotyear:this.endYear, pops:this.activePop})
              .then(response => {
                this.table = response.data.table
                this.makeGraphs(response.data)
                this.jsonData = response.data.jsondata
                this.jsonColors = response.data.jsoncolors
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

    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
