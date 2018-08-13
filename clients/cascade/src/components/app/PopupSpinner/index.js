// index.js -- index JavaScript file for PopupSpinner plugin
//
// Last update: 2018-08-12

// The Vue component for the actual modal dialog spinner.
import PopupSpinner from './PopupSpinner.vue'

const SpinnerPlugin = {
  install(Vue) {
    // Make sure that plugin can be installed only once
    if (this.installed) {
      return
    }
    this.installed = true
    
    // Create the event bus which allows plugin calls to talk to the 
    // PopupSpinner object through events.
    this.eventBus = new Vue()

    // Create the global $spinner functions the user can call 
    // from inside any component.
    Vue.prototype.$spinner = {
      start() {
        // Send a start event to the bus.
        SpinnerPlugin.eventBus.$emit('start')
      }, 
  
      stop() {
        // Send a stop event to the bus.
        SpinnerPlugin.eventBus.$emit('stop')
      }
    }
    
    // Load the PopupSpinner component so it can be used in the pages.
    Vue.component('PopupSpinner', PopupSpinner)
  }
}

export default SpinnerPlugin