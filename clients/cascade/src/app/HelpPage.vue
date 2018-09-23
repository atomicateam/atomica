<!--
Help page

Last update: 2018sep23
-->

<template>
  <div class="SitePage" style="text-align:center">
    <div style="display:inline-block; margin:auto; text-align:left" v-model="getVersionInfo">
      <div style="max-width:500px">
        <p>We are in the process of writing a user guide.</p>
    <p v-if="$globaltool=='cascade'">For assistance in the mean time, please email <a href="mailto:info@cascade.tools">info@cascade.tools">info@cascade.tools">info@cascade.tools</a>.</p>
    <p v-if="$globaltool=='tb'">     For assistance in the mean time, please email <a href="mailto:help@ocds.co">help@ocds.co</a>.</p>
        <p>Please copy and paste the information from the table below into your email.</p>
        <br>
      </div>

      <table class="table table-bordered table-striped table-hover">
        <thead>
        <tr>
          <th colspan=100>Optima Nutrition technical information</th>
        </tr>
        </thead>
        <tbody>
        <tr>
          <td class="tlabel">Version </td>
          <td>{{ version }}</td>
        </tr>
        <tr>
          <td class="tlabel">Date </td>
          <td>{{ date }}</td>
        </tr>
        <tr>
          <td class="tlabel">Branch </td>
          <td>{{ gitbranch }}</td>
        </tr>
        <tr>
          <td class="tlabel">Hash </td>
          <td>{{ githash }}</td>
        </tr>
        <tr>
          <td class="tlabel">Time </td>
          <td>{{ gitdate }}</td>
        </tr>
        <tr>
          <td class="tlabel">Server </td>
          <td>{{ server }}</td>
        </tr>
        <tr>
          <td class="tlabel">Load </td>
          <td>{{ cpu }}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
  import rpcs from '@/js/rpc-service'

  export default {
    name: 'About',

    data () {
      return {
        version: '',
        date: '',
        gitbranch: '',
        githash: '',
        gitdate: '',
        server: '',
        cpu: '',
      }
    },

    computed: {
      getVersionInfo() {
        rpcs.rpc('get_version_info')
          .then(response => {
            this.version   = response.data['version'];
            this.date      = response.data['date'];
            this.gitbranch = response.data['gitbranch'];
            this.githash   = response.data['githash'];
            this.gitdate   = response.data['gitdate'];
            this.server    = response.data['server'];
            this.cpu       = response.data['cpu'];
          })
      },
    },
  }
</script>

<style scoped>
  .tlabel {
    font-weight:bold;
  }
</style>