<!--
Help page

Last update: 2018sep23
-->

<template>
  <div class="SitePage" style="text-align:center">
    <div style="display:inline-block; margin:auto; text-align:left" v-model="getVersionInfo">
      <div>
        <p>We are in the process of writing a user guide.</p>
        <p v-if="$globaltool=='cascade'">For assistance in the mean time, please email <a href="mailto:info@cascade.tools">info@cascade.tools</a>.</p>
        <p v-if="$globaltool=='tb'">     For assistance in the mean time, please email <a href="mailto:help@ocds.co">help@ocds.co</a>.</p>
        <p>Please copy and paste the table below into your email, along with any error messages.</p>
      </div>

      <table class="table table-bordered table-striped table-hover">
        <thead>
        <tr>
          <th colspan=100>Technical information</th>
        </tr>
        </thead>
        <tbody>
        <tr><td class="tlabel">Username    </td><td>{{ username }}</td></tr>
        <tr><td class="tlabel">Browser     </td><td>{{ useragent }}</td></tr>
        <tr><td class="tlabel">App version </td><td>{{ toolName }} {{ version }} ({{ date }}) [{{ gitbranch }}/{{ githash }}]</td></tr>
        <tr><td class="tlabel">Timestamp   </td><td>{{ timestamp }}</td></tr>
        <tr><td class="tlabel">Server name </td><td>{{ server }}</td></tr>
        <tr><td class="tlabel">Server load </td><td>{{ cpu }}</td></tr>
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
        username: '',
        useragent: '',
        version: '',
        date: '',
        gitbranch: '',
        githash: '',
        server: '',
        cpu: '',
        timestamp: '',
      }
    },

    computed: {
      getVersionInfo() {
        rpcs.rpc('get_version_info')
          .then(response => {
            this.username  = this.$store.state.currentUser.username
            this.useragent = window.navigator.userAgent
            this.timestamp = Date(Date.now()).toLocaleString()
            this.version   = response.data['version'];
            this.date      = response.data['date'];
            this.gitbranch = response.data['gitbranch'];
            this.githash   = response.data['githash'];
            this.server    = response.data['server'];
            this.cpu       = response.data['cpu'];
          })
      },

      toolName() {
        if      (this.$globaltool === 'cascade') { return 'Cascade Analysis Tools'}
        else if (this.$globaltool === 'tb')      { return 'Optima TB'}
        else                                     { return 'Atomica'}
      },

    },
  }
</script>

<style scoped>
  .tlabel {
    font-weight:bold;
  }
</style>