<!--
Define health packages

Last update: 2018-07-25
-->

<template>
  <div class="SitePage">
  
    <div v-if="activeProjectID ==''">
      <div style="font-style:italic">
        <p>No project is loaded.</p>
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
        <button class="btn" @click="exportResults(activeProjectID)">Export results</button>

        <div class="parset-controls">
        <!--<div style="display: inline-block; padding-left: 100px">-->
          <b>Parameter set: &nbsp;</b>
          <select v-model="activeParset">
            <option v-for='parset in parsetOptions'>
              {{ parset }}
            </option>
          </select>
          &nbsp;
          <button class="btn small-button" @click="renameParsetModal()" title="Rename">
            <i class="ti-pencil"></i>
          </button>
          <button class="btn small-button" @click="copyParset()" title="Copy">
            <i class="ti-files"></i>
          </button>
          <button class="btn small-button" @click="deleteParset()" title="Delete">
            <i class="ti-trash"></i>
          </button>
        </div>
      </div>
    
      <br>

      <div class="calib-main" :class="{'calib-main--full': !areShowingParameters}">
        <div class="calib-params" v-if="areShowingParameters">
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
                       v-model="par.value"/>
              </td>
            </tr>
            </tbody>
          </table>
        </div>

        <div class="calib-graph">
          <div v-for="index in placeholders" :id="'fig'+index">
            <!--mpld3 content goes here-->
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


      <div>

      </div>
    </modal>
    
    <!-- Popup spinner -->
    <popup-spinner></popup-spinner>
    
  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import router from '@/router'
  import Vue from 'vue'
  import PopupSpinner from './Spinner.vue'
  
  export default {
    name: 'CalibrationPage',
    
    components: {
      PopupSpinner
    },
    
    data() {
      return {
        serverresponse: 'no response',
        sortColumn: 'parname',
        sortReverse: false,
        parList: [],
        areShowingParameters: true,
        activeParset: -1,
        parsetOptions: [],
        newParsetName: [],
      }
    },

    computed: {
      activeProjectID() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          let projectID = this.$store.state.activeProject.project.id
          this.updateParset()
          return projectID
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
      }

      else if (this.$store.state.activeProject.project != undefined) {
        this.viewTable();
      }
    },

    methods: {

      notImplemented(message) {
        this.$notifications.notify({
          message: 'Function "' + message + '" not yet implemented',
          icon: 'ti-face-sad',
          type: 'warning',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      },

      projectID() {
        var id = this.$store.state.activeProject.project.id // Shorten this
        return id
      },

      // TO_PORT
      updateParset() {
        console.log('updateParset() called')
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
            if      (this.sortColumn === 'parameter') { return par1.parlabel > par2.parlabel ? sortDir: -sortDir}
            else if (this.sortColumn === 'population') { return par1.poplabel > par2.poplabel ? sortDir: -sortDir}
            else if (this.sortColumn === 'value')   { return par1.value > par2.value ? sortDir: -sortDir}
          }
        )
      },

      viewTable() {
        console.log('viewTable() called')
        
        // Note: For some reason, the popup spinner doesn't work from inside created().
        
        // Start the loading bar.
        this.$Progress.start()

        // Go to the server to get the diseases from the burden set.
        rpcservice.rpcCall('get_y_factors', [this.$store.state.activeProject.project.id, this.activeParset])
        .then(response => {
          this.parList = response.data // Set the disease list.
          
          // Finish the loading bar.
          this.$Progress.finish()          
        })
        .catch(error => {
          // Fail the loading bar.
          this.$Progress.fail()
        
          // Failure popup.
          this.$notifications.notify({
            message: 'Could not load parameters',
            icon: 'ti-face-sad',
            type: 'warning',
            verticalAlign: 'top',
            horizontalAlign: 'center',
          })      
        })
      },

      toggleShowingParams() {
        this.areShowingParameters = !this.areShowingParameters
      },

      makeGraphs(project_id) {
        console.log('makeGraphs() called')
        this.$modal.show('popup-spinner') // Bring up a spinner.
        
        // Start the loading bar.
        this.$Progress.start()
        
        // Go to the server to get the results from the package set.
        rpcservice.rpcCall('set_y_factors', [project_id, this.activeParset, this.parList])
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
          // Pull out the error message.
          this.serverresponse = 'There was an error: ' + error.message

          // Set the server error.
          this.servererror = error.message
          
          // Dispel the spinner.
          this.$modal.hide('popup-spinner')
          
          // Fail the loading bar.
          this.$Progress.fail()
        
          // Failure popup.
          this.$notifications.notify({
            message: 'Could not make graphs',
            icon: 'ti-face-sad',
            type: 'warning',
            verticalAlign: 'top',
            horizontalAlign: 'center',
          })          
        }) 
      },

      autoCalibrate(project_id) {

        console.log('autoCalibrate() called')

        this.$modal.show('popup-spinner') // Bring up a spinner.

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
              message: 'Automatic calibration complete',
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
          }).then( response => {
          this.$notifications.notify({
            message: 'Graphs created',
            icon: 'ti-check',
            type: 'success',
            verticalAlign: 'top',
            horizontalAlign: 'center',
          });
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
        rpcservice.rpcDownloadCall('export_results', [project_id, this.activeParset]) // Make the server call to download the framework to a .prj file.
      },

      // TO_PORT
      renameParsetModal() {
        // Open a model dialog for creating a new project
        console.log('renameParsetModal() called');
        this.$modal.show('rename-parset');
      },

      // TO_PORT
      renameParset() {
        // Find the project that matches the UID passed in.
        let uid = this.$store.state.activeProject.project.id
        console.log('renameParset() called for ' + this.activeParset)
        this.$modal.hide('rename-parset');
        this.$modal.show('popup-spinner') // Bring up a spinner.
        rpcservice.rpcCall('rename_parset', [uid, this.activeParset, this.newParsetName]) // Have the server copy the project, giving it a new name.
          .then(response => {
            // Update the project summaries so the copied program shows up on the list.
            this.updateParset()
            this.$modal.hide('popup-spinner') // Dispel the spinner.
            this.$notifications.notify({ // Success popup.
              message: 'Parameter set "'+this.activeParset+'" renamed',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            })
          })
          .catch(error => {
            this.$modal.hide('popup-spinner') // Dispel the spinner.
            this.$notifications.notify({ // Failure popup.
              message: 'Could not rename parameter set',
              icon: 'ti-face-sad',
              type: 'warning',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            })
          })
      },

      // TO_PORT
      copyParset() {
        // Find the project that matches the UID passed in.
        let uid = this.$store.state.activeProject.project.id
        console.log('copyParset() called for ' + this.activeParset)
        this.$modal.show('popup-spinner') // Bring up a spinner.
        rpcservice.rpcCall('copy_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => {
            // Update the project summaries so the copied program shows up on the list.
            this.updateParset()
            this.$modal.hide('popup-spinner') // Dispel the spinner.
            this.$notifications.notify({ // Success popup.
              message: 'Parameter set "'+this.activeParset+'" copied',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            })
          })
          .catch(error => {
            this.$modal.hide('popup-spinner') // Dispel the spinner.
            this.$notifications.notify({ // Failure popup.
              message: 'Could not copy parameter set',
              icon: 'ti-face-sad',
              type: 'warning',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            })
          })
      },

      // TO_PORT
      deleteParset() {
        // Find the project that matches the UID passed in.
        let uid = this.$store.state.activeProject.project.id
        console.log('deleteParset() called for ' + this.activeParset)
        this.$modal.show('popup-spinner') // Bring up a spinner.
        rpcservice.rpcCall('delete_parset', [uid, this.activeParset]) // Have the server copy the project, giving it a new name.
          .then(response => {
            // Update the project summaries so the copied program shows up on the list.
            this.updateParset()
            this.$modal.hide('popup-spinner') // Dispel the spinner.
            this.$notifications.notify({ // Success popup.
              message: 'Parameter set "'+this.activeParset+'" deleted',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            })
          })
          .catch(error => {
            this.$modal.hide('popup-spinner') // Dispel the spinner.
            this.$notifications.notify({ // Failure popup.
              message: 'Cannot delete last parameter set: ensure there are at least 2 parameter sets before deleting one',
              icon: 'ti-face-sad',
              type: 'warning',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            })
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
  }
  .calib-main--full {
    display: block;
  }
  .calib-params {
    flex: 1 0 40%;
  }
  .calib-graph {
    flex: 1 0 60%;
  }
  .parset-controls {
    border: 2px solid #ddd;
    padding: 7px;
    display: inline-block;
  }
  .small-button {
    background: inherit;
    padding: 0 0 0 0;
  }
</style>
