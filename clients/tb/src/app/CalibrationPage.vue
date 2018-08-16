<!--
Calibration Page

Last update: 2018-08-16
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
      <div class="calib-controls">
        <button class="btn __green" @click="manualCalibration(projectID)">Save & run</button>
        <button class="btn" @click="toggleShowingParams()">
          <span v-if="areShowingParameters">Hide</span>
          <span v-else>Show</span>
          parameters
        </button>
        <div class="controls-box">
          <button class="btn" @click="autoCalibrate(projectID)">Automatic calibration</button>
          for&nbsp;
          <select v-model="calibTime">
            <option v-for='time in calibTimes'>
              {{ time }}
            </option>
          </select>
        </div>

        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <div class="controls-box">
        <!--<div style="display: inline-block; padding-left: 100px">-->
          <b>Parameter set: &nbsp;</b>
          <select v-model="activeParset">
            <option v-for='parset in parsetOptions'>
              {{ parset }}
            </option>
          </select>
          &nbsp;
          <button class="btn small-button" @click="renameParsetModal()" data-tooltip="Rename">
            <i class="ti-pencil"></i>
          </button>
          <button class="btn small-button" @click="copyParset()" data-tooltip="Copy">
            <i class="ti-files"></i>
          </button>
          <button class="btn small-button" @click="deleteParset()" data-tooltip="Delete">
            <i class="ti-trash"></i>
          </button>
        </div>

        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <div class="controls-box">
          <b>Start year: &nbsp;</b>
          <input type="text"
                 class="txbox"
                 v-model="startYear"
                 style="display: inline-block; width:70px"/>
          &nbsp;&nbsp;&nbsp;
          <b>End year: &nbsp;</b>
          <input type="text"
                 class="txbox"
                 v-model="endYear"
                 style="display: inline-block; width:70px"/>
        </div>

        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;


      </div>
      
       <div style="text-align: center">
        <button class="btn" @click="exportGraphs(projectID)">Export graphs</button>
        <button class="btn" @click="exportResults(projectID)">Export data</button>
        <button class="btn" @click="clearGraphs()">Clear graphs</button>
        <button class="btn" @click="toggleShowingPlots()"><span v-if="areShowingPlots">Hide</span><span v-else>Show</span> plot controls</button>
      </div>
          
      <div class="calib-main" :class="{'calib-main--full': !areShowingParameters}">
        <div class="calib-params" v-if="areShowingParameters">
          <table class="table table-bordered table-hover table-striped" style="width: 100%">
            <thead>
            <tr>
              <th @click="updateSorting('index')" class="sortable">
                No.
                <span v-show="sortColumn == 'index' && !sortReverse"><i class="fas fa-caret-down"></i></span>
                <span v-show="sortColumn == 'index' && sortReverse"><i class="fas fa-caret-up"></i></span>
                <span v-show="sortColumn != 'index'"><i class="fas fa-caret-up" style="visibility: hidden"></i></span>
              </th>
              <th @click="updateSorting('parameter')" class="sortable">
                Parameter
                <span v-show="sortColumn == 'parameter' && !sortReverse"><i class="fas fa-caret-down"></i></span>
                <span v-show="sortColumn == 'parameter' && sortReverse"><i class="fas fa-caret-up"></i></span>
                <span v-show="sortColumn != 'parameter'"><i class="fas fa-caret-up" style="visibility: hidden"></i></span>
              </th>
              <th @click="updateSorting('population')" class="sortable">
                Population
                <span v-show="sortColumn == 'population' && !sortReverse"><i class="fas fa-caret-down"></i></span>
                <span v-show="sortColumn == 'population' && sortReverse"><i class="fas fa-caret-up"></i></span>
                <span v-show="sortColumn != 'population'"><i class="fas fa-caret-up" style="visibility: hidden"></i></span>
              </th>
              <th @click="updateSorting('value')" class="sortable">
                Value
                <span v-show="sortColumn == 'value' && !sortReverse"><i class="fas fa-caret-down"></i></span>
                <span v-show="sortColumn == 'value' && sortReverse"><i class="fas fa-caret-up"></i></span>
                <span v-show="sortColumn != 'value'"><i class="fas fa-caret-up" style="visibility: hidden"></i></span>
              </th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="par in sortedPars">
              <td>
                {{par.index}}
              </td>
              <td>
                {{par.parlabel}}
              </td>
              <td>
                {{par.poplabel}}
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       v-model="par.dispvalue"/>
              </td>
            </tr>
            </tbody>
          </table>
        </div>

        <div class="calib-graphs">
          <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
            <!--mpld3 content goes here-->
          </div>
        </div>

        <div class="plotopts-main" :class="{'plotopts-main--full': !areShowingPlots}">
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

      </div>
      
    </div>

    <modal name="rename-parset"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Rename parameter set
        </div>
        <div class="dialog-c-text">
          New name:<br>
          <input type="text"
                 class="txbox"
                 v-model="newParsetName"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="renameParset()" class='btn __green' style="display:inline-block">
            Rename
          </button>

          <button @click="$modal.hide('rename-parset')" class='btn __red' style="display:inline-block">
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
  import status from '@/services/status-service'
  import router from '@/router'
  import Vue from 'vue'
  
  export default {
    name: 'CalibrationPage',
    
    data() {
      return {
        response: 'no response',
        sortColumn: 'index',
        sortReverse: false,
        parList: [],
        areShowingParameters: false,
        areShowingPlots: false,
        activeParset: -1,
        parsetOptions: [],
        newParsetName: [],
        startYear: 0,
        endYear: 0,
        plotOptions: [],
        calibTime: '30 seconds',
        calibTimes: ['30 seconds', 'Unlimited']
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      simStart()     { return utils.simStart(this) },
      simEnd()       { return utils.simEnd(this) },
      placeholders() { return utils.placeholders() },

      sortedPars() {
        var sortedParList = this.applySorting(this.parList);
        return sortedParList;
      },

    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      } else if ((this.$store.state.activeProject.project != undefined) && 
        (this.$store.state.activeProject.project.hasData) ) {
        this.startYear = this.simStart
        this.endYear = this.simEnd
        this.viewTable()
        this.getPlotOptions()
        this.updateParset()
        utils.sleep(1000)
          .then(response => {
            this.manualCalibration(this.projectID)
            }
          );
      }
    },

    methods: {

      getPlotOptions()          { return utils.getPlotOptions(this) },
      clearGraphs()             { return utils.clearGraphs() },
      makeGraphs(graphdata)     { return utils.makeGraphs(this, graphdata) },
      exportGraphs(project_id)  { return utils.exportGraphs(this, project_id) },
      exportResults(project_id) { return utils.exportResults(this, project_id) },
      
      updateParset() {
        console.log('updateParset() called')
        status.start(this) // Note: For some reason, the popup spinner doesn't work from inside created() so it doesn't show up here.        
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
          status.succeed(this, '')  // No green notification.
        })
        .catch(error => {
          status.fail(this, 'Could not update parset')
        })         
      },

      updateSorting(sortColumn) {
        console.log('updateSorting() called')
        if (this.sortColumn === sortColumn) {  // If the active sorting column is clicked... // Reverse the sort.
          this.sortReverse = !this.sortReverse
        }
        else { // Otherwise.
          this.sortColumn = sortColumn // Select the new column for sorting.
          this.sortReverse = false // Set the sorting for non-reverse.
        }
      },

      applySorting(pars) {
        return pars.slice(0).sort((par1, par2) =>
          {
            let sortDir = this.sortReverse ? -1: 1
            if      (this.sortColumn === 'index')      { return par1.index     > par2.index     ? sortDir: -sortDir}
            else if (this.sortColumn === 'parameter')  { return par1.parlabel  > par2.parlabel  ? sortDir: -sortDir}
            else if (this.sortColumn === 'population') { return par1.poplabel  > par2.poplabel  ? sortDir: -sortDir}
            else if (this.sortColumn === 'value')      { return par1.dispvalue > par2.dispvalue ? sortDir: -sortDir}
          }
        )
      },

      viewTable() {
        console.log('viewTable() called')
        rpcs.rpc('get_y_factors', [this.$store.state.activeProject.project.id, this.activeParset])
        .then(response => {
          this.parList = response.data // Get the parameter values
        })
        .catch(error => {
          status.failurePopup(this, 'Could not load parameters: ' + error.message)
        })
      },

      toggleShowingParams() {
        this.areShowingParameters = !this.areShowingParameters
      },

      toggleShowingPlots() {
        this.areShowingPlots = !this.areShowingPlots
      },

      manualCalibration(project_id) {
        console.log('manualCalibration() called')
        status.start(this) // Start indicating progress.
        rpcs.rpc('manual_calibration', [project_id, this.activeParset, this.parList, this.plotOptions, this.startYear, this.endYear]) // Go to the server to get the results from the package set.
          .then(response => {
            status.succeed(this, 'Simulation run') // Indicate success.
            this.makeGraphs(response.data.graphs)
          })
          .catch(error => {
            console.log(error.message)
            status.fail(this, 'Could not run manual calibration: ' + error.message)
          })
      },

      autoCalibrate(project_id) {
        console.log('autoCalibrate() called')
        status.start(this) // Start indicating progress.
        this.$Progress.start(7000)
        if (this.calibTime === '30 seconds') {
          let maxtime = 30
        } else {
          let maxtime = 9999
        }
        rpcs.rpc('automatic_calibration', [project_id, this.activeParset, maxtime]) // Go to the server to get the results from the package set.
          .then(response => {
            this.makeGraphs(response.data.graphs)
          })
          .catch(error => {
            console.log(error.message)
            status.fail(this, 'Could not run automatic calibration: ' + error.message)
          })
      },

      renameParsetModal() {
        console.log('renameParsetModal() called');
        this.$modal.show('rename-parset');
      },

      renameParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('renameParset() called for ' + this.activeParset)
        this.$modal.hide('rename-parset');
        status.start(this) // Start indicating progress.
        rpcs.rpc('rename_parset', [uid, this.activeParset, this.newParsetName]) // Have the server copy the project, giving it a new name.
        .then(response => {
          this.updateParset() // Update the project summaries so the copied program shows up on the list.
          status.succeed(this, 'Parameter set "'+this.activeParset+'" renamed') // Indicate success.
        })
        .catch(error => {
          status.fail(this, 'Could not rename parameter set') // Indicate failure.
        })
      },

      copyParset() { // TO_PORT
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('copyParset() called for ' + this.activeParset)
        status.start(this) // Start indicating progress.
        rpcs.rpc('copy_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
        .then(response => {
          this.updateParset() // Update the project summaries so the copied program shows up on the list.
          status.succeed(this, 'Parameter set "'+this.activeParset+'" copied') // Indicate success.
        })
        .catch(error => {
          status.fail(this, 'Could not copy parameter set') // Indicate failure.
        })
      },

      deleteParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('deleteParset() called for ' + this.activeParset)
        status.start(this) // Start indicating progress.
        rpcs.rpc('delete_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
        .then(response => {
          this.updateParset() // Update the project summaries so the copied program shows up on the list.
          status.succeed(this, 'Parameter set "'+this.activeParset+'" deleted') // Indicate success.
        })
        .catch(error => {
          status.fail(this, 'Cannot delete last parameter set: ensure there are at least 2 parameter sets before deleting one') // Indicate failure.
        })
      },
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>

</style>
