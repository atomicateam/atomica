<!--
Footer for content pages

Last update: 2018sep22
-->

<template>
  <footer class="footer">
    <div class="container-fluid">
      <div v-if="$globaltool=='cascade'" class="copyright pull-center">
        &copy; 2018 by the <a href="http://cascade.tools" target="_blank">Cascade Analysis Working Group</a>
      </div>
    </div>
    <div v-if="$globaltool=='tb'" class="copyright pull-center">
      &copy; 2018 by the <a href="http://ocds.co" target="_blank">Optima TB Working Group</a>. <a href="http://ocds.co/home/legal.html" target="_blank">Terms and conditions</a>
    </div>
  </footer>
</template>