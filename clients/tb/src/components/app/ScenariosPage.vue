<!--
Define health packages

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">

    <div>
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
</style>
