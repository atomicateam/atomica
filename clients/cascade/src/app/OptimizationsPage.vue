<!--
Optimizations Page

Last update: 2018-08-30
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
        <help reflink="define-optimizations" label="Define optimizations"></help>
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
              <button class="btn" :disabled="!canRunTask(optimSummary)" @click="runOptim(optimSummary, 5)">Test run</button>
<!--              <button class="btn" :disabled="!canRunTask(optimSummary)" @click="runOptim(optimSummary, 15)">Test run</button> -->          
              <button class="btn __red" :disabled="!canCancelTask(optimSummary)" @click="clearTask(optimSummary)">Clear run</button>
              <button class="btn" :disabled="!canPlotResults(optimSummary)" @click="plotOptimization(optimSummary)">Plot results</button>
              <button class="btn btn-icon" @click="editOptim(optimSummary)"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyOptim(optimSummary)"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteOptim(optimSummary)"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn __blue" @click="addOptimModal()">Add optimization</button>
        </div>
      </div>

      <!-- ### Start: results card ### -->
    <div class="card full-width-card">
      <div class="calib-title">
        <help reflink="op-results" label="Results"></help>
        <div>
          <b>{{ displayResultName }}</b>
          &nbsp; &nbsp; &nbsp;
          <b>Year: &nbsp;</b>
          <select v-model="endYear" @change="updateYearOrPopulation">
            <option v-for='year in simYears'>
              {{ year }}
            </option>
          </select>
          &nbsp;&nbsp;&nbsp;
          <b>Population: &nbsp;</b>
          <select v-model="activePop" @change="updateYearOrPopulation">
            <option v-for='pop in activePops'>
              {{ pop }}
            </option>
          </select>
          &nbsp;&nbsp;&nbsp;
          <button class="btn" @click="exportGraphs()">Export graphs</button>
          <button class="btn" @click="exportResults(projectID)">Export data</button>

        </div>
      </div>

      <div class="calib-main" :class="{'calib-main--full': true}">
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
      </div>

      <div class="calib-tables" v-if="table">
        <h4>Cascade stage losses</h4>
        <table class="table table-striped">
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
    </div>
      <!-- ### End: results card ### -->

      <modal name="add-optim"
             height="auto"
             :scrollable="true"
             :width="900"
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
            Optimization name:<br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.name"/><br>
            Parameter set:<br>
            <select v-model="parsetOptions[0]">
              <option v-for='parset in parsetOptions'>
                {{ parset }}
              </option>
            </select><br><br>
            Start year:<br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.start_year"/><br>
            End year:<br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.end_year"/><br>
            <!--Budget factor:<br>-->
            <!--<input type="text"-->
            <!--class="txbox"-->
            <!--v-model="modalOptim.budget_factor"/><br>-->
            <br>
            <b>Objective weights</b><br>
            <span v-for="(val,key) in modalOptim.objective_labels">
              {{ modalOptim.objective_labels[key] }}
              <input type="text"
                     class="txbox"
                     v-model="modalOptim.objective_weights[key]"/><br>
            </span>
            <br>
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
  import Vue from 'vue';
  import help from '@/app/HelpLink.vue'

  export default {
    name: 'OptimizationPage',

    components: {
      help
    },

    data() {
      return {
        response: 'no response',
        optimSummaries: [],
        defaultOptim: {},
        modalOptim: {},
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
        displayResultName: '',
        startYear: 0,
        endYear: 0,         
        graphData: [],
        areShowingPlotControls: false,
        plotOptions: [],
        table: null,
        activePop: "All",
        endYear: 0,
        addEditDialogMode: 'add',  // or 'edit'
        addEditDialogOldName: '',
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
        utils.sleep(1)  // used so that spinners will come up by callback func
          .then(response => {
            // Load the optimization summaries of the current project.
            this.startYear = this.simStart
            this.endYear = this.simEnd
            this.popOptions = this.activePops
            this.getOptimSummaries()
            this.getDefaultOptim()
            this.resetModal()
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
      exportGraphs(project_id)  { return utils.exportGraphs(this, project_id) },
      exportResults(project_id) { return utils.exportResults(this, project_id) },
      
      statusFormatStr(optimSummary) {
        if (optimSummary.status == 'not started') {
          return ''
        }
        else if (optimSummary.status == 'queued') {
          return 'Initializing... ' // + this.timeFormatStr(optimSummary.pendingTime)
        }
        else if (optimSummary.status == 'started') {
          return 'Running for ' // + this.timeFormatStr(optimSummary.executionTime)
        }
        else if (optimSummary.status == 'completed') {
          return 'Completed after  ' // + this.timeFormatStr(optimSummary.executionTime)
        }        
        else {
          return ''
        }
      },
      
      timeFormatStr(optimSummary) {
        let rawValue = ''
        if (optimSummary.status == 'queued') {
          rawValue = optimSummary.pendingTime
        }  
        else if ((optimSummary.status == 'started') || (optimSummary.status == 'completed')) {
          rawValue = optimSummary.executionTime
        }
        else {
          return ''
        }

        if (rawValue == '--') {
          return '--'
        }
        else {
          let numSecs = Number(rawValue).toFixed()
          let numHours = Math.floor(numSecs / 3600)
          numSecs -= numHours * 3600
          let numMins = Math.floor(numSecs / 60)
          numSecs -= numMins * 60
          let output = _.padStart(numHours.toString(), 2, '0') + ':' + _.padStart(numMins.toString(), 2, '0') + ':' + _.padStart(numSecs.toString(), 2, '0')
          return output
        }
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
      
      canRunTask(optimSummary) {
        return ((optimSummary.status == 'not started') || (optimSummary.status == 'completed'))
      },
      
      canCancelTask(optimSummary) {
        let output = (optimSummary.status != 'not started')
        return output
      },
      
      canPlotResults(optimSummary) {
        return (optimSummary.status == 'completed')
      },
      
      getOptimTaskState(optimSummary) {
        var statusStr = ''
        
        // Check the status of the task.
        rpcs.rpc('check_task', [optimSummary.server_datastore_id])
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
        console.log('Do a task poll...')
        // For each of the optimization summaries...
        this.optimSummaries.forEach(optimSum => {
          // If there is a valid task launched, check it.
          if ((optimSum.status != 'not started') && (optimSum.status != 'completed')) {
            this.getOptimTaskState(optimSum)
          }
        }) 
               
        // Hack to get the Vue display of optimSummaries to update
        this.optimSummaries.push(this.optimSummaries[0])
        this.optimSummaries.pop()
        
        // Sleep waitingtime seconds.
        var waitingtime = 2
        utils.sleep(waitingtime * 1000)
        .then(response => {
          // Only if we are still in the optimizations page, call ourselves.
          if (this.$route.path == '/optimizations') {
            this.pollAllTaskStates()
          }
        }) 
      },
      
      clearTask(optimSummary) {
        console.log('cancelRun() called for '+this.currentOptim)
        rpcs.rpc('delete_task', [optimSummary.server_datastore_id])
        .then(response => {
          // Get the task state for the optimization.
          this.getOptimTaskState(optimSummary)  

          // TODO: Delete cached result.          
        })
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
                status.failurePopup(this, 'Could not get progset info')
              })
          })
          .catch(error => {
            status.failurePopup(this, 'Could not get parset info')
          })
      },

      getDefaultOptim() {
        console.log('getDefaultOptim() called')
        rpcs.rpc('get_default_optim', [this.projectID, 'cascade'])  // CASCADE-TB DIFFERENCE
          .then(response => {
            this.defaultOptim = response.data // Set the optimization to what we received.
            console.log('This is the default:')
            console.log(this.defaultOptim);
          })
          .catch(error => {
            status.failurePopup(this, 'Could not get default optimization')
          })
      },

      getOptimSummaries() {
        console.log('getOptimSummaries() called')
        status.start(this)
        
        // Get the current project's optimization summaries from the server.
        rpcs.rpc('get_optim_info', [this.projectID])
        .then(response => {
          this.optimSummaries = response.data // Set the optimizations to what we received.
          
          // For each of the optimization summaries...
          this.optimSummaries.forEach(optimSum => {
            // Build a task and results cache ID from the project's hex UID and the optimization name.
            optimSum.server_datastore_id = this.$store.state.activeProject.project.id + ':opt-' + optimSum.name
            
            // Set the status to 'not started' by default, and the pending and execution 
            // times to '--'.
            optimSum.status = 'not started'
            optimSum.pendingTime = '--'
            optimSum.executionTime = '--'
            
            // Get the task state for the optimization.
            this.getOptimTaskState(optimSum)
          })
          
          // Start polling of tasks states.
          this.pollAllTaskStates()
          
          // Indicate success.
          status.succeed(this, 'Optimizations loaded')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not load optimizations')
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
            status.fail(this, 'Could not save optimizations')
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
        if (this.addEditDialogMode == 'edit') { // If we are editing an existing optimization...
          let index = optimNames.indexOf(this.addEditDialogOldName) // Get the index of the original (pre-edited) name
          if (index > -1) {  // 
            this.optimSummaries[index].name = newOptim.name  // hack to make sure Vue table updated            
            this.optimSummaries[index] = newOptim
            if (newOptim.name != this.addEditDialogOldName) {  // If we've renamed an optimization
              // Clear the present task.
              if (newOptim.status != 'not started') {
                this.clearTask(newOptim)  // Clear the task from the server. 
              }

              // Set a new server DataStore ID.
              newOptim.server_datastore_id = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name
              
              // TODO: Delete any cached results.
              
              this.getOptimTaskState(newOptim)
            }              
          }
          else {
            status.fail(this, 'Could not find optimization "' + this.addEditDialogOldName + '" to edit')
          }
        }
        else { // Else (we are adding a new optimization)...
          newOptim.name = utils.getUniqueName(newOptim.name, optimNames)
          newOptim.server_datastore_id = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name
          this.optimSummaries.push(newOptim)
          this.getOptimTaskState(newOptim)
        }

        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization added')
            this.resetModal()
          })
          .catch(error => {
            status.fail(this, 'Could not add optimization: ' + error.message)
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
        newOptim.server_datastore_id = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name
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
          status.fail(this, 'Could not delete optimization')
        })
      },

      toggleShowingPlotControls() {
        this.areShowingPlotControls = !this.areShowingPlotControls
      },

/*      runOptim(optimSummary, maxtime) {
        console.log('runOptim() called for '+this.currentOptim + ' for time: ' + maxtime)
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then(response => { // Go to the server to get the results
            taskservice.getTaskResultPolling('run_cascade_optimization', 9999, 1, 'run_cascade_optimization',
              [this.projectID, optimSummary.name], {'plot_options':this.plotOptions, 'maxtime':maxtime, 'tool':'cascade',  // CASCADE-TB DIFFERENCE
                'plotyear':this.endYear, 'pops':this.activePop, 'cascade':null})
              .then(response => {
                this.makeGraphs(response.data.result.graphs)
                this.table = response.data.result.table
                status.succeed(this, 'Optimization complete')
              })
              .catch(error => {
                console.log('There was an error: ' + error.message) // Pull out the error message.
                status.fail(this, 'Could not run optimization: ' + error.message)
              })
          })
          .catch(error => {
            console.log('There was an error: ' + error.message)
            status.fail(this, 'Could not set optimization info: ' + error.message)
          })
        })
        .catch(error => {
          this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
          console.log(this.serverresponse)
          this.servererror = error.message // Set the server error.
           
          // Indicate failure.
          status.fail(this, 'Could not make graphs: ' + error.message)
        })        
      }, */
      
      runOptim(optimSummary, maxtime) {
        console.log('runOptim() called for '+this.currentOptim + ' for time: ' + maxtime)
        this.clipValidateYearInput()  // Make sure the end year is sensibly set. 
        // Start indicating progress.
        status.start(this)       
        // Make sure they're saved first
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        .then(response => {
          rpcs.rpc('launch_task', [optimSummary.server_datastore_id, 'run_cascade_optimization', 
            [this.projectID, optimSummary.server_datastore_id, optimSummary.name], 
            {'plot_options':this.plotOptions, 'maxtime':maxtime, 'tool':'cascade',  
            // CASCADE-TB DIFFERENCE
            'plotyear':this.endYear, 'pops':this.activePop, 'cascade':null}])
          .then(response => {
            // Get the task state for the optimization.
            this.getOptimTaskState(optimSummary)
            
            // Indicate success.
            status.succeed(this, 'Started optimization')
          })
          .catch(error => {
            this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
            console.log(this.serverresponse)
            this.servererror = error.message // Set the server error.
             
            // Indicate failure.
            status.fail(this, 'Could not start optimization: ' + error.message)
          })        
        })
        .catch(error => {
          this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
          console.log(this.serverresponse)
          this.servererror = error.message // Set the server error.
           
          // Indicate failure.
          status.fail(this, 'Could not start optimization: ' + error.message)
        })        
      },
      
      plotOptimization(optimSummary) {
        console.log('plotOptimization() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range. 
        status.start(this)
        this.$Progress.start(2000)  // restart just the progress bar, and make it slower
        // Make sure they're saved first
        rpcs.rpc('plot_optimization_cascade', [this.projectID, optimSummary.server_datastore_id, this.plotOptions],
          {tool:'cascade', plotyear:this.endYear, pops:this.activePop})
          .then(response => {
            this.makeGraphs(response.data.graphs)
            this.table = response.data.table
            this.displayResultName = optimSummary.name
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
            this.servererror = error.message // Set the server error.
            status.fail(this, 'Could not make graphs') // Indicate failure.
          })
      },
      
      updateYearOrPopulation() {
        // Get the list of all of the current optimization names.
        let optimNames = [] 
        
        // Get the list of optimization names.
        this.optimSummaries.forEach(optimSum => {
          optimNames.push(optimSum.name)
        })
        
        // Get the index matching (if any) which optimization matches
        // the one being displayed.
        let index = optimNames.indexOf(this.displayResultName)
        if (index > -1) {  // If we have any match...
          // Plot the desired graph.
          this.plotOptimization(this.optimSummaries[index])
        }
      }
    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
