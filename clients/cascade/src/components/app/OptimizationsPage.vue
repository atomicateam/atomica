<!--
Optimizations Page

Last update: 2018-08-12
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
        &nbsp;&nbsp;&nbsp;
        <button class="btn" @click="clearGraphs()">Clear graphs</button>
        <!--<button class="btn" @click="toggleShowingPlots()">-->
          <!--<span v-if="areShowingPlots">Hide</span>-->
          <!--<span v-else>Show</span>-->
          <!--plot controls-->
        <!--</button>-->
        &nbsp;&nbsp;&nbsp;
        <button class="btn" @click="plotOptimization()">Refresh</button>
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
        </div>
      </div>


      <div class="calib-figures">
        <div class="calib-graphs">
          <div v-for="index in placeholders" :id="'fig'+index">
            <!--mpld3 content goes here-->
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
      </div>



      <div class="plotopts-main" :class="{'plotopts-main--full': !areShowingPlots}" style="max-width:400px">
        <div class="plotopts-params" v-if="areShowingPlots">
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
            Program set:<br>
            <select v-model="progsetOptions[0]">
              <option v-for='progset in progsetOptions'>
                {{ progset }}
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
  import rpcservice from '@/services/rpc-service'
  import taskservice from '@/services/task-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import Vue from 'vue';

  export default {
    name: 'OptimizationPage',

    data() {
      return {
        serverresponse: 'no response',
        optimSummaries: [],
        defaultOptim: [],
        modalOptim: [],
        objectiveOptions: [],
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions:  [],
        progsetOptions: [],
        newParsetName:  [],
        newProgsetName: [],
        graphData: [],
        areShowingPlots: false,
        plotOptions: [],
        table: null,
        endYear: 2018,
        addEditDialogMode: 'add',  // or 'edit'
        addEditDialogOldName: '',
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
      else if (this.$store.state.activeProject.project != undefined) { // Otherwise...
        this.sleep(1)  // used so that spinners will come up by callback func
        .then(response => {
          // Load the optimization summaries of the current project.
          this.getOptimSummaries()
          this.getDefaultOptim()
          this.sleep(1)  // used so that spinners will come up by callback func
            .then(response => {
              this.resetModal()
            })
          this.updateSets()
          this.getPlotOptions()          
        })
        // Load the optimization summaries of the current project.
/*        this.getOptimSummaries()
        this.getDefaultOptim()
        this.updateSets()
        this.getPlotOptions()  */      
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

      getDefaultOptim() {
        console.log('getDefaultOptim() called')
        rpcservice.rpcCall('get_default_optim', [this.projectID()])
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
        this.resetModal()
        rpcservice.rpcCall('get_default_optim', [this.projectID()])
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
        let newOptim = this.dcp(this.modalOptim) // Not sure if dcp is necessary
        
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
          newOptim.name = this.getUniqueName(newOptim.name, optimNames)
          this.optimSummaries.push(newOptim)
        }       
        
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
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
        this.modalOptim = this.dcp(this.defaultOptim)
        console.log(this.modalOptim)
      },

      editOptim(optimSummary) {
        // Open a model dialog for creating a new project
        console.log('editOptim() called');
        this.modalOptim = this.dcp(optimSummary)
        console.log('defaultOptim', this.defaultOptim.obj)
        this.addEditDialogMode = 'edit'
        this.addEditDialogOldName = this.modalOptim.name
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
          console.log('Trying ' + this.optimSummaries[i].name + ' vs ' + optimSummary.name)
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
          taskservice.getTaskResultPolling('run_cascade_optimization', 9999, 3, 'run_cascade_optimization',
            [this.projectID(), optimSummary.name, this.plotOptions, true, this.endYear])
          .then(response => {
            this.serverresponse = response.data // Pull out the response data.
//                this.graphData = response.data.graphs // Pull out the response data (use with the rpcCall).
            this.table = response.data.result.table
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

      plotOptimization() {
        console.log('plotOptimization() called')
        status.start(this)
        this.$Progress.start(2000)  // restart just the progress bar, and make it slower
        // Make sure they're saved first
        rpcservice.rpcCall('plot_optimization', [this.projectID(), this.plotOptions], {tool:'cascade', plotyear:this.endYear})
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
                console.log('Graph failed:' + err.message);
              }
            }
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
            this.servererror = error.message // Set the server error.
            status.fail(this, 'Could not make graphs') // Indicate failure.
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
  .calib-graphs {
    display: flex;
    flex-wrap: wrap;
    & > * {
      flex: 0 0 650px;
    }
  }

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
  .controls-box {
    border: 2px solid #ddd;
    padding: 7px;
    display: inline-block;
  }
</style>
