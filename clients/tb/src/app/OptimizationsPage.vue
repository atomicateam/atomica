<!--
Optimizations Page

Last update: 2018-08-15
-->

<template>
  <div class="SitePage">

    <div v-if="activeProjectID ==''">
      <div style="font-style:italic">
        <p>No project is loaded.</p>
      </div>
    </div>
    
    <div v-else-if="!activeProjectHasData">
      <div style="font-style:italic">
        <p>Data not yet uploaded for the project.  Please upload a databook in the Projects page.</p>
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
            <button class="btn __green" @click="runOptim(optimSummary, 3600)">Run</button>
            <button class="btn" @click="runOptim(optimSummary, 30)">Test run</button>
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
        <button class="btn" @click="toggleShowingPlots()">
          <span v-if="areShowingPlots">Hide</span>
          <span v-else>Show</span>
          plot controls
        </button>
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
        <div class="calib-graphs">
          <div v-for="index in placeholders" :id="'fig'+index">
            <!--mpld3 content goes here-->
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
          <div class="dialog-c-title" v-if="addEditModal.mode=='add'">
            Add scenario
          </div>
          <div class="dialog-c-title" v-else>
            Edit scenario
          </div>
          <div class="dialog-c-text">
            Optimization name:<br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.name"/><br>
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
            Start year:<br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.start_year"/><br>
            End year:<br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.end_year"/><br>
            Budget factor:<br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.budget_factor"/><br>
            <br>
            <b>Relative objective weights</b><br>
            People alive:
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.objective_weights.alive"/><br>
            TB-related deaths:
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.objective_weights.ddis"/><br>
            New TB infections:
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.objective_weights.acj"/><br>
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
              <tr v-for="(val,key) in addEditModal.optimSummary.prog_spending">
                <td>
                  {{ addEditModal.optimSummary.prog_spending[key].label }}
                </td>
                <td>
                  <input type="text"
                         class="txbox"
                         v-model="addEditModal.optimSummary.prog_spending[key].min"/>
                </td>
                <td>
                  <input type="text"
                         class="txbox"
                         v-model="addEditModal.optimSummary.prog_spending[key].max"/>
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

    </div>
  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcs from '@/services/rpc-service'
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
        defaultOptim: {  
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
        areShowingPlots: false,
        plotOptions: [],
        addEditModal: {
          optimSummary: {
            // set stuff here to avoid render errors before things are loaded
            objective_weights: {
              conversion: 0, 
              finalstage: 1
            }              
          },    
          origName: '',
          mode: 'add'
        }        
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
      
      activeProjectHasData() {
        if (this.$store.state.activeProject.project === undefined) {
          return false
        }
        else {        
          return this.$store.state.activeProject.project.hasData
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
      } else if ((this.$store.state.activeProject.project != undefined) && 
        (this.$store.state.activeProject.project.hasData) ) {
        // Load the optimization summaries of the current project.
        this.getOptimSummaries()
        this.getDefaultOptim()
        this.updateSets()
        this.getPlotOptions()
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
        rpcs.rpc('get_parset_info', [this.projectID()])
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
          rpcs.rpc('get_progset_info', [this.projectID()])
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
        rpcs.rpc('get_default_optim', [this.projectID()])
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
        rpcs.rpc('get_optim_info', [this.projectID()])
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
        
        rpcs.rpc('set_optim_info', [this.projectID(), this.optimSummaries])
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
        rpcs.rpc('get_default_optim', [this.projectID()])
        .then(response => {
          this.defaultOptim = response.data // Set the optimization to what we received.
          this.addEditModal.optimSummary = this.dcp(this.defaultOptim)
          this.addEditModal.origName = this.addEditModal.optimSummary.name
          this.addEditModal.mode = 'add'           
          this.$modal.show('add-optim');
          console.log(this.defaultOptim)
        })
      },

      addOptim() {
        console.log('addOptim() called')
        this.$modal.hide('add-optim')
        
        // Start indicating progress.
        status.start(this)       
        
        // Get the new optimization summary from the modal.
        let newOptim = this.dcp(this.addEditModal.optimSummary)
  
        // Get the list of all of the current optimization names.
        let optimNames = []
        this.optimSummaries.forEach(optimSum => {
          optimNames.push(optimSum.name)
        })
               
        // If we are editing an existing optimization...
        if (this.addEditModal.mode == 'edit') {
          // Get the index of the original (pre-edited) name
          let index = optimNames.indexOf(this.addEditModal.origName)
          if (index > -1) {
            this.optimSummaries[index].name = newOptim.name  // hack to make sure Vue table updated            
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
        console.log(newOptim)
        console.log(this.optimSummaries)
                
        rpcs.rpc('set_optim_info', [this.projectID(), this.optimSummaries])
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
        this.addEditModal.optimSummary = this.dcp(this.defaultOptim)
        this.addEditModal.origName = this.addEditModal.optimSummary.name         
        this.addEditModal.mode = 'edit'          
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
        rpcs.rpc('set_optim_info', [this.projectID(), this.optimSummaries])
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
        rpcs.rpc('set_optim_info', [this.projectID(), this.optimSummaries])
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
        rpcs.rpc('get_supported_plots', [true])
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

      runOptim(optimSummary, maxtime) {
        console.log('runOptim() called for '+this.currentOptim)
        // Start indicating progress.
        status.start(this)
        this.$Progress.start(9000)  // restart just the progress bar, and make it slower        
        // Make sure they're saved first
        rpcs.rpc('set_optim_info', [this.projectID(), this.optimSummaries])
        .then(response => {          
          // Go to the server to get the results from the package set.
//            rpcs.rpc('run_optimization',
          taskservice.getTaskResultPolling('run_optimization', 9999, 3, 'run_optimization',
            [this.projectID(), optimSummary.name, this.plotOptions, maxtime])
          .then(response => {
            this.serverresponse = response.data // Pull out the response data.
//                this.graphData = response.data.graphs // Pull out the response data (use with the rpc).
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
  .calib-main {
    display: flex;
    margin-top: 4rem;
  }
  .calib-params {
    flex: 0 0 30%;
  }
  .calib-graphs {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    & > div {
      flex: 0 0 650px;
    }
  }
</style>
