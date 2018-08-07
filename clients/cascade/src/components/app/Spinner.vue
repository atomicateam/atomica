<!--Based on MoonLoader.vue -->

<template>
  <modal name="popup-spinner"
         height="85px"
         width="80px"
         style="opacity: 1.0" 
         :click-to-close="false" 
         @before-open="beforeOpen" 
         @before-close="beforeClose">
    <div class="v-spinner" v-show="loading" style="padding: 15px; opacity:1.0">  <!--WARNING, opacity command doesn't work here-->
      <div class="v-moon v-moon1" v-bind:style="spinnerStyle">
        <div class="v-moon v-moon2" v-bind:style="[spinnerMoonStyle,animationStyle2]">
        </div>
        <div class="v-moon v-moon3" v-bind:style="[spinnerStyle,animationStyle3]">
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
  export default {
    name: 'PopupSpinner',
    
    props: {
      loading: {
        type: Boolean,
        default: true
      },
      color: {
        type: String,
        default: '#0000ff'
      },
      size: {
        type: String,
        default: '50px'
      },
      margin: {
        type: String,
        default: '2px'
      },
      radius: {
        type: String,
        default: '100%'
      }
    },
    
    data() {
      return {
        spinnerStyle: {
          height: this.size,
          width: this.size,
          borderRadius: this.radius
        }, 
        opened: false
      }
    },
    
    computed: {
      moonSize() {
        return parseFloat(this.size)/7
      },
      
      spinnerMoonStyle () {
        return {
          height: this.moonSize  + 'px',
          width: this.moonSize  + 'px',
          borderRadius: this.radius
        }
      },
      
      animationStyle2 () {
        return {
          top: parseFloat(this.size)/2 - this.moonSize/2 + 'px',
          backgroundColor: this.color
        }
      },
      
      animationStyle3 () {
        return {
          border: this.moonSize + 'px solid ' + this.color
        }
      }
    }, 
    
    methods: {
      beforeOpen() {
        window.addEventListener('keyup', this.onKey)
        this.opened = true
      }, 
      
      beforeClose() {
        window.removeEventListener('keyup', this.onKey)
        this.opened = false
      }, 
      
      onKey(event) {
        if (event.keyCode == 27) {
          console.log('Exited spinner through Esc key')
          this.$emit('spinner-cancel')
          this.$modal.hide('popup-spinner') // Dispel the spinner.
        }
      }
    }

  }
</script>

<style>

  .v-spinner .v-moon1
  {

    -webkit-animation: v-moonStretchDelay 0.6s 0s infinite linear;
    animation: v-moonStretchDelay 0.6s 0s infinite linear;
    -webkit-animation-fill-mode: forwards;
    animation-fill-mode: forwards;
    position: relative;
  }

  .v-spinner .v-moon2
  {
    -webkit-animation: v-moonStretchDelay 0.6s 0s infinite linear;
    animation: v-moonStretchDelay 0.6s 0s infinite linear;
    -webkit-animation-fill-mode: forwards;
    animation-fill-mode: forwards;
    opacity: 0.9;
    position: absolute;
  }

  .v-spinner .v-moon3
  {
    opacity: 0.1;
  }

  @-webkit-keyframes v-moonStretchDelay
  {
    100%
    {
      -webkit-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }

  @keyframes v-moonStretchDelay
  {
    100%
    {
      -webkit-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }

   .vue-dialog div {
     box-sizing: border-box;
   }
  .vue-dialog .dialog-flex {
    width: 100%;
    height: 100%;
  }
  .vue-dialog .dialog-content {
    flex: 1 0 auto;
    width: 100%;
    padding: 15px;
    font-size: 14px;
  }
  .vue-dialog .dialog-c-title {
    font-weight: 600;
    padding-bottom: 15px;
  }
  .vue-dialog .dialog-c-text {
  }
  .vue-dialog .vue-dialog-buttons {
    display: flex;
    flex: 0 1 auto;
    width: 100%;
    border-top: 1px solid #eee;
  }
  .vue-dialog .vue-dialog-buttons-none {
    width: 100%;
    padding-bottom: 15px;
  }
  .vue-dialog-button {
    font-size: 12px !important;
    background: transparent;
    padding: 0;
    margin: 0;
    border: 0;
    cursor: pointer;
    box-sizing: border-box;
    line-height: 40px;
    height: 40px;
    color: inherit;
    font: inherit;
    outline: none;
  }
  .vue-dialog-button:hover {
    background: rgba(0, 0, 0, 0.01);
  }
  .vue-dialog-button:active {
    background: rgba(0, 0, 0, 0.025);
  }
  .vue-dialog-button:not(:first-of-type) {
    border-left: 1px solid #eee;
  }

</style>