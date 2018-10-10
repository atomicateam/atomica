<!--
Optimizations Page

Last update: 2018-09-26
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
              <button class="btn" :disabled="!canRunTask(optimSummary)" @click="runOptim(optimSummary, 10)">Test run</button>
              <button class="btn __green" :disabled="!canPlotResults(optimSummary)" @click="plotResults(optimSummary)">Plot results</button>
              <button class="btn" :disabled="!canCancelTask(optimSummary)" @click="clearTask(optimSummary)">Clear run</button>
              <button class="btn btn-icon" @click="editOptim(optimSummary)" data-tooltip="Edit optimization"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyOptim(optimSummary)" data-tooltip="Copy optimization"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteOptim(optimSummary)" data-tooltip="Delete optimization"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn" @click="addOptimModal('outcome')">Add outcome optimization</button>&nbsp;&nbsp;
          <button v-if="$globaltool=='tb'" class="btn" @click="addOptimModal('money')">Add money optimization</button>
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
              <select v-model="endYear" @change="reloadGraphs(displayResultDatastoreId, true)">
                <option v-for='year in projectionYears'>
                  {{ year }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;
              <b>Population: &nbsp;</b>
              <select v-model="activePop" @change="reloadGraphs(displayResultDatastoreId, true)">
                <option v-for='pop in activePops'>
                  {{ pop }}
                </option>
              </select>&nbsp;&nbsp;&nbsp;
              <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
              <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
              <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>&nbsp;&nbsp;&nbsp;
              <button class="btn" @click="exportGraphs()">Export graphs</button>
              <button class="btn" @click="exportResults(displayResultDatastoreId)">Export data</button>
              <button v-if="false" class="btn btn-icon" @click="togglePlotControls()"><i class="ti-settings"></i></button> <!-- When popups are working: v-if="this.$globaltool=='tb'" -->
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
            <b>Use optimal allocation of funds beginning in year</b><br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.start_year"/><br>
            <b>Target year for optimizing outcomes</b><br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.end_year"/><br>
            <span v-if="modalOptim.optim_type!=='money'">
              <b>Budget factor</b><br>
              <input type="text"
                     class="txbox"
                     v-model="modalOptim.budget_factor"/><br>
            </span>
          </div>
          <br>
          <b>Objectives</b><br>
          <table class="table table-bordered table-hover table-striped" style="width: 100%">
            <thead>
            <tr>
              <th>Objective</th>
              <th v-if="modalOptim.optim_type=='outcome'">Weight</th>
              <th v-if="modalOptim.optim_type=='money'">Reduction target (%)</th>
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
          <b>Spending constraints (absolute)</b><br>
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
        pollingTasks: false,
        defaultOptim: {},
        modalOptim: {},
        objectiveOptions: [],
        displayResultName: '',
        displayResultDatastoreId: '',
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
        this.getPlotOptions(this.$store.state.activeProject.project.id)
          .then(response => {
            this.updateSets()
              .then(response2 => {
                this.getOptimSummaries()
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
      makeGraphs(graphdata)             { return graphs.makeGraphs(this, graphdata, '/optimizations') },
      reloadGraphs(cache_id, showErr)   { return graphs.reloadGraphs(this, this.projectID, cache_id, showErr, false, true) }, // Set to calibration=false, plotbudget=True
      maximize(legend_id)               { return graphs.maximize(this, legend_id) },
      minimize(legend_id)               { return graphs.minimize(this, legend_id) },

      statusFormatStr(optimSummary) {
        if      (optimSummary.status === 'not started') {return ''}
        else if (optimSummary.status === 'queued')      {return 'Initializing... '} // + this.timeFormatStr(optimSummary.pendingTime)
        else if (optimSummary.status === 'started')     {return 'Running for '} // + this.timeFormatStr(optimSummary.executionTime)
        else if (optimSummary.status === 'completed')   {return 'Completed after '} // + this.timeFormatStr(optimSummary.executionTime)
        else if (optimSummary.status === 'error')   {return 'Error after '} // + this.timeFormatStr(optimSummary.executionTime)
        else                                            {return ''}
      },

      timeFormatStr(optimSummary) {
        let rawValue = ''
        let is_queued = (optimSummary.status === 'queued')
        let is_executing = ((optimSummary.status === 'started') || 
          (optimSummary.status === 'completed') || (optimSummary.status === 'error'))        
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

      canRunTask(optimSummary)     { return (optimSummary.status === 'not started') },
      canCancelTask(optimSummary)  { return (optimSummary.status !== 'not started') },
      canPlotResults(optimSummary) { return (optimSummary.status === 'completed') },

      getOptimTaskState(optimSummary) {
        return new Promise((resolve, reject) => {
          console.log('getOptimTaskState() called for with: ' + optimSummary.status)
          let statusStr = '';
          rpcs.rpc('check_task', [optimSummary.serverDatastoreId]) // Check the status of the task.
            .then(result => {
              statusStr = result.data.task.status
              optimSummary.status = statusStr
              optimSummary.pendingTime = result.data.pendingTime
              optimSummary.executionTime = result.data.executionTime
              if (optimSummary.status == 'error') {
                console.log('Error in task: ', optimSummary.serverDatastoreId)
                console.log(result.data.task.errorText)
              }
              resolve(result)
            })
            .catch(error => {
              optimSummary.status = 'not started'
              optimSummary.pendingTime = '--'
              optimSummary.executionTime = '--'
              resolve(error)  // yes, resolve, not reject, because this means non-started task
            })
        })
      },
      
      needToPoll() {
        // Check if we're still on the Optimizations page.
        let routePath = (this.$route.path === '/optimizations')
        
        // Check if we have a queued or started task.
        let runningState = false
        this.optimSummaries.forEach(optimSum => {
          if ((optimSum.status === 'queued') || (optimSum.status === 'started')) {
            runningState = true
          }
        })
        
        // We need to poll if we are in the page and a task is going.
        return (routePath && runningState)
      },
      
      pollAllTaskStates(checkAllTasks) {
        return new Promise((resolve, reject) => {
          console.log('Polling all tasks...')
          
          // Clear the poll states.
          this.optimSummaries.forEach(optimSum => {
            optimSum.polled = false
          })
          
          // For each of the optimization summaries...
          this.optimSummaries.forEach(optimSum => { 
            console.log(optimSum.serverDatastoreId, optimSum.status)
            
            // If we are to check all tasks OR there is a valid task running, check it.
            if ((checkAllTasks) ||            
              ((optimSum.status !== 'not started') && (optimSum.status !== 'completed') && 
                (optimSum.status !== 'error'))) {
              this.getOptimTaskState(optimSum)
              .then(response => {
                // Flag as polled.
                optimSum.polled = true
                
                // Resolve the main promise when all of the optimSummaries are polled.
                let done = true
                this.optimSummaries.forEach(optimSum2 => {
                  if (!optimSum2.polled) {
                    done = false
                  }
                })
                if (done) {
                  resolve()
                }
              })
            }
            
            // Otherwise (no task to check), we are done polling for it.
            else {
              // Flag as polled.
              optimSum.polled = true
              
              // Resolve the main promise when all of the optimSummaries are polled.
              let done = true
              this.optimSummaries.forEach(optimSum2 => {
                if (!optimSum2.polled) {
                  done = false
                }
              })
              if (done) {
                resolve()
              }
            }           
          })   
        })     
      },
      
      doTaskPolling(checkAllTasks) {
        // Flag that we're polling.
        this.pollingTasks = true
        
        // Do the polling of the task states.
        this.pollAllTaskStates(checkAllTasks)
        .then(() => {
          // Hack to get the Vue display of optimSummaries to update
          this.optimSummaries.push(this.optimSummaries[0])
          this.optimSummaries.pop()
            
          // Only if we need to continue polling...
          if (this.needToPoll()) {
            // Sleep waitingtime seconds.
            let waitingtime = 1
            utils.sleep(waitingtime * 1000)
              .then(response => {
                this.doTaskPolling(false) // Call the next polling, in a way that doesn't check_task() for _every_ task.
              })         
          }
          
          // Otherwise, flag that we're no longer polling.
          else {
            this.pollingTasks = false
          }
        })
      },
      
      clearTask(optimSummary) {
        return new Promise((resolve, reject) => {
          let datastoreId = optimSummary.serverDatastoreId  // hack because this gets overwritten soon by caller
          console.log('clearTask() called for '+this.currentOptim)
          rpcs.rpc('del_result', [datastoreId, this.projectID]) // Delete cached result.
            .then(response => {
              rpcs.rpc('delete_task', [datastoreId])
                .then(response => {
                  this.getOptimTaskState(optimSummary) // Get the task state for the optimization.
                  if (!this.pollingTasks) {
                    this.doTaskPolling(true)
                  }                  
                  resolve(response)
                })
                .catch(error => {
                  resolve(error)  // yes, resolve because at least cache entry deletion succeeded
                })
            })
            .catch(error => {
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
            this.optimSummaries.forEach(optimSum => { // For each of the optimization summaries...
              optimSum.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + optimSum.name // Build a task and results cache ID from the project's hex UID and the optimization name.
              optimSum.status = 'not started' // Set the status to 'not started' by default, and the pending and execution times to '--'.
              optimSum.pendingTime = '--'
              optimSum.executionTime = '--'
            })
            this.doTaskPolling(true)  // start task polling, kicking off with running check_task() for all optimizations
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

      addOptimModal(optim_type) { // Open a model dialog for creating a new project
        console.log('addOptimModal() called for ' + optim_type);
        rpcs.rpc('get_default_optim', [this.projectID, this.$globaltool, optim_type])
          .then(response => {
            this.defaultOptim = response.data // Set the optimization to what we received.
            this.resetModal(response.data)
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
            if (newOptim.name !== this.addEditDialogOldName) {  // If we've renamed an optimization
              newOptim.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name // Set a new server DataStore ID.
            }
            if (newOptim.status !== 'not started') { // Clear the present task.
              this.clearTask(newOptim)  // Clear the task from the server.
            }
            newOptim.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name // Build a task and results cache ID from the project's hex UID and the optimization name.
            newOptim.status = 'not started' // Set the status to 'not started' by default, and the pending and execution times to '--'.
            newOptim.pendingTime = '--'
            newOptim.executionTime = '--'
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
          .then(result => {
            // Hack to get the Vue display of optimSummaries to update
            this.optimSummaries.push(this.optimSummaries[0])
            this.optimSummaries.pop()
          })          
        }

        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization added')
            this.resetModal(this.defaultOptim)
          })
          .catch(error => {
            status.fail(this, 'Could not add optimization', error)
          })
      },

      cancelOptim() {
        this.$modal.hide('add-optim')
        this.resetModal(this.defaultOptim)
      },

      resetModal(optimData) {
        console.log('resetModal() called')
        this.modalOptim = _.cloneDeep(optimData)
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
        var newOptim = _.cloneDeep(optimSummary);
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
            status.succeed(this, 'Optimization copied')
          })
          .catch(error => {
            status.fail(this, 'Could not copy optimization', error)
          })
      },

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        status.start(this)
        if (optimSummary.status !== 'not started') {
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
        this.validateYears()  // Make sure the end year is sensibly set.
        status.start(this)
        var RPCname = ''
        if (this.$globaltool === 'cascade') {RPCname = 'run_cascade_optimization'}
        if (this.$globaltool === 'tb')      {RPCname = 'run_tb_optimization'}
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries]) // Make sure they're saved first
          .then(response => {
            rpcs.rpc('launch_task', [optimSummary.serverDatastoreId, RPCname,
              [this.projectID, optimSummary.serverDatastoreId, optimSummary.name],
              { 'plot_options': this.plotOptions, 'maxtime': maxtime, 'tool': this.$globaltool,
                'plotyear': this.endYear, 'pops': this.activePop, 'cascade': null}])  // should this last be null?
              .then(response => {
                this.getOptimTaskState(optimSummary) // Get the task state for the optimization.
                if (!this.pollingTasks) {
                  this.doTaskPolling(true)
                }                
                status.succeed(this, 'Started optimization')
              })
              .catch(error => {
                status.fail(this, 'Could not start optimization', error)
              })
          })
          .catch(error => {
            status.fail(this, 'Could not save optimizations', error)
          })
      },

      plotResults(optimSummary) {
        this.displayResultName = optimSummary.name;
        this.displayResultDatastoreId = optimSummary.serverDatastoreId;
        this.reloadGraphs(optimSummary.serverDatastoreId, true)
      },

    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
