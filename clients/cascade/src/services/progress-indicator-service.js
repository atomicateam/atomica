// progress-indicator-service.js -- functions for showing progress
//
// Last update: 7/28/18 (gchadder3)

// Note: To use these functions, you need to pass in the Vue instance, this. 
// Also, the caller needs to have imported the Spinner.vue PopupSpinner 
// component and instantiated it.

function start(vueInstance) {
  // Bring up a spinner.
  vueInstance.$modal.show('popup-spinner')

  // Start the loading bar.
  vueInstance.$Progress.start()         
}

function succeed(vueInstance, successMessage) {
  // Dispel the spinner.
  vueInstance.$modal.hide('popup-spinner')

  // Finish the loading bar.
  vueInstance.$Progress.finish()
      
  // Success popup.
  if (successMessage != '') {
    vueInstance.$notifications.notify({
      message: successMessage,
      icon: 'ti-check',
      type: 'success',
      verticalAlign: 'top',
      horizontalAlign: 'center'
    })
  }  
}

function fail(vueInstance, failMessage) {
  // Dispel the spinner.
  vueInstance.$modal.hide('popup-spinner')

  // Fail the loading bar.
  vueInstance.$Progress.fail()

  // Put up a failure notification.
  if (failMessage != '') {  
    vueInstance.$notifications.notify({
      message: failMessage,
      icon: 'ti-face-sad',
      type: 'warning',
      verticalAlign: 'top',
      horizontalAlign: 'center'
    })
  }  
}

function successPopup(vueInstance, successMessage) {
  // Success popup.
  vueInstance.$notifications.notify({
    message: successMessage,
    icon: 'ti-check',
    type: 'success',
    verticalAlign: 'top',
    horizontalAlign: 'center'
  })        
}

function failurePopup(vueInstance, failMessage) {
  // Put up a failure notification.
  vueInstance.$notifications.notify({
    message: failMessage,
    icon: 'ti-face-sad',
    type: 'warning',
    verticalAlign: 'top',
    horizontalAlign: 'center'
  })         
}

export default {
  start,
  succeed,
  fail,
  successPopup,
  failurePopup
}