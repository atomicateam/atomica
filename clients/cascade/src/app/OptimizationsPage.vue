<!--
Optimizations Page

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
        <help reflink="optimizations" label="Define optimizations"></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th>Name</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="optimSummary in optimSummaries">
            <td>
              <b>{{ optimSummary.name }}</b>
            </td>
            <td style="white-space: nowrap">
              <button class="btn __green" @click="runOptim(optimSummary)">Run</button>
              <button class="btn btn-icon" @click="editOptim(scenSummary)"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyOptim(scenSummary)"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteOptim(scenSummary)"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn __blue" @click="addOptimModal()">Add optimization</button>
        </div>
      </div>

      <div class="card full-width-card">
        <div class="calib-title">
          <h5> Result plots </h5>
          <div>
            <!--<b>Start year: &nbsp;</b>-->
            <!--<input type="text"-->
                  <!--class="txbox"-->
                  <!--v-model="startYear"-->
                  <!--style="display: inline-block; width:70px"/>-->
            <!--&nbsp;&nbsp;&nbsp;-->

            <b>Year: &nbsp;</b>
            <input type="text"
                  class="txbox"
                  v-model="endYear"
                  style="display: inline-block; width:70px"/>
            &nbsp;&nbsp;&nbsp;
            <b>Population: &nbsp;</b>
            <select v-model="activePop">
              <option v-for='pop in activePops'>
                {{ pop }}
              </option>
            </select>
            &nbsp;&nbsp;&nbsp;
            <button class="btn" @click="exportGraphs(projectID)">Export graphs</button>
            <button class="btn" @click="exportResults(projectID)">Export data</button>
            <!-- <button class="btn btn-icon" @click="downloadProjectFile(projectSummary.project.id)" data-tooltip="Export">
              <i class="ti-download"></i>
            </button>
            <button class="btn btn-icon" @click="downloadProjectFile(projectSummary.project.id)" data-tooltip="Settings">
              <i class="ti-settings"></i>
            </button>
            <button class="btn btn-icon" @click="downloadProjectFile(projectSummary.project.id)" data-tooltip="Export">
              <i class="ti-zoom-in"></i>
            </button> -->
          </div>
        </div>
        <div class="calib-figures">
          <div class="calib-graphs">
            <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
              <!--mpld3 content goes here-->
            </div>
          </div>
          <div class="calib-tables" v-if="table">
            <h3>Cascade stage losses</h3>
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
      </div>

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
            Maximum time to run optimization (s):<br>
            <input type="text"
                   class="txbox"
                   v-model="modalOptim.maxtime"/><br>
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
            <b>Objective</b><br>
            <input type="radio" v-model="modalOptim.objective_weights.finalstage" value="1">&nbsp;Maximize the number of people in the final stage of the cascade<br>
            <input type="radio" v-model="modalOptim.objective_weights.finalstage" value="0">&nbsp;Maximize the conversion rates along each stage of the cascade<br>
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
        serverresponse: 'no response',
        optimSummaries: [],
        defaultOptim: {  
          // set stuff here to avoid render errors before things are loaded
          objective_weights: {
            conversion: 0, 
            finalstage: 1
          }          
        },
        modalOptim: {
          // set stuff here to avoid render errors before things are loaded
          objective_weights: {
            conversion: 0, 
            finalstage: 1
          }
        },
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
        graphData: [],
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
      activePops()   { return utils.activePops(this) },       
      placeholders() { return utils.placeholders() },
    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
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
      exportGraphs(project_id)  { return utils.exportGraphs(this, project_id) },
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
        if (this.endYear > this.simEnd) {
          this.endYear = this.simEnd
        }
        else if (this.endYear < this.simStart) {
          this.endYear = this.simStart
        }
      },
      
      updateSets() {
        console.log('updateSets() called')
        // Get the current user's parsets from the server.
        rpcs.rpc('get_parset_info', [this.projectID])
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
          
          // Get the current user's progsets from the server.
          rpcs.rpc('get_progset_info', [this.projectID])
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
            // Failure popup.
            status.failurePopup(this, 'Could not get progset info')
          })          
        })
        .catch(error => {
          // Failure popup.
          status.failurePopup(this, 'Could not get parset info')
        })              
      },

      getDefaultOptim() {
        console.log('getDefaultOptim() called')
        rpcs.rpc('get_default_optim', [this.projectID])
        .then(response => {
          this.defaultOptim = response.data // Set the optimization to what we received.
          this.resetModal()
          console.log('This is the default:')
          console.log(this.defaultOptim);
        })
        .catch(error => {
          // Failure popup.
          status.failurePopup(this, 'Could not get default optimization')
        })        
      },

      getOptimSummaries() {
        console.log('getOptimSummaries() called')
        
        // Start indicating progress.
        // Note: For some reason, the popup spinner doesn't work from inside created() 
        // so it doesn't show up here.         
        status.start(this)
        
        // Get the current project's optimization summaries from the server.
        rpcs.rpc('get_optim_info', [this.projectID])
        .then(response => {
          this.optimSummaries = response.data // Set the optimizations to what we received.
          
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
        
        // Start indicating progress.
        status.start(this)
        
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Optimizations saved')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not save optimizations')
        })        
      },

      addOptimModal() {
        // Open a model dialog for creating a new project
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
        
        // Start indicating progress.
        status.start(this)

        // Set the objectives
        this.modalOptim.objective_weights.conversion = (1.0-Number(this.modalOptim.objective_weights.finalstage))
        this.endYear = this.modalOptim.end_year
        
        // Get the optimization summary from the modal.
        let newOptim = utils.dcp(this.modalOptim) // Not sure if dcp is necessary
        
        // Get the list of all of the current optimization names.
        let optimNames = []
        this.optimSummaries.forEach(optimSum => {
          optimNames.push(optimSum.name)
        })
        
        // If we are editing an existing optimization...
        if (this.addEditDialogMode == 'edit') {
          // Get the index of the _old_ name
          let index = optimNames.indexOf(this.addEditDialogOldName)
          if (index > -1) {
            this.optimSummaries[index] = newOptim
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }            
        }
        // Else (we are adding a new optimization)...
        else {
          newOptim.name = utils.getUniqueName(newOptim.name, optimNames)
          this.optimSummaries.push(newOptim)
        }
        
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Optimization added')
          this.resetModal()
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not add optimization')
          
          // TODO: Should probably fix the corrupted this.optimSummaries.
        })        
      },

      cancelOptim() {
        this.$modal.hide('add-optim')
        this.resetModal()
      },

      resetModal() {
        console.log('resetModal() called')
        this.modalOptim = utils.dcp(this.defaultOptim)
        console.log(this.modalOptim)
      },

      editOptim(optimSummary) {
        // Open a model dialog for creating a new project
        console.log('editOptim() called');
        this.modalOptim = utils.dcp(optimSummary)
        console.log('defaultOptim', this.defaultOptim.obj)
        this.addEditDialogMode = 'edit'
        this.addEditDialogOldName = this.modalOptim.name
        this.$modal.show('add-optim');
      },

      copyOptim(optimSummary) {
        console.log('copyOptim() called')
        
        // Start indicating progress.
        status.start(this)
        
        var newOptim = utils.dcp(optimSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        })
        newOptim.name = utils.getUniqueName(newOptim.name, otherNames)
        this.optimSummaries.push(newOptim)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Opimization copied')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not copy optimization')
          
          // TODO: Should probably fix the corrupted this.optimSummaries.
        })        
      },

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        
        // Start indicating progress.
        status.start(this)
        
        for(var i = 0; i< this.optimSummaries.length; i++) {
          console.log('Trying ' + this.optimSummaries[i].name + ' vs ' + optimSummary.name)
          if(this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        .then(response => {
          // Indicate success.
          status.succeed(this, 'Optimization deleted')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not delete optimization')
          
          // TODO: Should probably fix the corrupted this.optimSummaries.
        })        
      },

      toggleShowingPlots() {
        this.areShowingPlots = !this.areShowingPlots
      },

      runOptim(optimSummary) {
        console.log('runOptim() called for '+this.currentOptim)
        this.clipValidateYearInput()  // Make sure the end year is sensibly set. 
        // Start indicating progress.
        status.start(this)
        this.$Progress.start(9000)  // restart just the progress bar, and make it slower        
        // Make sure they're saved first
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        .then(response => {          
          // Go to the server to get the results from the package set.
//            rpcservice.rpcCall('run_optimization',
          taskservice.getTaskResultPolling('run_cascade_optimization', 9999, 3, 'run_cascade_optimization',
            [this.projectID, optimSummary.name, this.plotOptions, true, this.endYear, this.activePop])
          .then(response => {
            this.makeGraphs(response.data.result.graphs)
            this.table = response.data.result.table
            
            // Indicate success.
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
            console.log(this.serverresponse)
            this.servererror = error.message // Set the server error.
             
            // Indicate failure.
            status.fail(this, 'Could not make graphs: ' + error.message)
          })
        })
        .catch(error => {
          this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
          console.log(this.serverresponse)
          this.servererror = error.message // Set the server error.
           
          // Indicate failure.
          status.fail(this, 'Could not make graphs: ' + error.message)
        })        
      },

      plotOptimization() {
        console.log('plotOptimization() called')
        this.clipValidateYearInput()  // Make sure the end year is sensibly set. 
        status.start(this)
        this.$Progress.start(2000)  // restart just the progress bar, and make it slower
        // Make sure they're saved first
        rpcs.rpc('plot_optimization', [this.projectID, this.plotOptions], 
          {tool:'cascade', plotyear:this.endYear, pops:this.activePop})
          .then(response => {
            this.makeGraphs(response.data.graphs)
            this.table = response.data.table
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
  /*
  HACK: The purpose of this code is to get things to line up a bit until
  we have a proper layout. Using fixed pixel widths is terrible and we
  shouldn't do it in other places.
  */
/*  .calib-tables span {
    display: block;
    margin-bottom: 1rem;
    font-weight: bold;
  }
  .calib-tables, .calib-tables table, .calib-tables tr, .calib-tables td {
    color: black; */ /* To match graph */
/*    font-family: Helvetica, sans-serif; */ /* To match graph */
/*  }
  .calib-tables table, .calib-tables tr, .calib-tables td {
    border: 2px solid #ddd;
  }
  .calib-tables table td {
    width: 96px;
    padding: 0.5rem;
    text-align: right;
  }
  .calib-tables table td:nth-child(1) {
    width: 192px; */ /* Header column */
/*    padding-right: 11px;
  } */
</style>
