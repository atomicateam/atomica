<!--
Calibration Page

Last update: 2018-09-06
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
      <div class="card">
        <help reflink="calibration" label="Calibration"></help>
        <div class="controls-box">
          <button class="btn __green" @click="manualCalibration(projectID)">Save & run</button>
          <button class="btn" @click="toggleShowingParams()">
            <span v-if="areShowingParameters">Hide</span>
            <span v-else>Show</span>
            parameters
          </button>
        </div>
        &nbsp;&nbsp;
        <div class="controls-box">
          <button class="btn" @click="autoCalibrate(projectID)">Automatic calibration</button>
          for&nbsp;
          <select v-model="calibTime">
            <option v-for='time in calibTimes'>
              {{ time }}
            </option>
          </select>
        </div>
        &nbsp;&nbsp;
        <div class="controls-box">
          <b>Parameter set: &nbsp;</b>
          <select v-model="activeParset">
            <option v-for='parset in parsetOptions'>
              {{ parset }}
            </option>
          </select>
          &nbsp;
          <button class="btn btn-icon" @click="renameParsetModal()" data-tooltip="Rename">
            <i class="ti-pencil"></i>
          </button>
          <button class="btn btn-icon" @click="copyParset()" data-tooltip="Copy">
            <i class="ti-files"></i>
          </button>
          <button class="btn btn-icon" @click="deleteParset()" data-tooltip="Delete">
            <i class="ti-trash"></i>
          </button>
          <button class="btn btn-icon" @click="downloadParset()" data-tooltip="Download">
            <i class="ti-download"></i>
          </button>
          <button class="btn btn-icon" @click="uploadParset()" data-tooltip="Upload">
            <i class="ti-upload"></i>
          </button>
          &nbsp;
        </div>

        <div class="controls-box">
          <button class="btn" @click="notImplemented()">
            Reconcile
          </button>
        </div>
      </div>



      <!-- ### Start: parameters and graphs ### -->
      <div>
        <!-- ### Start: parameters card ### -->
        <div class="card" v-show="areShowingParameters">
          <help reflink="parameters" label="Parameters"></help>
          <table class="table table-bordered table-hover table-striped" style="width: 100%">
            <thead>
            <tr>
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
        <!-- ### End: parameters card ### -->

        <!-- ### Start: results card ### -->
        <div class="card full-width-card">
          <!-- ### Start: plot controls ### -->
          <div class="calib-title">
            <help reflink="results-plots" label="Results"></help>
            <div>
              <!--<b>Start year: &nbsp;</b>-->
              <!--<input type="text"-->
              <!--class="txbox"-->
              <!--v-model="startYear"-->
              <!--style="display: inline-block; width:70px"/>-->
              <!--&nbsp;&nbsp;&nbsp;-->
              <b>Year: &nbsp;</b>
              <select v-model="endYear" @change="plotCalibration(true)">
                <option v-for='year in simYears'>
                  {{ year }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;
              <b>Population: &nbsp;</b>
              <select v-model="activePop" @change="plotCalibration(true)">
                <option v-for='pop in activePops'>
                  {{ pop }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;<!-- CASCADE-TB DIFFERENCE -->
              <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
              <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
              <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>
              &nbsp;&nbsp;&nbsp;
              <button class="btn" @click="exportGraphs()">Export plots</button>
              <button class="btn" @click="exportResults(serverDatastoreId)">Export data</button>
              <button class="btn btn-icon" @click="toggleShowingPlotControls()"><i class="ti-settings"></i></button>

            </div>
          </div>
          <!-- ### End: plot controls ### -->

          <!-- ### Start: results and plot selectors ### -->
          <div class="calib-card-body">

            <!-- ### Start: plots ### -->
            <div class="calib-graphs">
              <div class="featured-graphs">
                <div :id="'fig0'">
                  <!--mpld3 content goes here-->
                </div>
              </div>
              <div class="other-graphs">
                <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
                  <!--mpld3 content goes here-->
                </div>
              </div>
            </div>
            <!-- ### End: plots ### -->

            <!-- CASCADE-TB DIFFERENCE -->
            <!-- ### Start: plot selectors ### -->
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
            <!-- ### End: plot selectors ### -->
          </div>
          <!-- ### End: results and plot selectors ### -->
        </div>
        <!-- ### End: results card ### -->
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
                   v-model="activeParset"/><br>
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
  import help from '@/app/HelpLink.vue'

  export default {
    name: 'CalibrationPage',

    components: {
      help
    },

    data() {
      return {
        response: 'no response',
        sortColumn: 'index',
        sortReverse: false,
        parList: [],
        areShowingParameters: false,
        areShowingPlotControls: false,
        activeParset: -1,
        parsetOptions: [],
        origParsetName: [],
        startYear: 0,
        endYear: 2018, // TEMP FOR DEMO
        activePop: "All",
        plotOptions: [],
        yearOptions: [],
        popOptions: [],
        calibTime: '30 seconds',
        calibTimes: ['30 seconds', 'Unlimited'],
        figscale: 1.0,
        serverDatastoreId: ''        
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      simStart()     { return utils.simStart(this) },
      simEnd()       { return utils.simEnd(this) },
      simYears()     { return utils.simYears(this) },
      activePops()   { return utils.activePops(this) },
      placeholders() { return utils.placeholders(1) },

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
//        this.endYear = this.simEnd
        this.popOptions = this.activePops
        this.serverDatastoreId = this.$store.state.activeProject.project.id + ':calibration'
        this.getPlotOptions()
        .then(response => {
          this.updateParset()
          .then(response2 => {
            this.viewTable()
            .then(response3 => {
              this.plotCalibration(false)
            })    
          })
        })
      }
    },

    methods: {

      getPlotOptions()          { return utils.getPlotOptions(this) },
      clearGraphs()             { return utils.clearGraphs() },
      makeGraphs(graphdata)     { return utils.makeGraphs(this, graphdata) },
      exportGraphs()            { return utils.exportGraphs(this) },
      exportResults(serverDatastoreId) 
                                { return utils.exportResults(this, serverDatastoreId) },
                                
      notImplemented() {
        status.fail(this, 'Sorry, this feature is not implemented')
      },

      scaleFigs(frac) {
        this.figscale = this.figscale*frac;
        if (frac === 1.0) {
          frac = 1.0/this.figscale
          this.figscale = 1.0
        }
        return utils.scaleFigs(frac)
      },

      clipValidateYearInput() {
        if (this.startYear > this.simEnd) {
          this.startYear = this.simEnd
        }
        else if (this.startYear < this.simStart) {
          this.startYear = this.simStart
        }
        if (this.endYear > this.simEnd) {
          this.endYear = this.simEnd
        }
        else if (this.endYear < this.simStart) {
          this.endYear = this.simStart
        }
      },

      updateParset() {
        return new Promise((resolve, reject) => {
          console.log('updateParset() called')
          status.start(this)
          rpcs.rpc('get_parset_info', [this.projectID]) // Get the current user's parsets from the server.
          .then(response => {
            this.parsetOptions = response.data // Set the scenarios to what we received.
            if (this.parsetOptions.indexOf(this.activeParset) === -1) {
              console.log('Parameter set ' + this.activeParset + ' no longer found')
              this.activeParset = this.parsetOptions[0] // If the active parset no longer exists in the array, reset it
            } else {
              console.log('Parameter set ' + this.activeParset + ' still found')
            }
            console.log('Parset options: ' + this.parsetOptions)
            console.log('Active parset: ' + this.activeParset)
            status.succeed(this, '')  // No green notification.
            resolve(response)
          })
          .catch(error => {
            status.fail(this, 'Could not update parset')
            reject(error)
          })
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
        return new Promise((resolve, reject) => {
          console.log('viewTable() called')
          // TODO: Get spinners working right for this leg of initialization.
//          status.start(this)
          rpcs.rpc('get_y_factors', [this.$store.state.activeProject.project.id, this.activeParset])
          .then(response => {
            this.parList = response.data // Get the parameter values
//            status.succeed(this, '')  // No green notification.
            resolve(response)
          })
          .catch(error => {
//            status.fail(this, 'Could not load parameters: ' + error.message)
            reject(error)
          })          
        })
      },

      toggleShowingParams() {
        this.areShowingParameters = !this.areShowingParameters
      },

      toggleShowingPlotControls() {
        this.areShowingPlotControls = !this.areShowingPlotControls
      },

      manualCalibration(project_id) {
        console.log('manualCalibration() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this) // Start indicating progress.
        rpcs.rpc('manual_calibration', [project_id, this.serverDatastoreId], {'parsetname':this.activeParset, 'y_factors':this.parList, 'plot_options':this.plotOptions,
          'plotyear':this.endYear, 'pops':this.activePop, 'tool':'tb', 'cascade':null}
        ) // Go to the server to get the results from the package set.
          .then(response => {
//            status.succeed(this, 'Simulation run') // Indicate success.
            this.makeGraphs(response.data.graphs)
          })
          .catch(error => {
            console.log(error.message)
            status.fail(this, 'Could not run manual calibration: ' + error.message)
          })
      },

      autoCalibrate(project_id) {
        console.log('autoCalibrate() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this) // Start indicating progress.
        this.$Progress.start(7000)
        if (this.calibTime === '30 seconds') {
          var maxtime = 30
        } else {
          var maxtime = 9999
        }
        rpcs.rpc('automatic_calibration', [project_id, this.serverDatastoreId], {'parsetname':this.activeParset, 'max_time':maxtime, 'plot_options':this.plotOptions,
          'plotyear':this.endYear, 'pops':this.activePop, 'tool':'tb', 'cascade':null}
        ) // Go to the server to get the results from the package set.
          .then(response => {
            this.makeGraphs(response.data.graphs)
          })
          .catch(error => {
            console.log(error.message)
            status.fail(this, 'Could not run automatic calibration: ' + error.message)
          })
      },
      
      plotCalibration(showNoCacheError) {
        console.log('plotCalibration() called')
        this.clipValidateYearInput()  // Make sure the start end years are in the right range.
        status.start(this)
        this.$Progress.start(2000)  // restart just the progress bar, and make it slower
        // Make sure they're saved first
        rpcs.rpc('plot_results_cache_entry', [this.projectID, this.serverDatastoreId, this.plotOptions],
          {tool:'tb', 'cascade':null, plotyear:this.endYear, pops:this.activePop, calibration:true})
        .then(response => {
          this.makeGraphs(response.data.graphs)
          this.table = response.data.table
          status.succeed(this, 'Graphs created')
        })
        .catch(error => {
          this.serverresponse = 'There was an error: ' + error.message // Pull out the error message.
          this.servererror = error.message // Set the server error.
          if (showNoCacheError) {
            status.fail(this, 'Could not make graphs: ' + error.message) // Indicate failure.
          }
          else {
            status.succeed(this, '')  // Silently stop progress bar and spinner.
          }
        })
      },
      
      renameParsetModal() {
        console.log('renameParsetModal() called');
        this.origParsetName = this.activeParset // Store this before it gets overwritten
        this.$modal.show('rename-parset');
      },

      renameParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('renameParset() called for ' + this.activeParset)
        this.$modal.hide('rename-parset');
        status.start(this) // Start indicating progress.
        rpcs.rpc('rename_parset', [uid, this.origParsetName, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => {
            this.updateParset() // Update the project summaries so the copied program shows up on the list.
              // TODO: look into whether the above line is necessary
            status.succeed(this, 'Parameter set "'+this.activeParset+'" renamed') // Indicate success.
          })
          .catch(error => {
            status.fail(this, 'Could not rename parameter set') // Indicate failure.
          })
      },

      copyParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('copyParset() called for ' + this.activeParset)
        status.start(this) // Start indicating progress.
        rpcs.rpc('copy_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => {
            this.updateParset() // Update the project summaries so the copied program shows up on the list.
              // TODO: look into whether the above line is necessary            
            this.activeParset = response.data
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
              // TODO: look into whether the above line is necessary            
            status.succeed(this, 'Parameter set "'+this.activeParset+'" deleted') // Indicate success.
          })
          .catch(error => {
            status.fail(this, 'Cannot delete last parameter set: ensure there are at least 2 parameter sets before deleting one') // Indicate failure.
          })
      },

      downloadParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('downloadParset() called for ' + this.activeParset)
        status.start(this) // Start indicating progress.
        rpcs.download('download_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => { // Indicate success.
            status.succeed(this, '')  // No green popup message.
          })
          .catch(error => { // Indicate failure.
            status.fail(this, 'Could not download parameter set: ' + error.message)
          })
      },

      uploadParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('uploadParset() called')
        status.start(this) // Start indicating progress.
        rpcs.upload('upload_parset', [uid], {}, '.par') // Have the server copy the project, giving it a new name.
          .then(response => {
            this.updateParset() // Update the project summaries so the copied program shows up on the list.
              // TODO: look into whether the above line is necessary            
            this.activeParset = response.data
            status.succeed(this, 'Parameter set "' + this.activeParset + '" uploaded') // Indicate success.
          })
          .catch(error => { // Indicate failure.
            status.fail(this, 'Could not upload parameter set: ' + error.message)
          })
      },
    }
  }

</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
