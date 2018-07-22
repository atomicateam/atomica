<!--
Define health packages

Last update: 2018-07-21
-->

<template>
  <div class="SitePage">
  
    <div v-if="activeProjectID ==''">
      <div style="font-style:italic">
        <p>No project is loaded.</p>
      </div>
    </div>

    <div v-else>
    
      <div>
        <button class="btn __green" @click="makeGraphs(activeProjectID)">Save & run</button>
        <button class="btn" @click="clearGraphs()">Clear plots</button>
      </div>
    
      <br>

      <div style="width:200px; float:left">
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
              {{par.parname}}
            </td>
            <td>
              {{par.popname}}
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
      
      <div style="margin-left:350px">
        <div v-for="index in placeholders" :id="'fig'+index" style="width:550px; float:left;">
          <!--mpld3 content goes here-->
        </div>
      </div>

    </div>

  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import router from '@/router'
  import Vue from 'vue';

  export default {
    name: 'CalibrationPage',
    data() {
      return {
        serverresponse: 'no response',
        sortColumn: 'parname',
        sortReverse: false,
        parList: [],
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
        for (var i = 1; i <= 100; i++) {
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

      else {
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
            if      (this.sortColumn === 'parameter') { return par1.parname > par2.parname ? sortDir: -sortDir}
            else if (this.sortColumn === 'population') { return par1.popname > par2.popname ? sortDir: -sortDir}
            else if (this.sortColumn === 'value')   { return par1.value > par2.value ? sortDir: -sortDir}            
          }
        )
      },

      viewTable() {
        console.log('viewTable() called')

        // Go to the server to get the diseases from the burden set.
        rpcservice.rpcCall('get_y_factors', [this.$store.state.activeProject.project.id])
          .then(response => {
            this.parList = response.data // Set the disease list.
          })

//        // Set the active values from the loaded in data.
//        for (let ind=0; ind < this.parList.length; ind++) {
//          this.parList[ind].value = Number(this.value[ind][2]).toLocaleString()
//        }
      },

      makeGraphs(project_id) {
        console.log('makeGraphs() called')

        // Go to the server to get the results from the package set.
        rpcservice.rpcCall('set_y_factors', [project_id, this.parList])
          .then(response => {
            this.serverresponse = response.data // Pull out the response data.
            var n_plots = response.data.graphs.length
            console.log('Rendering ' + n_plots + ' graphs')

            for (var index = 1; index <= n_plots; index++) {
              console.log('Rendering plot ' + index)
              var divlabel = 'fig' + index
              var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
              while (div.firstChild) {
                div.removeChild(div.firstChild);
              }
              try {
                mpld3.draw_figure(divlabel, response.data.graphs[index]); // Draw the figure.
              }
              catch (err) {
                console.log('failled:' + err.message);
              }
            }
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
        for (var index = 1; index <= 100; index++) {
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
<style>
</style>
