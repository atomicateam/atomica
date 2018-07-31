<!--
Define equity

Last update: 2018-07-30
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
        <tr v-for="optimSummary in optimSummaries">
          <td>
            <b>{{ optimSummary.name }}</b>
          </td>
          <td style="white-space: nowrap">
            <button class="btn __green" @click="runOptim(optimSummary)">Run</button>
            <button class="btn" @click="editOptim(optimSummary)">Edit</button>
            <button class="btn" @click="copyOptim(optimSummary)">Copy</button>
            <button class="btn" @click="deleteOptim(optimSummary)">Delete</button>
          </td>
        </tr>
        </tbody>
      </table>

      <div>
        <button class="btn __blue" @click="addOptimModal()">Add optimization</button>
        <button class="btn" @click="clearGraphs()">Clear graphs</button>
      </div>

      <div>
        <div v-for="index in placeholders" :id="'fig'+index" style="width:650px; float:left;">
          <!--mpld3 content goes here-->
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

        <!--TO_PORT-->
        <div class="dialog-content">
          <div class="dialog-c-title">
            Add/edit optimization
          </div>
          <div class="dialog-c-text">
            Optimization name:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.name"/><br>
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
            Maximum time to run optimization (s):<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.maxtime"/><br>
            Start year:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.start_year"/><br>
            End year:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.end_year"/><br>
            Budget factor:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.budget_factor"/><br>
            <br>
            <b>Relative objective weights</b><br>
            People alive:
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.objective_weights.alive"/><br>
            TB-related deaths:
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.objective_weights.ddis"/><br>
            New TB infections:
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.objective_weights.acj"/><br>
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
              <tr v-for="(val,key) in defaultOptim.prog_spending">
                <td>
                  {{ defaultOptim.prog_spending[key].label }}
                </td>
                <td>
                  <input type="text"
                         class="txbox"
                         v-model="defaultOptim.prog_spending[key].min"/>
                </td>
                <td>
                  <input type="text"
                         class="txbox"
                         v-model="defaultOptim.prog_spending[key].max"/>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
          <div style="text-align:justify">
            <button @click="addOptim()" class='btn __green' style="display:inline-block">
              Save optimization
            </button>
            <button @click="$modal.hide('add-optim')" class='btn __red' style="display:inline-block">
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
    name: 'OptimizationPage',

    components: {
      PopupSpinner
    },

    data() {
      return {
        serverresponse: 'no response',
        optimSummaries: [],
        defaultOptim: [],
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
        graphData: [],
      }
    },

    computed: {
      activeProjectID() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
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
        // Load the optimization summaries of the current project.
        this.getOptimSummaries()
        this.getDefaultOptim()
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

      getDefaultOptim() {
        console.log('getDefaultOptim() called')
        rpcservice.rpcCall('get_default_optim', [this.projectID()])
        .then(response => {
          this.defaultOptim = response.data // Set the optimization to what we received.
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
        rpcservice.rpcCall('get_optim_info', [this.projectID()])
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
        
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
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
        rpcservice.rpcCall('get_default_optim', [this.projectID()])
        .then(response => {
          this.defaultOptim = response.data // Set the optimization to what we received.
          this.$modal.show('add-optim');
          console.log(this.defaultOptim)
        })
      },

      addOptim() {
        console.log('addOptim() called')
        this.$modal.hide('add-optim')
        
        // Start indicating progress.
        status.start(this)
        
        let newOptim = this.dcp(this.defaultOptim); // You've got to be kidding me, buster
        let otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        });
        let index = otherNames.indexOf(newOptim.name);
        if (index > -1) {
          console.log('Optimization named '+newOptim.name+' exists, overwriting...')
          this.optimSummaries[index] = newOptim
        }
        else {
          console.log('Optimization named '+newOptim.name+' does not exist, creating new...')
          this.optimSummaries.push(newOptim)
        }
        console.log(newOptim)
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Optimization added')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not add optimization')
          
          // TODO: Should probably fix the corrupted this.optimSummaries.
        })        
      },

      editOptim(optimSummary) {
        // Open a model dialog for creating a new project
        console.log('editOptim() called');
        this.defaultOptim = optimSummary
        console.log('defaultOptim', this.defaultOptim.obj)
        this.$modal.show('add-optim');
      },

      copyOptim(optimSummary) {
        console.log('copyOptim() called')
        
        // Start indicating progress.
        status.start(this)
        
        var newOptim = this.dcp(optimSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        })
        newOptim.name = this.getUniqueName(newOptim.name, otherNames)
        this.optimSummaries.push(newOptim)
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
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
          if(this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Optimization deleted')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not delete optimization')
          
          // TODO: Should probably fix the corrupted this.optimSummaries.
        })        
      },

      runOptim(optimSummary) {
        console.log('runOptim() called for '+this.currentOptim)
        // Start indicating progress.
        status.start(this)
        this.$Progress.start(9000)  // restart just the progress bar, and make it slower        
        // Make sure they're saved first
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
        .then(response => {          
          // Go to the server to get the results from the package set.
//            rpcservice.rpcCall('run_optimization',
          taskservice.getTaskResultPolling('run_optimization', 90, 3, 'run_optimization',
            [this.projectID(), optimSummary.name])
          .then(response => {
            this.serverresponse = response.data // Pull out the response data.
//                this.graphData = response.data.graphs // Pull out the response data (use with the rpcCall).
            this.graphData = response.data.result.graphs // Pull out the response data (use with task).
            var n_plots = this.graphData.length
            console.log('Rendering ' + n_plots + ' graphs')
            for (var index = 0; index <= n_plots; index++) {
              console.log('Rendering plot ' + index)
              var divlabel = 'fig' + index
              var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
              while (div.firstChild) {
                div.removeChild(div.firstChild);
              }
              try {
                console.log(this.graphData[index]);
                mpld3.draw_figure(divlabel, this.graphData[index], function(fig, element) {
                  fig.setXTicks(6, function(d) { return d3.format('.0f')(d); });
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

      reloadGraphs() {
        console.log('Reload graphs')
        let n_plots = this.graphData.length
        console.log('Rendering ' + n_plots + ' graphs')
        for (let index = 0; index <= n_plots; index++) {
          console.log('Rendering plot ' + index)
          var divlabel = 'fig' + index
          try {
            mpld3.draw_figure(divlabel, response.data.graphs[index], function(fig, element) {
              fig.setXTicks(6, function(d) { return d3.format('.0f')(d); });
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
<style scoped>
</style>
