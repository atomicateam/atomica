<!--
Optimizations Page

Last update: 2018-08-15
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
            <button class="btn" @click="runOptim(optimSummary, 15)">Test run</button>
            <button class="btn" @click="editOptim(optimSummary)">Edit</button>
            <button class="btn" @click="copyOptim(optimSummary)">Copy</button>
            <button class="btn" @click="deleteOptim(optimSummary)">Delete</button>
          </td>
        </tr>
        </tbody>
      </table>

      <div>
        <div style="text-align: center">
          <div class="controls-box">
            <button class="btn" @click="exportGraphs(projectID)">Export graphs</button>
            <button class="btn" @click="exportResults(projectID)">Export data</button>
          </div>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
          <div class="controls-box">
            <button class="btn" @click="clearGraphs()">Clear graphs</button>
            <button class="btn" @click="toggleShowingPlotControls()"><span v-if="areShowingPlotControls">Hide</span><span v-else>Show</span> plot controls</button>
          </div>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
          <div class="controls-box">
            <button class="btn" @click="scaleFigs(0.9)">-</button>
            <button class="btn" @click="scaleFigs(1.0)">Scale</button>
            <button class="btn" @click="scaleFigs(1.1)">+</button>
          </div>
        </div>

        <div class="calib-main" :class="{'calib-main--full': !areShowingPlotControls}">
          <div class="calib-graphs">
            <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
              <!--mpld3 content goes here-->
            </div>
          </div>

          <div class="plotopts-main" :class="{'plotopts-main--full': !areShowingPlotControls}" v-if="areShowingPlotControls">
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
    name: 'OptimizationPage',

    data() {
      return {
        response: 'no response',
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
        areShowingPlotControls: false,
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
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      simStart()     { return utils.simStart(this) },
      simEnd()       { return utils.simEnd(this) },
      placeholders() { return utils.placeholders() },
    },

    created() {
      if (this.$store.state.currentUser.displayname == undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      } else if ((this.projectID != '') && (this.hasData) ) {
        this.getOptimSummaries() // Load the optimization summaries of the current project.
        this.getDefaultOptim()
        this.updateSets()
        this.getPlotOptions()
      }
    },

    methods: {

      getPlotOptions()          { return utils.getPlotOptions(this) },
      clearGraphs()             { return utils.clearGraphs() },
      makeGraphs(graphdata)     { return utils.makeGraphs(this, graphdata) },
      exportGraphs(project_id)  { return utils.exportGraphs(this, project_id) },
      exportResults(project_id) { return utils.exportResults(this, project_id) },

      scaleFigs(frac) {
        this.figscale = this.figscale*frac;
        if (frac === 1.0) {
          frac = 1.0/this.figscale
        }
        this.figscale = 1.0
        return utils.scaleFigs(frac)
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
        rpcs.rpc('get_default_optim', [this.projectID])
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
        rpcs.rpc('get_optim_info', [this.projectID]) // Get the current project's optimization summaries from the server.
          .then(response => {
            this.optimSummaries = response.data // Set the optimizations to what we received.
            status.succeed(this, 'Optimizations loaded')
          })
          .catch(error => {
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
        rpcs.rpc('get_default_optim', [this.projectID])
          .then(response => {
            this.defaultOptim = response.data // Set the optimization to what we received.
            this.addEditModal.optimSummary = utils.dcp(this.defaultOptim)
            this.addEditModal.origName = this.addEditModal.optimSummary.name
            this.addEditModal.mode = 'add'
            this.$modal.show('add-optim');
            console.log(this.defaultOptim)
          })
      },

      addOptim() {
        console.log('addOptim() called')
        this.$modal.hide('add-optim')
        status.start(this)
        let newOptim = utils.dcp(this.addEditModal.optimSummary) // Get the new optimization summary from the modal.
        let optimNames = [] // Get the list of all of the current optimization names.
        this.optimSummaries.forEach(optimSum => {
          optimNames.push(optimSum.name)
        })
        if (this.addEditModal.mode == 'edit') { // If we are editing an existing optimization...
          let index = optimNames.indexOf(this.addEditModal.origName) // Get the index of the original (pre-edited) name
          if (index > -1) {
            this.optimSummaries[index].name = newOptim.name  // hack to make sure Vue table updated            
            this.optimSummaries[index] = newOptim
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }
        }
        else { // Else (we are adding a new optimization)...
          newOptim.name = utils.getUniqueName(newOptim.name, optimNames)
          this.optimSummaries.push(newOptim)
        }
        console.log(newOptim)
        console.log(this.optimSummaries)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization added')
          })
          .catch(error => {
            status.fail(this, 'Could not add optimization')
          })
      },

      editOptim(optimSummary) {
        console.log('editOptim() called');
        this.defaultOptim = optimSummary
        console.log('defaultOptim', this.defaultOptim.obj)
        this.addEditModal.optimSummary = utils.dcp(this.defaultOptim)
        this.addEditModal.origName = this.addEditModal.optimSummary.name
        this.addEditModal.mode = 'edit'
        this.$modal.show('add-optim');
      },

      copyOptim(optimSummary) {
        console.log('copyOptim() called')
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
            status.succeed(this, 'Opimization copied')
          })
          .catch(error => {
            status.fail(this, 'Could not copy optimization')
          })
      },

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        status.start(this)
        for(var i = 0; i< this.optimSummaries.length; i++) {
          if(this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization deleted')
          })
          .catch(error => {
            status.fail(this, 'Could not delete optimization')
          })
      },

      toggleShowingPlotControls() {
        this.areShowingPlotControls = !this.areShowingPlotControls
      },

      runOptim(optimSummary, maxtime) {
        console.log('runOptim() called for '+this.currentOptim)
        status.start(this)
        this.$Progress.start(9000)  // restart just the progress bar, and make it slower        
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then(response => {     // Go to the server to get the results
            taskservice.getTaskResultPolling('run_optimization', 9999, 3, 'run_optimization', [this.projectID, optimSummary.name, this.plotOptions, maxtime])
              .then(response => {
                this.response = response // Pull out the response data.
                console.log('ok done')
                console.log(this.response)
                this.makeGraphs(response.data.result.graphs)
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
      },
    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
