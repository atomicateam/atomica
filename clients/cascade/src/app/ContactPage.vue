<!--
Contact page

Last update: 2018sep09
-->

<template>
  <div class="SitePage">
  	<p v-if="$globaltool=='cascade'">You can reach us at <a href="mailto:info@cascade.tools">info@cascade.tools</a>.</p>
    <p v-if="$globaltool=='tb'">     You can reach us at <a href="mailto:info@ocds.co">info@ocds.co</a>.</p>
  </div>
</template>