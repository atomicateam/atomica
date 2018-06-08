<!--
Define health packages

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">
    <button class="btn" @click="makeGraph">Plot default scenario</button>

      <div>
        <div id="fig01" style="float:left" ></div>
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
      activeProjectName() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          return this.$store.state.activeProject.project.name
        }
      },
    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
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

      makeGraph(packageSet) {
        console.log('makeGraph() called')

        // Go to the server to get the results from the package set.
        rpcservice.rpcCall('get_default_scenario_plot')
          .then(response => {
            this.serverresponse = response.data // Pull out the response data.
            let theFig = response.data.graph1 // Extract hack info.
            mpld3.draw_figure('fig01', response.data.graph1) // Draw the figure.
          })
          .catch(error => {
            // Pull out the error message.
            this.serverresponse = 'There was an error: ' + error.message

            // Set the server error.
            this.servererror = error.message
          })
      },


    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
</style>
