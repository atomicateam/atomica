<!--
HelpLink component

Last update: 2018-08-23
-->

<template>
  <div>
    <h4>{{ label }}
      <button class="btn __blue small-button" @click="openLink(reflink)" data-tooltip="Help" style="padding-top:2px; margin-bottom:5px">
        <i class="ti-help"></i>
      </button>
      <!--<span @click="openLink(reflink)">-->
        <!--<i class="ti-help-alt"  style="margin-left: 0.5em; color: #29abe2; font-size: 30px; font-weight:bold"></i>-->
      <!--</span>-->
    </h4>
  </div>
</template>

<script>
  export default {
    name: 'help',
    
    props: {
      reflink: {
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
          'create-frameworks': 'h.8xzemda17sn7',
          'manage-frameworks': 'h.kjfpissnw4v8',
          'create-projects': 'h.wohgolfxe9ko', 
          'manage-projects': 'h.fcnvzbrouon2',
          'bl-overview': 'h.e5er3h94vkjk',
          'parameter-sets': 'h.ofwmxbimr7i',
          'automatic-calibration': 'h.81g1j4y0hcp1',
          'manual-calibration': 'h.da77fbanyz1n',
          'reconciliation': 'h.ojtskhsm6lx9',
          'bl-results': 'h.f2xv432x5yv',
          'define-scenarios': 'h.6u9a8cixezwv',
          'sc-results': 'h.syuxr0k2n3yy',
          'define-optimizations': 'h.9g4agtbijsjq',
          'op-results': 'h.n581zreqeowi'
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
