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

      <!-- ### Start: calibration card ### -->
      <div class="card">
        <div><help reflink="bl-overview" label="Calibration and reconciliation"></help></div>
        <div class="controls-box">
          <button class="btn __green" @click="manualCalibration(projectID)">Save & run</button>
          <button class="btn" @click="toggleParams()">
            <span v-if="showParameters">Hide</span>
            <span v-else>Show</span>
            parameters
          </button>
          &nbsp;<help reflink="manual-calibration"></help>
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
          &nbsp;<help reflink="automatic-calibration"></help>
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
          <help reflink="parameter-sets"></help>
        </div>

        <div class="controls-box">
          <button class="btn" @click="notImplemented()">
            Reconcile
          </button>&nbsp;
          <help reflink="reconciliation"></help>
        </div>
      </div>
      <!-- ### End: calibration card ### -->


      <!-- ### Start: parameters card ### -->
      <div class="PageSection" v-show="showParameters">
        <div class="card">
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
            <tr v-for="par in parList">
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
      </div>
      <!-- ### End: parameters card ### -->


      <!-- ### Start: results card ### -->
      <div class="PageSection" v-if="hasGraphs">
        <div class="card">
          <!-- ### Start: plot controls ### -->
          <div class="calib-title">
            <help reflink="bl-results" label="Results"></help>
            <div>

              <b>Year: &nbsp;</b>
              <select v-model="endYear" @change="reloadGraphs(true)">
                <option v-for='year in simYears'>
                  {{ year }}
                </option>
              </select>
              &nbsp;&nbsp;&nbsp;
              <b>Population: &nbsp;</b>
              <select v-model="activePop" @change="reloadGraphs(true)">
                <option v-for='pop in activePops'>
                  {{ pop }}
                </option>
              </select>
              <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
              <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
              <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>
              &nbsp;&nbsp;&nbsp;
              <button class="btn" @click="exportGraphs(projectID)">Export graphs</button>
              <button class="btn" @click="exportResults(serverDatastoreId)">Export data</button>
              <button v-if="false" class="btn btn-icon" @click="togglePlotControls()"><i class="ti-settings"></i></button> <!-- When popups are working: v-if="this.$globaltool=='tb'" -->

            </div>
          </div>
          <!-- ### End: plot controls ### -->

          <!-- ### Start: results and plot selectors ### -->
          <div class="calib-card-body">

            <!-- ### Start: plots ### -->
            <div class="calib-card-body">
              <div class="calib-graphs">
                <div class="featured-graphs">
                  <div :id="'fig0'">
                    <!-- mpld3 content goes here, no legend for it -->
                  </div>
                </div>
                <div class="other-graphs">
                  <div v-for="index in placeholders">
                    <div :id="'figcontainer'+index" style="display:flex; justify-content:flex-start; padding:5px; border:1px solid #ddd" v-show="showGraphDivs[index]">
                      <div :id="'fig'+index" class="calib-graph">
                        <!--mpld3 content goes here-->
                      </div>
                      <div style="display:inline-block">
                        <button class="btn __bw btn-icon" @click="maximize(index)" data-tooltip="Show legend"><i class="ti-menu-alt"></i></button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- ### End: plots ### -->

            <!-- ### Start: dialogs ### -->
            <div v-for="index in placeholders">
              <div class="dialogs" :id="'legendcontainer'+index" style="display:flex" v-show="showLegendDivs[index]">
                <dialog-drag :id="'DD'+index"
                             :key="index"
                             @close="minimize(index)"
                             :options="{top: openDialogs[index].options.top, left: openDialogs[index].options.left}">

                  <span slot='title' style="color:#fff">Legend</span>
                  <div :id="'legend'+index">
                    <!-- Legend content goes here-->
                  </div>
                </dialog-drag>
              </div>
            </div>
            <!-- ### End: dialogs ### -->

            <!-- ### Start: cascade table ### -->
            <div v-if="this.$globaltool=='cascade' && table" class="calib-tables" style="display:inline-block; padding-top:30px">
              <h4>Cascade stage losses</h4>
              <table class="table table-striped" style="text-align:right;">
                <thead>
                <tr>
                  <th></th>
                  <th v-for="label in table.collabels.slice(0, -1)">{{label}}</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="(label, index) in table.rowlabels">
                  <td>{{label}}</td>
                  <td v-for="text in table.text[index].slice(0, -1)">{{text}}</td>
                </tr>
                </tbody>
              </table>
            </div>
            <!-- ### End: cascade table ### -->

            <!-- ### Start: plot selectors ### -->
            <div class="plotopts-main" :class="{'plotopts-main--full': !showPlotControls}" v-if="showPlotControls">
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

          </div>  <!-- ### End: card body ### -->
        </div> <!-- ### End: results card ### -->
      </div> <!-- ### End: PageSection/hasGraphs ### -->
    </div> <!-- ### End: v-else project (results) ### -->


    <!-- ### Start: add scenarios modal ### -->
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
    <!-- ### End: rename parset modal ### -->

  </div>
</template>


<script>
  var filesaver = require('file-saver')
  import axios  from 'axios'
  import router from '@/router'
  import utils  from '@/js/utils'
  import graphs from '@/js/graphs'
  import shared from '@/js/shared'
  import rpcs   from '@/js/rpc-service'
  import status from '@/js/status-service'

  export default {
    name: 'CalibrationPage',

    data() {
      return {
        // Parameter and program set information
        activeParset:  -1,
        activeProgset: -1,
        parsetOptions: [],
        progsetOptions: [],

        // Plotting data
        showPlotControls: false,
        hasGraphs: false,
        table: null,
        startYear: 0,
        endYear: 2018, // TEMP FOR DEMO
        activePop: "All",
        popOptions: [],
        plotOptions: [],
        yearOptions: [],
        serverDatastoreId: '',
        openDialogs: [],
        showGraphDivs: [], // These don't actually do anything, but they're here for future use
        showLegendDivs: [],
        mousex:-1,
        mousey:-1,
        figscale: 1.0,

        // Page-specific data
        parList: [],
        origParsetName: [],
        showParameters: false,
        calibTime: '30 seconds',
        calibTimes: ['30 seconds', 'Unlimited'],
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      hasPrograms()  { return utils.hasPrograms(this) },
      simStart()     { return utils.simStart(this) },
      simEnd()       { return utils.simEnd(this) },
      simYears()     { return utils.simYears(this) },
      activePops()   { return utils.activePops(this) },
      placeholders() { return graphs.placeholders(this, 1) },
    },

    created() {
      graphs.addListener(this)
      graphs.createDialogs(this)
      if ((this.$store.state.activeProject.project !== undefined) &&
        (this.$store.state.activeProject.project.hasData) ) {
        console.log('created() called')
        this.startYear = this.simStart
//        this.endYear = this.simEnd // CK: Uncomment to set the end year to 2035 instead of 2018
        this.popOptions = this.activePops
        this.serverDatastoreId = this.$store.state.activeProject.project.id + ':calibration'
        this.getPlotOptions(this.$store.state.activeProject.project.id)
          .then(response => {
            this.updateSets()
              .then(response2 => {
                this.loadParTable()
                  .then(response3 => {
                    this.reloadGraphs(false)
                  })
              })
          })
      }
    },

    methods: {

      validateYears()                   { return shared.validateYears(this) },
      updateSets()                      { return shared.updateSets(this) },
      exportGraphs(datastoreID)         { return shared.exportGraphs(this, datastoreID) },
      exportResults(datastoreID)        { return shared.exportResults(this, datastoreID) },
      scaleFigs(frac)                   { return graphs.scaleFigs(this, frac)},
      clearGraphs()                     { return graphs.clearGraphs(this) },
      togglePlotControls()              { return graphs.togglePlotControls(this) },
      getPlotOptions(project_id)        { return graphs.getPlotOptions(this, project_id) },
      makeGraphs(graphdata)             { return graphs.makeGraphs(this, graphdata) },
      reloadGraphs(showErr)             { return graphs.reloadGraphs(this, showErr, true) }, // Set to calibration=true
      maximize(legend_id)               { return graphs.maximize(this, legend_id) },
      minimize(legend_id)               { return graphs.minimize(this, legend_id) },

      toggleParams() {
        this.showParameters = !this.showParameters
      },

      loadParTable() {
        return new Promise((resolve, reject) => {
          console.log('loadParTable() called')
          // TODO: Get spinners working right for this leg of initialization.
          rpcs.rpc('get_y_factors', [this.$store.state.activeProject.project.id, this.activeParset])
            .then(response => {
              this.parList = response.data // Get the parameter values
              resolve(response)
            })
            .catch(error => {
              status.fail(this, 'Could not load parameters', error)
              reject(error)
            })
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
        status.start(this)
        rpcs.rpc('rename_parset', [uid, this.origParsetName, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => {
            this.updateSets() // Update the project summaries so the copied program shows up on the list.
            // TODO: look into whether the above line is necessary
            status.succeed(this, 'Parameter set "'+this.activeParset+'" renamed') // Indicate success.
          })
          .catch(error => {
            status.fail(this, 'Could not rename parameter set', error)
          })
      },

      copyParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('copyParset() called for ' + this.activeParset)
        status.start(this)
        rpcs.rpc('copy_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => {
            this.updateSets() // Update the project summaries so the copied program shows up on the list.
            // TODO: look into whether the above line is necessary
            this.activeParset = response.data
            status.succeed(this, 'Parameter set "'+this.activeParset+'" copied') // Indicate success.
          })
          .catch(error => {
            status.fail(this, 'Could not copy parameter set', error)
          })
      },

      deleteParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('deleteParset() called for ' + this.activeParset)
        status.start(this)
        rpcs.rpc('delete_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => {
            this.updateSets() // Update the project summaries so the copied program shows up on the list.
            // TODO: look into whether the above line is necessary
            status.succeed(this, 'Parameter set "'+this.activeParset+'" deleted') // Indicate success.
          })
          .catch(error => {
            status.fail(this, 'Cannot delete last parameter set: ensure there are at least 2 parameter sets before deleting one', error)
          })
      },

      downloadParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('downloadParset() called for ' + this.activeParset)
        status.start(this)
        rpcs.download('download_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => { // Indicate success.
            status.succeed(this, '')  // No green popup message.
          })
          .catch(error => {
            status.fail(this, 'Could not download parameter set', error)
          })
      },

      uploadParset() {
        let uid = this.$store.state.activeProject.project.id // Find the project that matches the UID passed in.
        console.log('uploadParset() called')
        rpcs.upload('upload_parset', [uid], {}, '.par') // Have the server copy the project, giving it a new name.
          .then(response => {
            status.start(this)
            this.updateSets() // Update the project summaries so the copied program shows up on the list.
            // TODO: look into whether the above line is necessary
            this.activeParset = response.data
            status.succeed(this, 'Parameter set "' + this.activeParset + '" uploaded') // Indicate success.
          })
          .catch(error => {
            status.fail(this, 'Could not upload parameter set', error)
          })
      },

      manualCalibration(project_id) {
        console.log('manualCalibration() called')
        this.validateYears()  // Make sure the start end years are in the right range.
        status.start(this)
        rpcs.rpc('manual_calibration', [project_id, this.serverDatastoreId], {'parsetname':this.activeParset, 'y_factors':this.parList, 'plot_options':this.plotOptions,
          'plotyear':this.endYear, 'pops':this.activePop, 'tool':this.$globaltool, 'cascade':null}) // Go to the server to get the results
          .then(response => {
            this.makeGraphs(response.data)
            this.table = response.data.table
            status.succeed(this, 'Simulation run, graphs now rendering...')
          })
          .catch(error => {
            console.log(error.message)
            status.fail(this, 'Could not run manual calibration', error)
          })
      },

      autoCalibrate(project_id) {
        console.log('autoCalibrate() called')
        this.validateYears()  // Make sure the start end years are in the right range.
        status.start(this)
        if (this.calibTime === '30 seconds') {
          var maxtime = 30
        } else {
          var maxtime = 9999
        }
        rpcs.rpc('automatic_calibration', [project_id, this.serverDatastoreId], {'parsetname':this.activeParset, 'max_time':maxtime, 'plot_options':this.plotOptions,
          'plotyear':this.endYear, 'pops':this.activePop, 'tool':this.$globaltool, 'cascade':null}
        ) // Go to the server to get the results from the package set.
          .then(response => {
            this.makeGraphs(response.data.graphs)
          })
          .catch(error => {
            console.log(error.message)
            status.fail(this, 'Could not run automatic calibration', error)
          })
      },
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
</style>
