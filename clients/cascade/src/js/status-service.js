// progress-indicator-service.js -- functions for showing progress
//
// Last update: 8/12/18 (gchadder3)

// Note: To use these functions, you need to pass in the Vue instance, this. 
// Also, the caller needs to have imported the Spinner.vue PopupSpinner 
// component and instantiated it.

var complete = 0.0; // Put this here so it's global

function start(vm, message) {
  if (!message) { message = 'Starting progress' }
  var delay = 100;
  var stepsize = 1.0;
  complete = 0.0; // Reset this
  console.log(message)
  setTimeout(function run() { // Run in a delay loop
    setFunc();
    if (complete<99) {
      setTimeout(run, delay);
    }
  }, delay);
  function setFunc() {
    complete = complete + stepsize*(1-complete/100); // Increase asymptotically
    vm.$Progress.set(complete)
  }
  vm.$spinner.start() // Bring up a spinner.
}

function succeed(vm, successMessage) {
  console.log(successMessage)
  complete = 100; // End the counter
  vm.$spinner.stop() // Dispel the spinner.
  vm.$Progress.finish()   // Finish the loading bar -- redundant?
  if (successMessage !== '') { // Success popup.
    vm.$notifications.notify({
      message: successMessage,
      icon: 'ti-check',
      type: 'success',
      verticalAlign: 'top',
      horizontalAlign: 'right',
      timeout: 2000
    })
  }  
}

function fail(vm, failMessage, error) {
  console.log(failMessage)
  var msgsplit = error.message.split('Exception details:') // WARNING, must match sc_app.py
  var usermsg = msgsplit[0].replace(/\n/g,'<br>')
  console.log(error.message)
  console.log(usermsg)
  complete = 100;
  vm.$spinner.stop() // Dispel the spinner.
  vm.$Progress.fail() // Fail the loading bar.
  if (failMessage !== '') {  // Put up a failure notification.
    vm.$notifications.notify({
      message: '<b>' + failMessage + '</b>' + '<br><br>' + usermsg,
      icon: 'ti-face-sad',
      type: 'warning',
      verticalAlign: 'top',
      horizontalAlign: 'right',
      timeout: 0
    })
  }  
}

export default {
  start,
  succeed,
  fail,
}