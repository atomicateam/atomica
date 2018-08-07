// progress-indicator-service.js -- functions for showing progress
//
// Last update: 7/28/18 (gchadder3)

// Note: To use these functions, you need to pass in the Vue instance, this. 
// Also, the caller needs to have imported the Spinner.vue PopupSpinner 
// component and instantiated it.

function start(vueInstance) {
  console.log('Starting progress')
  vueInstance.$modal.show('popup-spinner') // Bring up a spinner.
  vueInstance.$Progress.start() // Start the loading bar.
}

function succeed(vueInstance, successMessage) {
  console.log(successMessage)
  vueInstance.$modal.hide('popup-spinner') // Dispel the spinner.
  vueInstance.$Progress.finish()   // Finish the loading bar.
  if (successMessage != '') { // Success popup.
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
  console.log(failMessage)
  vueInstance.$modal.hide('popup-spinner') // Dispel the spinner.
  vueInstance.$Progress.fail() // Fail the loading bar.
  if (failMessage != '') {  // Put up a failure notification.
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