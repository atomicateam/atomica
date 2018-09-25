<!--
Help page

Last update: 2018sep23
-->

<template>
  <div class="SitePage">
    <div style="text-align:center">
      <div style="display:inline-block; margin:auto; text-align:left" v-model="getVersionInfo">
        <div>
          <p v-if="$globaltool=='cascade'">For instructions on how to use the Cascade Analysis Tool, please see the user guide: <a href="https://cascade.tools/user-guide" target="_blank">https://cascade.tools/user-guide</a>.</p>
          <p v-if="$globaltool=='tb'">      For instructions on how to use Optima TB,                 please see the user guide: <a href="http://ocds.co/tb-user-guide" target="_blank">ocds.co/tb-user-guide</a>.</p>
          <p v-if="$globaltool=='cascade'">For assistance in the mean time, please <a href="mailto:robyn@math.ku.dk">contact us</a>.</p>
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

        <div>
          <button @click="adv_consoleModal">
            <span v-if="!adv_showConsole">Developer options</span>
            <span v-if="adv_showConsole">Hide developer options</span>
          </button>
        </div>

        <div v-if="adv_showConsole">
          <br><br>
          <div class="controls-box">
            <b>Token</b><br>
            <input type="password"
                   class="txbox"
                   v-model="adv_authentication"/><br>
            <b>Query</b><br>
            <textarea rows="10" cols="100" v-model="adv_query"/><br>
            <button @click="adv_submit">Submit</button><br><br><br>
            <b>Output</b><br>
            <span v-html="adv_response"></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import rpcs from '@/js/rpc-service'
  import status from '@/js/status-service'

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
        adv_showConsole: false,
        adv_authentication: '',
        adv_query: '',
        adv_response: 'No response',
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

    methods: {

      adv_consoleModal() {
        if (!this.adv_showConsole) {
          var obj = { // Alert object data
            message: 'WARNING: This option is for authorized developers only. Unless you have received prior written authorization to use this feature, exit now. If you click "Yes", your details will be logged, and any misuse will result in immediate account suspension.',
            useConfirmBtn: true,
            customConfirmBtnText: 'Yes, I will take the risk',
            customCloseBtnText: 'Oops, get me out of here',
            customConfirmBtnClass: 'btn __red',
            customCloseBtnClass: 'btn',
            onConfirm: this.adv_toggleConsole
          }
          this.$Simplert.open(obj)
        } else {
          this.adv_toggleConsole()
        }
      },

      adv_toggleConsole() {
        this.adv_showConsole = !this.adv_showConsole
      },

      adv_submit() {
        console.log('adv_submit() called')
        rpcs.rpc('run_query', [this.adv_authentication, this.adv_query]) // Have the server copy the project, giving it a new name.
          .then(response => {
            this.adv_response = response.data.replace(/\n/g,'<br>')
            status.succeed(this, 'Query run')    // Indicate success.
          })
          .catch(error => {
            status.fail(this, 'Could not run query', error)
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