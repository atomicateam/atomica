<!--
Calibration Page

Last update: 2018-08-15
-->

<template>
  <div>
  
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
      <div class="calib-controls">
        <button class="btn __green" @click="makeGraphs(activeProjectID)">Save & run</button>
        <button class="btn" @click="toggleShowingParams()">
          <span v-if="areShowingParameters">Hide</span>
          <span v-else>Show</span>
          parameters
        </button>
        <button class="btn" @click="autoCalibrate(activeProjectID)">Automatic calibration</button>

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
          &nbsp;&nbsp;&nbsp;
          <b>Population: &nbsp;</b>
          <select v-model="activePop">
            <option v-for='pop in active_pops'>
              {{ pop }}
            </option>
          </select>
        </div>

        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <button class="btn" @click="exportResults(activeProjectID)">Export data</button>
        <button class="btn" @click="clearGraphs()">Clear graphs</button>
        <!--<button class="btn" @click="toggleShowingPlotControls()">-->
          <!--<span v-if="areShowingPlotControls">Hide</span>-->
          <!--<span v-else>Show</span>-->
          <!--plot controls-->
        <!--</button>-->

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
  import rpcservice from '@/services/rpc-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import Vue from 'vue'
  
  export default {
    name: 'CalibrationPage',
    
    data() {
      return {
        serverresponse: 'no response',
        sortColumn: 'index',
        sortReverse: false,
        parList: [],
        areShowingParameters: false,
        areShowingPlotControls: false,
        activeParset: -1,
        parsetOptions: [],
        newParsetName: [],
        startYear: 0,
        endYear: 2018, // TEMP FOR DEMO
        activePop: "All",
        plotOptions: [],
        yearOptions: [],
        popOptions: []
      }
    },

    computed: {
      activeProjectID() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          let projectID = this.$store.state.activeProject.project.id
          return projectID
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
      
      active_sim_start() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          return this.$store.state.activeProject.project.sim_start
        }
      },

      active_sim_end() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          return this.$store.state.activeProject.project.sim_end
        }
      },

      active_pops() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          let pop_pairs = this.$store.state.activeProject.project.pops
          let pop_list = ["All"]
          for(let i = 0; i < pop_pairs.length; ++i) {
            pop_list.push(pop_pairs[i][1]);
          }
          return pop_list
        }
      },

      placeholders() {
        var indices = []
        for (var i = 0; i <= 100; i++) {
          indices.push(i);
        }
        return indices;
      },

      sortedPars() {
        var sortedParList = this.applySorting(this.parList);
/*        var sortedParList = this.parList;
        console.log(sortedParList); */
        return sortedParList;
      },

    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      } else if ((this.$store.state.activeProject.project != undefined) && 
        (this.$store.state.activeProject.project.hasData) ) {
        this.startYear = this.active_sim_start
//        this.endYear = this.active_sim_end
        this.popOptions = this.active_pops
        this.viewTable()
        this.getPlotOptions()
        this.sleep(1)  // used so that spinners will come up by callback func
        .then(response => {
          this.updateParset()
        })
        this.sleep(1000)
        .then(response => {
          this.makeGraphs(this.activeProjectID)
        })
      }
    },

    methods: {
      
      onSpinnerCancel() {
        console.log('The user has canceled a spinner!')
      },
      
      clipValidateYearInput() {
        if (this.endYear > this.active_sim_end) {
          this.endYear = this.active_sim_end
        }
        else if (this.endYear < this.active_sim_start) {
          this.endYear = this.active_sim_start
        }
      },

      sleep(time) {
        // Return a promise that resolves after _time_ milliseconds.
        console.log('Sleeping for ' + time)
        return new Promise((resolve) => setTimeout(resolve, time));
      },

      notImplemented(message) {
        status.failurePopup(this, 'Function "' + message + '" not yet implemented')
      },

      projectID() {
        var id = this.$store.state.activeProject.project.id // Shorten this
        return id
      },

      updateParset() {
        console.log('updateParset() called')
        status.start(this)       
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
          status.succeed(this, '')  // No green notification.
        })
        .catch(error => {
          // Failure popup.
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
            if      (this.sortColumn === 'index') { return par1.index > par2.index ? sortDir: -sortDir}
            else if (this.sortColumn === 'parameter') { return par1.parlabel > par2.parlabel ? sortDir: -sortDir}
            else if (this.sortColumn === 'population') { return par1.poplabel > par2.poplabel ? sortDir: -sortDir}
            else if (this.sortColumn === 'value')   { return par1.dispvalue > par2.dispvalue ? sortDir: -sortDir}
          }
        )
      },

      viewTable() {
        console.log('viewTable() called')
        rpcservice.rpcCall('get_y_factors', [this.$store.state.activeProject.project.id, this.activeParset])
        .then(response => {
          this.parList = response.data // Get the parameter values
        })
        .catch(error => {
          status.failurePopup(this, 'Could not load parameters: ' + error.message)
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

      toggleShowingParams() {
        this.areShowingParameters = !this.areShowingParameters
      },

      toggleShowingPlotControls() {
        this.areShowingPlotControls = !this.areShowingPlotControls
      },

      makeGraphs(project_id) {
        console.log('makeGraphs() called')
        
        // Make sure the end year is sensibly set.
        this.clipValidateYearInput()
        
        // Start indicating progress.
        status.start(this)
        
        // Go to the server to get the results from the package set.
        rpcservice.rpcCall('set_y_factors', [project_id, this.activeParset, this.parList, this.plotOptions, this.startYear, this.endYear, this.activePop, 'cascade'])
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
              mpld3.draw_figure(divlabel, response.data.graphs[index], function(fig, element) {
//                fig.setXTicks(6, function(d) { return d3.format('.0f')(d); });
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
      },

      autoCalibrate(project_id) {
        console.log('autoCalibrate() called')
        
        // Make sure the end year is sensibly set.
        this.clipValidateYearInput()
        
        // Start indicating progress.
        status.start(this)
        this.$Progress.start(7000)

        // Go to the server to get the results from the package set.
        rpcservice.rpcCall('automatic_calibration', [project_id, this.activeParset])
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
              mpld3.draw_figure(divlabel, response.data.graphs[index], function(fig, element) {
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
          status.succeed(this, 'Automatic calibration complete')
        })
        .catch(error => {
          // Pull out the error message.
          this.serverresponse = 'There was an error: ' + error.message

          // Set the server error.
          this.servererror = error.message
          
          // Indicate failure.
          status.fail(this, 'Automatic calibration failed')           
        })
      },

      clearGraphs() {
        for (var index = 0; index <= 100; index++) {
          console.log('Clearing plot ' + index)
          var divlabel = 'fig' + index
          var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
          while (div.firstChild) {
            div.removeChild(div.firstChild);
          }
        }
      },

      exportResults(project_id) {
        console.log('exportResults() called')
        status.start(this)
        rpcservice.rpcDownloadCall('export_results', [project_id]) // Make the server call to download the framework to a .prj file.
        .then(response => {
          // Indicate success.
          status.succeed(this, '')  // No green popup message.        
        })      
        .catch(error => {
          // Failure.
          status.fail(this, 'Could not export results')    
        })         
      },

      renameParsetModal() {
        // Open a model dialog for creating a new project
        console.log('renameParsetModal() called');
        this.$modal.show('rename-parset');
      },

      renameParset() {
        // Find the project that matches the UID passed in.
        let uid = this.$store.state.activeProject.project.id
        console.log('renameParset() called for ' + this.activeParset)
        this.$modal.hide('rename-parset');
        
        // Start indicating progress.
        status.start(this)
      
        rpcservice.rpcCall('rename_parset', [uid, this.activeParset, this.newParsetName]) // Have the server copy the project, giving it a new name.
        .then(response => {
          // Update the project summaries so the copied program shows up on the list.
          this.updateParset()
          
          // Indicate success.
          status.succeed(this, 'Parameter set "'+this.activeParset+'" renamed')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not rename parameter set')
        })
      },

      // TO_PORT
      copyParset() {
        // Find the project that matches the UID passed in.
        let uid = this.$store.state.activeProject.project.id
        console.log('copyParset() called for ' + this.activeParset)
        
        // Start indicating progress.
        status.start(this)
        
        rpcservice.rpcCall('copy_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
        .then(response => {
          // Update the project summaries so the copied program shows up on the list.
          this.updateParset()
          
          // Indicate success.
          status.succeed(this, 'Parameter set "'+this.activeParset+'" copied')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not copy parameter set')
        })
      },

      // TO_PORT
      deleteParset() {
        // Find the project that matches the UID passed in.
        let uid = this.$store.state.activeProject.project.id
        console.log('deleteParset() called for ' + this.activeParset)
        
        // Start indicating progress.
        status.start(this)
        
        rpcservice.rpcCall('delete_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
        .then(response => {
          // Update the project summaries so the copied program shows up on the list.
          this.updateParset()
          
          // Indicate success.
          status.succeed(this, 'Parameter set "'+this.activeParset+'" deleted')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Cannot delete last parameter set: ensure there are at least 2 parameter sets before deleting one')
        })
      },
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
