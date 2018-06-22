<!--
Define health packages

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">
    <button class="btn" @click="makeGraphs(activeProjectID)">Get plots</button>

    <div v-for="index in placeholders" :id="'fig'+index">
      <!--mpld3 content goes here-->
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
      }

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

      makeGraphs(project_id) {
        console.log('makeGraphs() called')

        // Go to the server to get the results from the package set.
        rpcservice.rpcCall('get_plots', [project_id])
          .then(response => {
            this.serverresponse = response.data // Pull out the response data.
            var n_plots = response.data.graphs.length
            console.log('Rendering '+n_plots+' graphs')

            for (var index = 1; index <= n_plots; index++) {
              console.log('Rendering plot '+index)
              try {
                mpld3.draw_figure('fig'+index, response.data.graphs[index]); // Draw the figure.
              }
              catch(err) {
                console.log('failled:'+err.message);
              }
            }
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
