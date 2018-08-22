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
          <td>
            <input type="checkbox" v-model="scenSummary.active"/>
          </td>          
          <td style="white-space: nowrap">
            <button class="btn" @click="editScen(scenSummary)">Edit</button>
            <button class="btn" @click="copyScen(scenSummary)">Copy</button>
            <button class="btn" @click="deleteScen(scenSummary)">Delete</button>
          </td>
        </tr>
        </tbody>
      </table>

      <div>
        <button class="btn __green" :disabled="!scenariosLoaded" @click="runScens()">Run scenarios</button>
        <!--<button class="btn __blue" @click="addBudgetScenModal()">Add parameter scenario</button>-->
        <button class="btn __blue" :disabled="!scenariosLoaded" @click="addBudgetScenModal()">Add scenario</button>

        <!--<button class="btn" :disabled="!scenariosLoaded" @click="toggleShowingPlots()">-->
          <!--<span v-if="areShowingPlots">Hide</span>-->
          <!--<span v-else>Show</span>-->
          <!--plot controls-->
        <!--</button>-->
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <div class="controls-box">
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
        </div>

      </div>
      
      <div style="text-align: center">
        <div class="controls-box">
          <button class="btn" @click="exportGraphs(projectID)">Export graphs</button>
          <button class="btn" @click="exportResults(projectID)">Export data</button>
        </div>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <div class="controls-box">
          <button class="btn" @click="clearGraphs()">Clear graphs</button>
          <button class="btn" :disabled="!scenariosLoaded" @click="plotScenarios()">Refresh graphs</button>
        </div>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <div class="controls-box">
          <button class="btn" @click="scaleFigs(0.9)">-</button>
          <button class="btn" @click="scaleFigs(1.0)">Scale</button>
          <button class="btn" @click="scaleFigs(1.1)">+</button>
        </div>
      </div>
      
      <div class="calib-main" :class="{'calib-main--full': true}">       
        <div class="calib-graphs">
          <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
            <!--mpld3 content goes here-->
          </div>
        </div>       
      </div>
      
      <div class="calib-tables" v-if="table">
        <span>Losses</span>
        <table>
          <tr v-for="(label, index) in table.labels">
            <td>{{label}}</td>
            <td v-for="text in table.text[index]">{{text}}</td>
          </tr>
        </table>
      </div>

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
  import Vue from 'vue';

  export default {
    name: 'scenarioPage',

    data() {
      return {
        serverresponse: 'no response',
        scenSummaries: [],
        defaultBudgetScen: {},
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
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
        // Load the scenario summaries of the current project.
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

      getDefaultBudgetScen() {
        console.log('getDefaultBudgetScen() called')
        rpcs.rpc('get_default_budget_scen', [this.projectID])
        .then(response => {
          this.defaultBudgetScen = response.data // Set the scenario to what we received.
          console.log('This is the default:')
          console.log(this.defaultBudgetScen);
        })
        .catch(error => {
          // Failure popup.
          status.failurePopup(this, 'Could not get default budget scenario')
        })         
      },

      getScenSummaries() {
        console.log('getScenSummaries() called')
        
        // Start indicating progress.
        status.start(this)

        // Get the current project's scenario summaries from the server.
        rpcs.rpc('get_scen_info', [this.projectID])
        .then(response => {
          this.scenSummaries = response.data // Set the scenarios to what we received.
          console.log('Scenario summaries:')
          console.log(this.scenSummaries)
          
          this.scenariosLoaded = true
          
          // Indicate success.
          status.succeed(this, 'Scenarios loaded')
        })
        .catch(error => {
          this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
          this.servererror = error.message // Set the server error.
          
          // Indicate failure.
          status.fail(this, 'Could not get scenarios: ' + error.message)
        })
      },

      setScenSummaries() {
        console.log('setScenSummaries() called')
        
        // Start indicating progress.
        status.start(this)
        
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Scenarios saved')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not save scenarios') 
        })        
      },

      addBudgetScenModal() {
        // Open a model dialog for creating a new project
        console.log('addBudgetScenModal() called');
        rpcs.rpc('get_default_budget_scen', [this.projectID])
        .then(response => {
          this.defaultBudgetScen = response.data // Set the scenario to what we received.
          this.addEditModal.scenSummary = utils.dcp(this.defaultBudgetScen)
          this.addEditModal.origName = this.addEditModal.scenSummary.name
          this.addEditModal.mode = 'add'
          this.$modal.show('add-budget-scen');
          console.log(this.defaultBudgetScen)
        })
        .catch(error => {
          this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
          this.servererror = error.message // Set the server error.
          
           // Failure popup.
          status.failurePopup(this, 'Could not open add scenario modal: '  + error.message)
        })
      },

      addBudgetScen() {
        console.log('addBudgetScen() called')
        this.$modal.hide('add-budget-scen')
        
        // Start indicating progress.
        status.start(this)
        
        // Get the new scenario summary from the modal.
        let newScen = utils.dcp(this.addEditModal.scenSummary)
  
        // Get the list of all of the current scenario names.
        let scenNames = []
        this.scenSummaries.forEach(scenSum => {
          scenNames.push(scenSum.name)
        })
               
        // If we are editing an existing scenario...
        if (this.addEditModal.mode == 'edit') {
          // Get the index of the original (pre-edited) name
          let index = scenNames.indexOf(this.addEditModal.origName)
          if (index > -1) {
            this.scenSummaries[index].name = newScen.name  // hack to make sure Vue table updated
            this.scenSummaries[index] = newScen
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }            
        }
        // Else (we are adding a new scenario)...
        else {
          newScen.name = utils.getUniqueName(newScen.name, scenNames)
          this.scenSummaries.push(newScen)
        }
        console.log(newScen)
        console.log(this.scenSummaries)        
        
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Scenario added')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not add scenario') 
          
          // TODO: Should probably fix the corrupted this.scenSummaries.
        })         
      },

      editScen(scenSummary) {
        // Open a model dialog for creating a new project
        console.log('editScen() called');
        this.defaultBudgetScen = scenSummary
        console.log('defaultBudgetScen')
        console.log(this.defaultBudgetScen)
        this.addEditModal.scenSummary = utils.dcp(this.defaultBudgetScen)
        this.addEditModal.origName = this.addEditModal.scenSummary.name         
        this.addEditModal.mode = 'edit' 
        this.$modal.show('add-budget-scen');
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        
        // Start indicating progress.
        status.start(this)
        
        var newScen = utils.dcp(scenSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = utils.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Scenario copied')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not copy scenario') 
          
          // TODO: Should probably fix the corrupted this.scenSummaries.
        })        
      },

      deleteScen(scenSummary) {
        console.log('deleteScen() called')
        
        // Start indicating progress.
        status.start(this)
        
        for(var i = 0; i< this.scenSummaries.length; i++) {
          if(this.scenSummaries[i].name === scenSummary.name) {
            this.scenSummaries.splice(i, 1);
          }
        }
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Scenario deleted')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not delete scenario') 
          
          // TODO: Should probably fix the corrupted this.scenSummaries.
        })        
      },

      runScens() {
        console.log('runScens() called')
        this.clipValidateYearInput()  // Make sure the end year is sensibly set.
        status.start(this)
        this.$Progress.start(7000)  // restart just the progress bar, and make it slower        
        // Make sure they're saved first
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
        .then(response => {
          // Go to the server to get the results from the package set.
          rpcs.rpc('run_scenarios', [this.projectID, this.plotOptions], 
            {saveresults: false, tool:'cascade', plotyear:this.endYear, pops:this.activePop})
          .then(response => {           
            this.makeGraphs(response.data.graphs)
            this.table = response.data.table
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
            this.servererror = error.message // Set the server error.
            status.fail(this, 'Could not make graphs: ' + error.message) // Indicate failure.
          })
        })
        .catch(error => {
          this.serverresponse = 'There was an error: ' + error.message
          this.servererror = error.message
          status.fail(this, 'Could not make graphs: ' + error.message)
        })        
      },

      plotScenarios() {
        console.log('plotScens() called')
        this.clipValidateYearInput()  // Make sure the end year is sensibly set.
        status.start(this)
        this.$Progress.start(2000)  // restart just the progress bar, and make it slower
        // Make sure they're saved first
        rpcs.rpc('plot_scenarios', [this.projectID, this.plotOptions], 
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
  .calib-tables span {
    display: block;
    margin-bottom: 1rem;
    font-weight: bold;
  }
  .calib-tables, .calib-tables table, .calib-tables tr, .calib-tables td {
    color: black; /* To match graph */
    font-family: Helvetica, sans-serif; /* To match graph */
  }
  .calib-tables table, .calib-tables tr, .calib-tables td {
    border: 2px solid #ddd;
  }
  .calib-tables table td {
    width: 96px;
    padding: 0.5rem;
    text-align: right;
  }
  .calib-tables table td:nth-child(1) {
    width: 192px; /* Header column */
    padding-right: 11px;
  }
</style>

