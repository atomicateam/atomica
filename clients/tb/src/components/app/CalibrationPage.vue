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
        areShowingParameters: true
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
        rpcservice.rpcCall('get_y_factors', [this.$store.state.activeProject.project.id])
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
            message: 'Could not load diseases',
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
        rpcservice.rpcCall('set_y_factors', [project_id, this.parList])
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
        rpcservice.rpcCall('automatic_calibration', [project_id])
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
        rpcservice.rpcDownloadCall('export_results', [project_id]) // Make the server call to download the framework to a .prj file.
      },
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
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
</style>
