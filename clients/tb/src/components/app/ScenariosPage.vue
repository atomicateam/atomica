<!--
Define equity

Last update: 2018-07-29
-->

<template>
  <div class="SitePage">

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
            <button class="btn __green" @click="runScen(scenSummary)">Run</button>
            <button class="btn" @click="editScen(scenSummary)">Edit</button>
            <button class="btn" @click="copyScen(scenSummary)">Copy</button>
            <button class="btn" @click="deleteScen(scenSummary)">Delete</button>
          </td>
        </tr>
        </tbody>
      </table>

      <div>
        <button class="btn __blue" @click="addBudgetScenModal()">Add budget scenario</button>
        <button class="btn" @click="clearGraphs()">Clear graphs</button>
      </div>

      <div>
        <div v-for="index in placeholders" :id="'fig'+index" style="width:650px; float:left;">
          <!--mpld3 content goes here-->
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
                   v-model="defaultScen.name"/><br>
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
            </select>
            Start year:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultScen.start_year"/><br>
            End year:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultScen.end_year"/><br>
            Budget factor:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultScen.budget_factor"/><br>
            <br>
            <!--<b>Relative objective weights</b><br>-->
            <!--People alive:-->
            <!--<input type="text"-->
                   <!--class="txbox"-->
                   <!--v-model="defaultScen.objective_weights.alive"/><br>-->
            <!--TB-related deaths:-->
            <!--<input type="text"-->
                   <!--class="txbox"-->
                   <!--v-model="defaultScen.objective_weights.ddis"/><br>-->
            <!--New TB infections:-->
            <!--<input type="text"-->
                   <!--class="txbox"-->
                   <!--v-model="defaultScen.objective_weights.acj"/><br>-->
            <!--<br>-->
            <!--<b>Relative spending constraints</b><br>-->
            <!--<table class="table table-bordered table-hover table-striped" style="width: 100%">-->
              <!--<thead>-->
              <!--<tr>-->
                <!--<th>Program</th>-->
                <!--<th>Minimum</th>-->
                <!--<th>Maximum</th>-->
              <!--</tr>-->
              <!--</thead>-->
              <!--<tbody>-->
              <!--<tr v-for="(val,key) in defaultScen.prog_spending">-->
                <!--<td>-->
                  <!--{{ key }}-->
                <!--</td>-->
                <!--<td>-->
                  <!--<input type="text"-->
                         <!--class="txbox"-->
                         <!--v-model="defaultScen.prog_spending[key][0]"/>-->
                <!--</td>-->
                <!--<td>-->
                  <!--<input type="text"-->
                         <!--class="txbox"-->
                         <!--v-model="defaultScen.prog_spending[key][1]"/>-->
                <!--</td>-->
              <!--</tr>-->
              <!--</tbody>-->
            <!--</table>-->
          </div>
          <div style="text-align:justify">
            <button @click="addScen()" class='btn __green' style="display:inline-block">
              Save scenario
            </button>
            <button @click="$modal.hide('add-scen')" class='btn __red' style="display:inline-block">
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
  import progressIndicator from '@/services/progress-indicator-service'
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
        defaultScen: [],
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
      }
    },

    computed: {
      activeProjectID() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
//          WARNING, these shouldn't be duplicated!
          this.getScenSummaries()
          this.getDefaultScen()
          this.updateSets()
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
        this.getScenSummaries()
        this.getDefaultScen()
        this.updateSets()
      }
    },

    methods: {

      dcp(input) {
        var output = JSON.parse(JSON.stringify(input))
        return output
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
          })
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
      },

      getDefaultScen() {
        console.log('getDefaultScen() called')
        rpcservice.rpcCall('get_default_scen', [this.projectID()])
          .then(response => {
            this.defaultScen = response.data // Set the scenario to what we received.
            console.log('This is the default:')
            console.log(this.defaultScen);
          });
      },

      getScenSummaries() {
        console.log('getScenSummaries() called')
        // Get the current project's scenario summaries from the server.
        rpcservice.rpcCall('get_scen_info', [this.projectID()])
          .then(response => {
            this.scenSummaries = response.data // Set the scenarios to what we received.
            this.$notifications.notify({
              message: 'scenarios loaded',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      setScenSummaries() {
        console.log('setScenSummaries() called')
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'scenarios saved',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      addBudgetScenModal() {
        // Open a model dialog for creating a new project
        console.log('addScenModal() called');
        rpcservice.rpcCall('get_default_scen', [this.projectID()])
          .then(response => {
            this.defaultScen = response.data // Set the scenario to what we received.
            this.$modal.show('add-scen');
            console.log(this.defaultScen)
          });
      },

      addBudgetScen() {
        console.log('addBudgetScen() called')
        this.$modal.hide('add-budget-scen')
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
            this.$notifications.notify({
              message: 'scenario added',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      openScen(scenSummary) {
        // Open a model dialog for creating a new project
        console.log('openScen() called');
        this.currentScen = scenSummary.name
        this.$notifications.notify({
          message: 'scenario "'+scenSummary.name+'" opened',
          icon: 'ti-check',
          type: 'success',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      },

      editScen(scenSummary) {
        // Open a model dialog for creating a new project
        console.log('editScen() called');
        this.defaultScen = scenSummary
        console.log('defaultScen', this.defaultScen.obj)
        this.$modal.show('add-scen');
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        var newScen = this.dcp(scenSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = this.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Opimization copied',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      deleteScen(scenSummary) {
        console.log('deleteScen() called')
        for(var i = 0; i< this.scenSummaries.length; i++) {
          if(this.scenSummaries[i].name === scenSummary.name) {
            this.scenSummaries.splice(i, 1);
          }
        }
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'scenario deleted',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      runScen(scenSummary) {
        console.log('runScen() called for '+this.currentScen)
        // Make sure they're saved first
        this.$modal.show('popup-spinner') // Dispel the spinner.
        rpcservice.rpcCall('set_scen_info', [this.projectID(), this.scenSummaries])
          .then(response => {
            // Go to the server to get the results from the package set.
            rpcservice.rpcCall('run_scenarios',
//            taskservice.getTaskResultPolling('run_scenario', 90, 3, 'run_scenario',
              [this.projectID(), scenSummary.name])
              .then(response => {
                this.serverresponse = response.data // Pull out the response data.
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
                    mpld3.draw_figure(divlabel, response.data.graphs[index]); // Draw the figure.
                    this.haveDrawnGraphs = true
                  }
                  catch (err) {
                    console.log('failled:' + err.message);
                  }
                }
                this.$modal.hide('popup-spinner') // Dispel the spinner.
                this.$Progress.finish() // Finish the loading bar.
                this.$notifications.notify({ // Success popup.
                  message: 'Graphs created',
                  icon: 'ti-check',
                  type: 'success',
                  verticalAlign: 'top',
                  horizontalAlign: 'center',
                })
              })
              .catch(error => {
                this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
                this.servererror = error.message // Set the server error.
                this.$modal.hide('popup-spinner') // Dispel the spinner.
                this.$Progress.fail() // Fail the loading bar.
                this.$notifications.notify({ // Failure popup.
                  message: 'Could not make graphs',
                  icon: 'ti-face-sad',
                  type: 'warning',
                  verticalAlign: 'top',
                  horizontalAlign: 'center',
                })
              })
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
            mpld3.draw_figure(divlabel, response.data.graphs[index]); // Draw the figure.
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
<style scoped>
</style>