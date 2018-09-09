<!--
Optimizations Page

Last update: 2018-09-06
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

      <!-- ### Start: optimizations card ### -->
      <div class="card">
        <help reflink="optimizations" label="Define optimizations"></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="optimSummary in optimSummaries">
            <td>
              <b>{{ optimSummary.name }}</b>
            </td>
            <td>
              {{ statusFormatStr(optimSummary) }}
              {{ timeFormatStr(optimSummary) }}
            </td>
            <td style="white-space: nowrap">
              <button class="btn __green" :disabled="!canRunTask(optimSummary)" @click="runOptim(optimSummary, 3600)">Run</button>
              <button class="btn __green" :disabled="!canPlotResults(optimSummary)" @click="reloadGraphs(optimSummary.serverDatastoreId, true)">Plot results</button>
              <button class="btn" :disabled="!canRunTask(optimSummary)" @click="runOptim(optimSummary, 5)">Test run</button>
              <button class="btn __red" :disabled="!canCancelTask(optimSummary)" @click="clearTask(optimSummary)">Clear run</button>
              <button class="btn btn-icon" @click="editOptim(optimSummary)" data-tooltip="Edit optimization"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyOptim(optimSummary)" data-tooltip="Copy optimization"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteOptim(optimSummary)" data-tooltip="Delete optimization"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn" @click="addOptimModal()">Add optimization</button>
        </div>
      </div>
      <!-- ### End: optimizations card ### -->


      <!-- ### Start: results card ### -->
      <div class="PageSection" v-if="hasGraphs">
        <div class="card">
          <!-- ### Start: plot controls ### -->
          <div class="calib-title">
            <help reflink="results-plots" label="Results"></help>
            <div>

              <b>Year: &nbsp;</b>
              <select v-model="endYear" @change="reloadGraphs(optimSummary.serverDatastoreId, true)">
                <option v-for='year in simYears'>
                  {{ year }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;
              <b>Population: &nbsp;</b>
              <select v-model="activePop" @change="reloadGraphs(optimSummary.serverDatastoreId, true)">
                <option v-for='pop in activePops'>
                  {{ pop }}
                </option>
              </select>
              <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
              <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
              <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>
              &nbsp;&nbsp;&nbsp;
              <button class="btn" @click="exportGraphs(projectID)">Export graphs</button>
              <button class="btn" @click="exportResults(serverDatastoreId)">Export data</button>
              <button v-if="false" class="btn btn-icon" @click="togglePlotControls()"><i class="ti-settings"></i></button> <!-- When popups are working: v-if="this.$globaltool=='tb'" -->
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
                </div>

              </div> <!-- ### End: calib-graphs ### -->
            </div>
            <!-- ### End: plots ### -->

            <!-- ### Start: dialogs ### -->
            <div v-for="index in placeholders">
              <div class="dialogs" :id="'legendcontainer'+index" style="display:flex" v-show="showLegendDivs[index]">
                <dialog-drag :id="'DD'+index"
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
    </div> <!-- ### End: v-else project (results) ### -->


    <!-- ### Start: add optimization modal ### -->
    <modal name="add-optim"
           height="auto"
           :scrollable="true"
           :width="800"
           :classes="['v--modal', 'vue-dialog']"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title" v-if="addEditDialogMode=='add'">
          Add optimization
        </div>
        <div class="dialog-c-title" v-else>
          Edit optimization
        </div>
        <div class="dialog-c-text">
          <div style="display:inline-block">
            <b>Optimization name</b><br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.name"/><br>
            <b>Parameter set</b><br>
            <select v-model="parsetOptions[0]">
              <option v-for='parset in parsetOptions'>
                {{ parset }}
              </option>
            </select><br><br>
            <b>Start year</b><br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.start_year"/><br>
            <b>End year</b><br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.end_year"/><br>
            <b>Budget factor</b><br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.budget_factor"/><br>
          </div>
          <br>
          <b>Objective weights</b><br>
          <table class="table table-bordered table-hover table-striped" style="width: 100%">
            <thead>
            <tr>
              <th>Objective</th>
              <th>Weight</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="(val,key) in modalOptim.objective_labels">
              <td>
                {{ modalOptim.objective_labels[key] }}
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       v-model="modalOptim.objective_weights[key]"/>
              </td>
            </tr>
            </tbody>
          </table>
          <b>Relative spending constraints</b><br>
          <table class="table table-bordered table-hover table-striped" style="width: 100%">
            <thead>
            <tr>
              <th>Program</th>
              <th>Minimum</th>
              <th>Maximum</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="(val,key) in modalOptim.prog_spending">
              <td>
                {{ modalOptim.prog_spending[key].label }}
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       v-model="modalOptim.prog_spending[key].min"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       v-model="modalOptim.prog_spending[key].max"/>
              </td>
            </tr>
            </tbody>
          </table>
        </div>
        <div style="text-align:justify">
          <button @click="saveOptim()" class='btn __green' style="display:inline-block">
            Save optimization
          </button>
          <button @click="cancelOptim()" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>
    </modal>
    <!-- ### End: add optimization modal ### -->

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

  export default {
    name: 'OptimizationsPage',

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
        optimSummaries: [],
        optimsLoaded: false,
        defaultOptim: {},
        modalOptim: {},
        objectiveOptions: [],
        displayResultName: '',
        addEditDialogMode: 'add',  // or 'edit'
        addEditDialogOldName: '',
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
        this.serverDatastoreId = this.$store.state.activeProject.project.id + ':optimization'
        this.getPlotOptions(this.$store.state.activeProject.project.id)
          .then(response => {
            this.updateSets()
              .then(response2 => {
                this.getDefaultOptim()
                  .then(response3 => {
                    // Order doesn't matter for these.
                    this.getOptimSummaries()
                    this.resetModal()
                  })
              })
          })
      }
    },

    methods: {

      validateYears()                   { return utils.validateYears(this) },
      updateSets()                      { return shared.updateSets(this) },
      exportGraphs(datastoreID)         { return shared.exportGraphs(this, datastoreID) },
      exportResults(datastoreID)        { return shared.exportResults(this, datastoreID) },
      scaleFigs(frac)                   { return graphs.scaleFigs(this, frac)},
      clearGraphs()                     { return graphs.clearGraphs(this) },
      togglePlotControls()              { return graphs.togglePlotControls(this) },
      getPlotOptions(project_id)        { return graphs.getPlotOptions(this, project_id) },
      makeGraphs(graphdata)             { return graphs.makeGraphs(this, graphdata) },
      reloadGraphs(cache_id, showErr)   { return graphs.reloadGraphs(this, this.projectID, cache_id, showErr, false, true) }, // Set to calibration=false, plotbudget=True
      maximize(legend_id)               { return graphs.maximize(this, legend_id) },
      minimize(legend_id)               { return graphs.minimize(this, legend_id) },

      statusFormatStr(optimSummary) {
        if      (optimSummary.status === 'not started') {return ''}
        else if (optimSummary.status === 'queued')      {return 'Initializing... '} // + this.timeFormatStr(optimSummary.pendingTime)
        else if (optimSummary.status === 'started')     {return 'Running for '} // + this.timeFormatStr(optimSummary.executionTime)
        else if (optimSummary.status === 'completed')   {return 'Completed after '} // + this.timeFormatStr(optimSummary.executionTime)
        else                                            {return ''}
      },

      timeFormatStr(optimSummary) {
        let rawValue = ''
        let is_queued = (optimSummary.status === 'queued')
        let is_executing = ((optimSummary.status === 'started') || (optimSummary.status === 'completed'))
        if      (is_queued)    {rawValue = optimSummary.pendingTime}
        else if (is_executing) {rawValue = optimSummary.executionTime}
        else                   {return ''}
        if (rawValue === '--') {
          return '--'
        } else {
          let numSecs = Number(rawValue).toFixed()
          let numHours = Math.floor(numSecs / 3600)
          numSecs -= numHours * 3600
          let numMins = Math.floor(numSecs / 60)
          numSecs -= numMins * 60
          let output = _.padStart(numHours.toString(), 2, '0') + ':' + _.padStart(numMins.toString(), 2, '0') + ':' + _.padStart(numSecs.toString(), 2, '0')
          return output
        }
      },

      canRunTask(optimSummary)     { return ((optimSummary.status === 'not started') || (optimSummary.status === 'completed')) },
      canCancelTask(optimSummary)  { return  (optimSummary.status !== 'not started') },
      canPlotResults(optimSummary) { return  (optimSummary.status === 'completed') },

      needToPoll(optimSummary) {
        let routePath = (this.$route.path === '/optimizations')
        let optimState = true; // ((optimSummary.status === 'queued') || (optimSummary.status === 'started')) // CK: this needs to be given a delay to work
        return (routePath && optimState)
      },

      getOptimTaskState(optimSummary) {
        console.log('getOptimTaskState() called for with: ' + optimSummary.status)
        let statusStr = '';

        // Check the status of the task.
        rpcs.rpc('check_task', [optimSummary.serverDatastoreId])
          .then(result => {
            statusStr = result.data.task.status
            optimSummary.status = statusStr
            optimSummary.pendingTime = result.data.pendingTime
            optimSummary.executionTime = result.data.executionTime
          })
          .catch(error => {
            optimSummary.status = 'not started'
            optimSummary.pendingTime = '--'
            optimSummary.executionTime = '--'
          })
      },

      pollAllTaskStates() {
        console.log('Do a task poll...');
        this.optimSummaries.forEach(optimSum => { // For each of the optimization summaries...
          if ((optimSum.status !== 'not started') && (optimSum.status !== 'completed')) { // If there is a valid task launched, check it.
            this.getOptimTaskState(optimSum)
          }
        });
        this.optimSummaries.push(this.optimSummaries[0]); // Hack to get the Vue display of optimSummaries to update
        this.optimSummaries.pop();
        let waitingtime = 1 // Sleep waitingtime seconds
        utils.sleep(waitingtime * 1000)
          .then(response => {
            if (this.needToPoll()) { // Only if we are still in the optimizations page, call ourselves.
              this.pollAllTaskStates()
            }
          })
      },

      clearTask(optimSummary) {
        let datastoreId = optimSummary.serverDatastoreId  // hack because this gets overwritten soon by caller
        console.log('clearTask() called for '+this.currentOptim)
        rpcs.rpc('delete_task', [optimSummary.serverDatastoreId])
          .then(response => {
            this.getOptimTaskState(optimSummary) // Get the task state for the optimization.
            rpcs.rpc('delete_results_cache_entry', [datastoreId]) // Delete cached result.
          })
        this.hasGraphs = false
      },

      getDefaultOptim() {
        return new Promise((resolve, reject) => {
          console.log('getDefaultOptim() called')
          rpcs.rpc('get_default_optim', [this.projectID, this.$globaltool])
            .then(response => {
              this.defaultOptim = response.data // Set the optimization to what we received.
              console.log('This is the default:')
              console.log(this.defaultOptim)
              resolve(response)
            })
            .catch(error => {
              status.fail(this, 'Could not get default optimization', error)
              reject(error)
            })
        })
      },

      getOptimSummaries() {
        console.log('getOptimSummaries() called')
        status.start(this)
        rpcs.rpc('get_optim_info', [this.projectID]) // Get the current project's optimization summaries from the server.
          .then(response => {
            this.optimSummaries = response.data // Set the optimizations to what we received.

            // For each of the optimization summaries...
            this.optimSummaries.forEach(optimSum => {
              // Build a task and results cache ID from the project's hex UID and the optimization name.
              optimSum.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + optimSum.name

              // Set the status to 'not started' by default, and the pending and execution
              // times to '--'.
              optimSum.status = 'not started'
              optimSum.pendingTime = '--'
              optimSum.executionTime = '--'

              // Get the task state for the optimization.
              this.getOptimTaskState(optimSum)
            })
            this.pollAllTaskStates() // Start polling of tasks states.
            this.optimsLoaded = true
            status.succeed(this, 'Optimizations loaded')
          })
          .catch(error => {
            status.fail(this, 'Could not load optimizations', error)
          })
      },

      setOptimSummaries() {
        console.log('setOptimSummaries() called')
        status.start(this)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimizations saved')
          })
          .catch(error => {
            status.fail(this, 'Could not save optimizations', error)
          })
      },

      addOptimModal() { // Open a model dialog for creating a new project
        console.log('addOptimModal() called');
        this.resetModal()
        rpcs.rpc('get_default_optim', [this.projectID])
          .then(response => {
            this.defaultOptim = response.data // Set the optimization to what we received.
            this.addEditDialogMode = 'add'
            this.addEditDialogOldName = this.modalOptim.name
            this.$modal.show('add-optim');
            console.log(this.defaultOptim)
          })
      },

      saveOptim() {
        console.log('saveOptim() called')
        this.$modal.hide('add-optim')
        status.start(this)
        this.endYear = this.modalOptim.end_year
        let newOptim = _.cloneDeep(this.modalOptim) // Get the new optimization summary from the modal.
        let optimNames = [] // Get the list of all of the current optimization names.
        this.optimSummaries.forEach(optimSum => {
          optimNames.push(optimSum.name)
        })
        if (this.addEditDialogMode === 'edit') { // If we are editing an existing optimization...
          let index = optimNames.indexOf(this.addEditDialogOldName) // Get the index of the original (pre-edited) name
          if (index > -1) {
            this.optimSummaries[index].name = newOptim.name  // hack to make sure Vue table updated            
            this.optimSummaries[index] = newOptim
            if (newOptim.name != this.addEditDialogOldName) {  // If we've renamed an optimization
              if (newOptim.status != 'not started') { // Clear the present task.
                this.clearTask(newOptim)  // Clear the task from the server. 
              }

              // Set a new server DataStore ID.
              newOptim.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name

              this.getOptimTaskState(newOptim)
            }
          }
          else {
            status.fail(this, 'Could not find optimization "' + this.addEditDialogOldName + '" to edit')
          }
        }
        else { // Else (we are adding a new optimization)...
          newOptim.name = utils.getUniqueName(newOptim.name, optimNames)
          newOptim.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name
          this.optimSummaries.push(newOptim)
          this.getOptimTaskState(newOptim)
        }

        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization added')
            this.resetModal()
          })
          .catch(error => {
            status.fail(this, 'Could not add optimization', error)
          })
      },

      cancelOptim() {
        this.$modal.hide('add-optim')
        this.resetModal()
      },

      resetModal() {
        console.log('resetModal() called')
        this.modalOptim = _.cloneDeep(this.defaultOptim)
        console.log(this.modalOptim)
      },

      editOptim(optimSummary) {
        // Open a model dialog for creating a new project
        console.log('editOptim() called');
        this.modalOptim = _.cloneDeep(optimSummary)
        console.log('defaultOptim', this.defaultOptim.obj)
        this.addEditDialogMode = 'edit'
        this.addEditDialogOldName = this.modalOptim.name
        this.$modal.show('add-optim');
      },

      copyOptim(optimSummary) {
        console.log('copyOptim() called')
        status.start(this)
        var newOptim = _.cloneDeep(optimSummary)
        var otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        })
        newOptim.name = utils.getUniqueName(newOptim.name, otherNames)
        newOptim.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name
        this.optimSummaries.push(newOptim)
        this.getOptimTaskState(newOptim)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Opimization copied')
          })
          .catch(error => {
            status.fail(this, 'Could not copy optimization')
          })
      },

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        status.start(this)
        if (optimSummary.status != 'not started') {
          this.clearTask(optimSummary)  // Clear the task from the server.
        }
        for(var i = 0; i< this.optimSummaries.length; i++) {
          if(this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then(response => {
            status.succeed(this, 'Optimization deleted')
          })
          .catch(error => {
            status.fail(this, 'Could not delete optimization', error)
          })
      },

      runOptim(optimSummary, maxtime) {
        console.log('runOptim() called for '+this.currentOptim + ' for time: ' + maxtime)
        this.validateYears()  // Make sure the start end years are in the right range.
        status.start(this)
        var RPCname = ''
        if (this.$globaltool === 'cascade') {
          RPCname = 'run_cascade_optimization'
        }
        if (this.$globaltool === 'tb') {
          RPCname = 'run_tb_optimization'
        }
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries]) // Make sure they're saved first
          .then(response => {
            rpcs.rpc('make_results_cache_entry', [optimSummary.serverDatastoreId])
              .then(response => {
                rpcs.rpc('launch_task', [optimSummary.serverDatastoreId, RPCname,
                  [this.projectID, optimSummary.serverDatastoreId, optimSummary.name],
                  {'plot_options':this.plotOptions, 'maxtime':maxtime, 'tool':this.$globaltool,
                    'plotyear':this.endYear, 'pops':this.activePop, 'cascade':null}])  // should this last be null?
                  .then(response => {
                    // Get the task state for the optimization.
                    this.getOptimTaskState(optimSummary)
                    status.succeed(this, 'Started optimization')
                  })
                  .catch(error => {
                    status.fail(this, 'Could not start optimization', error)
                  })
              })
              .catch(error => {
                status.fail(this, 'Could not start optimization', error)
              })
          })
          .catch(error => {
            status.fail(this, 'Could not start optimization', error)
          })
      },

    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
