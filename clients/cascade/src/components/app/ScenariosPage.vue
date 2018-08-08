<!--
Scenarios Page

Last update: 2018-08-08
-->

<template>
  <div>

    <div v-if="activeProjectID ==''">
      <div style="font-style:italic">
        <p>No project is loaded.</p>
      </div>
    </div>

    <div v-else>
      <table class="table table-bordered table-hover table-striped" style="width: 100%">
        <thead>
        <tr>
          <th>Name</th>
          <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="scenSummary in scenSummaries">
          <td>
            <b>{{ scenSummary.name }}</b>
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
        <button class="btn" :disabled="!scenariosLoaded" @click="clearGraphs()">Clear graphs</button>
        <!--<button class="btn" :disabled="!scenariosLoaded" @click="toggleShowingPlots()">-->
          <!--<span v-if="areShowingPlots">Hide</span>-->
          <!--<span v-else>Show</span>-->
          <!--plot controls-->
        <!--</button>-->
      </div>



      <div class="calib-main" :class="{'calib-main--full': !areShowingPlots}">
        <div class="calib-params" v-if="areShowingPlots">
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
        <div class="calib-figures">
          <div class="calib-graphs">
            <div v-for="index in placeholders" :id="'fig'+index">
              <!--mpld3 content goes here-->
            </div>
          </div>
          <div class="calib-tables">
            <table v-if="table">
              <tr v-for="(label, index) in table.labels">
                <td>{{label}}</td>
                <td v-for="text in table.text[index]">{{text}}</td>
              </tr>
            </table>
          </div>
        </div>
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

        <!--TO_PORT-->
        <div class="dialog-content">
          <div class="dialog-c-title">
            Add/edit scenario
          </div>
          <div class="dialog-c-text">
            Scenario name:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultBudgetScen.name"/><br>
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
                   v-model="defaultBudgetScen.start_year"/><br>
            <table class="table table-bordered table-hover table-striped" style="width: 100%">
              <thead>
              <tr>
                <th>Program</th>
                <th>Budget</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="item in defaultBudgetScen.alloc">
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

      <!-- Popup spinner -->
      <popup-spinner></popup-spinner>

    </div>
  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import taskservice from '@/services/task-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import Vue from 'vue';
  import PopupSpinner from './Spinner.vue'

  export default {
    name: 'scenarioPage',

    components: {
      PopupSpinner
    },

    data() {
      return {
        serverresponse: 'no response',
        scenSummaries: [],
        defaultBudgetScen: [],
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
        areShowingPlots: false,
        plotOptions: [],
        scenariosLoaded: false,
        table: null,
      }
    },

    computed: {
      activeProjectID() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          console.log('activeProjectID() called')
          return this.$store.state.activeProject.project.id
        }
      },

      placeholders() {
        var indices = []
        for (var i = 0; i <= 100; i++) {
          indices.push(i);
        }
        return indices;
      },

    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      }
      else { // Otherwise...
        // Load the scenario summaries of the current project.
        console.log('created() called')
        this.sleep(1)  // used so that spinners will come up by callback func
        .then(response => {
          this.getScenSummaries()
          this.getDefaultBudgetScen()
          this.updateSets()
          this.getPlotOptions()
        })
      }
    },

    methods: {

      dcp(input) {
        var output = JSON.parse(JSON.stringify(input))
        return output
      },
      
      sleep(time) {
        // Return a promise that resolves after _time_ milliseconds.
        console.log('Sleeping for ' + time)
        return new Promise((resolve) => setTimeout(resolve, time));
      },
      
      getUniqueName(fileName, otherNames) {
        let tryName = fileName
        let numAdded = 0
        while (otherNames.indexOf(tryName) > -1) {
          numAdded = numAdded + 1
          tryName = fileName + ' (' + numAdded + ')'
        }
        return tryName
      },

      projectID() {
        var id = this.$store.state.activeProject.project.id // Shorten this
        return id
      },

      // TO_PORT
      updateSets() {
        console.log('updateSets() called')
        // Get the current user's parsets from the server.
        rpcservice.rpcCall('get_parset_info', [this.projectID()])
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
          rpcservice.rpcCall('get_progset_info', [this.projectID()])
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
        rpcservice.rpcCall('get_default_budget_scen', [this.projectID()])
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
        rpcservice.rpcCall('get_scen_info', [this.projectID()])
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
        
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
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
        rpcservice.rpcCall('get_default_budget_scen', [this.projectID()])
        .then(response => {
          this.defaultBudgetScen = response.data // Set the scenario to what we received.
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
        
        let newScen = this.dcp(this.defaultBudgetScen); // You've got to be kidding me, buster
        let otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        });
        let index = otherNames.indexOf(newScen.name);
        if (index > -1) {
          console.log('scenario named '+newScen.name+' exists, overwriting...')
          this.scenSummaries[index] = newScen
        }
        else {
          console.log('scenario named '+newScen.name+' does not exist, creating new...')
          this.scenSummaries.push(newScen)
        }
        console.log(newScen)
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
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
        this.$modal.show('add-budget-scen');
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        
        // Start indicating progress.
        status.start(this)
        
        var newScen = this.dcp(scenSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = this.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
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
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
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

      getPlotOptions() {
        console.log('getPlotOptions() called')
        rpcservice.rpcCall('get_supported_plots', [true])
          .then(response => {
            this.plotOptions = response.data // Get the parameter values
          })
          .catch(error => {
            status.failurePopup(this, 'Could not get plot options: ' + error.message)
          })
      },

      toggleShowingPlots() {
        this.areShowingPlots = !this.areShowingPlots
      },

      runScens() {
        console.log('runScens() called')
        status.start(this)
        this.$Progress.start(7000)  // restart just the progress bar, and make it slower        
        // Make sure they're saved first
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
        .then(response => {
          // Go to the server to get the results from the package set.
          rpcservice.rpcCall('run_scenarios', [this.projectID(), this.plotOptions], {saveresults: false, tool: 'cascade'})
          .then(response => {
            this.serverresponse = response.data // Pull out the response data.
            this.table = response.data.table
            var n_plots = response.data.graphs.length
            console.log('Rendering ' + n_plots + ' graphs')
            for (var index = 0; index <= n_plots; index++) {
              console.log('Rendering plot ' + index)
              var divlabel = 'fig' + index
              var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
              while (div.firstChild) {
                div.removeChild(div.firstChild);
              }
              try {
                console.log(response.data.graphs[index]);
                mpld3.draw_figure(divlabel, response.data.graphs[index], function(fig, element) {
                  fig.setYTicks(null, function(d) { return d3.format('.2s')(d); });
                });
                this.haveDrawnGraphs = true
              }
              catch (err) {
                console.log('failled:' + err.message);
              }
            }
            
            // Indicate success.
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
            this.servererror = error.message // Set the server error.
            
            // Indicate failure.
            status.fail(this, 'Could not make graphs')
          })
        })
        .catch(error => {
          // Pull out the error message.
          this.serverresponse = 'There was an error: ' + error.message

          // Set the server error.
          this.servererror = error.message
          
          // Put up a failure notification.
          status.fail(this, 'Could not make graphs')      
        })        
      },

      reloadGraphs() {
        console.log('Reload graphs')
        let n_plots = this.graphData.length
        console.log('Rendering ' + n_plots + ' graphs')
        for (let index = 0; index <= n_plots; index++) {
          console.log('Rendering plot ' + index)
          var divlabel = 'fig' + index
          try {
            mpld3.draw_figure(divlabel, response.data.graphs[index], function(fig, element) {
              fig.setYTicks(null, function(d) { return d3.format('.2s')(d); });
            });
          }
          catch (err) {
            console.log('failled:' + err.message);
          }
        }
      },

      clearGraphs() {
        console.log('Clear graphs')
        this.graphData = []
        for (var index = 0; index <= 100; index++) {
          console.log('Clearing plot ' + index)
          var divlabel = 'fig' + index
          var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
          while (div.firstChild) {
            div.removeChild(div.firstChild);
          }
        }
      }

    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
  .calib-controls {
    margin-bottom: 3rem;
  }
  .calib-controls .control-group {
    display: inline-block;
  }
  .calib-controls button, .calib-controls .control-group {
    margin-right: 1rem;
  }

  .calib-main {
    margin-top: 4rem;
  }
  .calib-params {
    flex: 0 0 30%;
  }
  .calib-graphs {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    & > * {
      flex: 1;
    }
  }

  /*
  HACK: The purpose of this code is to get things to line up a bit until
  we have a proper layout. Using fixed pixel widths is terrible and we
  shouldn't do it in other places.
  */
  .calib-tables table, .calib-tables tr, .calib-tables td {
    // width: 960px; /* To match graph */
    color: black; /* To match graph */
    font-family: Helvetica, sans-serif; /* To match graph */
  }
  .calib-tables table td {
    width: 97px;
    text-align: center;
  }
  .calib-tables table td:nth-child(1) {
    width: 192px; /* Header column */
    text-align: right;
    padding-right: 11px;
  }

  .plotopts-main {
    /*width: 350px;*/
    /*padding-left: 20px;*/
    display: flex;
    /*float: left;*/
  }
  .plotopts-main--full {
    display: block;
  }
  .plotopts-params {
    flex: 1 0 10%;
  }
  .controls-box {
    border: 2px solid #ddd;
    padding: 7px;
    display: inline-block;
  }
  .small-button {
    background: inherit;
    padding: 0 0 0 0;
  }
</style>

