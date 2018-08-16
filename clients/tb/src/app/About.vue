<!--
About page

Last update: 2018may28
-->

<template>
  <div class="SitePage">
    <div style="max-width:800px; margin:auto" v-model="getVersionInfo">
      <div style="text-align:center;">
        <img src="static/img/optima-logo-tb.png" width="250px">
      </div>
      <br/><br/>
      <p>Optima TB is currently under development. Development is supported through a partnership
        between the <a href="http://www.burnet.edu.au">Burnet Institute</a> and the <a href="http://www.worldbank.org">World Bank</a>, under the auspices of the <a href="http://www.ocds.co">Optima Consortium for Decision Science</a>.</p>

    <p>Technical information:</p>

    <div class="divTable">
      <div class="divTableBody">
        <div class="divTableRow">
          <div class="divRowLabel">Version </div>
          <div class="divRowContent">{{ version }}</div>
        </div>
        <div class="divTableRow">
          <div class="divRowLabel">Date </div>
          <div class="divRowContent">{{ date }}</div>
        </div>
        <div class="divTableRow">
          <div class="divRowLabel">Branch </div>
          <div class="divRowContent">{{ gitbranch }}</div>
        </div>
        <div class="divTableRow">
          <div class="divRowLabel">Hash </div>
          <div class="divRowContent">{{ githash }}</div>
        </div>
        <div class="divTableRow">
          <div class="divRowLabel">Timestamp </div>
          <div class="divRowContent">{{ gitdate }}</div>
        </div>
      </div>
    </div>
      <!--<button @click="getVersionInfo">Update</button>-->
      <br/>
      <br/>
      <div class="divTable" style="width:100%">
        <div class="divTableBody">
          <div class="divTableRow">
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/burnet-logo-transparent.png" height="60px"></div>
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/world-bank-logo.png" height="60px"></div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>


<script>
  import rpcs from '@/services/rpc-service'
  import router from '@/router'

  export default {
    name: 'About',

    data () {
      return {
        version: '',
        date: '',
        gitbranch: '',
        githash: '',
        gitdate: '',
      }
    },

    computed: {
      getVersionInfo() {
        rpcs.rpc('get_version_info')
          .then(response => {
            this.version = response.data['version'];
            this.date = response.data['date'];
            this.gitbranch = response.data['gitbranch'];
            this.githash = response.data['githash'];
            this.gitdate = response.data['gitdate'];
          })
      },
    },
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
