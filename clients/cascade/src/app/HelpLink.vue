<!--
HelpLink component

Last update: 2018-08-23
-->

<template>
  <button class="btn" @click="openThang('https://docs.google.com/document/d/1x4Kb3hyB8NwVziE95UhT6bXpO1uRDFxJlN8QxvrLgvg/edit#heading=h.wohgolfxe9ko')">Create projects</button>
</template>

<script>
  export default {
    name: 'HelpLink',

    data() {
      return {
        xxx: '',
      }
    },

    methods: {
      openThang(thangLink) {
        let scrh = screen.height
        let scrw = screen.width
        let h = scrh * 0.8  // Height of window
        let w = scrw * 0.6  // Width of window
        let t = scrh * 0.1  // Position from top of screen -- centered
        let l = scrw * 0.37 // Position from left of screen -- almost all the way right      
        let newWindow = window.open(thangLink, 
          'Reference manual', 'width=' + w + ', height=' + h + ', top=' + t + ',left=' + l)
        if (window.focus) {
          newWindow.focus()
        }        
      }
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
