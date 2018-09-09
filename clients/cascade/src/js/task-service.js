// task-service.js -- task queuing functions for Vue to call
//
// Last update: 8/18/18 (gchadder3)

import rpcs from '@/services/rpc-service'
import utils from '@/services/utils'

// getTaskResultWaiting() -- given a task_id string, a waiting time (in 
// sec.), and a remote task function name and its args, try to launch 
// the task, then wait for the waiting time, then try to get the 
// result.
function getTaskResultWaiting(task_id, waitingtime, func_name, args, kwargs) {
  if (!args) { // Set the arguments to an empty list if none are passed in.
    args = []
  }
  return new Promise((resolve, reject) => {
    rpcs.rpc('launch_task', [task_id, func_name, args, kwargs]) // Launch the task.
    .then(response => {
      utils.sleep(waitingtime * 1000) // Sleep waitingtime seconds.
      .then(response2 => {
        rpcs.rpc('get_task_result', [task_id]) // Get the result of the task.
        .then(response3 => {
          rpcs.rpc('delete_task', [task_id]) // Clean up the task_id task.
          resolve(response3) // Signal success with the result response.
        })
        .catch(error => {
          // While we might want to clean up the task as below, the Celery
          // worker is likely to "resurrect" the task if it actually is
          // running the task to completion.
          // Clean up the task_id task.
          // rpcCall('delete_task', [task_id])
          reject(error) // Reject with the error the task result get attempt gave.
        })
      })
    })
    .catch(error => {
      reject(error) // Reject with the error the launch gave.
    })
  })
}

// getTaskResultPolling() -- given a task_id string, a timeout time (in 
// sec.), a polling interval (also in sec.), and a remote task function name
//  and its args, try to launch the task, then start the polling if this is 
// successful, returning the ultimate results of the polling process. 
function getTaskResultPolling(task_id, timeout, pollinterval, func_name, args, kwargs) {
  if (!args) { // Set the arguments to an empty list if none are passed in.
    args = []
  }
  return new Promise((resolve, reject) => {
    rpcs.rpc('launch_task', [task_id, func_name, args, kwargs]) // Launch the task.
    .then(response => {
      pollStep(task_id, timeout, pollinterval, 0) // Do the whole sequence of polling steps, starting with the first (recursive) call.
      .then(response2 => {
        resolve(response2) // Resolve with the final polling result.
      })
      .catch(error => {
        reject(error) // Reject with the error the polling gave.
      })
    })
    .catch(error => {
      reject(error) // Reject with the error the launch gave.
    })
  })
}

// pollStep() -- A polling step for getTaskResultPolling().  Uses the task_id, 
// a timeout value (in sec.) a poll interval (in sec.) and the time elapsed 
// since the start of the entire polling process.  If timeout is zero or 
// negative, no timeout check is applied.  Otherwise, an error will be 
// returned if the polling has gone on beyond the timeout period.  Otherwise, 
// this function does a sleep() and then a check_task().  If the task is 
// completed, it will get the result.  Otherwise, it will recursively spawn 
// another pollStep().
function pollStep(task_id, timeout, pollinterval, elapsedtime) {
  return new Promise((resolve, reject) => {
    if ((elapsedtime > timeout) && (timeout > 0)) { // Check to see if the elapsed time is longer than the timeout (and we have a timeout we actually want to check against) and if so, fail.
      reject(Error('Task polling timed out'))
    } else { // Otherwise, we've not run out of time yet, so do a polling step.
      utils.sleep(pollinterval * 1000) // Sleep timeout seconds.
      .then(response => {
        rpcs.rpc('check_task', [task_id]) // Check the status of the task.
        .then(response2 => {
          if (response2.data.task.status == 'completed') { // If the task is completed...
            rpcs.rpc('get_task_result', [task_id]) // Get the result of the task.
            .then(response3 => {
              rpcs.rpc('delete_task', [task_id]) // Clean up the task_id task.
              resolve(response3) // Signal success with the response.
            })
            .catch(error => {
              reject(error) // Reject with the error the task result get attempt gave.
            })
          } else if (response2.data.task.status == 'error') {  // Otherwise, if the task ended in an error...
            reject(Error(response2.data.task.errorText)) // Reject with an error for the exception.
          } else { // Otherwise, do another poll step, passing in an incremented elapsed time.
            pollStep(task_id, timeout, pollinterval, elapsedtime + pollinterval)
            .then(response3 => {
              resolve(response3) // Resolve with the result of the next polling step (which may include subsequent (recursive) steps.
            })
          }
        })
      })
    }
  })
}

export default {
  getTaskResultWaiting,
  getTaskResultPolling
}