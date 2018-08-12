// index.js -- index JavaScript file for PopupSpinner plugin

import PopupSpinner from './PopupSpinner.vue'

const SpinnerPlugin = {
  install(Vue) {
    // Make sure that plugin can be insstalled only once
    if (this.installed) {
      return
    }
    this.installed = true
    
    // Create the event bus which allows plugin calls to talk to the 
    // PopupSpinner object through events.
    this.eventBus = new Vue()

    // Create the global $spinner functions the user can call 
    // from any component.
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