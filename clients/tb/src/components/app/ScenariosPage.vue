<!--
Define health packages

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">

    <div>
      <button class="btn" @click="createNewScenarioModal">Add new scenario</button>
      <button class="btn __green" @click="defaultScenario(activeProjectID)">Plot default scenario</button>
      <button class="btn" @click="clearGraphs()">Clear plots</button>
    </div>
    <br>

    <div style="float:left">
    </div>
    <div>
      <div v-for="index in placeholders" :id="'fig'+index" style="width:550px; float:left;">
        <!--mpld3 content goes here-->
      </div>
    </div>

    <modal name="create-scenario"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Add new scenario
        </div>
        <div class="dialog-c-text">
          Scenario name:<br>
          <input type="text"
                 class="txbox"
                 v-model="scen_name"/><br>
          <table>
            <tr>
              <td>Model parameter:</td>
              <td>Population:</td>
              <td>Start year:</td>
              <td>Final year:</td>
              <td>Start value:</td>
              <td>Final value:</td>
            </tr>
            <tr>
              <td>
                <select name="pars">
                  <option value="dx">Testing rate</option>
                  <option value="tx">Treatment rate</option>
                  <option value="vx">Vaccination rate</option>
                  <option value="inf">Infection rate</option>
                </select></td>
              <td><select name="pop">
                <option value="dx">0-1</option>
                <option value="tx">2-5</option>
                <option value="vx">6-14</option>
                <option value="inf">15+</option>
              </select>
              </td>
              <td><input type="text"
                         class="txbox"
                         v-model="scen_start_year"/></td>
              <td><input type="text"
                         class="txbox"
                         v-model="scen_final_year"/></td>
              <td><input type="text"
                         class="txbox"
                         v-model="scen_start_val"/></td>
              <td><input type="text"
                         class="txbox"
                         v-model="scen_final_val"/></td>
            </tr>
          </table>
          <br>
        </div>
        <div style="text-align:justify">
          <button @click="$modal.hide('create-scenario')" class='btn __green' style="display:inline-block">
            Add scenario
          </button>

          <button @click="$modal.hide('create-scenario')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>


      <div>

      </div>
    </modal>

  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import router from '@/router'
  import Vue from 'vue';

  export default {
    name: 'ScenariosPage',
    data() {
      return {
        serverresponse: 'no response',
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

    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      }

    },

    methods: {

      createNewScenarioModal() {
        // Open a model dialog for creating a new project
        console.log('createNewScenarioModal() called');
        this.$modal.show('create-scenario');
      },

      defaultScenario(project_id) {
        console.log('defaultScenario() called')

        // Go to the server to get the results from the package set.
        rpcservice.rpcCall('run_default_scenario', [project_id])
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
  .vue-dialog div {
    box-sizing: border-box;
  }
  .vue-dialog .dialog-flex {
    width: 100%;
    height: 100%;
  }
  .vue-dialog .dialog-content {
    flex: 1 0 auto;
    width: 100%;
    padding: 15px;
    font-size: 14px;
  }
  .vue-dialog .dialog-c-title {
    font-weight: 600;
    padding-bottom: 15px;
  }
  .vue-dialog .dialog-c-text {
  }
  .vue-dialog .vue-dialog-buttons {
    display: flex;
    flex: 0 1 auto;
    width: 100%;
    border-top: 1px solid #eee;
  }
  .vue-dialog .vue-dialog-buttons-none {
    width: 100%;
    padding-bottom: 15px;
  }
  .vue-dialog-button {
    font-size: 12px !important;
    background: transparent;
    padding: 0;
    margin: 0;
    border: 0;
    cursor: pointer;
    box-sizing: border-box;
    line-height: 40px;
    height: 40px;
    color: inherit;
    font: inherit;
    outline: none;
  }
  .vue-dialog-button:hover {
    background: rgba(0, 0, 0, 0.01);
  }
  .vue-dialog-button:active {
    background: rgba(0, 0, 0, 0.025);
  }
  .vue-dialog-button:not(:first-of-type) {
    border-left: 1px solid #eee;
  }
</style>
