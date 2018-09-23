<!--
About page

Last update: 2018sep23
-->

<template>
  <div class="SitePage">
    <div style="max-width:800px; margin:auto" v-model="getVersionInfo">
      <div style="text-align:center;">
        <img v-if="$globaltool=='cascade'" src="static/img/cascade-logo-black.png" width="250px">
        <img v-if="$globaltool=='tb'"      src="static/img/optima-logo-tb.png"     width="250px">
      </div>
      <br/><br/>
      <p v-if="$globaltool=='cascade'">
        Development of Cascade Analysis Tools is supported through the
        <a href="https://www.ku.dk/english/">University of Copenhagen</a> under the auspices of the
        <a href="http://www.gatesfoundation.org">Bill and Melinda Gates Foundation</a>.
      </p>
      <p v-if="$globaltool=='tb'">
        Optima TB has been developed through a partnership
        between the <a href="http://www.burnet.edu.au">Burnet Institute</a> and the
        <a href="http://www.worldbank.org">World Bank</a>, under the auspices of the
        <a href="http://www.ocds.co">Optima Consortium for Decision Science</a>.
      </p>

      <br/>
      <br/>
      <div class="divTable" style="width:100%">
        <div class="divTableBody">
          <div v-if="$globaltool=='cascade'" class="divTableRow">
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/copenhagen-logo.png" height="60px"></div>
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/gatesfoundation-logo.png" height="60px"></div>
          </div>
          <div v-if="$globaltool=='tb'" class="divTableRow">
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/burnet-logo-transparent.png" height="60px"></div>
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/world-bank-logo.png" height="60px"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>