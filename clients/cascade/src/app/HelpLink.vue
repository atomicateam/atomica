<!--
HelpLink component

Last update: 2018-08-23
-->

<template>
  <div>
    <p>
      {{ label }} 
      <span @click="openLink(ref)">
        <i class="fas fa-book"  style="{ margin-left: 0.5em; color: #29abe2; font-size: 14px }"></i>
      </span>
    </p>
  </div>
</template>

<script>
  export default {
    name: 'HelpLink',
    
    props: {
      ref: {
        type: String,
        default: 'create-projects'
      }, 

      label: {
        type: String,
        default: 'Create projects'        
      }        
    },

    data() {
      return {
        baseURL: 'https://docs.google.com/document/d/1x4Kb3hyB8NwVziE95UhT6bXpO1uRDFxJlN8QxvrLgvg/edit#heading=', 
        linkMap: {
          'create-projects': 'h.wohgolfxe9ko'
        }
      }
    },

    methods: {
      openLink(linkKey) {
        // Build the full link from the base URL and the specific link info.
        let fullLink = this.baseURL + this.linkMap[linkKey]
        
        // Set the parameters for a new browser window.
        let scrh = screen.height
        let scrw = screen.width
        let h = scrh * 0.8  // Height of window
        let w = scrw * 0.6  // Width of window
        let t = scrh * 0.1  // Position from top of screen -- centered
        let l = scrw * 0.37 // Position from left of screen -- almost all the way right

        // Open a new browser window.        
        let newWindow = window.open(fullLink, 
          'Reference manual', 'width=' + w + ', height=' + h + ', top=' + t + ',left=' + l)
          
        // If the main browser window is in focus, cause the new window to come into focus.
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
