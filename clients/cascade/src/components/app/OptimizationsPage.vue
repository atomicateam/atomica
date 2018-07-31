<!--
Optimizations Page

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


      <modal name="add-optim"
             height="auto"
             :classes="['v--modal', 'vue-dialog']"
             :width="width"
             :pivot-y="0.3"
             :adaptive="true"
             :clickToClose="clickToClose"
             :transition="transition">

        <div class="dialog-content">
          <div class="dialog-c-title">
            Add/edit optimization
          </div>
          <div class="dialog-c-text">
            Optimization name:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.name"/><br>
            Parameter set name:<br>
            <select v-model="defaultOptim.parsetname">
              <option v-for='parset in parsetOptions'>
                {{ parset }}
              </option>
            </select><br><br>
            Program set name:<br>
            <select v-model="defaultOptim.progsetname">
              <option v-for='progset in progsetOptions'>
                {{ progset }}
              </option>
            </select><br><br>
            Optimization objective:<br>
            <select v-model="defaultOptim.obj">
              <option v-for='obj in objectiveOptions'>
                {{ obj }}
              </option>
            </select><br><br>
            Budget multiplier:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.budget_factor"/><br>
            Additional funds:<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.add_funds"/><br>
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

      <div>
        <div v-for="index in placeholders" :id="'fig'+index" style="width:650px; float:left;">
          <!--mpld3 content goes here-->
        </div>
      </div>
      
      <!-- Popup spinner -->
      <popup-spinner></popup-spinner>
    
    </div>
  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
//  import taskservice from '@/services/task-service'
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

      getDefaultOptim() {
        console.log('getDefaultOptim() called')
        rpcservice.rpcCall('get_default_optim', [this.projectID()])
          .then(response => {
            this.defaultOptim = response.data // Set the optimization to what we received.
            this.objectiveOptions = response.data.objective_options
            console.log('TEMPPPPPPP these are the options:'+this.objectiveOptions);
          });
      },

      getOptimSummaries() {
        console.log('getOptimSummaries() called')
        // Get the current project's optimization summaries from the server.
        rpcservice.rpcCall('get_optim_info', [this.projectID()])
          .then(response => {
            this.optimSummaries = response.data // Set the optimizations to what we received.
            this.$notifications.notify({
              message: 'Optimizations loaded',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      setOptimSummaries() {
        console.log('setOptimSummaries() called')
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Optimizations saved',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
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
          });
      },

      addOptim() {
        console.log('addOptim() called')
        this.$modal.hide('add-optim')
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
            this.$notifications.notify({
              message: 'Optimization added',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      openOptim(optimSummary) {
        // Open a model dialog for creating a new project
        console.log('openOptim() called');
        this.currentOptim = optimSummary.name
        this.$notifications.notify({
          message: 'Optimization "'+optimSummary.name+'" opened',
          icon: 'ti-check',
          type: 'success',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
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
        var newOptim = this.dcp(optimSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        })
        newOptim.name = this.getUniqueName(newOptim.name, otherNames)
        this.optimSummaries.push(newOptim)
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
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

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        for(var i = 0; i< this.optimSummaries.length; i++) {
          if(this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Optimization deleted',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      runOptim(optimSummary) {
        console.log('runOptim() called for '+this.currentOptim)

//        rpcservice.rpcCall('launch_task', ['my_crazy_id', 'async_add', [23, 57]])
//        rpcservice.rpcCall('check_task', ['my_crazy_id'])
//        rpcservice.rpcCall('get_task_result', ['my_crazy_id'])
//        rpcservice.rpcCall('delete_task', ['my_crazy_id'])
//        rpcservice.rpcCall('delete_task', ['run_optimization'])

        // Do an async_add() and try for at most 15 sec. to get a result, polling every 5 sec.
        // Should succeed.
        /*          taskservice.getTaskResultPolling('run_optimization', 15, 3, 'run_optim', [23, 57])
         .then(response => {
         console.log('The result is: ' + response.data.result)
         }) */

        // Make sure they're saved first
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then(response => {

            // Go to the server to get the results from the package set.
//          rpcservice.rpcCall('run_optim', [this.projectID(), optimSummary.name])
            taskservice.getTaskResultPolling('run_optimization', 9999, 3, 'run_optim',
              [this.projectID(), optimSummary.name])
              .then(response => {
                this.clearGraphs() // Once we receive a response, we can work with a clean slate
//            this.graphData = response.data.graphs // Pull out the response data (use with the rpcCall).
                this.graphData = response.data.result.graphs // Pull out the response data (use with task).
                let n_plots = this.graphData.length
                console.log('Rendering ' + n_plots + ' graphs')

                for (var index = 0; index <= n_plots; index++) {
                  console.log('Rendering plot ' + index)
                  var divlabel = 'fig' + index
                  var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
                  while (div.firstChild) {
                    div.removeChild(div.firstChild);
                  }
                  try {
//                mpld3.draw_figure(divlabel, response.data.graphs[index]); // Draw the figure (use with the rpcCall).
                    mpld3.draw_figure(divlabel, response.data.result.graphs[index]); // Draw the figure (use with task).
                  }
                  catch (err) {
                    console.log('failled:' + err.message);
                  }
                }

                // Success popup.
                this.$notifications.notify({
                  message: 'Graphs created',
                  icon: 'ti-check',
                  type: 'success',
                  verticalAlign: 'top',
                  horizontalAlign: 'center',
                })
              })
              .catch(error => {
                // Pull out the error message.
                this.serverresponse = 'There was an error: ' + error.message

                // Set the server error.
                this.servererror = error.message

                // Put up a failure notification.
                this.$notifications.notify({
                  message: 'Optimization failed',
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
